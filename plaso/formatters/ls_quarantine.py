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
"""Formatter for the Mac OS X launch services quarantine events."""

from plaso.lib import eventdata


class LSQuarantineFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for a LS Quarantine history event."""

  DATA_TYPE = 'macosx:lsquarantine'

  FORMAT_STRING_PIECES = [
      u'[{agent}]',
      u'Downloaded: {url}',
      u'<{data}>']

  FORMAT_STRING_SHORT_PIECES = [u'{url}']

  SOURCE_LONG = 'LS Quarantine Event'
  SOURCE_SHORT = 'LOG'
