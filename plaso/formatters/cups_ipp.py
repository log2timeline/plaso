# -*- coding: utf-8 -*-
"""Formatter for CUPS IPP file."""

from plaso.formatters import interface
from plaso.formatters import manager


class CupsIppFormatter(interface.ConditionalEventFormatter):
  """Formatter for CUPS IPP file."""

  DATA_TYPE = 'cups:ipp:event'

  FORMAT_STRING_PIECES = [
      u'Status: {status}',
      u'User: {user}',
      u'Owner: {owner}',
      u'Job Name: {job_name}',
      u'Application: {application}',
      u'Document type: {type_doc}',
      u'Printer: {printer_id}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Status: {status}',
      u'Job Name: {job_name}']

  SOURCE_LONG = 'CUPS IPP Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(CupsIppFormatter)
