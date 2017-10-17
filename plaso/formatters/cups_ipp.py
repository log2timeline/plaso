# -*- coding: utf-8 -*-
"""The CUPS IPP file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class CupsIppFormatter(interface.ConditionalEventFormatter):
  """Formatter for a CUPS IPP event."""

  DATA_TYPE = 'cups:ipp:event'

  FORMAT_STRING_PIECES = [
      'Status: {status}',
      'User: {user}',
      'Owner: {owner}',
      'Job Name: {job_name}',
      'Application: {application}',
      'Document type: {type_doc}',
      'Printer: {printer_id}']

  FORMAT_STRING_SHORT_PIECES = [
      'Status: {status}',
      'Job Name: {job_name}']

  SOURCE_LONG = 'CUPS IPP Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(CupsIppFormatter)
