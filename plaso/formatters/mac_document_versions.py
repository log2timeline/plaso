# -*- coding: utf-8 -*-
"""The Mac OS X Document Versions files event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class MacDocumentVersionsFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Mac OS X Document Versions page visited event."""

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
