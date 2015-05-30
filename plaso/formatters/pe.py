# -*- coding: utf-8 -*-
"""The PE event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class PEEventFormatter(interface.ConditionalEventFormatter):
  """Parent class for PE event formatters."""
  DATA_TYPE = u'pe'
  FORMAT_STRING_SEPARATOR = u' '

  FORMAT_STRING_PIECES = [
      u'PE Type: {pe_type}',
      u'Import hash: {imphash}',]

  FORMAT_STRING_SHORT_PIECES = [u'pe_type']

  SOURCE_LONG = u'PE Event'
  SOURCE_SHORT = u'PE'


class PECompilationFormatter(PEEventFormatter):
  """Formatter for a PE compilation event."""
  DATA_TYPE = u'pe:compilation:compilation_time'
  SOURCE_LONG = u'PE Compilation time'


class PEImportFormatter(PEEventFormatter):
  """Formatter for a PE import section event."""
  DATA_TYPE = u'pe:import:import_time'
  FORMAT_STRING_PIECES = [
      u'DLL name: {dll_name}',
      u'PE Type: {pe_type}',
      u'Import hash: {imphash}',]
  FORMAT_STRING_SHORT_PIECES = [u'{dll_name}']
  SOURCE_LONG = u'PE Import Time'


class PEDelayImportFormatter(PEEventFormatter):
  """Formatter for a PE delay import section event."""
  DATA_TYPE = u'pe:delay_import:import_time'
  FORMAT_STRING_PIECES = [
      u'DLL name: {dll_name}',
      u'PE Type: {pe_type}',
      u'Import hash: {imphash}',]
  FORMAT_STRING_SHORT_PIECES = [u'{dll_name}']
  SOURCE_LONG = u'PE Delay Import Time'


class PEResourceCreationFormatter(PEEventFormatter):
  """Formatter for a PE resource creation event."""
  DATA_TYPE = u'pe:resource:creation_time'
  SOURCE_LONG = u'PE Resource Creation Time'


class PELoadConfigModificationEvent(PEEventFormatter):
  """Formatter for a PE load configuration table event."""
  DATA_TYPE = u'pe:load_config:modification_time'
  SOURCE_LONG = u'PE Load Configuration Table Time'


manager.FormattersManager.RegisterFormatters([
    PECompilationFormatter, PEImportFormatter,
    PEDelayImportFormatter, PEResourceCreationFormatter,
    PELoadConfigModificationEvent])
