# -*- coding: utf-8 -*-
"""Formatter for the Google Chrome Preferences file."""

from plaso.formatters import interface
from plaso.formatters import manager


class ChromeExtensionInstallationEventFormatter(
    interface.ConditionalEventFormatter):
  """The event formatter for Chrome Preferences extension installation."""

  DATA_TYPE = 'chrome:preferences:extension_installation'

  FORMAT_STRING_PIECES = [
      u'CRX ID: {extension_id}',
      u'CRX Name: {extension_name}',
      u'Path: {path}',
  ]

  FORMAT_STRING_SHORT_PIECES = [
      u'{extension_id}',
      u'{path}',]

  SOURCE_LONG = 'Chrome Extension Installation'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(
    ChromeExtensionInstallationEventFormatter)
