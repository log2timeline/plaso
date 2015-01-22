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
"""Formatter for the McAfee AV Logs files."""

from plaso.formatters import interface
from plaso.formatters import manager


class McafeeAccessProtectionLogEventFormatter(interface.EventFormatter):
  """Class that formats the McAfee Access Protection Log events."""

  DATA_TYPE = 'av:mcafee:accessprotectionlog'

  # The format string.
  FORMAT_STRING = (u'File Name: {filename} User: {username} {trigger_location} '
                   u'{status} {rule} {action}')
  FORMAT_STRING_SHORT = u'{filename} {action}'

  SOURCE_LONG = 'McAfee Access Protection Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(
    McafeeAccessProtectionLogEventFormatter)
