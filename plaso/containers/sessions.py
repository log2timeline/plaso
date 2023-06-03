# -*- coding: utf-8 -*-
"""Session related attribute container definitions."""

import time
import uuid

from acstore.containers import interface
from acstore.containers import manager

import plaso


class Session(interface.AttributeContainer):
  """Session attribute container.

  Attributes:
    aborted (bool): True if the session was aborted.
    artifact_filters (list[str]): Names of artifact definitions that are
        used for filtering file system and Windows Registry key paths.
    command_line_arguments (str): command line arguments.
    completion_time (int): time that the session was completed. Contains the
        number of micro seconds since January 1, 1970, 00:00:00 UTC.
    debug_mode (bool): True if debug mode was enabled.
    enabled_parser_names (list[str]): parser and parser plugin names that
         were enabled.
    filter_file (str): path to a file with find specifications.
    identifier (str): unique identifier of the session.
    parser_filter_expression (str): parser filter expression.
    preferred_codepage (str): preferred codepage.
    preferred_encoding (str): preferred encoding.
    preferred_language (str): preferred language.
    preferred_time_zone (str): preferred time zone.
    preferred_year (int): preferred year.
    product_name (str): name of the product that created the session for
        example "log2timeline".
    product_version (str): version of the product that created the session.
    start_time (int): time that the session was started. Contains the number
        of micro seconds since January 1, 1970, 00:00:00 UTC.
  """

  CONTAINER_TYPE = 'session'

  SCHEMA = {
      'file_entropy': 'str',
      'aborted': 'bool',
      'artifact_filters': 'List[str]',
      'command_line_arguments': 'str',
      'completion_time': 'int',
      'debug_mode': 'bool',
      'enabled_parser_names': 'List[str]',
      'filter_file': 'str',
      'identifier': 'str',
      'parser_filter_expression': 'str',
      'preferred_codepage': 'str',
      'preferred_encoding': 'str',
      'preferred_language': 'str',
      'preferred_time_zone': 'str',
      'preferred_year': 'int',
      'product_name': 'str',
      'product_version': 'str',
      'start_time': 'int'}

  def __init__(self):
    """Initializes a session attribute container."""
    super(Session, self).__init__()
    self.aborted = False
    self.artifact_filters = None
    self.command_line_arguments = None
    self.completion_time = None
    self.debug_mode = False
    self.enabled_parser_names = None
    self.filter_file = None
    self.identifier = '{0:s}'.format(uuid.uuid4().hex)
    self.parser_filter_expression = None
    self.preferred_codepage = None
    self.preferred_encoding = 'utf-8'
    self.preferred_language = None
    self.preferred_time_zone = 'UTC'
    self.preferred_year = None
    self.product_name = 'plaso'
    self.product_version = plaso.__version__
    self.start_time = int(time.time() * 1000000)

  # This method is kept for backwards compatibility.
  def CopyAttributesFromSessionCompletion(self, session_completion):
    """Copies attributes from a session completion.

    Args:
      session_completion (SessionCompletion): session completion attribute
          container.

    Raises:
      ValueError: if the identifier of the session completion does not match
          that of the session.
    """
    if self.identifier != session_completion.identifier:
      raise ValueError('Session identifier mismatch.')

    self.aborted = session_completion.aborted
    self.completion_time = session_completion.timestamp

  # This method is kept for backwards compatibility.
  def CopyAttributesFromSessionConfiguration(self, session_configuration):
    """Copies attributes from a session configuration.

    Args:
      session_configuration (SessionConfiguration): session configuration
          attribute container.

    Raises:
      ValueError: if the identifier of the session configuration does not match
          that of the session.
    """
    if self.identifier != session_configuration.identifier:
      raise ValueError('Session identifier mismatch.')

    self.artifact_filters = session_configuration.artifact_filters
    self.command_line_arguments = session_configuration.command_line_arguments
    self.debug_mode = session_configuration.debug_mode
    self.enabled_parser_names = session_configuration.enabled_parser_names
    self.filter_file = session_configuration.filter_file
    self.parser_filter_expression = (
        session_configuration.parser_filter_expression)
    self.preferred_codepage = session_configuration.preferred_codepage
    self.preferred_encoding = session_configuration.preferred_encoding
    self.preferred_language = session_configuration.preferred_language
    self.preferred_time_zone = session_configuration.preferred_time_zone

  # This method is kept for backwards compatibility.
  def CopyAttributesFromSessionStart(self, session_start):
    """Copies attributes from a session start.

    Args:
      session_start (SessionStart): session start attribute container.
    """
    self.identifier = session_start.identifier
    self.product_name = session_start.product_name
    self.product_version = session_start.product_version
    self.start_time = session_start.timestamp

    # The following is for backward compatibility with older session start
    # attribute containers.
    self.artifact_filters = getattr(
        session_start, 'artifact_filters', self.artifact_filters)
    self.command_line_arguments = getattr(
        session_start, 'command_line_arguments', self.command_line_arguments)
    self.debug_mode = getattr(
        session_start, 'debug_mode', self.debug_mode)
    self.enabled_parser_names = getattr(
        session_start, 'enabled_parser_names', self.enabled_parser_names)
    self.filter_file = getattr(
        session_start, 'filter_file', self.filter_file)
    self.parser_filter_expression = getattr(
        session_start, 'parser_filter_expression',
        self.parser_filter_expression)
    self.preferred_codepage = getattr(
        session_start, 'preferred_codepage', self.preferred_codepage)
    self.preferred_encoding = getattr(
        session_start, 'preferred_encoding', self.preferred_encoding)
    self.preferred_language = getattr(
        session_start, 'preferred_language', self.preferred_language)
    self.preferred_time_zone = getattr(
        session_start, 'preferred_time_zone', self.preferred_time_zone)

  # This method is kept for backwards compatibility.
  def CreateSessionCompletion(self):
    """Creates a session completion.

    Returns:
      SessionCompletion: session completion attribute container.
    """
    self.completion_time = int(time.time() * 1000000)

    session_completion = SessionCompletion()
    session_completion.aborted = self.aborted
    session_completion.identifier = self.identifier
    session_completion.timestamp = self.completion_time
    return session_completion

  # This method is kept for backwards compatibility.
  def CreateSessionConfiguration(self):
    """Creates a session configuraion.

    Returns:
      SessionConfiguration: session configuration attribute container.
    """
    session_completion = SessionConfiguration()
    session_completion.artifact_filters = self.artifact_filters
    session_completion.command_line_arguments = self.command_line_arguments
    session_completion.debug_mode = self.debug_mode
    session_completion.enabled_parser_names = self.enabled_parser_names
    session_completion.filter_file = self.filter_file
    session_completion.identifier = self.identifier
    session_completion.parser_filter_expression = self.parser_filter_expression
    session_completion.preferred_codepage = self.preferred_codepage
    session_completion.preferred_encoding = self.preferred_encoding
    session_completion.preferred_language = self.preferred_language
    session_completion.preferred_time_zone = self.preferred_time_zone
    session_completion.preferred_year = self.preferred_year
    return session_completion

  # This method is kept for backwards compatibility.
  def CreateSessionStart(self):
    """Creates a session start.

    Returns:
      SessionStart: session start attribute container.
    """
    session_start = SessionStart()
    session_start.identifier = self.identifier
    session_start.product_name = self.product_name
    session_start.product_version = self.product_version
    session_start.timestamp = self.start_time
    return session_start


