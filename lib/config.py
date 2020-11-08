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


from os.path import join
import click
import sys
import random

from lib.config_parser import DefaultConfigParser

DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0"


class Mutex(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if: list = kwargs.pop("not_required_if")

        assert self.not_required_if, "'not_required_if' parameter required"
        kwargs["help"] = (kwargs.get("help", "") + ", option is mutually exclusive with " +
                          ", ".join(self.not_required_if)).strip()
        super(Mutex, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        current_opt: bool = self.consume_value(ctx, opts)
        for other_param in ctx.command.get_params(ctx):
            if other_param is self:
                continue
            if other_param.human_readable_name in self.not_required_if:
                other_opt: bool = other_param.consume_value(ctx, opts)
                if other_opt:
                    if current_opt:
                        raise click.UsageError(
                            "Illegal usage: '" + str(self.name)
                            + "' is mutually exclusive with "
                            + str(other_param.human_readable_name) + "."
                        )
                    else:
                        self.required = None
        return super(Mutex, self).handle_parse_result(ctx, opts, args)


class Config(object):
    def __init__(self, script_path):
        self.script_path = script_path
        config = DefaultConfigParser()
        config.read_file(open(join(self.script_path, "pidrila.cfg")))
        # General section
        self.chunk_size = config.safe_getint("general", "chunk_size", 65535)
        # self.autosave_logs = config.safe_getboolean("general", "autosave_logs", True) # To be implemented
        # Connection section
        self.follow_redirects = config.safe_getboolean("connection", "follow_redirects", False)
        self.giveup_timeout = config.safe_getint("connection", "giveup_timeout", 5)
        self.max_errors = config.safe_getint("connection", "max_errors", 5)
        self.max_retries = config.safe_getint("connection", "max_retries", 3)
        # CLI args
        arguments = self.parse_arguments(config)
        if not arguments:
            sys.exit(0)
        self.auth = arguments['auth']
        self.logs = arguments['logs']
        self.http_method = arguments['http_method']
        self.max_connections = arguments['max_connections']
        self.max_connections_per_host = arguments['max_connections_per_host']
        self.timeout = arguments['timeout']
        self.proxy = arguments['proxy']
        self.url = arguments['url']
        self.url_list = arguments['url_list']
        if self.url_list:
            self.url_list_name = arguments['url_list_name']
        self.pathlist = arguments['pathlist']
        if not arguments['user_agent']:
            if config.safe_getboolean("connection", "random_useragent", True):
                self.user_agent = self.pick_user_agent()
            else:
                self.user_agent = config.safe_get("connection", "useragent", DEFAULT_UA)
        else:
            self.user_agent = arguments['user_agent']

    def parse_arguments(self, config):
        @click.option(
            '--http-method',
            type=click.Choice(['head', 'get']),
            default="get",
            help="HTTP method: GET or HEAD",
            show_default=True
        )
        @click.option(
            '--logs', '-l',
            type=click.Path(exists=True, dir_okay=True, file_okay=False, writable=True),
            help="Destination directory for the logs",
            default=join(self.script_path, "logs")
        )
        @click.option(
            '--url', '-u',
            required=True,
            help="Target URL",
            cls=Mutex,
            not_required_if=['url_list']
        )
        @click.option(
            '--url-list', '-L',
            type=click.File('r'),
            help="Target URL list"
        )
        @click.option(
            '--pathlist', '-p',
            type=click.File('r'),
            help="Path list",
            default=join(self.script_path, "db", config.safe_get("general", "pathlist", "pathlist.txt"))
        )
        @click.option(
            '--proxy', '-p',
            help="Proxy address, like socks5h://127.0.0.1:9050",
            default=config.safe_get("connection", "proxy", None)
        )
        @click.option(
            '--max-connections', '-m',
            default=config.safe_getint("connection", "max_connections", 128),
            help="How many simultaneous connections should we open",
            show_default=True
        )
        @click.option(
            '--max-connections-per-host', '-M',
            default=config.safe_getint("connection", "max_connections_per_host", 16),
            help="How many simultaneous connections should we open (per each host)",
            show_default=True
        )
        @click.option(
            '--auth', '-A',
            help="Basic HTTP auth, i.e. login:password",
            callback=self.get_logpass
        )
        @click.option(
            '--timeout', '-t',
            default=config.safe_getint("connection", "timeout", 30),
            help="Request timeout",
            show_default=True
        )
        @click.option(
            '--user-agent', '-U',
            help="User-Agent"
        )
        @click.command()
        def _parse_arguments(**kwargs):
            kwargs['pathlist'] = tuple((x.rstrip() for x in kwargs['pathlist'].readlines()))
            if kwargs['url_list']:
                kwargs['url_list_name'] = kwargs['url_list'].name
                kwargs['url_list'] = tuple((x.rstrip() for x in kwargs['url_list'].readlines()))
            return kwargs

        try:
            return _parse_arguments(standalone_mode=False)
        except click.ClickException as e:
            e.show()
            sys.exit(-1)

    def pick_user_agent(self):
        lines = open(join(self.script_path, 'db', 'user-agents.txt')).read().splitlines()
        ua = random.choice(lines)
        return ua.strip()

    @staticmethod
    def get_logpass(ctx, param, value):
        if value is not None and ":" in value:
            return value.split(":")
