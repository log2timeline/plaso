# -*- coding: utf-8 -*-
"""The SCCM log formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SCCMEventFormatter(interface.ConditionalEventFormatter):
  """Class for SCCM event formatter."""

  DATA_TYPE = 'software_management:sccm:log'

  FORMAT_STRING_SEPARATOR = ' '

  FORMAT_STRING_PIECES = [
      '{component}',
      '{text}']

  FORMAT_STRING_SHORT_PIECES = ['{text}']

  SOURCE_LONG = 'SCCM Event'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(SCCMEventFormatter)
