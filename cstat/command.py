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

import os
import sys
import urwid
import argparse
import traceback
from .models import GraphModel, NodesModel, JobsModel
from .window import MainWindow
from urwid.raw_display import Screen


__version__ = '0.1.0'

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


class CrateStat(object):
    """
    Main entry point of application
    """

    def __init__(self, interval, hosts=[]):
        self.screen = Screen()
        self.screen.set_terminal_properties(256)
        self.models = [
            GraphModel(hosts),
            NodesModel(hosts),
            JobsModel(hosts),
        ]
        # don't allow refresh intervals < 100ms
        self.refresh_interval = max(0.1, interval)
        self.view = MainWindow(self)
        self.view.update_footer(hosts)
        self.loop = None
        self.exit_message = None

    def main(self):
        if not self.fetch_initial():
            return self.quit('Could not connect to {0}'.format(self.models[0].hosts))
        self.loop = urwid.MainLoop(self.view, PALETTE,
                                   screen=self.screen,
                                   unhandled_input=self.handle_input)
        self.loop.set_alarm_in(0.1, self.fetch)
        self.loop.run()

    def __enter__(self):
        return self

    def __exit__(self, ex, msg, trace):
        if self.exit_message:
            print(self.exit_message, file=sys.stderr)
        elif ex:
            for line in traceback.format_tb(trace):
                print(line, file=sys.stderr)

    def quit(self, msg=None):
        self.exit_message = msg
        if self.loop:
            raise urwid.ExitMainLoop()
        return 1

    def handle_input(self, key):
        if key in ('q', 'Q'):
            self.quit()
        elif key == 'f1':
            self.models[2].toggle()
            self.view.set_logging_state(self.models[2].enabled)
        else:
            self.view.handle_input(key)

    def fetch_initial(self):
        try:
            info = self.models[0].refresh()
        except Exception as e:
            return False
        else:
            self.view.update(info=info)
            stats_enabled = self.models[2].get_initial_state()
            self.view.set_logging_state(stats_enabled)
        return True

    def fetch(self, loop, args):
        try:
            # todo: execute HTTP requests asynchronous
            info, nodes, jobs = [m.refresh() for m in self.models]
        except Exception as e:
            self.quit(e)
        else:
            self.view.update(info, nodes, jobs)
        loop.set_alarm_in(self.refresh_interval, self.fetch)


def parse_cli():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser('cstat',
                                     description='A visual stat tool for CrateDB clusters')
    parser.add_argument('--hosts', '--crate-hosts',
                        help='one or more CrateDB hosts to connect to',
                        type=str, nargs='+', metavar='HOST',
                        default=['localhost:4200'])
    parser.add_argument('--interval', '--refresh-interval',
                        help='amount of time in seconds between each update',
                        default=2,
                        type=float)
    parser.add_argument('--version', action='version', version=__version__)
    return parser.parse_args()


def main():
    """
    Instantiate CrateStat and run its main loop by calling the instance.
    """
    cla = parse_cli()
    with CrateStat(cla.interval, hosts=cla.hosts) as stat:
        stat.main()

