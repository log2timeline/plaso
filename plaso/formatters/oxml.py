# -*- coding: utf-8 -*-
"""Formatter for OpenXML events."""

from plaso.formatters import interface
from plaso.formatters import manager


__author__ = 'David Nides (david.nides@gmail.com)'


class OpenXMLParserFormatter(interface.ConditionalEventFormatter):
  """Formatter for OXML events."""

  DATA_TYPE = 'metadata:openxml'

  FORMAT_STRING_PIECES = [
      u'Creating App: {creating_app}',
      u'App version: {app_version}',
      u'Title: {title}',
      u'Subject: {subject}',
      u'Last saved by: {last_saved_by}',
      u'Author: {author}',
      u'Total edit time (secs): {total_edit_time}',
      u'Keywords: {keywords}',
      u'Comments: {comments}',
      u'Revision Num: {revision_num}',
      u'Template: {template}',
      u'Num pages: {num_pages}',
      u'Num words: {num_words}',
      u'Num chars: {num_chars}',
      u'Num chars with spaces: {num_chars_w_spaces}',
      u'Num lines: {num_lines}',
      u'Company: {company}',
      u'Manager: {manager}',
      u'Shared: {shared}',
      u'Security: {security}',
      u'Hyperlinks changed: {hyperlinks_changed}',
      u'Links up to date: {links_up_to_date}',
      u'Scale crop: {scale_crop}',
      u'Digital signature: {dig_sig}',
      u'Slides: {slides}',
      u'Hidden slides: {hidden_slides}',
      u'Presentation format: {presentation_format}',
      u'MM clips: {mm_clips}',
      u'Notes: {notes}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Title: {title}',
      u'Subject: {subject}',
      u'Author: {author}']

  SOURCE_LONG = 'Open XML Metadata'
  SOURCE_SHORT = 'META'


manager.FormattersManager.RegisterFormatter(OpenXMLParserFormatter)
