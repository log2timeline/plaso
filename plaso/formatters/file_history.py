# -*- coding: utf-8 -*-
"""The file history ESE database event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class FileHistoryNamespaceEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a file history ESE database namespace table record."""

  DATA_TYPE = 'file_history:namespace:event'

  FORMAT_STRING_PIECES = [
      'Filename: {original_filename}',
      'Identifier: {identifier}',
      'Parent Identifier: {parent_identifier}',
      'Attributes: {file_attribute}',
      'USN number: {usn_number}']

  FORMAT_STRING_SHORT_PIECES = [
      'Filename: {original_filename}']

  SOURCE_LONG = 'File History Namespace'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(FileHistoryNamespaceEventFormatter)
