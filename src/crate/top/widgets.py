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

import urwid


class HorizontalBar(urwid.Text):

    STA = '*'
    EQU = '='
    PIP = '|'

    def __init__(self, percent=0.0, symbol=PIP):
        self.symbol = symbol
        bar = symbol * int(percent)
        super(HorizontalBar, self).__init__(bar)

    def set_percent(self, percent):
        self.set_text([('default', self.symbol * int(percent))])


class HorizontalGraphWidget(urwid.Pile):

    def __init__(self, title, percent=0.0):
        self._title = title
        self.title = urwid.Text([title])
        self.bar = urwid.ProgressBar('progress_bg', 'green', percent)
        self.details = urwid.Pile([])
        widgets = [
            self.title,
            self.bar,
            self.details,
        ]
        self._last_value = []
        super(HorizontalGraphWidget, self).__init__(widgets)

    def _new_bar(self, value=0.0):
        return urwid.ProgressBar('progress_bg', 'progress_fg', value)

    def toggle_details(self):
        if len(self.details.contents):
            self.details.contents = []
        else:
            bars = []
            for value in self._last_value:
                bars.append((self._new_bar(value), ('pack', None)))
            self.details.contents = bars

    def update_title(self, total=0.0, unit='mb'):
        self.title.set_text([
            self._title,
            ' ',
            '({0:.2f}{1})'.format(total, unit)
        ])

    def set_data(self, values=[]):
        self._last_value = values
        self.bar.set_completion(sum(values) / len(values))
        num = len(self.details.contents)
        if num:
            for idx in range(num):
                self.details.contents[idx][0].set_completion(values[idx])

