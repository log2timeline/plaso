# -*- coding: utf-8 -*-
"""Formatter for the AppCompatCache entries inside the Windows Registry."""

from plaso.formatters import interface
from plaso.formatters import manager


class AppCompatCacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for an AppCompatCache Windows Registry entry."""

  DATA_TYPE = 'windows:registry:appcompatcache'

  FORMAT_STRING_PIECES = [
      u'[{keyname}]',
      u'Cached entry: {entry_index}',
      u'Path: {path}']

  FORMAT_STRING_SHORT_PIECES = [u'Path: {path}']

  SOURCE_LONG = 'AppCompatCache Registry Entry'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(AppCompatCacheFormatter)
