# -*- coding: utf-8 -*-
"""mac notes formatter."""
from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
#from plaso.lib import errors


class MacNotesNotesFormatter(interface.ConditionalEventFormatter):
  """mac notes zhtmlstring event formatter."""

  DATA_TYPE = 'mac:notes:zhtmlstring'
  """Correct Format String Pieces where needed"""

  FORMAT_STRING_PIECES = [
    'note_body:{zhtmlstring}',
    'last_modified:{last_modified_time}']
  
  FORMAT_STRING_SHORT_PIECES = [
  	'note_body:{zhtmlstring}']


  # TODO: Change the default string formatter.
  SOURCE_LONG = 'Mac Notes Zhtmlstring'
  SOURCE_SHORT = 'Mac Notes'


manager.FormattersManager.RegisterFormatter(MacNotesNotesFormatter)
