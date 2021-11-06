# -*- coding: utf-8 -*-
"""The artifact knowledge base object.

The knowledge base is filled by user provided input and the pre-processing
phase. It is intended to provide successive phases, like the parsing and
analysis phases, with essential information like the time zone and codepage
of the source data.
"""

import codecs
import pytz

from plaso.containers import artifacts
from plaso.engine import logger
from plaso.helpers.windows import time_zones


class KnowledgeBase(object):
  """The knowledge base."""

  _DEFAULT_ACTIVE_SESSION = '00000000000000000000000000000000'

  def __init__(self):
    """Initializes a knowledge base."""
    super(KnowledgeBase, self).__init__()
    self._active_session = self._DEFAULT_ACTIVE_SESSION
    self._available_time_zones = {}
    self._codepage = 'cp1252'
    self._environment_variables = {}
    self._hostnames = {}
    self._language = 'en-US'
    self._mount_path = None
    self._time_zone = pytz.UTC
    self._user_accounts = {}
    self._values = {}
    self._windows_eventlog_providers = {}

  @property
  def available_time_zones(self):
    """list[TimeZone]: available time zones of the current session."""
    return self._available_time_zones.get(self._active_session, {}).values()

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

  @property
  def user_accounts(self):
    """list[UserAccountArtifact]: user accounts of the current session."""
    return self._user_accounts.get(self._active_session, {}).values()

  @property
  def year(self):
    """int: year of the current session."""
    return self.GetValue('year', default_value=0)

  def AddAvailableTimeZone(self, time_zone):
    """Adds an available time zone.

    Args:
      time_zone (TimeZoneArtifact): time zone artifact.

    Raises:
      KeyError: if the time zone already exists.
    """
    if self._active_session not in self._available_time_zones:
      self._available_time_zones[self._active_session] = {}

    available_time_zones = self._available_time_zones[self._active_session]
    if time_zone.name in available_time_zones:
      raise KeyError('Time zone: {0:s} already exists.'.format(time_zone.name))

    available_time_zones[time_zone.name] = time_zone

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

  def AddUserAccount(self, user_account):
    """Adds an user account.

    Args:
      user_account (UserAccountArtifact): user account artifact.

    Raises:
      KeyError: if the user account already exists.
    """
    if self._active_session not in self._user_accounts:
      self._user_accounts[self._active_session] = {}

    user_accounts = self._user_accounts[self._active_session]
    if user_account.identifier in user_accounts:
      raise KeyError('User account: {0:s} already exists.'.format(
          user_account.identifier))

    user_accounts[user_account.identifier] = user_account

  def AddWindowsEventLogProvider(self, windows_eventlog_provider):
    """Adds a Windows Event Log provider.

    Args:
      windows_eventlog_provider (WindowsEventLogProviderArtifact): Windows
          Event Log provider.

    Raises:
      KeyError: if the Windows Event Log provider already exists.
    """
    log_source = windows_eventlog_provider.log_source
    if log_source in self._windows_eventlog_providers:
      raise KeyError('Windows Event Log provider: {0:s} already exists.'.format(
          log_source))

    # TODO: store on a per-volume basis?
    self._windows_eventlog_providers[log_source] = windows_eventlog_provider

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

  def GetSystemConfigurationArtifact(self):
    """Retrieves the knowledge base as a system configuration artifact.

    Returns:
      SystemConfigurationArtifact: system configuration artifact.
    """
    system_configuration = artifacts.SystemConfigurationArtifact()

    system_configuration.code_page = self.GetValue(
        'codepage', default_value=self._codepage)

    system_configuration.hostname = self._hostnames.get(
        self._active_session, None)

    system_configuration.keyboard_layout = self.GetValue('keyboard_layout')

    system_configuration.language = self._language

    system_configuration.operating_system = self.GetValue('operating_system')
    system_configuration.operating_system_product = self.GetValue(
        'operating_system_product')
    system_configuration.operating_system_version = self.GetValue(
        'operating_system_version')

    time_zone = self._time_zone.zone
    if isinstance(time_zone, bytes):
      time_zone = time_zone.decode('ascii')

    system_configuration.time_zone = time_zone

    available_time_zones = self._available_time_zones.get(
        self._active_session, {})
    # In Python 3 dict.values() returns a type dict_values, which will cause
    # the JSON serializer to raise a TypeError.
    system_configuration.available_time_zones = list(
        available_time_zones.values())

    user_accounts = self._user_accounts.get(self._active_session, {})
    # In Python 3 dict.values() returns a type dict_values, which will cause
    # the JSON serializer to raise a TypeError.
    system_configuration.user_accounts = list(user_accounts.values())

    return system_configuration

  def GetUsernameByIdentifier(self, user_identifier):
    """Retrieves the username based on an user identifier.

    Args:
      user_identifier (str): user identifier, either a UID or SID.

    Returns:
      str: username.
    """
    user_accounts = self._user_accounts.get(self._active_session, {})
    user_account = user_accounts.get(user_identifier, None)
    if not user_account:
      return ''

    return user_account.username or ''

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

    user_accounts = self._user_accounts.get(self._active_session, {})
    for user_account in user_accounts.values():
      if not user_account.user_directory:
        continue

      user_directory = user_account.user_directory.lower()
      if path.startswith(user_directory):
        return user_account.username

    return None

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

  def GetWindowsEventLogProvider(self, log_source):
    """Retrieves a Windows EventLog provider by log source.

    Args:
      log_source (str): EventLog source, such as "Application Error".

    Returns:
      WindowsEventLogProviderArtifact: Windows EventLog provider artifact or
          None if not available.
    """
    return self._windows_eventlog_providers.get(log_source, None)

  def GetWindowsEventLogProviders(self):
    """Retrieves the Windows EventLog providers.

    Returns:
      list[WindowsEventLogProviderArtifact]: Windows EventLog provider
          artifacts.
    """
    return self._windows_eventlog_providers.values()

  def HasUserAccounts(self):
    """Determines if the knowledge base contains user accounts.

    Returns:
      bool: True if the knowledge base contains user accounts.
    """
    return self._user_accounts.get(self._active_session, {}) != {}

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

    # Set the available time zones before the system time zone so that localized
    # time zone names can be mapped to their corresponding Python time zone.
    self._available_time_zones[self._active_session] = {
        time_zone.name: time_zone
        for time_zone in system_configuration.available_time_zones}

    if system_configuration.time_zone:
      try:
        self.SetTimeZone(system_configuration.time_zone)
      except ValueError:
        logger.warning(
            'Unsupported time zone: {0:s}, defaulting to {1:s}'.format(
                system_configuration.time_zone, self._time_zone.zone))

    self._user_accounts[self._active_session] = {
        user_account.identifier: user_account
        for user_account in system_configuration.user_accounts}

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
    # Get the "normalized" name of a Windows time zone name.
    if time_zone.startswith('@tzres.dll,'):
      mui_form_time_zones = {
          time_zone_artifact.mui_form: time_zone_artifact.name
          for time_zone_artifact in self.available_time_zones}

      time_zone = mui_form_time_zones.get(time_zone, time_zone)
    else:
      localized_time_zones = {
          time_zone_artifact.localized_name: time_zone_artifact.name
          for time_zone_artifact in self.available_time_zones}

      time_zone = localized_time_zones.get(time_zone, time_zone)

    # Map a Windows time zone name to a Python time zone name.
    time_zone = time_zones.WINDOWS_TIME_ZONES.get(time_zone, time_zone)

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
