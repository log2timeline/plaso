# -*- coding: utf-8 -*-
"""The Windows installation event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsRegistryInstallationEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Windows installation event."""

  DATA_TYPE = 'windows:registry:installation'

  FORMAT_STRING_PIECES = [
      '{product_name}',
      '{version}',
      '{build_number}',
      '{service_pack}',
      'Owner: {owner}',
      'Origin: {key_path}']

  FORMAT_STRING_SHORT_PIECES = [
      '{product_name}',
      '{version}',
      '{build_number}',
      '{service_pack}',
      'Origin: {key_path}']

  SOURCE_LONG = 'System'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(
    WindowsRegistryInstallationEventFormatter)
