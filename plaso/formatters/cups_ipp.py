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
"""Formatter for CUPS IPP file."""

from plaso.formatters import interface


class CupsIppFormatter(interface.ConditionalEventFormatter):
  """Formatter for CUPS IPP file."""

  DATA_TYPE = 'cups:ipp:event'

  FORMAT_STRING_PIECES = [
      u'Status: {status}',
      u'User: {user}',
      u'Owner: {owner}',
      u'Job Name: {job_name}',
      u'Application: {application}',
      u'Document type: {type_doc}',
      u'Printer: {printer_id}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Status: {status}',
      u'Job Name: {job_name}']

  SOURCE_LONG = 'CUPS IPP Log'
  SOURCE_SHORT = 'LOG'
