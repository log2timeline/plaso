# -*- coding: utf-8 -*-
"""This file contains preprocessors for Linux."""

import csv

from dfvfs.helpers import text_file

from plaso.lib import errors
from plaso.preprocessors import interface
from plaso.preprocessors import manager


class LinuxHostname(interface.PreprocessPlugin):
  """A preprocessing class that fetches hostname on Linux."""

  SUPPORTED_OS = ['Linux']
  WEIGHT = 1
  ATTRIBUTE = 'hostname'

  def GetValue(self, searcher, unused_knowledge_base):
    """Determines the hostname based on the contents of /etc/hostname.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.

    Returns:
      The hostname.

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

    hostname, _, _ = file_data.partition('\n')
    return u'{0:s}'.format(hostname)


class LinuxUsernames(interface.PreprocessPlugin):
  """A preprocessing class that fetches usernames on Linux."""

  SUPPORTED_OS = ['Linux']
  WEIGHT = 1
  ATTRIBUTE = 'users'

  def GetValue(self, searcher, unused_knowledge_base):
    """Determines the user information based on the contents of /etc/passwd.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.

    Returns:
      A list containing username information dicts.

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

    reader = csv.reader(text_file_object, delimiter=':')

    users = []
    for row in reader:
      # TODO: as part of artifacts, create a proper object for this.
      user = {
          'uid': row[2],
          'gid': row[3],
          'name': row[0],
          'path': row[5],
          'shell': row[6]}
      users.append(user)

    file_object.close()
    return users


manager.PreprocessPluginsManager.RegisterPlugins([
    LinuxHostname, LinuxUsernames])
