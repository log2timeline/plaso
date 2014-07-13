#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Formatter for Mac wifi.log file."""

from plaso.formatters import interface


class MacWifiLogFormatter(interface.ConditionalEventFormatter):
  """Formatter for Mac Wifi file."""

  DATA_TYPE = 'mac:wifilog:line'

  FORMAT_STRING_PIECES = [
      u'Action: {action}',
      u'Agent: {user}',
      u'({function})',
      u'Log: {text}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Action: {action}']

  SOURCE_LONG = 'Mac Wifi Log'
  SOURCE_SHORT = 'LOG'
