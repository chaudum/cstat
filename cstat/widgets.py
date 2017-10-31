# vi: set encoding=utf-8
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
from .log import get_logger

logger = get_logger(__name__)


class BarWidgetBase(urwid.Text):

    START  = '['
    END    = ']'
    SINGLE = '='
    DOUBLE = '#'

    WATERMARK_LOW  = 0.80
    WATERMARK_HIGH = 0.95

    def __init__(self, label, symbol):
        self.label = '{0:<10}'.format(label[:9])
        self.symbol = symbol
        super().__init__(self.label)

    def rows(self, size, focus=False):
        return 1


class HorizontalBar(BarWidgetBase):

    def __init__(self, label, current=0.0, total=100.0, symbol=BarWidgetBase.DOUBLE):
        super().__init__(label, symbol)
        self.set_progress(current, total)

    def set_progress(self, current=0.0, total=100.0):
        self.progress = total > 0 and current / total or 0.0
        self.current = current
        self.total = total
        self._invalidate()

    def color(self):
        if self.progress < self.WATERMARK_LOW:
            return 'text_green'
        elif self.progress < self.WATERMARK_HIGH:
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
        line = self.label + self.START + base + self.END
        return urwid.TextCanvas([line.encode('utf-8'), ],
                                attr=[line_attr],
                                maxcol=maxcol)


class HorizontalPercentBar(HorizontalBar):

    def progress_text(self):
        return '{:.1%}'.format(self.progress)


class HorizontalBytesBar(HorizontalBar):

    def progress_text(self):
        return '{}/{}'.format(byte_size(self.current), byte_size(self.total))


class MultiBarWidget(urwid.Pile):

    def __init__(self, title, bar_cls=HorizontalPercentBar, **bar_options):
        self.title = title
        self.bar_cls = bar_cls
        self.bar = bar_cls('', **bar_options)
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
            self.append_node_bars()

    def append_node_bars(self):
        bars = []
        for value in self._history:
            bar = self.bar_cls(value[2], value[0], value[1],
                               symbol=HorizontalBar.SINGLE)
            bars.append((bar, ('pack', None)))
        self.details.contents = bars
        return len(bars)

    def sum(self, values=[]):
        logger.debug('%s', [sum([x[0] for x in values]), sum([x[1] for x in values])])
        return (sum([x[0] for x in values]), sum([x[1] for x in values]))

    def set_data(self, values=[]):
        self._history = values
        self.bar.set_progress(*self.sum(values))
        if len(self.details.contents) and \
                self.append_node_bars():
            for idx, widget in enumerate(self.details.contents):
                bar = widget[0]
                bar.set_progress(*values[idx][:2])


class IOBar(BarWidgetBase):
    """
    Tx ... sent/written/outbound
    Rx ... received/read/inbound
    """

    def __init__(self, label, suffix='p/s'):
        super().__init__(label, 'x')
        self.tpl = '{0}: {1:>11}'
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
                 10 1 1    4         11    1    4         11 1 1
        +--------------+---------------+...-+---------------+---+
                     12              15    1              15   2
        +-------------------------------...---------------------+
                                                              43
        """
        (maxcol, ) = size
        label_len = len(self.label) # sanity check. should always be 10
        var = maxcol - 45
        if var < 1:
            raise AssertionError('IOBar requires a minimum width of 45 columns!')
        text = ' '
        text += self.tpl.format('Tx', byte_size(self.tx, suffix=self.suffix, k=1000))
        text += ' ' * var
        text += self.tpl.format('Rx', byte_size(self.rx, suffix=self.suffix, k=1000))
        text += ' '
        line_attr = [
            ('default', 12),
            ('tx', 15),
            ('default', var),
            ('rx', 15),
            ('default', 2),
        ]
        line = self.label + self.START + text + self.END
        return urwid.TextCanvas([line.encode('utf-8'), ],
                                attr=[line_attr],
                                maxcol=maxcol)


class IOStatWidget(MultiBarWidget):

    def __init__(self, title, suffix):
        super().__init__(title, bar_cls=IOBar, suffix=suffix)
        self.suffix = suffix

    def append_node_bars(self):
        bars = []
        for ts, packets, name in self._history:
            bar = self.bar_cls(name, suffix=self.suffix)
            bars.append((bar, ('pack', None)))
        self.details.contents = bars
        return len(bars)

    def sum(self, values=[]):
        tx_total = 0.0
        rx_total = 0.0
        if len(self._history):
            for idx, value in enumerate(values):
                if self._history[idx][0] < values[idx][0]:
                    tx, rx = self._calculate(values[idx], self._history[idx])
                    tx_total += tx
                    rx_total += rx
        return tx_total, rx_total

    def set_data(self, values=[]):
        """
        :param values: a list of [timestamp, {'tx': ..., 'rx': ...}, node_name]
        """
        if len(self._history) and \
                len(self.details.contents) and \
                self.append_node_bars():
            for idx, widget in enumerate(self.details.contents):
                bar = widget[0]
                if self._history[idx][0] >= values[idx][0]:
                    tx, rx = bar.tx, bar.rx
                else:
                    tx, rx = self._calculate(values[idx], self._history[idx])
                bar.set_progress(tx, rx)
        self.bar.set_progress(*self.sum(values))
        self._history = values

    def _calculate(self, value, last_value):
        prev_timestamp, prev_values, prev_name = last_value
        timestamp, values, name = value
        assert prev_name == name
        diff = (timestamp - prev_timestamp).total_seconds()
        tx = (values['tx'] - prev_values['tx']) / diff
        rx = (values['rx'] - prev_values['rx']) / diff
        return tx, rx
