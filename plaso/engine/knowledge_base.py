# -*- coding: utf-8 -*-
"""The artifact knowledge base object.

The knowledge base is filled by user provided input and the pre-processing
phase. It is intended to provide successive phases, like the parsing and
analysis phases, with essential information like e.g. the timezone and
codepage of the source data.
"""

import logging

from plaso.containers import artifacts
from plaso.lib import py2to3

import pytz  # pylint: disable=wrong-import-order


class KnowledgeBase(object):
  """Class that implements the artifact knowledge base."""

  def __init__(self):
    """Initializes a knowledge base object."""
    super(KnowledgeBase, self).__init__()
    self._default_codepage = u'cp1252'
    self._environment_variables = {}
    self._hostnames = {}
    self._timezone = pytz.UTC
    self._user_accounts = {}
    self._values = {}

  @property
  def codepage(self):
    """str: codepage."""
    return self._values.get(u'codepage', self._default_codepage)

  @property
  def hostname(self):
    """str: hostname."""
    # TODO: refactor the use of store number.
    hostname_artifact = self._hostnames.get(0, None)
    if not hostname_artifact:
      return u''

    return hostname_artifact.name or u''

  @property
  def platform(self):
    """str: platform."""
    return self._values.get(u'guessed_os', u'')

  @platform.setter
  def platform(self, value):
    """str: platform."""
    self._values[u'guessed_os'] = value

  @property
  def timezone(self):
    """datetime.tzinfo: timezone."""
    return self._timezone

  @property
  def year(self):
    """int: year."""
    return self._values.get(u'year', 0)

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

  # TODO: refactor.
  def GetHostname(self, store_number, default_hostname=u'-'):
    """Retrieves the hostname related to the event.

    If the hostname is not stored in the event it is determined based
    on the preprocessing information that is stored inside the storage file.

    Args:
      store_number (int): store number.
      default_hostname (Optional[str]): default hostname.

    Returns:
      str: hostname.
    """
    return self._hostnames.get(store_number, default_hostname)

  def GetPathAttributes(self):
    """Retrieves the path attributes.

    Returns:
      dict[str, str]: path attributes, typically environment variables
          that are expanded e.g. $HOME or %SystemRoot%.
    """
    return {
        environment_variable.name: environment_variable.value
        for environment_variable in iter(self._environment_variables.values())}

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

  def GetSystemConfigurationArtifact(self, session_number=0):
    """Retrieves the knowledge base as a system configuration artifact.

    Args:
      session_number (Optional[int]): session number, where 0 represents
          the active session.

    Returns:
      SystemConfigurationArtifact: system configuration artifact.
    """
    system_configuration = artifacts.SystemConfigurationArtifact()

    system_configuration.code_page = self._values.get(
        u'codepage', self._default_codepage)

    system_configuration.hostname = self._hostnames.get(session_number, None)

    system_configuration.keyboard_layout = self._values.get(
        u'keyboard_layout', None)
    system_configuration.operating_system = self._values.get(
        u'operating_system', None)
    system_configuration.operating_system_product = self._values.get(
        u'operating_system_product', None)
    system_configuration.operating_system_version = self._values.get(
        u'operating_system_version', None)
    system_configuration.time_zone = self._values.get(u'time_zone_str', u'UTC')

    user_accounts = self._user_accounts.get(session_number, {})
    system_configuration.user_accounts = user_accounts.values()

    return system_configuration

  # TODO: refactor.
  def GetUsername(self, user_identifier, store_number, default_username=u'-'):
    """Retrieves the username related to the event.

    Args:
      user_identifier (str): user identifier.
      store_number (int): store number.
      default_username (Optional[str]): default username.

    Returns:
      str: username.
    """
    # TODO: refactor the use of store number.
    if store_number not in self._user_accounts or not user_identifier:
      return default_username

    user_accounts = self._user_accounts[store_number]
    user_account = user_accounts.get(user_identifier, None)
    if not user_account or not user_account.username:
      return default_username

    return user_account.username

  def GetUsernameByIdentifier(self, identifier):
    """Retrieves the username based on an identifier.

    Args:
      identifier (str): user identifier, either a UID or SID.

    Returns:
      str: username or '-' if not available.
    """
    return self.GetUsername(identifier, 0)

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

    # TODO: refactor the use of store number.
    user_accounts = self._user_accounts.get(0, {})
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

  def ReadSystemConfigurationArtifact(self, store_number, system_configuration):
    """Reads the knowledge base values from a system configuration artifact.

    Note that this overwrites existing values in the knowledge base.

    Args:
      store_number (int): store number.
      system_configuration (SystemConfigurationArtifact): system configuration
          artifact.
    """
    # TODO: refactor the use of store number.
    self._hostnames[store_number] = system_configuration.hostname

    # TODO: refactor the use of store number.
    self._user_accounts[store_number] = {
        user_account.username: user_account
        for user_account in system_configuration.user_accounts}

    try:
      self.SetTimezone(system_configuration.time_zone)
    except ValueError:
      logging.warning(
          u'Unsupported time zone: {0:s}, defaulting to {1:s}'.format(
              system_configuration.time_zone, self.timezone.zone))

  def SetDefaultCodepage(self, codepage):
    """Sets the default codepage.

    Args:
      codepage (str): default codepage.
    """
    # TODO: check if value is sane.
    self._default_codepage = codepage

  def SetTimezone(self, timezone):
    """Sets the timezone.

    Args:
      timezone (str): timezone.

    Raises:
      ValueError: if the timezone is not supported.
    """
    try:
      self._timezone = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
      raise ValueError(u'Unsupported timezone: {0:s}'.format(timezone))

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
    # TODO: refactor the use of store number.
    self._hostnames[hostname.store_number] = hostname

  def SetUserAccount(self, user_account):
    """Sets an user account.

    Args:
      user_account (UserAccountArtifact): user account artifact.
    """
    if user_account.store_number not in self._user_accounts:
      # TODO: refactor the use of store number.
      self._user_accounts[user_account.store_number] = {}

    user_accounts = self._user_accounts[user_account.store_number]
    user_accounts[user_account.identifier] = user_account

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
