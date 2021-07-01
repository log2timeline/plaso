# -*- coding: utf-8 -*-
"""The preprocess mediator."""

from plaso.containers import warnings
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

  @property
  def knowledge_base(self):
    """KnowledgeBase: knowledge base."""
    return self._knowledge_base

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
    """Adds a Windows Event Log provider.

    Args:
      windows_eventlog_provider (WindowsEventLogProviderArtifact): Windows
          Event Log provider.

    Raises:
      KeyError: if the Windows Event Log provider already exists.
    """
    self._knowledge_base.AddWindowsEventLogProvider(windows_eventlog_provider)

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

  def SetFileEntry(self, file_entry):
    """Sets the active file entry.

    Args:
      file_entry (dfvfs.FileEntry): file entry.
    """
    self._file_entry = file_entry
