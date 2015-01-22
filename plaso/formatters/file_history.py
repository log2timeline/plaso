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
"""Formatters for the file history ESE database events."""

from plaso.formatters import interface
from plaso.formatters import manager


class FileHistoryNamespaceEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a file history ESE database namespace table record."""

  DATA_TYPE = 'file_history:namespace:event'

  FORMAT_STRING_PIECES = [
      u'Filename: {original_filename}',
      u'Identifier: {identifier}',
      u'Parent Identifier: {parent_identifier}',
      u'Attributes: {file_attribute}',
      u'USN number: {usn_number}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Filename: {original_filename}']

  SOURCE_LONG = 'File History Namespace'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(FileHistoryNamespaceEventFormatter)
