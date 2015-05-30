# -*- coding: utf-8 -*-
"""The Mac OS X application usage event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class ApplicationUsageFormatter(interface.EventFormatter):
  """Formatter for a Mac OS X Application usage event."""

  DATA_TYPE = u'macosx:application_usage'

  FORMAT_STRING = (
      u'{application} v.{app_version} (bundle: {bundle_id}). '
      u'Launched: {count} time(s)')
  FORMAT_STRING_SHORT = u'{application} ({count} time(s))'

  SOURCE_LONG = u'Application Usage'
  SOURCE_SHORT = u'LOG'


manager.FormattersManager.RegisterFormatter(ApplicationUsageFormatter)
