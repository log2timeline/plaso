# -*- coding: utf-8 -*-
"""The Network drive event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class NetworkDriveEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Network drive event."""

  DATA_TYPE = 'windows:registry:network_drive'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'DriveLetter: {drive_letter}',
      'RemoteServer: {server_name}',
      'ShareName: {share_name}',
      'Type: Mapped Drive']

  SOURCE_LONG = 'Registry Key : Network Drive'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(NetworkDriveEventFormatter)
