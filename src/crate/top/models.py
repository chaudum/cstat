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


import sys
import json
import urwid
import urllib3
from collections import namedtuple
from urllib3.exceptions import MaxRetryError
from crate.client import connect


class GraphModel(object):

    QUERY = """SELECT id,
                      name,
                      hostname,
                      os['cpu'] as cpu,
                      process['cpu'] as process,
                      os_info['available_processors'] as cpus,
                      load,
                      heap,
                      mem
               FROM sys.nodes
               ORDER BY name"""

    def __init__(self, hosts=[]):
        self.hosts = hosts
        self.cursor = connect(self.hosts).cursor()
        self.http = urllib3.PoolManager(3)
        self._cluster_info = None

    def sql(self, query, args=[]):
        self.cursor.execute(query, args)
        Row = namedtuple('Row', [c[0] for c in self.cursor.description])
        return [Row(*r) for r in self.cursor.fetchall()]

    def refresh(self):
        return self.sql(self.QUERY)

    def cluster_info(self):
        if not self._cluster_info:
            response = self.http.request('GET', self.hosts[0])
            self._cluster_info = response.status == 200 \
                and json.loads(response.data.decode('utf-8')) \
                or None
        return self._cluster_info

