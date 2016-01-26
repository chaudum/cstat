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
from urllib3.exceptions import MaxRetryError
from .logging import ColorLog
from .models import GraphModel, NodesModel, JobsModel
from .widgets import HorizontalGraphWidget
from .window import CrateTopWindow


LOGGER = ColorLog(__name__)


class CrateTop(object):

    REFRESH_INTERVAL = 2.0

    def __init__(self, hosts=[]):
        self.models = [
            GraphModel(hosts),
            NodesModel(hosts),
            JobsModel(hosts),
        ]
        self.view = CrateTopWindow(self)
        self.view.update_footer(hosts)
        self.loop = None
        self.exit_message = None

    def __call__(self):
        if not self.fetch_initial():
            return self.quit('Could not connect to {0}'.format(self.models[0].hosts))
        self.loop = urwid.MainLoop(self.view,
                                   self.view.PALETTE,
                                   unhandled_input=self.handle_input)
        self.loop.set_alarm_in(0.1, self.fetch)
        self.loop.run()

    def __enter__(self):
        return self

    def __exit__(self, ex, msg, trace):
        if self.exit_message:
            print(self.exit_message, file=sys.stderr)
        elif ex:
            LOGGER.error(ex.__name__, msg)
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
            self.view.update(info=info)
            stats_enabled = self.models[2].enabled
            self.view.set_logging_state(stats_enabled)
        except MaxRetryError as e:
            return False
        return True

    def fetch(self, loop, args):
        try:
            # todo: make this multithreaded
            info, nodes, jobs = [m.refresh() for m in self.models]
        except Exception as e:
            self.quit(e)
        else:
            self.view.update(info, nodes, jobs)
        loop.set_alarm_in(self.REFRESH_INTERVAL, self.fetch)


def parse_cli():
    """
    Parse command line arguments
    """
    def splitter(input):
        return input.split(',')
    parser = argparse.ArgumentParser('CrateTop')
    parser.add_argument('--hosts', '--crate-hosts',
                        help='Comma separated list of Crate hosts to connect to.',
                        default='localhost:4200',
                        type=splitter)
    return parser.parse_args()


def main():
    """
    Instantiate CrateTop and run its main loop by calling the instance.
    """
    args = parse_cli()
    with CrateTop(args.hosts) as top:
        top()

