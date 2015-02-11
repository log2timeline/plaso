# -*- coding: utf-8 -*-
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
