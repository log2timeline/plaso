# -*- coding: utf-8 -*-
"""This file contains preprocessors for Linux."""

import csv

from dfvfs.helpers import text_file

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.preprocessors import interface
from plaso.preprocessors import manager


class LinuxHostnamePreprocessPlugin(interface.FilePreprocessPlugin):
  """Linux hostname preprocessing plugin."""

  _PATH = u'/etc/hostname'

  def _ParseFileObject(self, knowledge_base, file_object):
    """Parses a hostname file-like object.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      file_object (dfvfs.FileIO): file-like object.
    """
    text_file_object = text_file.TextFile(file_object)
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


class LinuxTimeZonePreprocessPlugin(interface.FilePreprocessPlugin):
  """Linux time zone preprocessing plugin."""

  _PATH = u'/etc/timezone'

  def _ParseFileObject(self, knowledge_base, file_object):
    """Parses a time zone file-like object.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      file_object (dfvfs.FileIO): file-like object.
    """
    text_file_object = text_file.TextFile(file_object)
    file_data = text_file_object.readline()

    time_zone = file_data.strip()
    if not time_zone:
      return

    try:
      knowledge_base.SetTimeZone(time_zone)
    except ValueError:
      # TODO: add and store preprocessing errors.
      pass


class LinuxUserAccountsPreprocessPlugin(interface.FilePreprocessPlugin):
  """Linux user accounts preprocessing plugin."""

  _PATH = u'/etc/passwd'

  def _ParseFileObject(self, knowledge_base, file_object):
    """Parses a passwd file-like object.

    A passwd file consist of colon seperated values in the format:
    "username:password:uid:gid:full name:home directory:shell".

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    text_file_object = text_file.TextFile(file_object)

    try:
      reader = csv.reader(text_file_object, delimiter=b':')
    except csv.Error:
      raise errors.PreProcessFail(u'Unable to read: {0:s}.'.format(self._PATH))

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
      except KeyError:
        # TODO: add and store preprocessing errors.
        pass


manager.PreprocessPluginsManager.RegisterPlugins([
    LinuxHostnamePreprocessPlugin, LinuxTimeZonePreprocessPlugin,
    LinuxUserAccountsPreprocessPlugin])
