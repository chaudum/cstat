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
import sys
import json
import urwid
import urllib3
from time import mktime
from datetime import datetime, timedelta
from collections import namedtuple
from urllib3.exceptions import MaxRetryError
from crate.client import connect
from .logging import ColorLog

LOGGER = ColorLog(__name__)


class ModelBase(object):

    def __init__(self, hosts=[]):
        self.hosts = hosts
        self.cursor = connect(self.hosts).cursor()
        self.http = urllib3.PoolManager(3)
        self.last_update = datetime.now()

    def sql(self, query, args=[]):
        self.cursor.execute(query, args)
        Row = namedtuple('Row', [c[0] for c in self.cursor.description])
        return [Row(*r) for r in self.cursor.fetchall()]

    def refresh(self):
        self.last_update = datetime.now()
        return self.sql(self.QUERY)


class JobsModel(ModelBase):

    RANGE = 60 #seconds
    LIMIT = 5

    QUERY = re.sub('\n|\s+', ' ', """
        SELECT upper(regexp_matches(stmt, '^(\w+).*')[1]) as stmt,
               min(ended - started) as min_duration,
               max(ended - started) as max_duration,
               avg(ended - started) as avg_duration,
               count(*) as count
        FROM sys.jobs_log
        WHERE ended > ? AND error IS NULL
        GROUP BY stmt
        ORDER BY count DESC
        LIMIT ?
    """.strip('\n '))

    def __init__(self, hosts=[]):
        super(JobsModel, self).__init__(hosts)
        try:
            self.enabled = self.get_initial_state()
        except Exception:
            self.enabled = False


    def get_initial_state(self):
        res = self.sql("""SELECT settings['stats']['enabled'] as enabled FROM sys.cluster""")
        return res[0].enabled

    def refresh(self):
        ts = int(mktime((datetime.now() - timedelta(seconds=self.RANGE)).timetuple()) * 1000)
        self.last_update = datetime.now()
        return self.sql(self.QUERY, (ts, self.LIMIT, ))

    def toggle(self):
        LOGGER.info(self.enabled and 'Disable' or 'Enable', 'jobs logging')
        self.set_stats_enabled(not self.enabled)
        self.enabled = not self.enabled

    def set_stats_enabled(self, bool):
        self.sql("""SET GLOBAL TRANSIENT "stats.enabled" = ?""", args=[bool,])


class NodesModel(ModelBase):

    QUERY = re.sub('\n|\s+', ' ', """
        SELECT id,
               name,
               hostname,
               os['cpu'] as cpu,
               process['cpu'] as process,
               os_info['available_processors'] as cpus,
               load,
               heap,
               mem,
               fs
        FROM sys.nodes
        ORDER BY name
    """.strip('\n '))

    def enable(self):
        pass

    def disable(self):
        pass


class GraphModel(ModelBase):

    def refresh(self):
        self.last_update = datetime.now()
        return self.cluster_info()

    def cluster_info(self):
        response = self.http.request('GET', self.hosts[0])
        return response.status == 200 \
            and json.loads(response.data.decode('utf-8')) \
            or None

