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


class HorizontalBar(urwid.Text):

    START = b'['
    END = b']'

    STAR = b'*'
    EQUI = b'='
    PIPE = b'|'

    def __init__(self, label, current=0.0, total=100.0, symbol=PIPE):
        self.label = '{0:<9} '.format(label[:9]).encode('utf-8')
        self.symbol = symbol
        self.set_progress(current, total)
        super(HorizontalBar, self).__init__('')

    def set_progress(self, current=0.0, total=100.0):
        self.progress = current / total
        self._invalidate()

    def color(self):
        if self.progress < 0.8:
            return 'text_green'
        elif self.progress < 0.95:
            return 'text_yellow'
        return 'text_red'

    def rows(self, size, focus=False):
        return 1

    def render(self, size, focus=False):
        (maxcol, ) = size
        l = len(self.label)
        steps = maxcol - 2 - l
        chars = round(float(steps) * self.progress)
        bar = self.symbol * chars
        t = '{0:.1f}%'.format(self.progress * 100.0).encode('utf-8')
        base = bar + b' ' * (steps - chars)
        base = base[:len(base)-len(t)] + t
        line_attr = [('default', 1+l), (self.color(), steps), ('default', 1)]
        return urwid.TextCanvas([self.label + self.START + base + self.END],
                                attr=[line_attr,],
                                maxcol=maxcol)


class HorizontalGraphWidget(urwid.Pile):

    def __init__(self, title, percent=0.0):
        self.title = title
        self.bar = HorizontalBar(title, percent)
        self.details = urwid.Pile([])
        widgets = [
            self.bar,
            self.details,
        ]
        self._last_value = []
        super(HorizontalGraphWidget, self).__init__(widgets)

    def toggle_details(self):
        if len(self.details.contents):
            self.details.contents = []
        else:
            bars = []
            for value in self._last_value:
                bar = HorizontalBar(value[2], value[0], value[1],
                                    symbol=HorizontalBar.STAR)
                bars.append((bar, ('pack', None)))
            bars.append((urwid.Divider(), ('pack', None)))
            self.details.contents = bars

    def sum(self, values=[]):
        return (sum([x[0] for x in values]), sum([x[1] for x in values]))

    def set_data(self, values=[]):
        self._last_value = values
        self.bar.set_progress(*self.sum(values))
        num = len(self.details.contents) - 1
        if num == 0:
            return
        for idx in range(num):
            bar = self.details.contents[idx]
            if idx < len(values):
                bar[0].set_progress(*values[idx][:2])
            else:
                self.details.contents.remove(bar)

