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

import argparse
from distutils.version import StrictVersion
from urwid.raw_display import Screen
from crate.client import connect
from .command import CrateStat


__version__ = '0.1.0'

EXIT_SUCCESS, EXIT_ERROR = 0, 1


def parse_cli():
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser('cstat',
                                     description='A visual stat tool for CrateDB clusters')
    parser.add_argument('--hosts', '--crate-hosts',
                        help='one or more CrateDB hosts to connect to',
                        type=str, nargs='+', metavar='HOST',
                        default=['localhost:4200'])
    parser.add_argument('--interval', '--refresh-interval',
                        help='amount of time in seconds between each update',
                        default=2,
                        type=float)
    parser.add_argument('--version', action='version', version=__version__)
    return parser.parse_args()


def main():
    args = parse_cli()

    with connect(args.hosts) as conn:

        if conn.lowest_server_version == StrictVersion('0.0.0'):
            print(f'Could not connect to {args.hosts}')
            return EXIT_ERROR

        screen = Screen()
        screen.set_terminal_properties(256)

        with CrateStat(screen, conn) as ui:
            ui.serve(interval=args.interval)

    return EXIT_SUCCESS
