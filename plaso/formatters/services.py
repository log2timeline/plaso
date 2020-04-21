# -*- coding: utf-8 -*-
"""The Windows services event formatter.

The Windows services are derived from Windows Registry files.
"""

from __future__ import unicode_literals

from plaso.formatters import manager
from plaso.formatters import interface
from plaso.winnt import human_readable_service_enums


class WinRegistryServiceFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows service event."""

  DATA_TYPE = 'windows:registry:service'

  FORMAT_STRING_PIECES = [
      '[{key_path}]',
      'Type: {service_type}',
      'Start: {start_type}',
      'Image path: {image_path}',
      'Error control: {error_control}',
      '{values}']

  FORMAT_STRING_SHORT_PIECES = [
      '[{key_path}]',
      'Type: {service_type}',
      'Start: {start_type}',
      'Image path: {image_path}',
      'Error control: {error_control}',
      '{values}']

  def __init__(self):
    """Initializes a Windows service event format helper."""
    super(WinRegistryServiceFormatter, self).__init__()
    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='error_control',
        output_attribute='error_control', values=(
            human_readable_service_enums.SERVICE_ENUMS['ErrorControl']))

    self.helpers.append(helper)

    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='service_type',
        output_attribute='service_type', values=(
            human_readable_service_enums.SERVICE_ENUMS['Type']))

    self.helpers.append(helper)

    helper = interface.EnumerationEventFormatterHelper(
        default='UNKNOWN', input_attribute='start_type',
        output_attribute='start_type', values=(
            human_readable_service_enums.SERVICE_ENUMS['Start']))

    self.helpers.append(helper)


manager.FormattersManager.RegisterFormatter(WinRegistryServiceFormatter)
