#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Formatter for ASL securityd log file."""

from plaso.lib import eventdata


class MacSecuritydLogFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for ASL Securityd file."""

  DATA_TYPE = 'mac:asl:securityd:line'

  FORMAT_STRING_PIECES = [
      u'Sender: {sender}',
      u'({sender_pid})',
      u'Level: {level}',
      u'Facility: {facility}',
      u'Text: {message}']

  FORMAT_STRING_SHORT_PIECES = [u'Text: {message}']

  SOURCE_LONG = 'Mac ASL Securityd Log'
  SOURCE_SHORT = 'LOG'

