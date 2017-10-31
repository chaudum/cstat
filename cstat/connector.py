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
import aiopg
import asyncio
import functools
from collections import namedtuple
from .log import get_logger

logger = get_logger(__name__)
NamedQuery = namedtuple('NamedQuery', ['name', 'stmt', 'args'])


NODE_QUERY = NamedQuery('nodes', '''
SELECT id,
       name,
       hostname,
       format('%s:%d', hostname, port['http']) as host,
       os['cpu']['system'] + os['cpu']['user'] + os['cpu']['stolen'] AS cpu_used,
       os['cpu']['idle'] AS cpu_idle,
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
''', None)

JOBS_QUERY = NamedQuery('jobs', '''
SELECT upper(regexp_matches(stmt, '^\s*(\w+).*')[1]) AS stmt,
       min(ended - started) AS "min",
       avg(ended - started) AS "avg",
       max(ended - started) AS "max",
       percentile(ended - started, 0.5) AS "median",
       percentile(ended - started, 0.95) AS "perc95",
       percentile(ended - started, 0.99) AS "perc99",
       count(*) AS count
FROM sys.jobs_log
WHERE ended > CURRENT_TIMESTAMP - 60000
  AND error IS NULL
GROUP BY 1
ORDER BY count DESC
''', None)

SETTINGS_QUERY = NamedQuery('settings', '''
SELECT name,
       settings['stats']['enabled'] AS "stats_enabled",
       settings['license']['enterprise'] AS "enterprise_enabled",
       settings['udc']['enabled'] AS "udc_enabled"
FROM sys.cluster
''', None)

VERSION_QUERY = NamedQuery('version', '''
SELECT min(version['number']) AS version FROM sys.nodes
''', None)

STATS_STMT = '''
SET GLOBAL TRANSIENT "stats.enabled" = %s
'''


def unwrap_task_result(callback):
    def inner(t):
        callback(t.result())
    return inner


def toggle_stats(current_value, pool, callback):
    set_stmt = NamedQuery('toggle_stats', STATS_STMT, [not current_value])
    task = asyncio.ensure_future(exec_query(pool, [set_stmt, SETTINGS_QUERY]))
    task.add_done_callback(unwrap_task_result(callback))


def resultset(cursor):
    Record = namedtuple('Record', [c.name for c in cursor.description])
    return [Record(*r) for r in cursor]


async def pool(args):
    return await aiopg.create_pool(host=args.host, port=args.port,
                                   user=args.user, password=None,
                                   enable_json=False, enable_hstore=False,
                                   enable_uuid=False)


async def exec_query(pool, queries):
    rs = {}
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            for name, stmt, params in queries:
                await cur.execute(stmt, params)
                rs[name] = resultset(cur) if cur.rowcount > -1 else None
    return rs


class DataProvider:

    PROVIDERS = [
        VERSION_QUERY,
        NODE_QUERY,
        JOBS_QUERY,
        SETTINGS_QUERY,
    ]

    def __init__(self, pool, consumer, interval):
        self.pool = pool
        self.interval = interval
        self.consumer = consumer
        self.state = {}
        self.fetch()

    def fetch(self, *args):
        task = asyncio.ensure_future(exec_query(self.pool, self.PROVIDERS))
        task.add_done_callback(self.on_result)

    def on_result(self, t):
        try:
            state = t.result()
        except Exception as e:
            self.consumer.apply(failure=e)
        else:
            self.consumer.apply(state)
            self.state.update(state)
        finally:
            loop = asyncio.get_event_loop()
            loop.call_later(self.interval, self.fetch)

    def __getitem__(self, key):
        return self.state.get(key)
