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
"""This file contains a MacKeepr Cache formatter in plaso."""
from plaso.lib import eventdata


class MacKeeperCacheFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for MacKeeper Cache extracted events."""
  DATA_TYPE = 'mackeeper:cache'

  FORMAT_STRING_PIECES = [
      u'{description}', u'<{event_type}>', u':', u'{text}', u'[',
      u'URL: {url}', u'Event ID: {record_id}', 'Room: {room}', u']']

  FORMAT_STRING_SHORT_PIECES = [u'<{event_type}>', u'{text}']

  SOURCE_LONG = 'MacKeeper Cache'
  SOURCE_SHORT = 'LOG'
