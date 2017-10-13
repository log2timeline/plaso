# -*- coding: utf-8 -*-
"""The Android Application Usage event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class AndroidApplicationFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Application Last Resumed event."""

  DATA_TYPE = 'android:event:last_resume_time'

  FORMAT_STRING_PIECES = [
      'Package: {package}',
      'Component: {component}']

  SOURCE_LONG = 'Android App Usage'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(AndroidApplicationFormatter)
