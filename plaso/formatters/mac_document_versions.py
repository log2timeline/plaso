# -*- coding: utf-8 -*-
"""The MacOS Document Versions files event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacDocumentVersionsFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MacOS Document Versions page visited event."""

  DATA_TYPE = 'mac:document_versions:file'

  FORMAT_STRING_PIECES = [
      'Version of [{name}]',
      '({path})',
      'stored in {version_path}',
      'by {user_sid}']

  FORMAT_STRING_SHORT_PIECES = [
      'Stored a document version of [{name}]']

  SOURCE_LONG = 'Document Versions'
  SOURCE_SHORT = 'HISTORY'


manager.FormattersManager.RegisterFormatter(MacDocumentVersionsFormatter)
