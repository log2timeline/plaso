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
"""This file contains a formatter for the Firefox cookie."""

from plaso.lib import eventdata


class FirefoxCookieFormatter(eventdata.ConditionalEventFormatter):
  """The event formatter for cookie data in Firefox Cookies database."""

  DATA_TYPE = 'firefox:cookie:entry'

  FORMAT_STRING_PIECES = [
      u'{url}',
      u'({cookie_name})',
      u'Flags:',
      u'[HTTP only]: {httponly}',
      u'(GA analysis: {ga_data})']

  FORMAT_STRING_SHORT_PIECES = [
      u'{host}',
      u'({cookie_name})']

  SOURCE_LONG = 'Firefox Cookies'
  SOURCE_SHORT = 'WEBHIST'
