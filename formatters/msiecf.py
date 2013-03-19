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
"""Formatter for Microsoft Internet Explorer (MSIE) Cache Files (CF) events."""
from plaso.lib import eventdata


class MsiecfUrlFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for a MSIECF URL item."""
  DATA_TYPE = 'msiecf:url'

  FORMAT_STRING_PIECES = [
      u'Location: {location}',
      u'Number of hits: {number_of_hits}',
      u'Filename: {filename}',
      u'Cached file size: {cached_file_size}',
      u'HTTP headers: {http_headers}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Location: {location}']
