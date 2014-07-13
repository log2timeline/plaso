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
"""Formatter for the shell item events."""

from plaso.formatters import interface


class ShellItemFileEntryEventFormatter(interface.ConditionalEventFormatter):
  """Class that formats Windows volume creation events."""

  DATA_TYPE = 'windows:shell_item:file_entry'

  FORMAT_STRING_PIECES = [
      u'Name: {name}',
      u'Long name: {long_name}',
      u'Localized name: {localized_name}',
      u'Origin: {origin}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Name: {name}',
      u'Origin: {origin}']

  SOURCE_LONG = 'File entry shell item'
  SOURCE_SHORT = 'FILE'
