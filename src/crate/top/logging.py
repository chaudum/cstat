# -*- coding: utf-8; -*-
# vi: set encoding=utf-8
#
# Licensed to CRATE Technology GmbH ("Crate") under one or more contributor
# license agreements.  See the NOTICE file distributed with this work for
# additional information regarding copyright ownership.  Crate licenses
# this file to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  You may
# obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations
# under the License.
#
# However, if you have executed another commercial license agreement
# with Crate these terms will supersede the license and you may use the
# software solely pursuant to the terms of the relevant commercial agreement.

from __future__ import print_function

from os import path, mkdir
from datetime import datetime
from colorama import Fore, Style


class ColorLog(object):

    def __init__(self, name):
        self.name = name
        self.stream = open(path.join(self.logdir(), 'ctop.log'), 'a')

    def __del__(self):
        self.stream.close()

    def logdir(self):
        dir = path.expanduser(path.join('~', '.ctop'))
        if not path.exists(dir):
            mkdir(dir)
        return dir

    def _print(self, color, level, *args):
        msg = '[{0}]{4}[{1:<5}]{5}[{2:<20}] {3}'.format(
                datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'),
                level,
                self.name,
                ' '.join([str(x) for x in args]),
                color,
                Style.RESET_ALL,
                )
        print(msg, file=self.stream)
        self.stream.flush()

    def debug(self, *args):
        self._print(Fore.CYAN, 'DEBUG', *args)

    def info(self, *args):
        self._print(Fore.GREEN, 'INFO', *args)

    def warn(self, *args):
        self._print(Fore.YELLOW, 'WARN', *args)

    def error(self, *args):
        self._print(Fore.RED, 'ERROR', *args)

