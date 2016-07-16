# -*- coding: utf-8 -*-
"""This file contains classes used for preprocessing in plaso."""

import abc
import logging

from dfvfs.helpers import file_system_searcher

from plaso.lib import definitions
from plaso.lib import errors


class PreprocessPlugin(object):
  """Class that defines the preprocess plugin object interface.

  Any preprocessing plugin that implements this interface
  should define which operating system this plugin supports.

  The OS variable supports the following values:

  * Windows
  * Linux
  * MacOSX

  Since some plugins may require knowledge gained from
  other checks all plugins have a weight associated to it.
  The weight variable can have values from one to three:
  * 1 - Requires no prior knowledge, can run immediately.
  * 2 - Requires knowledge from plugins with weight 1.
  * 3 - Requires knowledge from plugins with weight 2.

  The default weight of 3 is assigned to plugins, so each
  plugin needs to overwrite that value if needed.

  The plugins are grouped by the operating system they work
  on and then on their weight. That means that if the tool
  is run against a Windows system all plugins that support
  Windows are grouped together, and only plugins with weight
  one are run, then weight two followed by the rest of the
  plugins with the weight of three. There is no priority or
  guaranteed order of plugins that have the same weight, which
  makes it important to define the weight appropriately.
  """

  # Defines the OS that this plugin supports.
  SUPPORTED_OS = []

  # Weight is an INT, with the value of 1-3.
  WEIGHT = 3

  # Defines the knowledge base attribute to be set.
  ATTRIBUTE = u''

  @property
  def plugin_name(self):
    """Return the name of the plugin."""
    return self.__class__.__name__

  # TODO: refactor to PathPreprocessPlugin or equivalent.
  def _FindFileEntry(self, searcher, path):
    """Searches for a file entry that matches the path.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      path: The location of the file entry relative to the file system
            of the searcher.

    Returns:
      The file entry if successful or None otherwise.

    Raises:
      errors.PreProcessFail: if the file entry cannot be found or opened.
    """
    path_specs = self._FindPathSpecs(searcher, path)
    if not path_specs or len(path_specs) != 1:
      raise errors.PreProcessFail(u'Unable to find: {0:s}'.format(path))

    try:
      return searcher.GetFileEntryByPathSpec(path_specs[0])
    except IOError as exception:
      raise errors.PreProcessFail(
          u'Unable to retrieve file entry: {0:s} with error: {1:s}'.format(
              path, exception))

  # TODO: refactor to PathPreprocessPlugin or equivalent.
  def _FindPathSpecs(self, searcher, path):
    """Searches for path specifications that matches the path.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      path: The location of the file entry relative to the file system
            of the searcher.

    Returns:
      A list of path specifcations.
    """
    find_spec = file_system_searcher.FindSpec(
        location_regex=path, case_sensitive=False)
    return list(searcher.Find(find_specs=[find_spec]))

  @abc.abstractmethod
  def GetValue(self, searcher, knowledge_base):
    """Retrieves the attribute value.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.

    Returns:
      The attribute value.
    """

  def Run(self, searcher, knowledge_base):
    """Runs the plugins to determine the value of the preprocessing attribute.

    The resulting preprocessing attribute value is stored in the knowledge base.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
    """
    value = self.GetValue(searcher, knowledge_base)
    knowledge_base.SetValue(self.ATTRIBUTE, value)
    value = knowledge_base.GetValue(self.ATTRIBUTE, default_value=u'N/A')
    logging.info(u'[PreProcess] Set attribute: {0:s} to {1:s}'.format(
        self.ATTRIBUTE, value))


class PathPreprocessPlugin(PreprocessPlugin):
  """Return a simple path."""

  WEIGHT = 1

  def GetValue(self, searcher, unused_knowledge_base):
    """Returns the path as found by the searcher.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.

    Returns:
      The first path location string.

    Raises:
      PreProcessFail: if the path could not be found.
    """
    path_specs = self._FindPathSpecs(searcher, self.PATH)
    if not path_specs:
      raise errors.PreProcessFail(
          u'Unable to find path: {0:s}'.format(self.PATH))

    relative_path = searcher.GetRelativePath(path_specs[0])
    if not relative_path:
      raise errors.PreProcessFail(
          u'Missing relative path for: {0:s}'.format(self.PATH))

    return relative_path


def GuessOS(searcher):
  """Returns a string representing what we think the underlying OS is.

  The available return strings are:

  * Linux
  * MacOSX
  * Windows

  Args:
    searcher: The file system searcher object (instance of
              dfvfs.FileSystemSearcher).

  Returns:
     A string indicating which OS we are dealing with.
  """
  find_specs = [
      file_system_searcher.FindSpec(
          location=u'/etc', case_sensitive=False),
      file_system_searcher.FindSpec(
          location=u'/System/Library', case_sensitive=False),
      file_system_searcher.FindSpec(
          location=u'/Windows/System32', case_sensitive=False),
      file_system_searcher.FindSpec(
          location=u'/WINNT/System32', case_sensitive=False),
      file_system_searcher.FindSpec(
          location=u'/WINNT35/System32', case_sensitive=False),
      file_system_searcher.FindSpec(
          location=u'/WTSRV/System32', case_sensitive=False)]

  locations = []
  for path_spec in searcher.Find(find_specs=find_specs):
    relative_path = searcher.GetRelativePath(path_spec)
    if relative_path:
      locations.append(relative_path.lower())

  # We need to check for both forward and backward slashes since the path
  # spec will be OS dependent, as in running the tool on Windows will return
  # Windows paths (backward slash) vs. forward slash on *NIX systems.
  windows_locations = set([
      u'/windows/system32', u'\\windows\\system32', u'/winnt/system32',
      u'\\winnt\\system32', u'/winnt35/system32', u'\\winnt35\\system32',
      u'\\wtsrv\\system32', u'/wtsrv/system32'])

  if windows_locations.intersection(set(locations)):
    return definitions.OS_WINDOWS

  if u'/system/library' in locations:
    return definitions.OS_MACOSX

  if u'/etc' in locations:
    return definitions.OS_LINUX

  return definitions.OS_UNKNOWN
