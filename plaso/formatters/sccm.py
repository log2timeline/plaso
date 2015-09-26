# -*- coding: utf-8 -*-
"""The SCCM log formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class SCCMEventFormatter(interface.ConditionalEventFormatter):
  """Class for SCCM event formatter."""

  DATA_TYPE = u'software_management:sccm:log'

  FORMAT_STRING_SEPARATOR = u' '

  FORMAT_STRING_PIECES = [u'{component}',
                          u'{text}']

  FORMAT_STRING_SHORT_PIECES = [u'{text}']

  SOURCE_LONG = u'SCCM Event'
  SOURCE_SHORT = u'LOG'

manager.FormattersManager.RegisterFormatter(SCCMEventFormatter)
