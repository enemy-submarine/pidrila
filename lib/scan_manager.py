# -*- coding: utf-8 -*-
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#  Author: Enemy Submarine

import asyncio
import signal
from aiohttp import ClientSession, ClientTimeout, TCPConnector, client_exceptions
from aiohttp.helpers import BasicAuth
from aiohttp_socks import ProxyConnector
from lib.util import chunks, sizeof_fmt
from lib.logger import get_logger, TqdmLoggingHandler
from tqdm.asyncio import tqdm
from collections import defaultdict
import gc


class ScanManager:
    def __init__(self, config, targets):
        self.config = config
        self.targets = targets
        if self.config.url:
            total = len(self.config.pathlist)
        else:
            total = len(self.config.pathlist) * len(self.config.url_list)
        self.pbar = tqdm(total=total, ascii=True, position=0, leave=False, dynamic_ncols=True)
        self.logger = get_logger('SCAN', 'INFO', handler=TqdmLoggingHandler(self.pbar))
        self.scan_logger = get_logger('URL', 'INFO', log_format="[%(asctime)s] %(message)s",
                                      handler=TqdmLoggingHandler(self.pbar))
        self.sessions = []
        self.loop = asyncio.get_event_loop()
        self.loop.set_exception_handler(self.handle_exception)
        self.setup_sighandler()
        if not self.config.proxy:
            self.conn = TCPConnector(limit=self.config.max_connections,
                                     limit_per_host=self.config.max_connections_per_host,
                                     ttl_dns_cache=300)
        else:
            if self.config.proxy.startswith('socks5h'):
                proxy_addr = self.config.proxy.replace("socks5h", "socks5")
                self.conn = ProxyConnector.from_url(proxy_addr)
                self.conn._rdns = True
        self.tasks = defaultdict(list)
        self.sem = asyncio.Semaphore(self.config.max_connections)
        self.setup_sessions()
        self.running = asyncio.Event()
        self.running.set()

    def handle_exception(self, loop, context):
        msg = context.get("exception", context["message"])
        self.logger.error(f"Caught exception: {msg}")

    @staticmethod
    async def add_callback(fut, callback):
        try:
            result = await fut
            await callback(result)
            return result
        except asyncio.exceptions.CancelledError:
            # Ignore cancelled requests
            pass

    async def fetch_callback(self, task):
        self.pbar.update()
        target_id, result = task

        if not self.targets[target_id].is_running():
            return
        if not isinstance(result, Exception):
            return
        elif isinstance(result, (client_exceptions.ServerDisconnectedError, client_exceptions.ClientOSError)):
            self.logger.warning(f"Server dropped connection on target {self.targets[target_id].get_target_name()}")
        elif isinstance(result, asyncio.exceptions.TimeoutError):
            self.logger.warning(f"Timeout occured on target {self.targets[target_id].get_target_name()}")
        else:
            self.logger.warning(f"Error occured on target {target_id}: {str(result)}")

        self.targets[target_id].inc_error_counter()
        if self.targets[target_id].get_error_status():
            await self.block_target(target_id)

    async def block_target(self, target_id):
        self.running.clear()
        self.logger.warning(f"Giving up on target {self.targets[target_id].get_target_name()}")
        self.targets[target_id].stop()
        tasks = [t for t in self.tasks[target_id] if t is not asyncio.current_task()]
        task_cnt = len(tasks)
        self.logger.warning(f"Dropping {task_cnt} requests to target {self.targets[target_id].get_target_name()}")
        [t.cancel() for t in tasks]
        for t in tasks:
            await t
        self.pbar.update(task_cnt)
        self.running.set()

    async def fetch(self, target_id, url):
        retries = 0
        exception = None
        async with self.sem:
            while retries < self.config.max_retries:
                try:
                    if self.config.http_method == "head":
                        f = self.sessions[target_id % self.config.max_connections].head
                    else:
                        f = self.sessions[target_id % self.config.max_connections].get
                    await self.running.wait()
                    async with f(url, ssl=False, allow_redirects=self.config.follow_redirects) as response:
                        return target_id, response
                except Exception as e:
                    exception = e
                    retries += 1
                    continue
            return target_id, exception

    async def create_task_group(self, r):
        tasks = []
        for target_id, url in r:
            task = self.loop.create_task(self.add_callback(self.fetch(target_id, url), self.fetch_callback))
            self.tasks[target_id].append(task)
            tasks.append(task)
        return tasks

    async def process_task_group(self, tasks):
        for f in asyncio.as_completed(tasks):
            packed = await f
            if not packed:
                continue
            await self.handle_response(packed)

    def cleanup_task_group(self):
        for target_id in self.tasks.keys():
            self.tasks[target_id] = []
        gc.collect()

    def setup_sessions(self):
        for i in range(self.config.max_connections):
            if self.config.auth:
                auth = BasicAuth(login=self.config.auth[0], password=self.config.auth[1])
            else:
                auth = None
            session = ClientSession(connector=self.conn, headers={'User-Agent': self.config.user_agent},
                                    timeout=ClientTimeout(total=self.config.timeout),
                                    skip_auto_headers=['Accept-Encoding'],
                                    connector_owner=False, auth=auth)
            self.sessions.append(session)

    async def close_sessions(self):
        self.logger.info(f"Closing sessions")
        for session in self.sessions:
            await session.close()

    async def handle_response(self, packed):
        target_id, response = packed
        if response and not isinstance(response, Exception) and response.status != 404:
            content_length = response.content_length if response.content_length else 0
            if response.status in (301, 302):
                if 'Location' in response.headers:
                    url = str(response.url) + ' -> ' + response.headers['Location']
                else:
                    url = str(response.url)
            else:
                url = str(response.url)
            log_event = f'{str(response.status)} - {sizeof_fmt(content_length)}\t-\t{url}'
            self.scan_logger.info(log_event)
            self.targets[target_id].save_link(log_event + '\n')

    def run_loop(self):
        try:
            self.loop.run_until_complete(self.run())
            self.loop.close()
        except Exception as e:
            print(str(e))

    def generate_links(self):
        generators = [x.link_generator() for x in self.targets]
        for urls in zip(*generators):
            for url in urls:
                if url[1]:
                    yield url
                else:
                    self.pbar.update()  # count dropped requests

    async def run(self):
        for chunk in chunks(self.generate_links(), self.config.chunk_size):
            tasks = await self.create_task_group(chunk)
            await self.process_task_group(tasks)
            self.cleanup_task_group()
        await self.close_sessions()
        await self.conn.close()

    def setup_sighandler(self):
        signals = (signal.SIGHUP, signal.SIGTERM)
        for s in signals:
            self.loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(self.shutdown(s)))
        self.loop.add_signal_handler(signal.SIGINT, lambda s=signal.SIGINT: asyncio.create_task(self.interrupt_menu()))

    async def interrupt_menu(self):
        self.loop.remove_signal_handler(signal.SIGINT)  # second Ctrl-C would lead to exit
        self.running.clear()
        self.logger.warning('CTRL+C detected: Pausing PIDRILA...')
        try:
            while True:
                self.pbar.write('[e]xit / [c]ontinue: ')
                option = input()
                if option.lower() == 'e':
                    await self.shutdown(signal.SIGINT)
                    raise KeyboardInterrupt
                elif option.lower() == 'c':
                    self.logger.warning('Resuming PIDRILA...')
                    self.running.set()
                    self.loop.add_signal_handler(signal.SIGINT, lambda s=signal.SIGINT:
                                                 asyncio.create_task(self.interrupt_menu()))  # Restore handler
                    return
                else:
                    continue
        except KeyboardInterrupt:
            await self.shutdown(signal.SIGINT)
            raise KeyboardInterrupt

    async def shutdown(self, signal_evt):
        self.logger.warning(f'Received exit signal {signal_evt.name}...')
        tasks = [t for t in asyncio.all_tasks() if t is not
                 asyncio.current_task()]
        [task.cancel() for task in tasks]
        self.logger.info(f"Cancelling {len(tasks)}  requests")
        await asyncio.gather(*tasks)
        await self.close_sessions()
        self.logger.info(f"Flusing log files")
        for target in self.targets:
            if target.is_running():
                target.close_log()
        await asyncio.sleep(self.config.giveup_timeout)
        self.loop.stop()
