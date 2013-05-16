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
"""This file contains a formatter for the Google Chrome history."""
from plaso.lib import eventdata


class ChromePageVisitedFormatter(eventdata.ConditionalEventFormatter):
  """The event formatter for page visited data in Chrome History."""
  DATA_TYPE = 'chrome:history:page_visited'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({title})',
      u'[count: {typed_count}]',
      u'Host: {host}',
      u'{extra}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{url}',
      u'({title})']


class ChromeFileDownloadFormatter(eventdata.EventFormatter):
  """The event formatter for file downloaded data in Chrome History."""
  DATA_TYPE = 'chrome:history:file_downloaded'

  FORMAT_STRING = (u'{url} ({full_path}). Received: {received_bytes} bytes '
                   u'out of: {total_bytes} bytes.')
  FORMAT_STRING_SHORT = u'{full_path} downloaded ({received_bytes} bytes)'
