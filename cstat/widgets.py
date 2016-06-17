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
from .utils import byte_size


class BarWidgetBase(urwid.Text):

    START = '['
    END   = ']'

    STAR = '*'
    EQUI = '='
    PIPE = '|'

    def __init__(self, label, symbol):
        self.label = '{0:<10}'.format(label[:9])
        self.symbol = symbol
        super().__init__(self.label)

    def rows(self, size, focus=False):
        return 1


class HorizontalBar(BarWidgetBase):

    def __init__(self, label, current=0.0, total=100.0, symbol=BarWidgetBase.PIPE):
        super().__init__(label, symbol)
        self.set_progress(current, total)

    def set_progress(self, current=0.0, total=100.0):
        self.progress = total > 0 and current / total or 0.0
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
        text = self.progress_text()
        base = bar + ' ' * (steps - chars)
        base = base[:len(base)-len(text)] + text
        line_attr = [('default', label_len + 1)]
        if chars:
            line_attr += [(self.color(), chars)]
        line_attr += [('default', 1 + steps - chars)]
        lines = [self.label + self.START + base + self.END]
        return urwid.TextCanvas([l.encode('utf-8') for l in lines],
                                attr=[line_attr], maxcol=maxcol)


class HorizontalPercentBar(HorizontalBar):

    def progress_text(self):
        return '{:.1%}'.format(self.progress)


class HorizontalBytesBar(HorizontalBar):

    def progress_text(self):
        return byte_size(self.current) + '/' + byte_size(self.total)


class MultiBarWidget(urwid.Pile):

    def __init__(self, title, bar_cls=HorizontalPercentBar, **bar_options):
        self.title = title
        self.bar_cls = bar_cls
        self.bar = bar_cls(title, **bar_options)
        self.details = urwid.Pile([])
        widgets = [
            self.bar,
            self.details,
        ]
        self._history = []
        super().__init__(widgets)

    def toggle_details(self):
        if len(self.details.contents):
            self.details.contents = []
        else:
            bars = []
            for value in self._history:
                bar = self.bar_cls(value[2], value[0], value[1],
                                   symbol=BarWidgetBase.STAR)
                bars.append((bar, ('pack', None)))
            bars.append((urwid.Divider(), ('pack', None)))
            self.details.contents = bars

    def sum(self, values=[]):
        return (sum([x[0] for x in values]), sum([x[1] for x in values]))

    def set_data(self, values=[]):
        self._history = values
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


class IOBar(BarWidgetBase):
    """
    Tx ... sent/written/outbound
    Rx ... received/read/inbound
    """

    def __init__(self, label, suffix='p/s'):
        super().__init__(label, 'x')
        self.tpl = '{0}: {1:>10}'
        self.suffix = suffix
        self.set_progress(0.0, 0.0)

    def set_progress(self, tx=0.0, rx=0.0):
        self.tx = tx
        self.rx = rx
        self._invalidate()

    def render(self, size, focus=False):
        """
         LABEL      [   Tx:     0.0 b/s      Rx:      0.0b/s   ]
        +----------+-+-+----+----------+...-+----+----------+-+-+
                 10 1 1    4         10    1    4         10 1 1
        +--------------+---------------+...-+---------------+---+
                     12              14    1              14   2
        +-------------------------------...---------------------+
                                                              43
        """
        (maxcol, ) = size
        label_len = len(self.label) # sanity check. should always be 10
        var = maxcol - 42
        if var < 1:
            raise AssertionError('IOBar requires a minimum width of 43 columns!')
        text = ' '
        text += self.tpl.format('Tx', byte_size(self.tx, suffix=self.suffix))
        text += ' ' * var
        text += self.tpl.format('Rx', byte_size(self.rx, suffix=self.suffix))
        text += ' '
        line_attr = [
            ('default', 12),
            ('tx', 14),
            ('default', var),
            ('rx', 14),
            ('default', 2),
        ]
        lines = [self.label + self.START + text + self.END]
        return urwid.TextCanvas([l.encode('utf-8') for l in lines],
                                attr=[line_attr], maxcol=maxcol)


class IOStatWidget(MultiBarWidget):

    def __init__(self, title, suffix):
        super().__init__(title, bar_cls=IOBar, suffix=suffix)
        self.suffix = suffix

    def toggle_details(self):
        if len(self.details.contents):
            self.details.contents = []
        else:
            bars = []
            for ts, packets, name in self._history:
                bar = self.bar_cls(name, suffix=self.suffix)
                bars.append((bar, ('pack', None)))
            bars.append((urwid.Divider(), ('pack', None)))
            self.details.contents = bars

    def set_data(self, values=[]):
        if len(self._history):
            tx_total = 0.0
            rx_total = 0.0
            ## TODO: if details are not shown - no total is calculated!
            for idx, bar in enumerate(self.details.contents):
                if idx < len(values):
                    if self._history[idx][0] >= values[idx][0]:
                        tx, rx = bar[0].tx, bar[0].rx
                    else:
                        tx, rx = self._calculate(values[idx], self._history[idx])
                    tx_total += tx
                    rx_total += rx
                    bar[0].set_progress(tx, rx)
                else:
                    self.details.contents.remove(bar)
            self.bar.set_progress(tx_total, rx_total)
        self._history= values

    def _calculate(self, value, last_value):
        prev_timestamp, prev_values, prev_name = last_value
        timestamp, values, name = value
        assert prev_name == name
        diff = (timestamp - prev_timestamp) / 1000.0
        tx = (values['tx'] - prev_values['tx']) / diff
        rx = (values['rx'] - prev_values['rx']) / diff
        return tx, rx

