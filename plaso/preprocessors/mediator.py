# -*- coding: utf-8 -*-
"""The preprocess mediator."""

import pytz

from plaso.containers import warnings
from plaso.helpers.windows import eventlog_providers
from plaso.helpers.windows import time_zones
from plaso.preprocessors import logger


class PreprocessMediator(object):
  """Preprocess mediator.

  Attributes:
    code_page (str): code page.
    hostname (HostnameArtifact): hostname.
    language (str): language.
    time_zone (datetime.tzinfo): time zone.
  """

  def __init__(self, storage_writer):
    """Initializes a preprocess mediator.

    Args:
      storage_writer (StorageWriter): storage writer, to store preprocessing
          information in.
    """
    super(PreprocessMediator, self).__init__()
    self._available_time_zones = {}
    self._environment_variables = {}
    self._file_entry = None
    self._storage_writer = storage_writer
    self._windows_eventlog_providers_helper = (
        eventlog_providers.WindowsEventLogProvidersHelper())
    self._windows_eventlog_providers = {}
    self._windows_eventlog_providers_by_identifier = {}
    self._values = {}

    self.code_page = None
    self.hostname = None
    self.language = None
    self.time_zone = None

  def AddArtifact(self, artifact_attribute_container):
    """Adds a pre-processing artifact attribute container.

    Args:
      artifact_attribute_container (ArtifactAttributeContainer): artifact
          attribute container.
    """
    if self._storage_writer:
      self._storage_writer.AddAttributeContainer(artifact_attribute_container)

  def AddEnvironmentVariable(self, environment_variable_artifact):
    """Adds an environment variable.

    Args:
      environment_variable_artifact (EnvironmentVariableArtifact): environment
          variable artifact.

    Raises:
      KeyError: if the environment variable already exists.
    """
    logger.debug('setting environment variable: {0:s} to: "{1:s}"'.format(
        environment_variable_artifact.name,
        environment_variable_artifact.value))

    name = environment_variable_artifact.name.upper()
    if name in self._environment_variables:
      raise KeyError('Environment variable: {0:s} already exists.'.format(
          environment_variable_artifact.name))

    self._environment_variables[name] = environment_variable_artifact

    if self._storage_writer:
      self._storage_writer.AddAttributeContainer(environment_variable_artifact)

  def AddHostname(self, hostname_artifact):
    """Adds a hostname.

    Args:
      hostname_artifact (HostnameArtifact): hostname artifact.
    """
    # TODO: change storage and pre-processor to handle more than 1 hostname.
    self.hostname = hostname_artifact

  def AddTimeZoneInformation(self, time_zone_artifact):
    """Adds a time zone defined by the operating system.

    Args:
      time_zone_artifact (TimeZoneArtifact): time zone artifact.

    Raises:
      KeyError: if the time zone already exists.
    """
    if time_zone_artifact.name in self._available_time_zones:
      raise KeyError('Time zone: {0:s} already exists.'.format(
          time_zone_artifact.name))

    self._available_time_zones[time_zone_artifact.name] = time_zone_artifact

    if self._storage_writer:
      self._storage_writer.AddAttributeContainer(time_zone_artifact)

  def AddUserAccount(self, user_account):
    """Adds an user account.

    Args:
      user_account (UserAccountArtifact): user account artifact.

    Raises:
      KeyError: if the user account already exists.
    """
    logger.debug('adding user account: {0:s}'.format(user_account.username))

    if self._storage_writer:
      self._storage_writer.AddAttributeContainer(user_account)

  def AddWindowsEventLogProvider(self, windows_eventlog_provider):
    """Adds a Windows EventLog provider.

    Args:
      windows_eventlog_provider (WindowsEventLogProviderArtifact): Windows
          EventLog provider.

    Raises:
      KeyError: if the Windows EventLog provider already exists.
    """
    existing_provider = None
    provider_identifier = windows_eventlog_provider.identifier
    log_source = windows_eventlog_provider.log_sources[0]

    if provider_identifier:
      existing_provider = self._windows_eventlog_providers_by_identifier.get(
          provider_identifier, None)

    if not existing_provider:
      existing_provider = self._windows_eventlog_providers.get(log_source, None)

    if existing_provider:
      self._windows_eventlog_providers_helper.Merge(
          existing_provider, windows_eventlog_provider)

      if self._storage_writer:
        self._storage_writer.UpdateAttributeContainer(existing_provider)

    else:
      self._windows_eventlog_providers_helper.NormalizeMessageFiles(
          windows_eventlog_provider)

      self._windows_eventlog_providers[log_source] = windows_eventlog_provider

      if self._storage_writer:
        self._storage_writer.AddAttributeContainer(windows_eventlog_provider)

      if provider_identifier:
        self._windows_eventlog_providers_by_identifier[provider_identifier] = (
            windows_eventlog_provider)

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

  def GetValue(self, identifier):
    """Retrieves a value by identifier.

    Args:
      identifier (str): case insensitive unique identifier for the value.

    Returns:
      object: value or None if not available.
    """
    identifier = identifier.lower()
    return self._values.get(identifier, None)

  def GetValues(self):
    """Retrieves the values.

    Returns:
      list[tuple[str, object]]: values.
    """
    return self._values.items()

  def ProducePreprocessingWarning(self, plugin_name, message):
    """Produces a preprocessing warning.

    Args:
      plugin_name (str): name of the preprocess plugin.
      message (str): message of the warning.
    """
    if self._storage_writer:
      path_spec = None
      if self._file_entry:
        path_spec = self._file_entry.path_spec

      warning = warnings.PreprocessingWarning(
          message=message, path_spec=path_spec, plugin_name=plugin_name)
      self._storage_writer.AddAttributeContainer(warning)

    logger.debug('[{0:s}] {1:s}'.format(plugin_name, message))

  def Reset(self):
    """Resets the values stored in the mediator."""
    self._available_time_zones = {}
    self._environment_variables = {}
    self._file_entry = None
    self._windows_eventlog_providers = {}
    self._windows_eventlog_providers_by_identifier = {}
    self._values = {}

    self.code_page = None
    self.hostname = None
    self.language = None
    self.time_zone = None

  def SetCodePage(self, code_page):
    """Sets the code page.

    Args:
      code_page (str): code_page.

    Raises:
      ValueError: if the code page is not supported.
    """
    logger.debug('setting code page to: "{0:s}"'.format(code_page))
    self.code_page = code_page

  def SetFileEntry(self, file_entry):
    """Sets the active file entry.

    Args:
      file_entry (dfvfs.FileEntry): file entry.
    """
    self._file_entry = file_entry

  def SetLanguage(self, language):
    """Sets the language.

    Args:
      language (str): language.

    Raises:
      ValueError: if the language is not supported.
    """
    self.language = language

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
          for time_zone_artifact in self._available_time_zones.values()}

      time_zone = mui_form_time_zones.get(time_zone, time_zone)
    else:
      localized_time_zones = {
          time_zone_artifact.localized_name: time_zone_artifact.name
          for time_zone_artifact in self._available_time_zones.values()}

      time_zone = localized_time_zones.get(time_zone, time_zone)

    # Map a Windows time zone name to a Python time zone name.
    time_zone = time_zones.WINDOWS_TIME_ZONES.get(time_zone, time_zone)

    try:
      self.time_zone = pytz.timezone(time_zone)
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
    identifier = identifier.lower()
    if identifier not in self._values:
      self._values[identifier] = value
