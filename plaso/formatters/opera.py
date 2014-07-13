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
"""Formatter for Opera history events."""

from plaso.formatters import interface


class OperaGlobalHistoryFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Opera global history event."""

  DATA_TYPE = 'opera:history:entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({title})',
      u'[{description}]']

  SOURCE_LONG = 'Opera Browser History'
  SOURCE_SHORT = 'WEBHIST'


class OperaTypedHistoryFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Opera typed history event."""

  DATA_TYPE = 'opera:history:typed_entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({entry_selection})']

  SOURCE_LONG = 'Opera Browser History'
  SOURCE_SHORT = 'WEBHIST'
