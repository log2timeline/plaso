# -*- coding: utf-8 -*-
"""Session related attribute container object definitions."""

import collections
import time
import uuid

import plaso
from plaso.containers import interface
from plaso.containers import manager


class Session(interface.AttributeContainer):
  """Class to represent a session attribute container.

  Attributes:
    analysis_reports_counter (collections.Counter): number of analysis reports
        per analysis plugin.
    command_line_arguments (str): command line arguments.
    completion_time (int): time that the session was completed. Contains the
        number of micro seconds since January 1, 1970, 00:00:00 UTC.
    debug_mode (bool): True if debug mode was enabled.
    enabled_parser_names (list[str]): parser and parser plugin names that
         were enabled.
    event_labels_counter (collections.Counter): number of event tags per label.
    filter_expression (str): expression to filter events.
    filter_file (str): path to a file with find specifications.
    identifier (str): unique identifier of the session.
    parser_filter_expression (str): parser filter expression.
    parsers_counter (collections.Counter): number of events per parser or
        parser plugin.
    preferred_encoding (str): preferred encoding.
    preferred_year (int): preferred year.
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
    self.command_line_arguments = None
    self.completion_time = None
    self.debug_mode = False
    self.enabled_parser_names = None
    self.event_labels_counter = collections.Counter()
    self.filter_expression = None
    self.filter_file = None
    self.identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    self.parser_filter_expression = None
    self.parsers_counter = collections.Counter()
    self.preferred_encoding = u'utf-8'
    self.preferred_year = None
    self.product_name = u'plaso'
    self.product_version = plaso.GetVersion()
    self.start_time = int(time.time() * 1000000)

  def CopyAttributesFromSessionCompletion(self, session_completion):
    """Copies attributes from a session completion.

    Args:
      session_completion (SessionCompletion): session completion attribute
          container.

    Raises:
      ValueError: if the identifier fo the session completion does not match
          that of the session.
    """
    if self.identifier != session_completion.identifier:
      raise ValueError(u'Session identifier mismatch.')

    if session_completion.analysis_reports_counter:
      self.analysis_reports_counter = (
          session_completion.analysis_reports_counter)

    self.completion_time = session_completion.timestamp

    if session_completion.event_labels_counter:
      self.event_labels_counter = session_completion.event_labels_counter

    if session_completion.parsers_counter:
      self.parsers_counter = session_completion.parsers_counter

  def CopyAttributesFromSessionStart(self, session_start):
    """Copies attributes from a session start.

    Args:
      session_start (SessionStart): session start attribute container.
    """
    self.command_line_arguments = session_start.command_line_arguments
    self.debug_mode = session_start.debug_mode
    self.enabled_parser_names = session_start.enabled_parser_names
    self.filter_expression = session_start.filter_expression
    self.filter_file = session_start.filter_file
    self.identifier = session_start.identifier
    self.parser_filter_expression = session_start.parser_filter_expression
    self.preferred_encoding = session_start.preferred_encoding
    self.product_name = session_start.product_name
    self.product_version = session_start.product_version
    self.start_time = session_start.timestamp

  def CreateSessionCompletion(self):
    """Creates a session completion.

    Returns:
      SessionCompletion: session completion attribute container.
    """
    self.completion_time = int(time.time() * 1000000)

    session_completion = SessionCompletion()
    session_completion.analysis_reports_counter = self.analysis_reports_counter
    session_completion.event_labels_counter = self.event_labels_counter
    session_completion.identifier = self.identifier
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
    session_start.enabled_parser_names = self.enabled_parser_names
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
    analysis_reports_counter (collections.Counter): number of analysis reports
        per analysis plugin.
    event_labels_counter (collections.Counter): number of event tags per label.
    identifier (str): unique identifier of the session.
    parsers_counter (collections.Counter): number of events per parser or
        parser plugin.
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
    self.event_labels_counter = None
    self.identifier = identifier
    self.parsers_counter = None
    self.timestamp = None


class SessionStart(interface.AttributeContainer):
  """Class to represent a session start attribute container.

  Attributes:
    command_line_arguments (str): command line arguments.
    debug_mode (bool): True if debug mode was enabled.
    enabled_parser_names (list[str]): parser and parser plugin names that
         were enabled.
    filter_expression (str): expression to filter events.
    filter_file (str): path to a file with find specifications.
    identifier (str): unique identifier of the session.
    parser_filter_expression (str): parser filter expression.
    preferred_encoding (str): preferred encoding.
    preferred_year (int): preferred year.
    product_name (str): name of the product that created the session
        e.g. 'log2timeline'.
    product_version (str): version of the product that created the session.
    timestamp (int): time that the session was started. Contains the number
        of micro seconds since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = u'session_start'

  def __init__(self, identifier=None):
    """Initializes a session start attribute container.

    Args:
      identifier (Optional[str]): unique identifier of the session.
          The identifier should match that of the corresponding
          session completion information.
    """
    super(SessionStart, self).__init__()
    self.command_line_arguments = None
    self.debug_mode = False
    self.enabled_parser_names = None
    self.filter_expression = None
    self.filter_file = None
    self.identifier = identifier
    self.parser_filter_expression = None
    self.preferred_encoding = None
    self.preferred_year = None
    self.product_name = None
    self.product_version = None
    self.timestamp = None


manager.AttributeContainersManager.RegisterAttributeContainers([
    Session, SessionCompletion, SessionStart])
