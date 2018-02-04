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

import asyncio
import getpass
import argparse
from .command import CrateStat

__version__ = '0.1.0'

EXIT_SUCCESS, EXIT_ERROR = 0, 1


def red(text: str) -> str:
    return f'\033[31m{text}\033[0m'


def blue(text: str) -> str:
    return f'\033[34m{text}\033[0m'


def yellow(text: str) -> str:
    return f'\033[33m{text}\033[0m'


def parse_cli():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser('cstat',
                                     description='A visual stat tool for CrateDB clusters')
    parser.add_argument('--host', '--crate-host',
                        help='CrateDB host to connect to',
                        type=str, metavar='HOST',
                        default='127.0.0.1')
    parser.add_argument('--port', '--psql-port',
                        help='PSQL port of CrateDB host',
                        type=int, metavar='PORT',
                        default=5432)
    parser.add_argument('--interval', '--refresh-interval',
                        help='amount of time in seconds between each update',
                        default=2,
                        type=float)
    parser.add_argument('--user', '--db-user',
                        help='database user',
                        default=None,
                        type=str)
    parser.add_argument('-V', '--prompt-user',
                        help='prompt for user name',
                        action='store_true',
                        default=False)
    parser.add_argument('--password', '--db-password',
                        help='user password',
                        default=None,
                        type=str)
    parser.add_argument('-W', '--prompt-password',
                        help='prompt for user password',
                        action='store_true',
                        default=False)
    parser.add_argument('--version', action='version', version=__version__)
    return parser.parse_args()


def main():
    args = parse_cli()
    if args.prompt_user and not args.user:
        args.user = input('User: ')
    if args.prompt_password and not args.password:
        args.password = getpass.getpass()
    aioloop = asyncio.get_event_loop()
    ui = CrateStat(args)
    try:
        ui.serve(aioloop)
    except Exception as e:
        print(red('An error occured: ') + str(e))
        print('Please file a bug report on https://github.com/chaudum/crate-top/issues')
        return EXIT_ERROR
    else:
        print(yellow('Bye!'))
        return EXIT_SUCCESS
