# -*- coding: utf-8 -*-
"""The Windows Registry AppCompatCache entries event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class AppCompatCacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for an AppCompatCache Windows Registry event."""

  DATA_TYPE = 'windows:registry:appcompatcache'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Cached entry: {entry_index}',
      'Path: {path}']

  FORMAT_STRING_SHORT_PIECES = ['Path: {path}']

  SOURCE_LONG = 'AppCompatCache Registry Entry'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(AppCompatCacheFormatter)
