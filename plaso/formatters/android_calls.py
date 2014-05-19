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
"""Formatter for Android contacts2.db database events."""

from plaso.lib import eventdata


class AndroidCallFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for Android call history events."""

  DATA_TYPE = 'android:event:call'

  FORMAT_STRING_PIECES = [
      u'{call_type}',
      u'Number: {number}',
      u'Name: {name}',
      u'Duration: {duration} seconds']

  FORMAT_STRING_SHORT_PIECES = [u'{call_type} Call']

  SOURCE_LONG = 'Android Call History'
  SOURCE_SHORT = 'LOG'
