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


import re
import urwid
from functools import reduce
from .widgets import (
    MultiBarWidget,
    HorizontalPercentBar,
    HorizontalBytesBar,
    IOStatWidget,
)

RE_PADDING = re.compile('^(\s*)(.*[^\s])(\s*)$')


def padded_text(text):
    return re.sub(RE_PADDING, r' \2 ', text)


class EmptyWidget(urwid.Divider):
    pass


class Tab(urwid.WidgetWrap):

    def __init__(self, widgets, title, color):
        self.title = title
        self.content = urwid.Pile(widgets)
        super().__init__(urwid.AttrMap(self.content, color))


class Menu(urwid.Columns):

    EMPTY_COL = ('pack', urwid.Text(''))

    def __init__(self, items, **kwargs):
        self.items = items
        cols = self.generate_columns()
        super().__init__(cols, **kwargs)

    def can_handle_input(self, key):
        return key in [i.ident for i in self.items]

    def width(self):
        return reduce(lambda x, y: x + y[0][0] + y[1][0] + 2,
                      [i.contents for i in self.items],
                      0)

    def generate_columns(self):
        cols = []
        for item in self.items:
            cols += item.contents
        return cols

    def set_active(self, ident):
        for item in self.items:
            if item.ident == ident:
                item.set_active()

    def set_inactive(self, ident=None):
        for item in self.items:
            if ident and item.ident == ident or ident is None:
                item.set_inactive()


class MenuItem:

    def __init__(self, left, right):
        self.ident = left
        self.left = urwid.AttrMap(urwid.Text(left), 'menu')
        label = padded_text(right)
        self.right = urwid.AttrMap(urwid.Text(label), 'inactive')
        self.contents = [
            (len(left), self.left),
            (len(label), self.right),
        ]

    def set_active(self):
        self.set_attr('active')

    def set_inactive(self):
        self.set_attr('inactive')

    def set_attr(self, attr):
        self.right.set_attr_map({None: attr})


