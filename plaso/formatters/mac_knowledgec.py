# -*- coding: utf-8 -*-
"""The MacOS Document Versions files event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacKnowledgeCApplicationFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MacOS KnowledgeC application event."""

  DATA_TYPE = 'mac:knowledgec:application'

  FORMAT_STRING_PIECES = [
      'Application {bundle_id} executed',
      'during {usage_in_seconds} seconds']

  FORMAT_STRING_SHORT_PIECES = ['Application {bundle_id}']

  SOURCE_LONG = 'KnowledgeC Application'
  SOURCE_SHORT = 'HISTORY'


class MacKnowledgeCSafariFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MacOS KnowledgeC Safari event."""

  DATA_TYPE = 'mac:knowledgec:safari'

  FORMAT_STRING_PIECES = [
      'Safari open uri {uri}',
      'with title {uri_title}',
      'and was visited during {usage_in_seconds} seconds']

  FORMAT_STRING_SHORT_PIECES = ['Safari open uri {uri}']

  SOURCE_LONG = 'KnowledgeC Safari'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatters([
    MacKnowledgeCApplicationFormatter,
    MacKnowledgeCSafariFormatter])
