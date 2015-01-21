#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 The Plaso Project Authors.
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
"""Formatter for the Google Chrome Preferences file."""

from plaso.formatters import interface


class ChromeExtensionInstallationEventFormatter(
    interface.ConditionalEventFormatter):
  """The event formatter for Chrome Preferences extension installation."""

  DATA_TYPE = 'chrome:preferences:extension_installation'

  FORMAT_STRING_PIECES = [
    u'CRX ID: {extension_id}',
    u'CRX Name: {extension_name}',
    u'Path: {path}',
  ]

  FORMAT_STRING_SHORT_PIECES = [
      u'{extension_id}',
      u'{path}',]

  SOURCE_LONG = 'Chrome Extension Installation'
  SOURCE_SHORT = 'LOG'
