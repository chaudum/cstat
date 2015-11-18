# -*- coding: utf-8; -*-
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
from colorama import Fore, Back, Style
from crate.client import connect
from .widgets import HorizontalGraphWidget


class GraphModel(object):

    QUERY = """SELECT id,
                      name,
                      hostname,
                      os['cpu'] as cpu_usage,
                      process['cpu']['percent'] as process_cpu,
                      load,
                      load['1'] / os_info['available_processors'] as load_rel,
                      heap['max'] as heap,
                      heap['used'] * 100.0 / heap['max'] as heap_usage,
                      mem['free'] + mem['used'] as memory,
                      mem['used'] * 100.0 / (mem['free'] + mem['used']) as memory_usage
               FROM sys.nodes
               ORDER BY name"""

    def __init__(self, hosts=[]):
        self.hosts = hosts
        self.cursor = connect(self.hosts).cursor()
        self.http = urllib3.PoolManager(3)
        self._cluster_info = None

    def sql(self, query, args=[]):
        self.cursor.execute(query, args)
        return (self.cursor.fetchall(), [c[0] for c in self.cursor.description])

    def refresh(self):
        rows, cols = self.sql(self.QUERY)
        return self.preprocess(rows, cols)

    def preprocess(self, rows=[], cols=[]):
        data = []
        for row in rows:
            data.append(dict(list(zip(cols, row))))
        return data

    def cluster_info(self):
        if not self._cluster_info:
            response = self.http.request('GET', self.hosts[0])
            self._cluster_info = response.status == 200 \
                and json.loads(response.data.decode('utf-8')) \
                or None
        return self._cluster_info


class MainWindow(urwid.WidgetWrap):

    PALETTE = [
        ('inverted', 'black', 'white'),
        ('green', 'black', 'dark green'),
        ('yellow', 'black', 'yellow'),
        ('red', 'white', 'dark red'),
        ('text_green', 'dark green', 'default'),
        ('text_yellow', 'yellow', 'default'),
        ('text_red', 'dark red', 'default'),
        ('progress_bg', 'white', 'dark gray'),
        ('progress_fg', 'black', 'yellow'),
    ]

    def __init__(self, controller):
        self.controller = controller
        self.frame = self.layout()
        super(MainWindow, self).__init__(self.frame)

    def layout(self):
        self.cpu_widget = HorizontalGraphWidget('[1] CPU Usage', 0.0)
        self.process_widget = HorizontalGraphWidget('[2] Crate CPU Usage', 0.0)
        self.memory_widget = HorizontalGraphWidget('[3] Memory Usage', 0.0)
        self.heap_widget = HorizontalGraphWidget('[4] Heap Usage', 0.0)
        self.debug = urwid.Text('')
        self.body = urwid.Pile([
            urwid.Divider(),
            self.cpu_widget,
            self.process_widget,
            self.memory_widget,
            self.heap_widget,
            urwid.Divider(),
        ])
        self.t_cluster_name = urwid.Text(b'-', align='center')
        self.t_version = urwid.Text(b'-', align='center')
        self.t_load = urwid.Text(b'-/-/-', align='right')
        self.t_hosts = urwid.Text(b'')
        self.update_header(None)
        return urwid.Frame(urwid.Filler(self.body, valign='top'),
                           header=urwid.Columns([
                               urwid.Text(b'CrateTop v0.1'),
                               self.t_cluster_name,
                               self.t_version,
                               self.t_load,
                            ]),
                           footer=urwid.Columns([self.t_hosts]))

    def update(self, data):
        cpu_percent = []
        process_cpu = []
        heap_percent = []
        heap_total = []
        memory_percent = []
        memory_total = []
        load = [0.0, 0.0, 0.0]
        num = float(len(data))
        for node in data:
            self.debug.set_text([('red', json.dumps(node))])
            cpu_percent.append(node['cpu_usage']['used'])
            process_cpu.append(node['process_cpu'])
            heap_percent.append(node['heap_usage'])
            heap_total.append(node['heap'])
            memory_percent.append(node['memory_usage'])
            memory_total.append(node['memory'])
            for idx, k in enumerate(['1', '5', '15']):
                load[idx] += node['load'][k] / num
        self.cpu_widget.set_data(cpu_percent)
        self.process_widget.set_data(process_cpu)
        self.heap_widget.set_data(heap_percent)
        self.heap_widget.update_title(sum(heap_total)/math.pow(1024.0,3))
        self.memory_widget.set_data(memory_percent)
        self.memory_widget.update_title(sum(memory_total)/math.pow(1024.0,3))
        self.t_load.set_text('Load: {0:.2f}/{1:.2f}/{2:.2f}'.format(*load))

    def update_header(self, info=None):
        if info is None:
            self.t_cluster_name.set_text(["Cluster Name: ", ('red', '---')])
            self.t_version.set_text(["Version: ", ('red', '---')])
        else:
            self.t_cluster_name.set_text([
                "Cluster Name: ",
                ('inverted', info['cluster_name']),
            ])
            self.t_version.set_text([
                "Version: ",
                ('inverted', info['version']['number']),
            ])

    def update_footer(self, hosts):
        self.t_hosts.set_text(['Connected to: ', ('inverted', ' '.join(hosts))])


class CrateTop(object):

    REFRESH_INTERVAL = 2.0

    def __init__(self, hosts=[]):
        self.model = GraphModel(hosts)
        self.view = MainWindow(self)
        self.view.update_footer(hosts)

    def __call__(self):
        self.loop = urwid.MainLoop(self.view,
                                   self.view.PALETTE,
                                   unhandled_input=self.handle_input)
        self.loop.set_alarm_in(0.1, self.fetch_initial)
        self.loop.set_alarm_in(0.1, self.fetch)
        self.loop.run()

    def __enter__(self):
        return self

    def __exit__(self, ex, msg, trace):
        msg = 'Thanks for using CrateTop!\n' \
              'Please send feedback to christian.haudum@crate.io'
        print(Fore.YELLOW + msg + Style.RESET_ALL)

    def handle_input(self, key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif key == '1':
            self.view.cpu_widget.toggle_details()
        elif key == '2':
            self.view.process_widget.toggle_details()
        elif key == '3':
            self.view.memory_widget.toggle_details()
        elif key == '4':
            self.view.heap_widget.toggle_details()

    def fetch_initial(self, loop, args):
        info = self.model.cluster_info()
        self.view.update_header(info)

    def fetch(self, loop, args):
        try:
            data = self.model.refresh()
        except Exception as e:
            pass
        else:
            self.view.update(data)
        loop.set_alarm_in(self.REFRESH_INTERVAL, self.fetch)


def splitter(input):
    return input.split(',')

def parse_cli():
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

