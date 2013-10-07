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
"""Formatters for OLE Compound File (OLECF) events."""

from plaso.lib import eventdata


class OleCfItemFormatter(eventdata.EventFormatter):
  """Formatter for an OLECF item."""
  DATA_TYPE = 'olecf:item'

  FORMAT_STRING = u'Name: {name}'
  FORMAT_STRING_SHORT = u'Name: {name}'

  SOURCE_LONG = 'OLECF Item'
  SOURCE_SHORT = 'OLECF'


class OleCfDocumentSummaryInfoFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for an OLECF Summary Info property set stream."""
  DATA_TYPE = 'olecf:document_summary_info'

  FORMAT_STRING_PIECES = [
      u'Number of bytes: {number_of_bytes}',
      u'Number of lines: {number_of_lines}',
      u'Number of paragraphs: {number_of_paragraphs}',
      u'Number of slides: {number_of_slides}',
      u'Number of notes: {number_of_notes}',
      u'Number of hidden slides: {number_of_hidden_slides}',
      u'Number of multi-media clips: {number_of_clips}',
      u'Company: {company}',
      u'Manager: {manager}']

      # TODO: add support for the following properties.
      # u'Is shared: {shared}',
      # u'Document version: {document_version}',
      # u'Language: {language}'
      # u'Digital signature: {digital_signature}',
      # u'Version: {version}',

  FORMAT_STRING_SHORT_PIECES = [
      u'Company: {company}']

  SOURCE_LONG = 'OLECF Document Summary Info'
  SOURCE_SHORT = 'OLECF'


class OleCfSummaryInfoFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for an OLECF Summary Info property set stream."""
  DATA_TYPE = 'olecf:summary_info'

  FORMAT_STRING_PIECES = [
      u'Title: {title}',
      u'Subject: {subject}',
      u'Author: {author}',
      u'Keywords: {keywords}',
      u'Comments: {comments}',
      u'Template: {template}',
      u'Revision number: {revision_number}',
      u'Last saved by: {last_saved_by}',
      u'Total edit time: {total_edit_time}',
      u'Number of pages: {number_of_pages}',
      u'Number of words: {number_of_words}',
      u'Number of characters: {number_of_characters}',
      u'Application: {application}',
      u'Security: {security}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Title: {title}',
      u'Subject: {subject}',
      u'Author: {author}',
      u'Revision number: {revision_number}']

  SOURCE_LONG = 'OLECF Summary Info'
  SOURCE_SHORT = 'OLECF'

  # TODO: add a function to print the security as a descriptive string.
