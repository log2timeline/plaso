# -*- coding: utf-8 -*-
"""The MacOS application usage event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ApplicationUsageFormatter(interface.EventFormatter):
  """Formatter for a MacOS Application usage event."""

  DATA_TYPE = 'macosx:application_usage'

  FORMAT_STRING = (
      '{application} v.{app_version} (bundle: {bundle_id}). '
      'Launched: {count} time(s)')
  FORMAT_STRING_SHORT = '{application} ({count} time(s))'

  SOURCE_LONG = 'Application Usage'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(ApplicationUsageFormatter)
