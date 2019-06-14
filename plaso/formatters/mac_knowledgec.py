# -*- coding: utf-8 -*-
"""The MacOS KnowledgeC datbase event formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MacKnowledgeCApplicationFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MacOS KnowledgeC application event."""

  DATA_TYPE = 'mac:knowledgec:application'

  FORMAT_STRING_PIECES = [
      'Application {bundle_identifier} executed',
      'for {duration} seconds']

  FORMAT_STRING_SHORT_PIECES = ['Application {bundle_identifier}']

  SOURCE_LONG = 'KnowledgeC Application'
  SOURCE_SHORT = 'LOG'


class MacKnowledgeCSafariFormatter(interface.ConditionalEventFormatter):
  """Formatter for a MacOS KnowledgeC Safari event."""

  DATA_TYPE = 'mac:knowledgec:safari'

  FORMAT_STRING_PIECES = [
      'Visited: {url}',
      '({title})',
      'Duration: {duration}'
    ]

  FORMAT_STRING_SHORT_PIECES = ['Safari: {url}']

  SOURCE_LONG = 'KnowledgeC Safari'
  SOURCE_SHORT = 'WEBHIST'


manager.FormattersManager.RegisterFormatters([
    MacKnowledgeCApplicationFormatter,
    MacKnowledgeCSafariFormatter])
