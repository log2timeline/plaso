# -*- coding: utf-8 -*-
"""This file contains preprocessors for Linux."""

import csv

from dfvfs.helpers import text_file as dfvfs_text_file

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.preprocessors import interface
from plaso.preprocessors import manager


class LinuxHostnamePlugin(interface.FileArtifactPreprocessorPlugin):
  """The Linux hostname plugin."""

  ARTIFACT_DEFINITION_NAME = u'LinuxHostnameFile'

  def _ParseFileData(self, knowledge_base, file_object):
    """Parses file content (data) for a hostname preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      file_object (dfvfs.FileIO): file-like object that contains the artifact
          value data.

    Returns:
      bool: True if all the preprocessing attributes were found and
          the preprocessor plugin is done.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    result = False
    text_file_object = dfvfs_text_file.TextFile(file_object)
    hostname = text_file_object.readline()

    try:
      hostname = hostname.decode(u'utf-8')
    except UnicodeDecodeError:
      # TODO: add and store preprocessing errors.
      hostname = hostname.decode(u'utf-8', errors=u'replace')

    hostname = hostname.strip()
    if hostname:
      hostname_artifact = artifacts.HostnameArtifact(name=hostname)
      knowledge_base.SetHostname(hostname_artifact)
      result = True

    return result


class LinuxTimeZonePlugin(interface.FileArtifactPreprocessorPlugin):
  """The Linux time zone plugin."""

  ARTIFACT_DEFINITION_NAME = u'LinuxTimezoneFile'

  def _ParseFileData(self, knowledge_base, file_object):
    """Parses file content (data) for a time zone preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      file_object (dfvfs.FileIO): file-like object that contains the artifact
          value data.

    Returns:
      bool: True if all the preprocessing attributes were found and
          the preprocessor plugin is done.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    result = False
    text_file_object = dfvfs_text_file.TextFile(file_object)
    file_data = text_file_object.readline()

    time_zone = file_data.strip()
    if time_zone:
      try:
        knowledge_base.SetTimeZone(time_zone)
        result = True
      except ValueError:
        # TODO: add and store preprocessing errors.
        pass

    return result


class LinuxUserAccountsPlugin(interface.FileArtifactPreprocessorPlugin):
  """The Linux user accounts plugin."""

  ARTIFACT_DEFINITION_NAME = u'LinuxPasswdFile'

  def _ParseFileData(self, knowledge_base, file_object):
    """Parses file content (data) for user account preprocessing attributes.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      file_object (dfvfs.FileIO): file-like object that contains the artifact
          value data.

    Returns:
      bool: True if all the preprocessing attributes were found and
          the preprocessor plugin is done.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    result = False
    text_file_object = dfvfs_text_file.TextFile(file_object)

    try:
      reader = csv.reader(text_file_object, delimiter=b':')
    except csv.Error as exception:
      raise errors.PreProcessFail(
          u'Unable to read: {0:s} with error: {1!s}'.format(
              self.ARTIFACT_DEFINITION_NAME, exception))

    for row in reader:
      if len(row) < 7 or not row[0] or not row[2]:
        # TODO: add and store preprocessing errors.
        continue

      user_account = artifacts.UserAccountArtifact(
          identifier=row[2], username=row[0])
      user_account.group_identifier = row[3] or None
      user_account.full_name = row[4] or None
      user_account.user_directory = row[5] or None
      user_account.shell = row[6] or None

      try:
        knowledge_base.AddUserAccount(user_account)
        result = True
      except KeyError:
        # TODO: add and store preprocessing errors.
        pass

    return result


manager.PreprocessPluginsManager.RegisterPlugins([
    LinuxHostnamePlugin, LinuxTimeZonePlugin, LinuxUserAccountsPlugin])
