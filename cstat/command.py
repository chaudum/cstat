# vi: set encoding=utf-8
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

import os
import sys
import urwid
import asyncio
import traceback
from distutils.version import StrictVersion
from urwid.raw_display import Screen
from .connector import DataProvider, pool, toggle_stats
from .window import MainWindow
from .log import get_logger

logger = get_logger(__name__)


PALETTE = [
    ('active', 'black, bold', 'dark cyan'),
    ('inactive', 'light gray', 'default'),
    ('menu', 'light gray', 'dark gray'),
    ('inverted', 'black, bold', 'light gray'),
    ('headline', 'default, bold', 'default'),
    ('bg_green', 'black', 'dark green'),
    ('bg_yellow', 'black', 'brown'),
    ('bg_red', 'black', 'dark red'),
    ('text_green', 'dark green', 'default'),
    ('text_yellow', 'yellow', 'default'),
    ('text_red', 'dark red, bold', 'default'),
    ('tx', 'dark cyan', 'default'),
    ('rx', 'dark magenta', 'default'),
    ('head', 'black, bold', 'dark cyan'),
]


class ResultConsumer:

    def __init__(self, on_result=lambda x: x, on_failure=lambda x: x):
        self._apply_result = on_result
        self._apply_failure = on_failure

    def apply(self, result=None, failure=None):
        if result is not None:
            self._apply_result(result)
        if failure is not None:
            self._apply_failure(failure)


class CrateStat:

    def __init__(self, args):
        self._args = args
        self.pool = None
        self.loop = None
        self.exit_message = None
        self.view = None

    def serve(self, aioloop):
        screen = Screen()
        screen.set_terminal_properties(256)
        self.view = MainWindow(self)
        self.loop = urwid.MainLoop(self.view, PALETTE,
                                   screen=screen,
                                   event_loop=urwid.AsyncioEventLoop(loop=aioloop),
                                   unhandled_input=self.on_input)
        task = asyncio.ensure_future(pool(self._args))
        task.add_done_callback(self.on_connect)
        self.loop.run()

    def on_connect(self, t):
        self.pool = t.result()
        consumer = ResultConsumer(on_result=self.on_data,
                                  on_failure=self.on_error)
        self.provider = DataProvider(self.pool,
                                     consumer,
                                     interval=self._args.interval)
        logger.debug('on_connect: %s %s %s',
                     self.pool, consumer, self.provider)

    def quit(self, msg=None):
        if msg:
            print(msg, file=sys.stderr)
        raise urwid.ExitMainLoop()

    def on_input(self, key):
        logger.debug('handle input: %s', key)
        if key in ('q', 'Q'):
            self.quit('Bye!')
        elif key == 'f3':
            current_value = self.provider['settings'][0].stats_enabled
            toggle_stats(current_value, self.pool, self.on_data)
        else:
            self.view.handle_input(key)

    def on_data(self, data):
        self.view.update(**data)

    def on_error(self, failure):
        self.quit(msg=str(failure))
