# -*- coding: utf-8 -*-
"""The preprocess mediator."""

from plaso.containers import warnings
from plaso.helpers.windows import eventlog_providers
from plaso.preprocessors import logger


class PreprocessMediator(object):
  """Preprocess mediator."""

  def __init__(self, session, storage_writer, knowledge_base):
    """Initializes a preprocess mediator.

    Args:
      session (Session): session the preprocessing is part of.
      storage_writer (StorageWriter): storage writer, to store preprocessing
          information in.
      knowledge_base (KnowledgeBase): knowledge base, to fill with
          preprocessing information.
    """
    super(PreprocessMediator, self).__init__()
    self._file_entry = None
    self._knowledge_base = knowledge_base
    self._session = session
    self._storage_writer = storage_writer
    self._windows_eventlog_providers_helper = (
        eventlog_providers.WindowsEventLogProvidersHelper())
    self._windows_eventlog_providers_by_identifier = {}

  @property
  def knowledge_base(self):
    """KnowledgeBase: knowledge base."""
    return self._knowledge_base

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
    self._knowledge_base.AddEnvironmentVariable(environment_variable_artifact)

    if self._storage_writer:
      self._storage_writer.AddAttributeContainer(environment_variable_artifact)

  def AddHostname(self, hostname_artifact):
    """Adds a hostname.

    Args:
      hostname_artifact (HostnameArtifact): hostname artifact.
    """
    # TODO: change storage and knowledge base to handle more than 1 hostname.
    if not self._knowledge_base.GetHostname():
      self._knowledge_base.SetHostname(hostname_artifact)

  def AddTimeZoneInformation(self, time_zone_artifact):
    """Adds a time zone defined by the operating system.

    Args:
      time_zone_artifact (TimeZoneArtifact): time zone artifact.

    Raises:
      KeyError: if the time zone already exists.
    """
    self._knowledge_base.AddAvailableTimeZone(time_zone_artifact)

  def AddUserAccount(self, user_account):
    """Adds an user account.

    Args:
      user_account (UserAccountArtifact): user account artifact.

    Raises:
      KeyError: if the user account already exists.
    """
    self._knowledge_base.AddUserAccount(user_account)

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

    if provider_identifier:
      existing_provider = self._windows_eventlog_providers_by_identifier.get(
          provider_identifier, None)

    if not existing_provider:
      existing_provider = self._knowledge_base.GetWindowsEventLogProvider(
          windows_eventlog_provider.log_sources[0])

    if existing_provider:
      self._windows_eventlog_providers_helper.Merge(
          existing_provider, windows_eventlog_provider)

      if self._storage_writer:
        self._storage_writer.UpdateAttributeContainer(existing_provider)

    else:
      self._windows_eventlog_providers_helper.NormalizeMessageFiles(
          windows_eventlog_provider)

      if self._storage_writer:
        self._storage_writer.AddAttributeContainer(windows_eventlog_provider)

      self._knowledge_base.AddWindowsEventLogProvider(
          windows_eventlog_provider)

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
    return self._knowledge_base.GetEnvironmentVariable(name)

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

  def SetCodepage(self, codepage):
    """Sets the codepage.

    Args:
      codepage (str): codepage.

    Raises:
      ValueError: if the codepage is not supported.
    """
    if not self._knowledge_base.codepage:
      self._knowledge_base.SetCodepage(codepage)

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
    self._knowledge_base.SetLanguage(language)

  def SetTimeZone(self, time_zone):
    """Sets the time zone.

    Args:
      time_zone (str): time zone.

    Raises:
      ValueError: if the time zone is not supported.
    """
    # TODO: check if time zone is set in knowledge base.
    self._knowledge_base.SetTimeZone(time_zone)

  def SetValue(self, identifier, value):
    """Sets a value by identifier.

    Args:
      identifier (str): case insensitive unique identifier for the value.
      value (object): value.

    Raises:
      TypeError: if the identifier is not a string type.
    """
    if not self._knowledge_base.GetValue(identifier):
      self._knowledge_base.SetValue(identifier, value)
