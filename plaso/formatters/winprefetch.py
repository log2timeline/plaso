#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""Formatter for the Windows Prefetch files."""
from plaso.lib import eventdata


class WinPrefetchFormatter(eventdata.ConditionalEventFormatter):
  """Class that formats Windows Prefetch events."""
  DATA_TYPE = 'windows:prefetch'

  # The format string.
  FORMAT_STRING_PIECES = [
      u'{prefetch_type}',
      u'[{executable}] was executed -',
      u'run count {run_count}',
      u'path: {path}',
      u'hash: 0x{prefetch_hash:08X}',
      u'[',
      u'volume serial: 0x{volume_serial:08X}',
      u'volume path: {volume_path}'
      u']']

  FORMAT_STRING_SHORT_PIECES = [
      u'{executable} was run',
      u'{run_count} time(s)']

  SOURCE_LONG = 'WinPrefetch'
  SOURCE_SHORT = 'LOG'

  def GetMessages(self, event_object):
    """Return the message strings."""
    if event_object.version == 0x11:
      event_object.prefetch_type = 'Prefetch'
    else:
      event_object.prefetch_type = 'Superfetch'

    return super(WinPrefetchFormatter, self).GetMessages(event_object)

