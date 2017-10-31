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


import re
import json
import urllib3
from collections import namedtuple

from .log import get_logger

logger = get_logger(__name__)
http = urllib3.PoolManager(3)


NODE_QUERY = '''
SELECT id,
       name,
       hostname,
       format('%s:%d', hostname, port['http']) as host,
       GREATEST(0, LEAST((os['cpu']['system'] + os['cpu']['user'] + os['cpu']['stolen'])::LONG, 100)) AS cpu_used,
       GREATEST(0, LEAST((os['cpu']['idle'])::LONG, 100)) AS cpu_idle,
       os['timestamp'] as hosttime,
       process['cpu'] as process,
       os_info['available_processors'] as cpus,
       load,
       heap,
       mem,
       fs,
       network['probe_timestamp'] as net_timestamp,
       network['tcp']['packets'] as net_packets
FROM sys.nodes
ORDER BY name
'''

JOBS_QUERY = '''
SELECT upper(regexp_matches(stmt, '^\s*(\w+).*')[1]) AS stmt,
       min(ended - started) AS min_duration,
       max(ended - started) AS max_duration,
       avg(ended - started) AS avg_duration,
       count(*) AS count
FROM sys.jobs_log
WHERE ended > CURRENT_TIMESTAMP - 600000
  AND error IS NULL
GROUP BY 1
ORDER BY count DESC
'''

SETTINGS_QUERY = '''
SELECT settings['stats']['enabled'] AS "stats_enabled",
       settings['license']['enterprise'] AS "enterprise_enabled",
       settings['udc']['enabled'] AS "udc_enabled"
FROM sys.cluster
'''

STATS_STMT = '''
SET GLOBAL TRANSIENT "stats.enabled" = ?
'''


def normalize_query(query):
    return re.sub('\n|\s+', ' ', query).strip('\n ')


def sql_provider(conn, query):
    cursor = conn.cursor()
    q = normalize_query(query)
    def execute():
        cursor.execute(q)
        Row = namedtuple('Row', [c[0] for c in cursor.description])
        return [Row(*r) for r in cursor.fetchall()]
    return execute


def json_provider(conn, path=''):
    host = conn.client.active_servers[0]
    def execute():
        response = http.request('GET', host + path)
        return response.status == 200 \
            and json.loads(response.data.decode('utf-8')) \
            or None
    return execute


def logging_state(conn):
    cursor = conn.cursor()
    cursor.execute(normalize_query(SETTINGS_QUERY))
    return cursor.fetchone()[0]


def toggle_stats(conn):
    new_state = not logging_state(conn)
    cursor = conn.cursor()
    cursor.execute(normalize_query(STATS_STMT), (new_state, ))
    logger.debug('new logging state: %s', new_state)
    return new_state


class DataProvider:

    def __init__(self, connection, loop, consumer, interval=1):
        self.loop = loop
        self.interval = interval
        self.consumer = consumer
        self.providers = [
            ('info', json_provider(connection, '')),
            ('nodes', sql_provider(connection, NODE_QUERY)),
            ('jobs', sql_provider(connection, JOBS_QUERY)),
            ('settings', sql_provider(connection, SETTINGS_QUERY)),
        ]
        self.last_state = {}
        self.loop.set_alarm_in(0.1, self.fetch)

    def fetch(self, loop, *args):
        try:
            state = {n: p() for n, p in self.providers}
        except Exception as e:
            logger.error(e)
            self.consumer.apply(failure=e)
        else:
            self.consumer.apply(state)
            self.last_state = state
            loop.set_alarm_in(self.interval, self.fetch)

    def __getitem__(self, key):
        return self.last_state.get(key)
