# -*- coding: utf-8 -*-
"""Event formatter for the MountPoints2 key."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class MountPoints2Formatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows Boot Execute event."""

  DATA_TYPE = 'windows:registry:mount_points2'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Label: {label}',
      'Remote_Server: {server_name}',
      'Share_Name: {share_name}',
      'Type: {type}',
      'Volume: {name}']

  FORMAT_STRING_SHORT_PIECES = [
      '[{key_path}]',
      'Label: {label}',
      'Remote_Server: {server_name}',
      'Share_Name: {share_name}',
      'Type: {type}',
      'Volume: {name}']

  SOURCE_LONG = 'Registry Key'
  SOURCE_SHORT = 'REG'


manager.FormattersManager.RegisterFormatter(MountPoints2Formatter)
