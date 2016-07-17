# -*- coding: utf-8 -*-
"""This file contains preprocessors for Linux."""

import csv

from dfvfs.helpers import text_file

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.preprocessors import interface
from plaso.preprocessors import manager


class LinuxHostname(interface.PreprocessPlugin):
  """A preprocessing class that fetches hostname on Linux."""

  SUPPORTED_OS = [u'Linux']
  WEIGHT = 1
  ATTRIBUTE = u'hostname'

  def GetValue(self, searcher, unused_knowledge_base):
    """Determines the hostname based on the contents of /etc/hostname.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.

    Returns:
      HostnameArtifact: hostname artifact or None.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    path = u'/etc/hostname'
    file_entry = self._FindFileEntry(searcher, path)
    if not file_entry:
      raise errors.PreProcessFail(
          u'Unable to find file entry for path: {0:s}.'.format(path))

    file_object = file_entry.GetFileObject()
    file_data = file_object.read(512)
    file_object.close()

    hostname, _, _ = file_data.partition(b'\n')
    try:
      hostname = hostname.decode(u'utf-8')
    except UnicodeDecodeError:
      # TODO: add and store preprocessing errors.
      hostname = hostname.decode(u'utf-8', errors=u'replace')

    if hostname:
      return artifacts.HostnameArtifact(name=hostname)


class LinuxTimezone(interface.PreprocessPlugin):
  """A preprocessing class that fetches the timezone on Linux."""

  ATTRIBUTE = u'time_zone_str'
  DEFAULT_ATTRIBUTE_VALUE = u'UTC'
  SUPPORTED_OS = [u'Linux']
  WEIGHT = 1

  def GetValue(self, searcher, unused_knowledge_base):
    """Determines the timezone based on the contents of /etc/timezone.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.

    Returns:
      str: an Olsen, or tzdata, timezone name, e.g. 'America/New_York'.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    path = u'/etc/timezone'
    file_entry = self._FindFileEntry(searcher, path)
    if not file_entry:
      raise errors.PreProcessFail(
          u'Unable to find file entry for path: {0:s}.'.format(path))

    file_object = file_entry.GetFileObject()
    try:
      text_file_object = text_file.TextFile(file_object)
      file_data = text_file_object.readline()
    finally:
      file_object.close()
    return file_data.strip()


class LinuxUsernames(interface.PreprocessPlugin):
  """A preprocessing class that fetches usernames on Linux."""

  SUPPORTED_OS = [u'Linux']
  WEIGHT = 1
  ATTRIBUTE = u'users'

  def GetValue(self, searcher, unused_knowledge_base):
    """Determines the user information based on the contents of /etc/passwd.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.

    Returns:
      list[UserAccountArtifact]: user account artifacts.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    # TODO: Add passwd.cache, might be good if nss cache is enabled.

    path = u'/etc/passwd'
    file_entry = self._FindFileEntry(searcher, path)
    if not file_entry:
      raise errors.PreProcessFail(
          u'Unable to find file entry for path: {0:s}.'.format(path))

    file_object = file_entry.GetFileObject()
    text_file_object = text_file.TextFile(file_object)

    # username:password:uid:gid:full name:home directory:shell
    try:
      reader = csv.reader(text_file_object, delimiter=b':')
    except csv.Error:
      raise errors.PreProcessFail(u'Unable to read: {0:s}.'.format(path))

    users = []
    for row in reader:
      if len(row) < 7 or not row[0] or not row[2]:
        # TODO: add and store preprocessing errors.
        continue

      user_account_artifact = artifacts.UserAccountArtifact(
          identifier=row[2], username=row[0])
      user_account_artifact.group_identifier = row[3] or None
      user_account_artifact.full_name = row[4] or None
      user_account_artifact.user_directory = row[5] or None
      user_account_artifact.shell = row[6] or None

      users.append(user_account_artifact)

    file_object.close()

    if not users:
      raise errors.PreProcessFail(u'Unable to find any users on the system.')
    return users


manager.PreprocessPluginsManager.RegisterPlugins([
    LinuxHostname, LinuxTimezone, LinuxUsernames])
