# -*- coding: utf-8 -*-
"""The Android Application Usage event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class AndroidApplicationFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Application Last Resumed event."""

  DATA_TYPE = u'android:event:last_resume_time'

  FORMAT_STRING_PIECES = [
      u'Package: {package}',
      u'Component: {component}']

  SOURCE_LONG = u'Android App Usage'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(AndroidApplicationFormatter)
