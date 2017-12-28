# -*- coding: utf-8 -*-
"""The OpenXML event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class OpenXMLParserFormatter(interface.ConditionalEventFormatter):
  """Formatter for an OXML event."""

  DATA_TYPE = 'metadata:openxml'

  FORMAT_STRING_PIECES = [
      'Creating App: {creating_app}',
      'App version: {app_version}',
      'Title: {title}',
      'Subject: {subject}',
      'Last saved by: {last_saved_by}',
      'Author: {author}',
      'Total edit time (secs): {total_edit_time}',
      'Keywords: {keywords}',
      'Comments: {comments}',
      'Revision number: {revision_number}',
      'Template: {template}',
      'Number of pages: {number_of_pages}',
      'Number of words: {number_of_words}',
      'Number of characters: {number_of_characters}',
      'Number of characters with spaces: {number_of_characters_with_spaces}',
      'Number of lines: {number_of_lines}',
      'Company: {company}',
      'Manager: {manager}',
      'Shared: {shared}',
      'Security: {security}',
      'Hyperlinks changed: {hyperlinks_changed}',
      'Links up to date: {links_up_to_date}',
      'Scale crop: {scale_crop}',
      'Digital signature: {dig_sig}',
      'Slides: {slides}',
      'Hidden slides: {hidden_slides}',
      'Presentation format: {presentation_format}',
      'MM clips: {mm_clips}',
      'Notes: {notes}']

  FORMAT_STRING_SHORT_PIECES = [
      'Title: {title}',
      'Subject: {subject}',
      'Author: {author}']

  SOURCE_LONG = 'Open XML Metadata'
  SOURCE_SHORT = 'META'


manager.FormattersManager.RegisterFormatter(OpenXMLParserFormatter)
