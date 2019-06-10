# -*- coding: utf-8 -*-
"""Event formatters for the Less Frequently Used Keys."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WindowsBootExecuteFormatter(interface.EventFormatter):
  """Formatter for a Windows Boot Execute event."""

  DATA_TYPE = 'windows:registry:boot_execute'

  FORMAT_STRING = '[{key_path}] BootExecute: {value}'
  FORMAT_STRING_ALTERNATIVE = 'BootExecute: {value}'

  SOURCE_LONG = 'Registry Key'
  SOURCE_SHORT = 'REG'


class WindowsBootVerificationFormatter(interface.EventFormatter):
  """Formatter for a Windows Boot Verification event."""

  DATA_TYPE = 'windows:registry:boot_verification'

  FORMAT_STRING = '[{key_path}] ImagePath: {image_path}'
  FORMAT_STRING_ALTERNATIVE = 'ImagePath: {image_path}'

  SOURCE_LONG = 'Registry Key'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatters([
    WindowsBootExecuteFormatter, WindowsBootVerificationFormatter])