class MainWindow(urwid.WidgetWrap):

    def __init__(self, controller):
        self.controller = controller
        self.frame = self.layout()
        super().__init__(self.frame)

    def layout(self):
        self.cpu_widget = MultiBarWidget('CPU')
        self.process_widget = MultiBarWidget('PROC')
        self.memory_widget = MultiBarWidget('MEM', bar_cls=HorizontalBytesBar)
        self.heap_widget = MultiBarWidget('HEAP', bar_cls=HorizontalBytesBar)
        self.disk_widget = MultiBarWidget('DISK', bar_cls=HorizontalBytesBar)
        self.net_io_widget = IOStatWidget('NET', suffix='p/s')
        self.disk_io_widget = IOStatWidget('DISK', suffix='b/s')
        self.logging_state = urwid.Text([('headline', 'Jobs Logging')])
        self.logs = urwid.SimpleFocusListWalker([])

        self.t_cluster_name = urwid.Text('-')
        self.t_version = urwid.Text('-')
        self.t_load = urwid.Text('-/-/-', align='right')
        self.t_hosts = urwid.Text('-')
        self.t_handler = urwid.Text('-')

        self.menu1 = Menu([
            MenuItem('0', 'Info'),
        ], dividechars=1)
        self.menu1.set_active('0')

        self.menu2 = Menu([
            MenuItem('1', 'Utilization'),
            MenuItem('2', 'I/O Stats'),
            MenuItem('3', 'Job Logging'),
        ], dividechars=1)

        self.menu3 = Menu([
            #MenuItem('?', 'Help'),
            MenuItem('q', 'Quit'),
        ], dividechars=1)

        menu = urwid.Pile([
            urwid.AttrMap(urwid.Text('cstat'), 'inverted'),
            urwid.AttrMap(urwid.Columns([
                (self.menu1.width(), self.menu1),
                (self.menu2.width(), self.menu2),
                (self.menu3.width(), self.menu3),
                Menu.EMPTY_COL,
            ]), 'menu'),
        ])

        footer = urwid.AttrMap(urwid.Columns([
            self.t_load,
        ], dividechars=1), 'inverted')

        self.tab_1 = Tab([
            urwid.LineBox(
                urwid.Columns([
                    (10, urwid.Pile([
                        urwid.Text('Cluster'),
                        urwid.Text('Version'),
                        urwid.Text('Handler'),
                        urwid.Text('Hosts'),
                    ])),
                    urwid.Pile([
                        self.t_cluster_name,
                        self.t_version,
                        self.t_handler,
                        self.t_hosts,
                    ]),
                ]), title='Cluster Info'
            ),
        ], 'Cluster Info', 'menu')

        self.tab_2 = Tab([
            urwid.Columns([
                urwid.Pile([
                    urwid.LineBox(self.cpu_widget, 'CPU Usage'),
                    urwid.LineBox(self.memory_widget, 'Memory Usage'),
                    urwid.LineBox(self.disk_widget, 'Disk Usage'),
                ]),
                urwid.Pile([
                    urwid.LineBox(self.process_widget, 'Crate Process'),
                    urwid.LineBox(self.heap_widget, 'HEAP Usage'),
                ]),
            ], dividechars=1),
        ], 'Utilization', 'default')

        self.tab_3 = Tab([
            urwid.Columns([
                urwid.Pile([
                    urwid.LineBox(self.net_io_widget, 'Network I/O'),
                ]),
                urwid.Pile([
                    urwid.LineBox(self.disk_io_widget, 'Disk I/O'),
                ]),
            ], dividechars=1),
        ], 'I/O Stats', 'default')

        self.tab_4 = Tab([
            self.logging_state,
            urwid.AttrMap(urwid.Columns([
                urwid.Text('Statement Type'),
                (10, urwid.Text('Count', align='right')),
                (10, urwid.Text('Min', align='right')),
                (10, urwid.Text('Avg', align='right')),
                (10, urwid.Text('Max', align='right')),
            ], dividechars=1), 'head'),
            urwid.BoxAdapter(urwid.ListBox(self.logs), height=10),
        ], 'Jobs Logging', 'default')

        self.tab_holder = urwid.WidgetPlaceholder(EmptyWidget())
        self.tab_header = urwid.WidgetPlaceholder(self.tab_1)
        body = urwid.Pile([
            self.tab_header,
            self.tab_holder,
        ])

        self.update_info(None)
        return urwid.Frame(urwid.Filler(body, valign='top'),
                           header=menu, footer=footer)

    def update(self, info=None, nodes=[], jobs=[]):
        if info:
            self.update_info(info)
        if nodes:
            self.update_nodes(nodes)
        if jobs:
            self.update_jobs(jobs)

    def update_jobs(self, jobs=[]):
        if jobs is None:
            self.logs[:] = []
        elif jobs:
            self.logs[:] = [self._jobs_row('{0}'.format(r.count),
                                           '{0:.0f}ms'.format(r.min_duration),
                                           '{0:.0f}ms'.format(r.max_duration),
                                           '{0:.0f}ms'.format(r.avg_duration),
                                           r.stmt) for r in jobs]

    def _jobs_row(self, count, min, max, avg, stmt):
        return urwid.Columns([
            urwid.Text([('default', stmt) if stmt else ('bg_red', '???')]),
            (10, urwid.Text([('default', count)], align='right')),
            (10, urwid.Text([('text_green', min)], align='right')),
            (10, urwid.Text([('text_yellow', avg)], align='right')),
            (10, urwid.Text([('text_red', max)], align='right')),
        ], dividechars=1)

    def set_logging_state(self, enabled):
        state = enabled and ('bg_green', 'ON') or ('bg_red', 'OFF')
        self.logging_state.set_text([
            ('default', 'Logging: '),
            state,
            ('default', ' (F1 to toggle)')
        ])
        if not enabled:
            self.update_jobs(jobs=None)

    def update_nodes(self, data=[]):
        cpu = []
        process = []
        heap = []
        memory = []
        disk = []
        net_io = []
        disk_io = []
        load = [0.0, 0.0, 0.0]
        num = float(len(data))
        for node in data:
            used = node.cpu['system'] + node.cpu['user'] + node.cpu['stolen']
            cpu.append([
                min(used, 100),
                min(used + node.cpu['idle'], 100),
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
            net_io.append([
                node.net_timestamp,
                dict(
                    tx=node.net_packets['sent'],
                    rx=node.net_packets['received']),
                node.name,
            ])
            disk_io.append([
                node.hosttime,
                self.calculate_disk_io(node.fs),
                node.name,
            ])
            for idx, k in enumerate(['1', '5', '15']):
                load[idx] += node.load[k] / num
        self.memory_widget.set_data(memory)
        self.heap_widget.set_data(heap)
        self.cpu_widget.set_data(cpu)
        self.process_widget.set_data(process)
        self.disk_widget.set_data(disk)
        self.net_io_widget.set_data(net_io)
        self.disk_io_widget.set_data(disk_io)
        self.t_load.set_text('{0:.2f}/{1:.2f}/{2:.2f}'.format(*load))
        self.t_hosts.set_text(', '.join([n.hostname for n in data]))

    def _data_disks(self, data):
        data_disks = [disk['dev'] for disk in data['data']]
        for disk in data['disks']:
            if disk['dev'] in data_disks:
                yield disk

    def calculate_disk_usage(self, data):
        fs = [0, 0]
        for disk in self._data_disks(data):
            fs[0] += disk['used']
            fs[1] += disk['size']
        return fs

    def calculate_disk_io(self, data):
        io = dict(tx=0, rx=0)
        for disk in self._data_disks(data):
            io['tx'] += disk['bytes_written']
            io['rx'] += disk['bytes_read']
        return io

    def update_info(self, info=None):
        if info is None:
            self.t_cluster_name.set_text([('text_red', '---')])
            self.t_version.set_text([('text_red', '---')])
        else:
            self.t_cluster_name.set_text(info['cluster_name'])
            self.t_version.set_text(info['version']['number'])

    def update_footer(self, hosts):
        self.t_handler.set_text(' '.join(hosts))

    def handle_input(self, key):
        if self.menu1.can_handle_input(key):
            if key == '0':
                if self.tab_header.original_widget is self.tab_1:
                    self.tab_header.original_widget = EmptyWidget()
                    self.menu1.set_inactive(key)
                else:
                    self.tab_header.original_widget = self.tab_1
                    self.menu1.set_active(key)
        elif self.menu2.can_handle_input(key):
            self.menu2.set_inactive()
            if key == '1':
                self.set_active_tab(self.tab_2)
                self.menu2.set_active(key)
            elif key == '2':
                self.set_active_tab(self.tab_3)
                self.menu2.set_active(key)
            elif key == '3':
                self.set_active_tab(self.tab_4)
                self.menu2.set_active(key)
        elif self.menu3.can_handle_input(key):
            self.menu3.set_inactive()
        else:
            if key == 'x':
                self.cpu_widget.toggle_details()
                self.process_widget.toggle_details()
                self.memory_widget.toggle_details()
                self.heap_widget.toggle_details()
                self.disk_widget.toggle_details()
                self.net_io_widget.toggle_details()
                self.disk_io_widget.toggle_details()



    def get_active_tab(self):
        return len(self.body.contents) and \
            self.body.contents[0][0] or None

    def set_active_tab(self, tab):
        self.tab_holder.original_widget = tab

