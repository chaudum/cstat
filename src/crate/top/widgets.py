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
from datetime import datetime
from .exceptions import AbstractMethodNotImplemented


class ByteSizeFormat(object):

    FMT_TEMPLATE = '{0:.1f}{1}{2}'
    SIZES = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']

    @classmethod
    def format(cls, num, suffix='b'):
        for unit in cls.SIZES:
            if abs(num) < 10240:
                return cls.FMT_TEMPLATE.format(num, unit, suffix)
            num /= 1024.0
        return cls.FMT_TEMPLATE.format(num, 'Y', suffix)


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


class AbstractBar(BarWidgetBase):

    def __init__(self, label, current=0.0, total=100.0, symbol=BarWidgetBase.PIPE):
        super(AbstractBar, self).__init__(label, symbol)
        self.set_progress(current, total)

    def set_progress(self, current=0.0, total=100.0):
        raise AbstractMethodNotImplemented(self.__class__,
                                           self.set_progress.__name__)

    def progress_text(self):
        raise AbstractMethodNotImplemented(self.__class__,
                                           self.progress_text.__name__)


class HorizontalBar(AbstractBar):

    def set_progress(self, current=0.0, total=100.0):
        self.progress = current / total
        self.current = current
        self.total = total
        self._invalidate()

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

    def progress_text(self):
        return '{0}/{1}'.format(ByteSizeFormat.format(self.current),
                                ByteSizeFormat.format(self.total))


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


class IOBar(AbstractBar):

    def __init__(self, label, tx=0.0, rx=0.0, symbol=None):
        self.template = 'Tx: {0:>8}/s Rx: {1:>8}/s'
        super(IOBar, self).__init__(label, 0.0, 0.0, symbol)

    def set_progress(self, tx=0.0, rx=0.0):
        self.tx = tx
        self.rx = rx
        self._invalidate()

    def render(self, size, focus=False):
        # TODO: improve coloring
        (maxcol, ) = size
        label_len = len(self.label)
        max_text_width = maxcol - 2 - label_len
        text = self.template.format(
            ByteSizeFormat.format(self.tx, suffix='p'),
            ByteSizeFormat.format(self.rx, suffix='p')
        )
        base = ' ' * max_text_width
        if len(text) > max_text_width:
            base = text[:max_text_width]
        else:
            base = text + ' ' * (max_text_width - len(text))
        base = base[:max_text_width].encode('utf-8')
        line_attr = [
            ('default', label_len + 1),
            ('text_green', min(len(text), max_text_width)),
            ('default', 1),
        ]
        return urwid.TextCanvas([self.label + self.START + base + self.END],
                                attr=[line_attr],
                                maxcol=maxcol)


class IOStatWidget(MultiBarWidget):

    def toggle_details(self):
        if len(self.details.contents):
            self.details.contents = []
        else:
            bars = []
            for ts, packets, name in self._last_value:
                bar = self.bar_cls(name, 0.0, 0.0, symbol=None)
                bars.append((bar, ('pack', None)))
            bars.append((urwid.Divider(), ('pack', None)))
            self.details.contents = bars

    def set_data(self, values=[]):
        if len(self._last_value):
            tx_total = 0.0
            rx_total = 0.0
            for idx, bar in enumerate(self.details.contents):
                if idx < len(values):
                    tx, rx = self._calculate(values[idx], self._last_value[idx])
                    tx_total += tx
                    rx_total += rx
                    bar[0].set_progress(tx, rx)
                else:
                    self.details.contents.remove(bar)
            self.bar.set_progress(tx_total, rx_total)
        self._last_value = values

    def _calculate(self, value, last_value):
        last_timestamp, last_packets, last_name = last_value
        timestamp, packets, name = value 
        assert last_name == name
        diff = (timestamp - last_timestamp) / 1000.0
        tx, rx = 0.0, 0.0
        if diff > 0.0:
            tx = (packets['sent'] - last_packets['sent']) / diff
            rx = (packets['received'] - last_packets['received']) / diff
        return (tx, rx)

