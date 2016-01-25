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
import re
import sys
import json
import math
import urwid
import urllib3
import argparse
import traceback
from collections import namedtuple
from urllib3.exceptions import MaxRetryError
from crate.client import connect
from .logging import ColorLog
from .widgets import HorizontalGraphWidget
from .window import CrateTopWindow


LOGGER = ColorLog(__name__)


class GraphModel(object):

    QUERY = """SELECT id,
                      name,
                      hostname,
                      os['cpu'] as cpu,
                      process['cpu'] as process,
                      os_info['available_processors'] as cpus,
                      load,
                      heap,
                      mem
               FROM sys.nodes
               ORDER BY name"""

    def __init__(self, hosts=[]):
        self.hosts = hosts
        self.cursor = connect(self.hosts).cursor()
        self.http = urllib3.PoolManager(3)
        self._cluster_info = None

    def sql(self, query, args=[]):
        self.cursor.execute(query, args)
        Row = namedtuple('Row', [c[0] for c in self.cursor.description])
        return [Row(*r) for r in self.cursor.fetchall()]

    def refresh(self):
        return self.sql(self.QUERY)

    def cluster_info(self):
        if not self._cluster_info:
            response = self.http.request('GET', self.hosts[0])
            self._cluster_info = response.status == 200 \
                and json.loads(response.data.decode('utf-8')) \
                or None
        return self._cluster_info




class CrateTop(object):

    REFRESH_INTERVAL = 2.0

    def __init__(self, hosts=[]):
        self.model = GraphModel(hosts)
        self.view = CrateTopWindow(self)
        self.view.update_footer(hosts)
        self.loop = None
        self.exit_message = None

    def __call__(self):
        if not self.fetch_initial():
            return self.quit('Could not connect to {0}'.format(self.model.hosts))
        self.loop = urwid.MainLoop(self.view,
                                   self.view.PALETTE,
                                   unhandled_input=self.handle_input)
        self.loop.set_alarm_in(0.1, self.fetch)
        self.loop.run()

    def __enter__(self):
        return self

    def __exit__(self, ex, msg, trace):
        if self.exit_message:
            LOGGER.error(self.exit_message)
        elif ex:
            LOGGER.error(ex.__name__)
            for line in traceback.format_tb(trace):
                LOGGER.error(line.strip('\n'))
        else:
            msg = 'Thanks for using CrateTop!\n' \
                  'Please send feedback to christian.haudum@crate.io'
            print(msg, file=sys.stderr)

    def quit(self, msg=None):
        self.exit_message = msg
        if self.loop:
            raise urwid.ExitMainLoop()
        return 1

    def handle_input(self, key):
        if key in ('q', 'Q'):
            self.quit()
        else:
            self.view.handle_input(key)

    def fetch_initial(self):
        try:
            info = self.model.cluster_info()
            self.view.update_header(info)
        except MaxRetryError as e:
            return False
        return True

    def fetch(self, loop, args):
        try:
            data = self.model.refresh()
        except Exception as e:
            self.quit(e)
        else:
            self.view.update(data)
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

