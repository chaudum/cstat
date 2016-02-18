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

import logging
from logging.handlers import SysLogHandler
from .exceptions import ProgrammingError


class CrateTopLog(object):

    def __init__(self, name):
        raise ProgrammingError("""{0} is a utility wrapper for Python's
        logging module. Please use `{0}.getLogger(name)` to obtain a logger
        instance.""".format(self.__class__.__name__))

    @staticmethod
    def getLogger(name, level=logging.INFO):
        """ Return new logger instance with global config """
        sysLog = SysLogHandler()
        sysLog.setLevel(level)
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(sysLog)
        return logger

