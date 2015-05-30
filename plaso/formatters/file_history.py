# -*- coding: utf-8 -*-
"""The file history ESE database event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class FileHistoryNamespaceEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a file history ESE database namespace table record."""

  DATA_TYPE = u'file_history:namespace:event'

  FORMAT_STRING_PIECES = [
      u'Filename: {original_filename}',
      u'Identifier: {identifier}',
      u'Parent Identifier: {parent_identifier}',
      u'Attributes: {file_attribute}',
      u'USN number: {usn_number}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Filename: {original_filename}']

  SOURCE_LONG = u'File History Namespace'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(FileHistoryNamespaceEventFormatter)
