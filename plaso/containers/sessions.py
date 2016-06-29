# -*- coding: utf-8 -*-
"""Session related attribute container object definitions."""

import collections
import time
import uuid

import plaso
from plaso.containers import interface


class Session(interface.AttributeContainer):
  """Class to represent a session attribute container.

  Attributes:
    analysis_reports_counter (collections.Counter): number of analysis reports.
    command_line_arguments (str): command line arguments.
    completion_time (int): time that the session was completed. Contains the
                           number of micro seconds since January 1, 1970,
                           00:00:00 UTC.
    debug_mode (bool): True if debug mode was enabled.
    event_tags_counter (collections.Counter): number of event tags per label.
    filter_expression (str): filter expression.
    filter_file (str): path to a file with find specifications.
    identifier (str): unique identifier of the session.
    parser_filter_expression (str): parser filter expression.
    parser_plugins_counter (collections.Counter): number of events per parser
                                                  plugin.
    parsers_counter (collections.Counter): number of events per parser.
    preferred_encoding (str): preferred encoding.
    product_name (str): name of the product that created the session
                        e.g. 'log2timeline'.
    product_version (str): version of the product that created the session.
    start_time (int): time that the session was started. Contains the number
                     of micro seconds since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = u'session'

  def __init__(self):
    """Initializes a session attribute container."""
    super(Session, self).__init__()
    self.analysis_reports_counter = collections.Counter()
    self.command_line_arguments = u''
    self.completion_time = None
    self.debug_mode = False
    self.event_tags_counter = collections.Counter()
    self.filter_expression = u''
    self.filter_file = u''
    self.identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    self.parser_filter_expression = u''
    self.parser_plugins_counter = collections.Counter()
    self.parsers_counter = collections.Counter()
    self.preferred_encoding = u'utf-8'
    self.product_name = u'plaso'
    self.product_version = plaso.GetVersion()
    self.start_time = int(time.time() * 1000000)

  def CreateSessionCompletion(self):
    """Creates a session completion.

    Returns:
      SessionCompletion: session completion attribute container.
    """
    self.completion_time = int(time.time() * 1000000)

    session_completion = SessionCompletion()
    session_completion.analysis_reports_counter = self.analysis_reports_counter
    session_completion.event_tags_counter = self.event_tags_counter
    session_completion.identifier = self.identifier
    session_completion.parser_plugins_counter = self.parser_plugins_counter
    session_completion.parsers_counter = self.parsers_counter
    session_completion.timestamp = self.completion_time
    return session_completion

  def CreateSessionStart(self):
    """Creates a session start.

    Returns:
      SessionStart: session start attribute container.
    """
    session_start = SessionStart()
    session_start.command_line_arguments = self.command_line_arguments
    session_start.debug_mode = self.debug_mode
    session_start.filter_expression = self.filter_expression
    session_start.filter_file = self.filter_file
    session_start.identifier = self.identifier
    session_start.parser_filter_expression = self.parser_filter_expression
    session_start.preferred_encoding = self.preferred_encoding
    session_start.product_name = self.product_name
    session_start.product_version = self.product_version
    session_start.timestamp = self.start_time
    return session_start


class SessionCompletion(interface.AttributeContainer):
  """Class to represent a session completion attribute container.

  Attributes:
    analysis_reports_counter (collections.Counter): number of analysis reports.
    event_tags_counter (collections.Counter): number of event tags per label.
    identifier (str): unique identifier of the session.
    parser_plugins_counter (collections.Counter): number of events per parser
                                                  plugin.
    parsers_counter (collections.Counter): number of events per parser.
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
    self.analysis_reports_counter = None
    self.event_tags_counter = None
    self.identifier = identifier
    self.parser_plugins_counter = None
    self.parsers_counter = None
    self.timestamp = None


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
    self.timestamp = None
