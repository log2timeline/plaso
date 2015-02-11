# -*- coding: utf-8 -*-
"""This file contains a formatter for the Mac OS X application usage."""

from plaso.formatters import interface
from plaso.formatters import manager


class ApplicationUsageFormatter(interface.EventFormatter):
  """Define the formatting for Application Usage information."""

  DATA_TYPE = 'macosx:application_usage'

  FORMAT_STRING = (
      u'{application} v.{app_version} (bundle: {bundle_id}). '
      u'Launched: {count} time(s)')
  FORMAT_STRING_SHORT = u'{application} ({count} time(s))'

  SOURCE_LONG = 'Application Usage'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(ApplicationUsageFormatter)
