# -*- coding: utf-8 -*-
"""Formatter for the shell item events."""

from plaso.formatters import interface
from plaso.formatters import manager


class ShellItemFileEntryEventFormatter(interface.ConditionalEventFormatter):
  """Class that formats Windows volume creation events."""

  DATA_TYPE = 'windows:shell_item:file_entry'

  FORMAT_STRING_PIECES = [
      u'Name: {name}',
      u'Long name: {long_name}',
      u'Localized name: {localized_name}',
      u'NTFS file reference: {file_reference}',
      u'Origin: {origin}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Name: {name}',
      u'NTFS file reference: {file_reference}',
      u'Origin: {origin}']

  SOURCE_LONG = 'File entry shell item'
  SOURCE_SHORT = 'FILE'


manager.FormattersManager.RegisterFormatter(ShellItemFileEntryEventFormatter)
