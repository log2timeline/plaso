# -*- coding: utf-8 -*-
"""Session related attribute container object definitions."""

import time

import plaso
from plaso.containers import interface


class SessionCompletion(interface.AttributeContainer):
  """Class to represent a session completion attribute container.

  Attributes:
    parsers_counter: TODO
    parser_plugins_counter: TODO
    timestamp: an integer containing a timestamp of the completion of the
               session. The integer represents the number of micro seconds
               since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = u'session_completion'

  def __init__(self):
    """Initializes a session completion attribute container."""
    super(SessionCompletion, self).__init__()
    self.parsers_counter = None
    self.parser_plugins_counter = None
    self.timestamp = int(time.time() * 100000)


class SessionStart(interface.AttributeContainer):
  """Class to represent a session start attribute container.

  Attributes:
    command_line_arguments: string containing the command line arguments.
    filter_expression: string containing the filter expression.
    filter_file: string containing the path to a file with find specifications.
    debug_mode: a boolean value to indicate the debug mode was enabled.
    parser_filter_expression: string containining the parser filter expression.
    preferred_encoding: string containing the preferred encoding.
    product_name: a string containing the name of the product that created
                  the session.
    product_version: a string containing the version of the product that
                     created the session.
    timestamp: an integer containing a timestamp of the start of the
               session. The integer represents the number of micro seconds
               since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = u'session_start'

  def __init__(self):
    """Initializes a session start attribute container."""
    super(SessionStart, self).__init__()
    self.command_line_arguments = u''
    self.debug_mode = False
    self.filter_expression = u''
    self.filter_file = u''
    self.parser_filter_expression = u''
    self.preferred_encoding = u'utf-8'
    self.product_name = u'plaso'
    self.product_version = plaso.GetVersion()
    self.timestamp = int(time.time() * 100000)
