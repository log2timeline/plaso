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
"""Formatter for MS Office 2003 events."""

from plaso.lib import eventdata

__author__ = 'David Nides (david.nides@gmail.com)'


class Office2003Formatter(eventdata.ConditionalEventFormatter):
  """Formatter for MS Office 2003 based events."""

  DATA_TYPE = 'metadata:office2003'

  FORMAT_STRING_PIECES = [
      u'Title: {title}',
      u'Subject: {subject}',
      u'Author: {author}',
      u'Keywords: {keywords}',
      u'Comments: {comments}',
      u'Template: {template}',
      u'Last saved by: {last_saved_by}',
      u'Revision number: {revision_number}',
      u'Total edit time: {total_edit_time}',
      u'Num pages: {num_pages}',
      u'Num words: {num_words}',
      u'Num chars: {num_chars}',
      u'Security: {security}',
      u'Codepage: {codepage}',
      u'Creating application: {creating_application}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Title: {title}',
      u'Subject: {subject}',
      u'Author: {author}']

  SOURCE_LONG = 'Office Metadata'
  SOURCE_SHORT = 'META'
