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
"""This file contains a formatter for the Mac OS X Document Versions files."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacDocumentVersionsFormatter(interface.ConditionalEventFormatter):
  """The event formatter for page visited data in Document Versions."""

  DATA_TYPE = 'mac:document_versions:file'

  FORMAT_STRING_PIECES = [
      u'Version of [{name}]',
      u'({path})',
      u'stored in {version_path}',
      u'by {user_sid}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Stored a document version of [{name}]']

  SOURCE_LONG = 'Document Versions'
  SOURCE_SHORT = 'HISTORY'


manager.FormattersManager.RegisterFormatter(MacDocumentVersionsFormatter)
