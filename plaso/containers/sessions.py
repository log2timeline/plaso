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


manager.AttributeContainersManager.RegisterAttributeContainer(Session)
