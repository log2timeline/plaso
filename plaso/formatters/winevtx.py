#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""Formatters for Windows XML EventLog (EVTX) related events."""
from plaso.lib import eventdata


class WinEvtxFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for a Windows XML EventLog (EVTX) record."""
  DATA_TYPE = 'windows:evtx:record'

  FORMAT_STRING_PIECES = [
      u'[0x{event_identifier:08x}]',
      u'Record Number: {record_number}',
      u'Event Level: {event_level}',
      u'Source Name: {source_name}',
      u'Computer Name: {computer_name}',
      u'User SID: {user_sid}',
      u'Strings: {strings}',
      u'XML string: {xml_strings}']

  FORMAT_STRING_SHORT_PIECES = [
      u'[0x{event_identifier:08x}]',
      u'Strings: {strings}']
