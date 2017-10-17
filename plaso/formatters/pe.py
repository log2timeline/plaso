# -*- coding: utf-8 -*-
"""The PE event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class PEEventFormatter(interface.ConditionalEventFormatter):
  """Parent class for PE event formatters."""
  DATA_TYPE = 'pe'
  FORMAT_STRING_SEPARATOR = ' '

  FORMAT_STRING_PIECES = [
      'PE Type: {pe_type}',
      'Import hash: {imphash}',]

  FORMAT_STRING_SHORT_PIECES = ['pe_type']

  SOURCE_LONG = 'PE Event'
  SOURCE_SHORT = 'PE'


class PECompilationFormatter(PEEventFormatter):
  """Formatter for a PE compilation event."""
  DATA_TYPE = 'pe:compilation:compilation_time'
  SOURCE_LONG = 'PE Compilation time'


class PEImportFormatter(PEEventFormatter):
  """Formatter for a PE import section event."""
  DATA_TYPE = 'pe:import:import_time'
  FORMAT_STRING_PIECES = [
      'DLL name: {dll_name}',
      'PE Type: {pe_type}',
      'Import hash: {imphash}',]
  FORMAT_STRING_SHORT_PIECES = ['{dll_name}']
  SOURCE_LONG = 'PE Import Time'


class PEDelayImportFormatter(PEEventFormatter):
  """Formatter for a PE delay import section event."""
  DATA_TYPE = 'pe:delay_import:import_time'
  FORMAT_STRING_PIECES = [
      'DLL name: {dll_name}',
      'PE Type: {pe_type}',
      'Import hash: {imphash}',]
  FORMAT_STRING_SHORT_PIECES = ['{dll_name}']
  SOURCE_LONG = 'PE Delay Import Time'


class PEResourceCreationFormatter(PEEventFormatter):
  """Formatter for a PE resource creation event."""
  DATA_TYPE = 'pe:resource:creation_time'
  SOURCE_LONG = 'PE Resource Creation Time'


class PELoadConfigModificationEvent(PEEventFormatter):
  """Formatter for a PE load configuration table event."""
  DATA_TYPE = 'pe:load_config:modification_time'
  SOURCE_LONG = 'PE Load Configuration Table Time'


manager.FormattersManager.RegisterFormatters([
    PECompilationFormatter, PEImportFormatter,
    PEDelayImportFormatter, PEResourceCreationFormatter,
    PELoadConfigModificationEvent])