# This class is kept for backwards compatibility.
class SessionCompletion(interface.AttributeContainer):
  """Session completion attribute container.

  Attributes:
    aborted (bool): True if the session was aborted.
    identifier (str): unique identifier of the session.
    timestamp (int): time that the session was completed. Contains the number
        of micro seconds since January 1, 1970, 00:00:00 UTC.
  """

  CONTAINER_TYPE = 'session_completion'

  def __init__(self, identifier=None):
    """Initializes a session completion attribute container.

    Args:
      identifier (Optional[str]): unique identifier of the session.
          The identifier should match that of the corresponding
          session start information.
    """
    super(SessionCompletion, self).__init__()
    self.aborted = False
    self.identifier = identifier
    self.timestamp = None


# This class is kept for backwards compatibility.
class SessionConfiguration(interface.AttributeContainer):
  """Session configuration attribute container.

  The session configuration contains various settings used within a session,
  such as parser and collection filters that are used, and information about
  the source being processed, such as the system configuration determined by
  pre-processing.

  Attributes:
    artifact_filters (list[str]): names of artifact definitions that are
        used for filtering file system and Windows Registry key paths.
    command_line_arguments (str): command line arguments.
    debug_mode (bool): True if debug mode was enabled.
    enabled_parser_names (list[str]): parser and parser plugin names that
         were enabled.
    filter_file (str): path to a file with find specifications.
    identifier (str): unique identifier of the session.
    parser_filter_expression (str): parser filter expression.
    preferred_codepage (str): preferred codepage.
    preferred_encoding (str): preferred encoding.
    preferred_language (str): preferred language.
    preferred_time_zone (str): preferred time zone.
    preferred_year (int): preferred year.
  """

  CONTAINER_TYPE = 'session_configuration'

  def __init__(self, identifier=None):
    """Initializes a session configuration attribute container.

    Args:
      identifier (Optional[str]): unique identifier of the session.
          The identifier should match that of the corresponding
          session start information.
    """
    super(SessionConfiguration, self).__init__()
    self.artifact_filters = None
    self.command_line_arguments = None
    self.debug_mode = False
    self.enabled_parser_names = None
    self.filter_file = None
    self.identifier = identifier
    self.parser_filter_expression = None
    self.preferred_codepage = None
    self.preferred_encoding = None
    self.preferred_language = None
    self.preferred_time_zone = None
    self.preferred_year = None


# This class is kept for backwards compatibility.
class SessionStart(interface.AttributeContainer):
  """Session start attribute container.

  Attributes:
    identifier (str): unique identifier of the session.
    product_name (str): name of the product that created the session for
        example "log2timeline".
    product_version (str): version of the product that created the session.
    timestamp (int): time that the session was started. Contains the number
        of micro seconds since January 1, 1970, 00:00:00 UTC.
  """

  CONTAINER_TYPE = 'session_start'

  def __init__(self, identifier=None):
    """Initializes a session start attribute container.

    Args:
      identifier (Optional[str]): unique identifier of the session.
          The identifier should match that of the corresponding
          session completion information.
    """
    super(SessionStart, self).__init__()
    self.identifier = identifier
    self.product_name = None
    self.product_version = None
    self.timestamp = None


manager.AttributeContainersManager.RegisterAttributeContainers([
    Session, SessionCompletion, SessionConfiguration, SessionStart])
