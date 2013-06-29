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
"""Formatter for OLECF events."""

from plaso.lib import eventdata

__author__ = 'David Nides (david.nides@gmail.com)'


class OLECFFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for OLECF based events."""

  DATA_TYPE = 'metadata:OLECF'

  FORMAT_STRING_PIECES = [
      u'Creating application: {creating_application}',
      u'Title: {title}',
      u'Subject: {subject}',
      u'Last saved by: {last_saved_by}',
      u'Author: {author}',
      u'Total edit time (secs): {total_edit_time}',
      u'Keywords: {keywords}',
      u'Comments: {comments}',
      u'Revision number: {revision_number}',
      u'Version: {version}',
      u'Doc Version: {doc_version}',
      u'Template: {template}',
      u'Num pages: {num_pages}',
      u'Num words: {num_words}',
      u'Num chars: {num_chars}',
      u'Company: {company}',
      u'Manager: {manager}',
      u'Shared: {shared_doc}',
      u'Security: {security}',
      u'Digital Signature: {dig_sig}',
      u'Codepage: {codepage}',
      u'Language: {language}',
      u'Slides: {slides}',
      u'Hidden Slides: {hidden_slides}',
      u'MM Clips: {mm_clips}',
      u'Notes: {m_notes}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Title: {title}',
      u'Subject: {subject}',
      u'Author: {author}']

  SOURCE_LONG = 'OLECF Metadata'
  SOURCE_SHORT = 'META'
