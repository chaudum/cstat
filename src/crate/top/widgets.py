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

    def __init__(self, current=0.0, total=100.0, symbol=PIPE):
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
        chars = float(maxcol - 2) * self.progress
        bar = self.symbol * int(chars)
        space = b' ' * (maxcol - int(chars) - 2)
        line_attr = [('default', 1), (self.color(), maxcol-2), ('default', 1)]
        return urwid.TextCanvas([self.START + bar + space + self.END],
                                attr=[line_attr,],
                                maxcol=maxcol)

class HorizontalGraphWidget(urwid.Pile):

    def __init__(self, title, percent=0.0):
        self._title = title
        self.title = urwid.Text(title)
        self.bar = HorizontalBar(percent)
        self.details = urwid.Pile([])
        widgets = [
            self.title,
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
                bar = HorizontalBar(*value)
                bars.append((bar, ('pack', None)))
            self.details.contents = bars

    def sum(self, values=[]):
        return (sum([x[0] for x in values]), sum([x[1] for x in values]))

    def set_data(self, values=[]):
        self._last_value = values
        self.bar.set_progress(*self.sum(values))
        num = len(self.details.contents)
        if num == 0:
            return
        for idx in range(num):
            bar = self.details.contents[idx]
            if idx < len(values):
                bar[0].set_progress(*values[idx])
            else:
                self.details.contents.remove(bar)

