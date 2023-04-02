# -*- coding: utf-8 -*-
"""The artifact knowledge base object.

The knowledge base is filled by user provided input and the pre-processing
phase. It is intended to provide successive phases, like the parsing and
analysis phases, with essential information like the time zone and codepage
of the source data.
"""

import codecs
import pytz

from plaso.engine import logger


class KnowledgeBase(object):
  """The knowledge base."""

  _DEFAULT_ACTIVE_SESSION = '00000000000000000000000000000000'

  def __init__(self):
    """Initializes a knowledge base."""
    super(KnowledgeBase, self).__init__()
    self._active_session = self._DEFAULT_ACTIVE_SESSION
    self._codepage = 'cp1252'
    self._environment_variables = {}
    self._hostnames = {}
    self._language = 'en-US'
    self._mount_path = None
    self._time_zone = pytz.UTC
    self._values = {}

  @property
  def codepage(self):
    """str: codepage of the current session."""
    return self.GetValue('codepage', default_value=self._codepage)

  @property
  def language(self):
    """str: language of the current session."""
    return self.GetValue('language', default_value=self._language)

  @property
  def timezone(self):
    """datetime.tzinfo: time zone of the current session."""
    return self._time_zone

  def AddEnvironmentVariable(self, environment_variable):
    """Adds an environment variable.

    Args:
      environment_variable (EnvironmentVariableArtifact): environment variable
          artifact.

    Raises:
      KeyError: if the environment variable already exists.
    """
    name = environment_variable.name.upper()
    if name in self._environment_variables:
      raise KeyError('Environment variable: {0:s} already exists.'.format(
          environment_variable.name))

    self._environment_variables[name] = environment_variable

  def GetEnvironmentVariable(self, name):
    """Retrieves an environment variable.

    Args:
      name (str): name of the environment variable.

    Returns:
      EnvironmentVariableArtifact: environment variable artifact or None
          if there was no value set for the given name.
    """
    name = name.upper()
    return self._environment_variables.get(name, None)

  def GetEnvironmentVariables(self):
    """Retrieves the environment variables.

    Returns:
      list[EnvironmentVariableArtifact]: environment variable artifacts.
    """
    return self._environment_variables.values()

  def GetHostname(self):
    """Retrieves the hostname related to the event.

    If the hostname is not stored in the event it is determined based
    on the preprocessing information that is stored inside the storage file.

    Returns:
      str: hostname.
    """
    hostname_artifact = self._hostnames.get(self._active_session, None)
    if not hostname_artifact:
      return ''

    return hostname_artifact.name or ''

  def GetValue(self, identifier, default_value=None):
    """Retrieves a value by identifier.

    Args:
      identifier (str): case insensitive unique identifier for the value.
      default_value (object): default value.

    Returns:
      object: value or default value if not available.

    Raises:
      TypeError: if the identifier is not a string type.
    """
    if not isinstance(identifier, str):
      raise TypeError('Identifier not a string type.')

    identifier = identifier.lower()
    return self._values.get(identifier, default_value)

  def ReadSystemConfigurationArtifact(self, system_configuration):
    """Reads the knowledge base values from a system configuration artifact.

    Note that this overwrites existing values in the knowledge base.

    Args:
      system_configuration (SystemConfigurationArtifact): system configuration
          artifact.
    """
    if not system_configuration:
      return

    if system_configuration.code_page:
      try:
        self.SetCodepage(system_configuration.code_page)
      except ValueError:
        logger.warning(
            'Unsupported codepage: {0:s}, defaulting to {1:s}'.format(
                system_configuration.code_page, self._codepage))

    self._hostnames[self._active_session] = system_configuration.hostname

    self.SetValue('keyboard_layout', system_configuration.keyboard_layout)

    if system_configuration.language:
      self.SetLanguage(system_configuration.language)

    self.SetValue('operating_system', system_configuration.operating_system)
    self.SetValue(
        'operating_system_product',
        system_configuration.operating_system_product)
    self.SetValue(
        'operating_system_version',
        system_configuration.operating_system_version)

    if system_configuration.time_zone:
      try:
        self.SetTimeZone(system_configuration.time_zone)
      except ValueError:
        logger.warning(
            'Unsupported time zone: {0:s}, defaulting to {1:s}'.format(
                system_configuration.time_zone, self._time_zone.zone))

  def SetActiveSession(self, session_identifier):
    """Sets the active session.

    Args:
      session_identifier (str): session identifier where None represents
          the default active session.
    """
    self._active_session = session_identifier or self._DEFAULT_ACTIVE_SESSION

  def SetCodepage(self, codepage):
    """Sets the codepage.

    Args:
      codepage (str): codepage.

    Raises:
      ValueError: if the codepage is not supported.
    """
    try:
      codecs.getencoder(codepage)
      self._codepage = codepage
    except LookupError:
      raise ValueError('Unsupported codepage: {0:s}'.format(codepage))

  def SetEnvironmentVariable(self, environment_variable):
    """Sets an environment variable.

    Args:
      environment_variable (EnvironmentVariableArtifact): environment variable
          artifact.
    """
    name = environment_variable.name.upper()
    self._environment_variables[name] = environment_variable

  def SetHostname(self, hostname):
    """Sets a hostname.

    Args:
      hostname (HostnameArtifact): hostname artifact.
    """
    self._hostnames[self._active_session] = hostname

  def SetLanguage(self, language):
    """Sets the language.

    Args:
      language (str): language.
    """
    self._language = language

  def SetTimeZone(self, time_zone):
    """Sets the time zone.

    Args:
      time_zone (str): time zone.

    Raises:
      ValueError: if the time zone is not supported.
    """
    try:
      self._time_zone = pytz.timezone(time_zone)
    except pytz.UnknownTimeZoneError:
      raise ValueError('Unsupported time zone: {0!s}'.format(time_zone))

  def SetValue(self, identifier, value):
    """Sets a value by identifier.

    Args:
      identifier (str): case insensitive unique identifier for the value.
      value (object): value.

    Raises:
      TypeError: if the identifier is not a string type.
    """
    if not isinstance(identifier, str):
      raise TypeError('Identifier not a string type.')

    identifier = identifier.lower()
    self._values[identifier] = value
