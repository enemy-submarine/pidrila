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
import os

from lib.logger import get_logger
from lib.scan_manager import ScanManager
from lib.scan_target import ScanTarget
from lib.util import normalize_url

MAYOR_VERSION = 0
MINOR_VERSION = 1
REVISION = 0
VERSION = {
    "MAYOR_VERSION": MAYOR_VERSION,
    "MINOR_VERSION": MINOR_VERSION,
    "REVISION": REVISION
}


class Controller(object):
    def __init__(self, script_path, config):
        self.config = config
        self.logger = get_logger('MAIN', 'INFO')
        program_banner = open(os.path.join(script_path, "lib", "banner.txt")).read().format(
            **VERSION)

        print(program_banner)
        self.print_config()
        self.checker = ScanManager(self.config, self.prepare_targets())
        try:
            self.checker.run_loop()
        except (asyncio.exceptions.CancelledError, KeyboardInterrupt):
            self.logger.info(f'Scan cancelled by user')
        else:
            self.logger.info(f'Scan completed')

    def prepare_targets(self):
        if self.config.url:
            return [ScanTarget(0, normalize_url(self.config.url), self.config)]
        elif self.config.url_list:
            return [ScanTarget(i, normalize_url(url), self.config) for i, url in enumerate(self.config.url_list)]

    def print_config(self):
        self.logger.info('Initializing PIDRILA...')
        self.logger.info(f'User-Agent: {self.config.user_agent}')
        if self.config.url:
            self.logger.info(f'Target: {self.config.url}')
        else:
            self.logger.info(f'Target list: {self.config.url_list_name} ({len(self.config.url_list)} targets total)')
        self.logger.info(f'HTTP method: {self.config.http_method}')
        self.logger.info(f'Max connections: {self.config.max_connections}')
        self.logger.info(f'Max retries: {self.config.max_retries}')
        self.logger.info(f'Max errors per host: {self.config.max_errors}')
        self.logger.info(f'Word list size: {len(self.config.pathlist)}')
        self.logger.info(f'Requests group size: {self.config.chunk_size}')
        if self.config.url_list:
            self.logger.info(f'Requests total: {len(self.config.pathlist) * len(self.config.url_list)}')
        if self.config.proxy:
            self.logger.info(f'Using socks proxy: {self.config.proxy}')
        else:
            self.logger.info(f'Proxy: none')
