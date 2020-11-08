#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This project is libre, and licenced under the terms of the
# DO WHAT THE FUCK YOU WANT TO PUBLIC LICENCE, version 3.1,
# as published by dtf on July 2019. See the COPYING file or
# https://ph.dtf.wtf/w/wtfpl/#version-3-1 for more details.
#
#  Author: Enemy Submarine

import os
import sys

if sys.version_info < (3, 0):
    sys.stdout.write("Sorry, PIDRILA requires Python 3.x\n")
    sys.exit(1)

from lib import Config, Controller


class Pidrila(object):
    def __init__(self):
        self.script_path = os.path.dirname(os.path.realpath(__file__))
        self.arguments = Config(self.script_path)
        self.controller = Controller(self.script_path, self.arguments)


if __name__ == "__main__":
    main = Pidrila()
