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
"""Formatter for the Google extension activity database events."""

from plaso.formatters import interface


class ChromeExtensionActivityEventFormatter(
    interface.ConditionalEventFormatter):
  """The event formatter for Chrome extension activity log entries."""

  DATA_TYPE = 'chrome:extension_activity:activity_log'

  FORMAT_STRING_PIECES = [
      u'Chrome extension: {extension_id}',
      u'Action type: {action_type}',
      u'Activity identifier: {activity_id}',
      u'Page URL: {page_url}',
      u'Page title: {page_title}',
      u'API name: {api_name}',
      u'Args: {args}',
      u'Other: {other}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{extension_id}',
      u'{api_name}',
      u'{args}']

  SOURCE_LONG = 'Chrome Extension Activity'
  SOURCE_SHORT = 'WEBHIST'

  # TODO: add action_type string representation.
