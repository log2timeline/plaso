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
"""Formatter for PL-Sql Recall events."""

from plaso.formatters import interface


class PlsRecallFormatter(interface.EventFormatter):
  """Formatter for a for a PL-Sql Recall file container."""
  DATA_TYPE = 'PLSRecall:event'
  SOURCE_LONG = 'PL-Sql Developer Recall file'
  SOURCE_SHORT = 'PLSRecall'

  # The format string.
  FORMAT_STRING = (u'Sequence #{sequence} User: {username} '
                   u'Database Name: {database_name} Query: {query}')
  FORMAT_STRING_SHORT = u'{sequence} {username} {database_name} {query}'

