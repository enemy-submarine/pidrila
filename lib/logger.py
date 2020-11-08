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


import logging


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, pbar, level=logging.NOTSET):
        self.pbar = pbar
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            self.pbar.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def get_logger(logger_name, log_level, log_format="[%(asctime)s] %(levelname)s: %(module_name)s | %(message)s",
               handler=logging.StreamHandler()):
    log_level = logging.getLevelName(log_level)
    logformat = log_format
    extra = {'module_name': logger_name}
    logging.root.setLevel(log_level)
    formatter = logging.Formatter(logformat)
    stream = handler
    stream.setLevel(log_level)
    stream.setFormatter(formatter)
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    logger.addHandler(stream)
    logger = logging.LoggerAdapter(logger, extra)
    return logger
