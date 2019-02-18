# -*- coding: utf-8 -*-
"""mac notes formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class MacNotesZhtmlstringFormatter(interface.ConditionalEventFormatter):
  """mac notes zhtmlstring event formatter."""

  DATA_TYPE = 'mac:notes:zhtmlstring'
  """Correct Format String Pieces where needed"""

  FORMAT_STRING_PIECES = [
    'zhtmlstring:{zhtmlstring}']


  # TODO: Change the default string formatter.
  SOURCE_LONG = 'Mac Notes Zhtmlstring'
  SOURCE_SHORT = 'Mac Notes'


manager.FormattersManager.RegisterFormatter([MacNotesZhtmlstringFormatter])
