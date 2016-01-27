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
from .exceptions import AbstractMethodNotImplemented


class BarWidgetBase(urwid.Text):

    START = b'['
    END = b']'

    STAR = b'*'
    EQUI = b'='
    PIPE = b'|'

    def __init__(self, label, symbol):
        self.label = '{0:<9} '.format(label[:9]).encode('utf-8')
        self.symbol = symbol
        super(BarWidgetBase, self).__init__(self.label)

    def rows(self, size, focus=False):
        return 1


class HorizontalBar(BarWidgetBase):

    def __init__(self, label, current=0.0, total=100.0, symbol=BarWidgetBase.PIPE):
        super(HorizontalBar, self).__init__(label, symbol)
        self.set_progress(current, total)

    def set_progress(self, current=0.0, total=100.0):
        self.progress = current / total
        self.current = current
        self.total = total
        self._invalidate()

    def progress_text(self):
        """
        Value/text that should appear at the end of the progress bar
        """
        raise AbstractMethodNotImplemented(self.__class__,
                                           HorizontalBar.progress_text.__name__)

    def color(self):
        if self.progress < 0.8:
            return 'text_green'
        elif self.progress < 0.95:
            return 'text_yellow'
        return 'text_red'

    def render(self, size, focus=False):
        (maxcol, ) = size
        label_len = len(self.label)
        steps = maxcol - 2 - label_len
        chars = round(float(steps) * self.progress)
        bar = self.symbol * chars
        text = self.progress_text().encode('utf-8')
        base = bar + b' ' * (steps - chars)
        base = base[:len(base)-len(text)] + text
        line_attr = [('default', label_len + 1)]
        if chars:
            line_attr += [(self.color(), chars)]
        line_attr += [('default', 1 + steps - chars)]
        return urwid.TextCanvas([self.label + self.START + base + self.END],
                                attr=[line_attr],
                                maxcol=maxcol)


class HorizontalPercentBar(HorizontalBar):

    def progress_text(self):
        return '{0:.1%}'.format(self.progress)


class HorizontalBytesBar(HorizontalBar):

    FMT_TEMPLATE = '{0:.1f}{1}{2}'
    SIZES = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']

    def bytesize_format(self, num, suffix='b'):
        for unit in self.SIZES:
            if abs(num) < 10240:
                return self.FMT_TEMPLATE.format(num, unit, suffix)
            num /= 1024.0
        return self.FMT_TEMPLATE.format(num, 'Y', suffix)

    def progress_text(self):
        return '{0}/{1}'.format(self.bytesize_format(self.current),
                                self.bytesize_format(self.total))


class MultiBarWidget(urwid.Pile):

    def __init__(self, title, bar_cls=HorizontalPercentBar):
        self.title = title
        self.bar_cls = bar_cls
        self.bar = bar_cls(title)
        self.details = urwid.Pile([])
        widgets = [
            self.bar,
            self.details,
        ]
        self._last_value = []
        super(MultiBarWidget, self).__init__(widgets)

    def toggle_details(self):
        if len(self.details.contents):
            self.details.contents = []
        else:
            bars = []
            for value in self._last_value:
                bar = self.bar_cls(value[2], value[0], value[1],
                                   symbol=BarWidgetBase.STAR)
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

