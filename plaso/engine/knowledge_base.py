# -*- coding: utf-8 -*-
"""The artifact knowledge base object.

The knowledge base is filled by user provided input and the pre-processing
phase. It is intended to provide successive phases, like the parsing and
analysis phases, with essential information like e.g. the timezone and
codepage of the source data.
"""

import codecs
import logging

from plaso.containers import artifacts
from plaso.lib import py2to3

import pytz  # pylint: disable=wrong-import-order


class KnowledgeBase(object):
  """Class that implements the artifact knowledge base."""

  CURRENT_SESSION = 0

  def __init__(self):
    """Initializes a knowledge base."""
    super(KnowledgeBase, self).__init__()
    self._codepage = u'cp1252'
    self._environment_variables = {}
    self._hostnames = {}
    self._time_zone = pytz.UTC
    self._user_accounts = {}
    self._values = {}

  @property
  def codepage(self):
    """str: codepage of the current session."""
    return self._values.get(u'codepage', self._codepage)

  @property
  def hostname(self):
    """str: hostname of the current session."""
    hostname_artifact = self._hostnames.get(self.CURRENT_SESSION, None)
    if not hostname_artifact:
      return u''

    return hostname_artifact.name or u''

  @property
  def platform(self):
    """str: platform of the current session."""
    return self._values.get(u'guessed_os', u'')

  @platform.setter
  def platform(self, value):
    """str: platform of the current session."""
    self._values[u'guessed_os'] = value

  @property
  def timezone(self):
    """datetime.tzinfo: timezone of the current session."""
    return self._time_zone

  @property
  def user_accounts(self):
    """list[UserAccountArtifact]: user accounts of the current session."""
    return self._user_accounts.get(self.CURRENT_SESSION, {}).values()

  @property
  def year(self):
    """int: year of the current session."""
    return self._values.get(u'year', 0)

  def AddUserAccount(self, user_account, session_identifier=CURRENT_SESSION):
    """Adds an user account.

    Args:
      user_account (UserAccountArtifact): user account artifact.
      session_identifier (Optional[str])): session identifier, where
          CURRENT_SESSION represents the active session.

    Raises:
      KeyError: if the user account already exists.
    """
    if session_identifier not in self._user_accounts:
      self._user_accounts[session_identifier] = {}

    user_accounts = self._user_accounts[session_identifier]
    if user_account.identifier in user_accounts:
      raise KeyError(u'User account: {0:s} already exists.'.format(
          user_account.identifier))

    user_accounts[user_account.identifier] = user_account

  def AddEnvironmentVariable(self, enviroment_variable):
    """Adds an environment variable.

    Args:
      enviroment_variable (EnvironmentVariableArtifact): environment variable
          artifact.

    Raises:
      KeyError: if the environment variable already exists.
    """
    name = enviroment_variable.name.upper()
    if name in self._environment_variables:
      raise KeyError(u'Environment variable: {0:s} already exists.'.format(
          enviroment_variable.name))

    self._environment_variables[name] = enviroment_variable

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

  def GetHostname(self, session_identifier=CURRENT_SESSION):
    """Retrieves the hostname related to the event.

    If the hostname is not stored in the event it is determined based
    on the preprocessing information that is stored inside the storage file.

    Args:
      session_identifier (Optional[str])): session identifier, where
          CURRENT_SESSION represents the active session.

    Returns:
      str: hostname.
    """
    hostname_artifact = self._hostnames.get(session_identifier, None)
    if not hostname_artifact:
      return u''

    return hostname_artifact.name or u''

  # TODO: remove this function it is incorrect.
  def GetStoredHostname(self):
    """Retrieves the stored hostname.

    The hostname is determined based on the preprocessing information
    that is stored inside the storage file.

    Returns:
      str: hostname.
    """
    store_number = len(self._hostnames)
    return self._hostnames.get(store_number, None)

  def GetSystemConfigurationArtifact(self, session_identifier=CURRENT_SESSION):
    """Retrieves the knowledge base as a system configuration artifact.

    Args:
      session_identifier (Optional[str])): session identifier, where
          CURRENT_SESSION represents the active session.

    Returns:
      SystemConfigurationArtifact: system configuration artifact.
    """
    system_configuration = artifacts.SystemConfigurationArtifact()

    system_configuration.code_page = self._values.get(
        u'codepage', self._codepage)

    system_configuration.hostname = self._hostnames.get(
        session_identifier, None)

    system_configuration.keyboard_layout = self._values.get(
        u'keyboard_layout', None)
    system_configuration.operating_system = self._values.get(
        u'operating_system', None)
    system_configuration.operating_system_product = self._values.get(
        u'operating_system_product', None)
    system_configuration.operating_system_version = self._values.get(
        u'operating_system_version', None)
    system_configuration.time_zone = self._values.get(u'time_zone_str', u'UTC')

    user_accounts = self._user_accounts.get(session_identifier, {})
    system_configuration.user_accounts = user_accounts.values()

    return system_configuration

  def GetUsernameByIdentifier(
      self, user_identifier, session_identifier=CURRENT_SESSION):
    """Retrieves the username based on an user identifier.

    Args:
      user_identifier (str): user identifier, either a UID or SID.
      session_identifier (Optional[str])): session identifier, where
          CURRENT_SESSION represents the active session.

    Returns:
      str: username.
    """
    user_accounts = self._user_accounts.get(session_identifier, {})
    user_account = user_accounts.get(user_identifier, None)
    if not user_account:
      return u''

    return user_account.username or u''

  def GetUsernameForPath(self, path):
    """Retrieves a username for a specific path.

    This is determining if a specific path is within a user's directory and
    returning the username of the user if so.

    Args:
      path (str): path.

    Returns:
      str: username or None if the path does not appear to be within a user's
          directory.
    """
    path = path.lower()

    user_accounts = self._user_accounts.get(self.CURRENT_SESSION, {})
    for user_account in iter(user_accounts.values()):
      if not user_account.user_directory:
        continue

      user_directory = user_account.user_directory.lower()
      if path.startswith(user_directory):
        return user_account.username

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
    if not isinstance(identifier, py2to3.STRING_TYPES):
      raise TypeError(u'Identifier not a string type.')

    identifier = identifier.lower()
    return self._values.get(identifier, default_value)

  def HasUserAccounts(self):
    """Determines if the knowledge base contains user accounts.

    Returns:
      bool: True if the knowledge base contains user accounts.
    """
    return self._user_accounts.get(self.CURRENT_SESSION, {}) != {}

  def ReadSystemConfigurationArtifact(
      self, system_configuration, session_identifier=CURRENT_SESSION):
    """Reads the knowledge base values from a system configuration artifact.

    Note that this overwrites existing values in the knowledge base.

    Args:
      system_configuration (SystemConfigurationArtifact): system configuration
          artifact.
      session_identifier (Optional[str])): session identifier, where
          CURRENT_SESSION represents the active session.
    """
    self._hostnames[session_identifier] = system_configuration.hostname

    self._user_accounts[session_identifier] = {
        user_account.username: user_account
        for user_account in system_configuration.user_accounts}

    if not system_configuration.time_zone:
      return

    try:
      self.SetTimeZone(system_configuration.time_zone)
    except ValueError:
      logging.warning(
          u'Unsupported time zone: {0:s}, defaulting to {1:s}'.format(
              system_configuration.time_zone, self.timezone.zone))

  def SetCodepage(self, codepage):
    """Sets the codepage.

    Args:
      codepage (str): codepage.
    """
    try:
      codecs.getencoder(codepage)
      self._codepage = codepage
    except LookupError:
      raise ValueError(u'Unsupported codepage: {0:s}'.format(codepage))

  def SetEnvironmentVariable(self, environment_variable):
    """Sets an environment variable.

    Args:
      environment_variable (EnvironmentVariableArtifact): environment variable
          artifact.
    """
    name = environment_variable.name.upper()
    self._environment_variables[name] = environment_variable

  def SetHostname(self, hostname, session_identifier=CURRENT_SESSION):
    """Sets a hostname.

    Args:
      hostname (HostnameArtifact): hostname artifact.
      session_identifier (Optional[str])): session identifier, where
          CURRENT_SESSION represents the active session.
    """
    self._hostnames[session_identifier] = hostname

  def SetTimeZone(self, time_zone):
    """Sets the time zone.

    Args:
      time_zone (str): time zone.

    Raises:
      ValueError: if the timezone is not supported.
    """
    try:
      self._time_zone = pytz.timezone(time_zone)
    except (AttributeError, pytz.UnknownTimeZoneError):
      raise ValueError(u'Unsupported timezone: {0!s}'.format(time_zone))

  def SetValue(self, identifier, value):
    """Sets a value by identifier.

    Args:
      identifier (str): case insensitive unique identifier for the value.
      value (object): value.

    Raises:
      TypeError: if the identifier is not a string type.
    """
    if not isinstance(identifier, py2to3.STRING_TYPES):
      raise TypeError(u'Identifier not a string type.')

    identifier = identifier.lower()
    self._values[identifier] = value
