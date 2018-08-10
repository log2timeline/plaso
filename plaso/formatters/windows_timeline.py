# -*- coding: utf-8 -*-
"""The Windows Timeline event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

class WindowsTimelineGenericEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for generic Windows Timeline events."""

  DATA_TYPE = 'windows:timeline:generic'

  FORMAT_STRING_PIECES = [
      'Application Display Name: {application_display_name}',
      'Package Identifier: {package_identifier}',
      'Description: {description}']

  FORMAT_STRING_SHORT_PIECES = ['{package_identifier}']

  SOURCE_LONG = 'Windows Timeline - Generic'
  SOURCE_SHORT = 'Windows Timeline'

class WindowsTimelineUserEngagedEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for User Engaged Windows Timeline events"""

  DATA_TYPE = 'windows:timeline:user_engaged'

  FORMAT_STRING_PIECES = [
      'Package Identifier: {package_identifier}',
      'Active Duration (seconds): {active_duration_seconds}',
      'Reporting App: {reporting_app}']

  FORMAT_STRING_SHORT_PIECES = ['{package_identifier}']

  SOURCE_LONG = 'Windows Timeline - User Engaged'
  SOURCE_SHORT = 'Windows Timeline'

manager.FormattersManager.RegisterFormatters([
    WindowsTimelineGenericEventFormatter,
    WindowsTimelineUserEngagedEventFormatter])
