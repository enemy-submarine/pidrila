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


from urllib.parse import urlparse
from datetime import datetime
from os.path import join


class ScanTarget:
    def __init__(self, target_id, target_url, config):
        self.target_id = target_id
        self.target_url = target_url
        self.config = config
        self.logfile = self.init_log()
        self.err_cnt = 0
        self.running = True

    def init_log(self):
        ts = datetime.strftime(datetime.now(), "%d-%m-%y_%H_%M")
        site_name = urlparse(self.target_url).netloc.replace(':', '_')
        file_name = f"{ts}_{site_name}.txt"
        return open(join(self.config.logs, file_name), "w")

    def save_link(self, event):
        self.logfile.write(event)

    def link_generator(self):
        for url in self.config.pathlist:
            if self.running:
                yield self.target_id, self.target_url + '/' + url
            else:
                yield self.target_id, None

    def close_log(self):
        self.logfile.flush()
        self.logfile.close()

    def inc_error_counter(self):
        self.err_cnt += 1
        return

    def get_error_status(self):
        if self.err_cnt > self.config.max_errors:
            return True
        return False

    def get_target_name(self):
        return urlparse(self.target_url).netloc

    def is_running(self):
        return self.running

    def stop(self):
        self.running = False
        self.close_log()
