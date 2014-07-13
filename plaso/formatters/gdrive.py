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
"""This file contains a formatter for the Google Drive snaphots."""

from plaso.formatters import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class GDriveCloudEntryFormatter(interface.ConditionalEventFormatter):
  """Formatter for Google Drive snapshot cloud entry."""

  DATA_TYPE = 'gdrive:snapshot:cloud_entry'

  FORMAT_STRING_PIECES = [
      u'File Path: {path}',
      u'[{shared}]',
      u'Size: {size}',
      u'URL: {url}',
      u'Type: {document_type}']
  FORMAT_STRING_SHORT_PIECES = [u'{path}']

  SOURCE_LONG = 'Google Drive (cloud entry)'
  SOURCE_SHORT = 'LOG'


class GDriveLocalEntryFormatter(interface.ConditionalEventFormatter):
  """Formatter for Google Drive snapshot local entry."""

  DATA_TYPE = 'gdrive:snapshot:local_entry'

  FORMAT_STRING_PIECES = [
      u'File Path: {path}',
      u'Size: {size}']

  FORMAT_STRING_SHORT_PIECES = [u'{path}']

  SOURCE_LONG = 'Google Drive (local entry)'
  SOURCE_SHORT = 'LOG'
