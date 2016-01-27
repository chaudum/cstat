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


import urwid
from .logging import ColorLog
from .widgets import (
    MultiBarWidget,
    HorizontalPercentBar,
    HorizontalBytesBar,
)


LOGGER = ColorLog(__name__)


class CrateTopWindow(urwid.WidgetWrap):

    PALETTE = [
        ('inverted', 'black, bold', 'white'),
        ('headline', 'default, bold', 'default'),
        ('health_green', 'black', 'dark green'),
        ('health_yellow', 'black', 'yellow'),
        ('health_red', 'white', 'dark red'),
        ('text_green', 'dark green', 'default'),
        ('text_yellow', 'yellow', 'default'),
        ('text_red', 'dark red', 'default'),
    ]

    def __init__(self, controller):
        self.controller = controller
        self.frame = self.layout()
        super(CrateTopWindow, self).__init__(self.frame)

    def layout(self):
        self.cpu_widget = MultiBarWidget('CPU')
        self.process_widget = MultiBarWidget('PROC')
        self.memory_widget = MultiBarWidget('MEM', bar_cls=HorizontalBytesBar)
        self.heap_widget = MultiBarWidget('HEAP', bar_cls=HorizontalBytesBar)
        self.disk_widget = MultiBarWidget('DISK', bar_cls=HorizontalBytesBar)
        self.logging_state = urwid.Text([('headline', b'Job Logging')])
        self.logs = urwid.SimpleFocusListWalker([])
        self.body = urwid.Pile([
            urwid.Divider(),
            urwid.Text([('headline', b'Cluster Info')]),
            urwid.Divider(),
            urwid.Columns([
                urwid.Pile([
                    self.cpu_widget,
                    self.process_widget,
                ]),
                urwid.Pile([
                    self.memory_widget,
                    self.heap_widget,
                ]),
            ], dividechars=3),
            urwid.Divider(),
            self.disk_widget,
            urwid.Divider(),
            urwid.Pile([
                self.logging_state,
                urwid.Divider(),
                self._jobs_row('Count', 'Min', 'Max', 'Avg', 'Statement Type'),
                urwid.Divider(),
                urwid.BoxAdapter(urwid.ListBox(self.logs), height=10),
            ]),
            urwid.Divider(),
        ])
        self.t_cluster_name = urwid.Text(b'-', align='left')
        self.t_version = urwid.Text(b'-', align='center')
        self.t_load = urwid.Text(b'-/-/-', align='right')
        self.t_hosts = urwid.Text(b'')
        self.update_info(None)

        return urwid.Frame(urwid.Filler(self.body, valign='top'),
                           header=urwid.Columns([
                               self.t_cluster_name,
                               self.t_version,
                               self.t_load,
                           ]),
                           footer=urwid.Columns([self.t_hosts]))

    def update(self, info=None, nodes=[], jobs=[]):
        if info:
            self.update_info(info)
        if nodes:
            self.update_nodes(nodes)
        if jobs:
            self.update_jobs(jobs)

    def update_jobs(self, jobs=[], clear=False):
        if not clear and jobs:
            self.logs[:] = [self._jobs_row('{0}'.format(r.count),
                                           '{0:.1f}'.format(r.min_duration),
                                           '{0:.1f}'.format(r.max_duration),
                                           '{0:.1f}'.format(r.avg_duration),
                                           r.stmt) for r in jobs]
        else:
            self.logs[:] = []

    def _jobs_row(self, count, min, max, avg, stmt):
        return urwid.Columns([
            (10, urwid.Text([('default', count)])),
            (10, urwid.Text([('text_green', min)])),
            (10, urwid.Text([('text_red', max)])),
            (10, urwid.Text([('text_yellow', avg)])),
            urwid.Text(stmt),
        ], dividechars=1)

    def set_logging_state(self, enabled):
        state = enabled and ('text_green', b'ON') or ('text_red', b'OFF')
        self.logging_state.set_text([
            ('headline', b'Job Logging'),
            ('default', b' '),
            state
        ])

    def update_nodes(self, data=[]):
        cpu = []
        process = []
        heap = []
        memory = []
        disk = []
        load = [0.0, 0.0, 0.0]
        num = float(len(data))
        for node in data:
            cpu.append([
                node.cpu['used'],
                node.cpu['used'] + node.cpu['idle'],
                node.name,
            ])
            process.append([
                node.process['percent'],
                100.0 * node.cpus,
                node.name,
            ])
            heap.append([
                node.heap['used'],
                node.heap['max'],
                node.name,
            ])
            memory.append([
                node.mem['used'],
                node.mem['free'] + node.mem['used'],
                node.name,
            ])
            disk.append(self.calculate_disk_usage(node.fs) + [node.name])
            for idx, k in enumerate(['1', '5', '15']):
                load[idx] += node.load[k] / num
        self.memory_widget.set_data(memory)
        self.heap_widget.set_data(heap)
        self.cpu_widget.set_data(cpu)
        self.process_widget.set_data(process)
        self.disk_widget.set_data(disk)
        self.t_load.set_text('Load: {0:.2f}/{1:.2f}/{2:.2f}'.format(*load))

    def calculate_disk_usage(self, data):
        fs = [0, 0]
        data_disks = [disk['dev'] for disk in data['data']]
        for disk in data['disks']:
            if disk['dev'] in data_disks:
                fs[0] += disk['used']
                fs[1] += disk['size']
        return fs

    def update_info(self, info=None):
        if info is None:
            self.t_cluster_name.set_text(["Cluster: ", ('text_red', '---')])
            self.t_version.set_text(["Version: ", ('text_red', '---')])
        else:
            self.t_cluster_name.set_text([
                "Cluster: ",
                ('inverted', info['cluster_name']),
            ])
            self.t_version.set_text([
                "Version: ",
                ('inverted', info['version']['number']),
            ])

    def update_footer(self, hosts):
        self.t_hosts.set_text(['Connected to: ', ('inverted', ' '.join(hosts))])

    def handle_input(self, key):
        if key == '1':
            self.cpu_widget.toggle_details()
            self.process_widget.toggle_details()
            self.memory_widget.toggle_details()
            self.heap_widget.toggle_details()
        elif key == '2':
            self.disk_widget.toggle_details()
        else:
            LOGGER.warn('Unhandled input:', key)
