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
SELECT UPPER(REGEXP_MATCHES(stmt, '^\s*(\w+).*')[1]) AS stmt,
       min(ended - started) AS min_duration,
       max(ended - started) AS max_duration,
       avg(ended - started) AS avg_duration,
       count(*) AS count
FROM sys.jobs_log
WHERE ended > CURRENT_TIMESTAMP - 600000
  AND error IS NULL
GROUP BY stmt
ORDER BY count DESC
'''

STATS_QUERY = '''
SELECT settings['stats']['enabled'] AS enabled
FROM sys.cluster
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


class Connector:

    def __init__(self, connection, loop, consumer, interval=1):
        self.loop = loop
        self.interval = interval
        self.consumer = consumer
        self.providers = [
            ('info', json_provider(connection, '')),
            ('nodes', sql_provider(connection, NODE_QUERY)),
            ('jobs', sql_provider(connection, JOBS_QUERY)),
        ]
        self.loop.set_alarm_in(0.1, self.fetch)

    def fetch(self, loop, *args):
        try:
            state = {n: p() for n, p in self.providers}
        except Exception as e:
            logger.error(e)
            self.consumer.apply(failure=e)
        else:
            self.consumer.apply(state)
            loop.set_alarm_in(self.interval, self.fetch)
