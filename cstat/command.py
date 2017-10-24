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
import traceback
from .connector import DataProvider, toggle_stats, logging_state
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

    def __init__(self, screen, conn):
        self.screen = screen
        self.conn = conn
        self.loop = None
        self.exit_message = None
        self.provider = None
        self.view = None
        self.consumer = None

    def serve(self, interval=5):
        self.loop = urwid.MainLoop(self.view, PALETTE,
                                   screen=self.screen,
                                   unhandled_input=self.on_input)
        self.provider = DataProvider(self.conn,
                                     self.loop,
                                     self.consumer,
                                     interval=interval)
        self.loop.run()

    def __enter__(self):
        self.consumer = ResultConsumer(on_result=self.on_data,
                                       on_failure=self.on_error)
        self.view = MainWindow(self)
        self.view.update_footer(self.conn.client.active_servers)
        self.view.set_logging_state(logging_state(self.conn))
        return self

    def __exit__(self, ex, msg, trace):
        if self.exit_message:
            print(self.exit_message, file=sys.stderr)
        elif ex:
            for line in traceback.format_tb(trace):
                print(line, file=sys.stderr)

    def quit(self, msg=None):
        self.exit_message = msg
        raise urwid.ExitMainLoop()

    def on_input(self, key):
        logger.debug('handle input: %s', key)
        if key in ('q', 'Q'):
            self.quit('Bye!')
        elif key == 'f3':
            self.view.set_logging_state(toggle_stats(self.conn))
        else:
            self.view.handle_input(key)

    def on_data(self, data):
        self.view.update(**data)

    def on_error(self, failure):
        self.quit(msg=str(failure))
