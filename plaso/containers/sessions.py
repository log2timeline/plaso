# -*- coding: utf-8 -*-
"""Session related attribute container object definitions."""

import time
import uuid

import plaso
from plaso.containers import interface


class SessionCompletion(interface.AttributeContainer):
  """Class to represent a session completion attribute container.

  Attributes:
    identifier (str): unique identifier of the session.
    parsers_counter (collections.Counter): number of events per parser.
    parser_plugins_counter (collections.Counter): number of events per parser
                                                  plugin.
    timestamp (int): time that the session was completed. Contains the number
                     of micro seconds since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = u'session_completion'

  def __init__(self, identifier=None):
    """Initializes a session completion attribute container.

    Args:
      identifier (Optional[str]): unique identifier of the session.
          The identifier should match that of the corresponding
          session start information.
    """
    super(SessionCompletion, self).__init__()
    self.identifier = identifier
    self.parsers_counter = None
    self.parser_plugins_counter = None
    self.timestamp = int(time.time() * 1000000)


class SessionStart(interface.AttributeContainer):
  """Class to represent a session start attribute container.

  Attributes:
    command_line_arguments (str): command line arguments.
    debug_mode (bool): True if debug mode was enabled.
    filter_expression (str): filter expression.
    filter_file (str): path to a file with find specifications.
    identifier (str): unique identifier of the session.
    parser_filter_expression (str): parser filter expression.
    preferred_encoding (str): preferred encoding.
    product_name (str): name of the product that created the session
                        e.g. 'log2timeline'.
    product_version (str): version of the product that created the session.
    timestamp (int): time that the session was started. Contains the number
                     of micro seconds since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = u'session_start'

  def __init__(self):
    """Initializes a session start attribute container."""
    super(SessionStart, self).__init__()
    self.command_line_arguments = u''
    self.debug_mode = False
    self.filter_expression = u''
    self.filter_file = u''
    self.identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    self.parser_filter_expression = u''
    self.preferred_encoding = u'utf-8'
    self.product_name = u'plaso'
    self.product_version = plaso.GetVersion()
    self.timestamp = int(time.time() * 1000000)
