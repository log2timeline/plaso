# -*- coding: utf-8 -*-
"""This file contains preprocessors for Mac OS X."""

import abc
import logging
import plistlib

from plaso.lib import errors
from plaso.lib import plist
from plaso.parsers.plist_plugins import interface as plist_interface
from plaso.preprocessors import interface
from plaso.preprocessors import manager


class PlistPreprocessPlugin(interface.PreprocessPlugin):
  """Class that defines the plist preprocess plugin object."""

  def _GetPlistRootKey(self, file_entry):
    """Open a plist file entry.

    Args:
      file_entry: The plist file entry (instance of dfvfs.FileEntry).

    Returns:
      The plist root key (instance of plistlib._InternalDict).

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    file_object = file_entry.GetFileObject()

    plist_file = plist.PlistFile()
    try:
      plist_file.Read(file_object)

    except IOError as exception:
      location = getattr(file_entry.path_spec, u'location', u'')
      raise errors.PreProcessFail(
          u'Unable to read plist file: {0:s} with error: {1:s}'.format(
              location, exception))

    finally:
      file_object.close()

    return plist_file.root_key

  @abc.abstractmethod
  def GetValue(self, searcher, knowledge_base):
    """Return the value for the attribute.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.
    """
    raise NotImplementedError


class PlistKeyPreprocessPlugin(PlistPreprocessPlugin):
  """Class that defines the plist key preprocess plugin object.

  The plist key preprocess plugin retieves values from key names,
  defined in PLIST_KEYS, from a specific plist file, defined in
  PLIST_PATH.
  """

  SUPPORTED_OS = [u'MacOSX']
  WEIGHT = 2

  # Path to the plist file to be parsed, can depend on paths discovered
  # in previous preprocessors.
  PLIST_PATH = u''

  # The key that's value should be returned back. It is an ordered list
  # of preference. If the first value is found it will be returned and no
  # others will be searched.
  PLIST_KEYS = [u'']

  def _FindKeys(self, key, names, matches):
    """Searches the plist key hierarchy for keys with matching names.

    If a match is found a tuple of the key name and value is added to
    the matches list.

    Args:
      key: a plist key (instance of plistlib._InternalDict).
      names: list of names of the keys to match.
      matches: a list to add the keys with matching names.
    """
    for name, subkey in key.iteritems():
      if name in names:
        matches.append((name, subkey))

      if isinstance(subkey, plistlib._InternalDict):
        self._FindKeys(subkey, names, matches)

  def GetValue(self, searcher, unused_knowledge_base):
    """Returns a value retrieved from keys within a plist file.

    Where the name of the keys are defined in PLIST_KEYS.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.

    Returns:
      The value of the first key that is found.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    file_entry = self._FindFileEntry(searcher, self.PLIST_PATH)
    if not file_entry:
      raise errors.PreProcessFail(
          u'Unable to open file: {0:s}'.format(self.PLIST_PATH))

    root_key = self._GetPlistRootKey(file_entry)
    if not root_key:
      location = getattr(file_entry.path_spec, u'location', u'')
      raise errors.PreProcessFail(
          u'Missing root key in plist: {0:s}'.format(location))

    matches = []

    self._FindKeys(root_key, self.PLIST_KEYS, matches)
    if not matches:
      raise errors.PreProcessFail(u'No such keys: {0:s}.'.format(
          u', '.join(self.PLIST_KEYS)))

    key_name = None
    key_value = None
    for key_name, key_value in matches:
      if key_value:
        break

    if key_value is None:
      raise errors.PreProcessFail(u'No values found for keys: {0:s}.'.format(
          u', '.join(self.PLIST_KEYS)))

    return self.ParseValue(key_name, key_value)

  def ParseValue(self, unused_key_name, key_value):
    """Parses a key value.

    Args:
      key_name: The name of the key.
      key_value: The value of the key.

    Returns:
      The parsed value.

    Raises:
      errors.PreProcessFail: if the value cannot be parsed.
    """
    return key_value


class MacOSXBuild(PlistKeyPreprocessPlugin):
  """Fetches build information about a Mac OS X system."""

  ATTRIBUTE = u'build'
  PLIST_PATH = u'/System/Library/CoreServices/SystemVersion.plist'

  PLIST_KEYS = [u'ProductUserVisibleVersion']


class MacOSXHostname(PlistKeyPreprocessPlugin):
  """Fetches hostname information about a Mac OS X system."""

  ATTRIBUTE = u'hostname'
  PLIST_PATH = u'/Library/Preferences/SystemConfiguration/preferences.plist'

  PLIST_KEYS = [u'ComputerName', u'LocalHostName']


class MacOSXKeyboard(PlistKeyPreprocessPlugin):
  """Fetches keyboard information from a Mac OS X system."""

  ATTRIBUTE = u'keyboard_layout'
  PLIST_PATH = u'/Library/Preferences/com.apple.HIToolbox.plist'

  PLIST_KEYS = [u'AppleCurrentKeyboardLayoutInputSourceID']

  def ParseValue(self, unused_key_name, key_value):
    """Parses a key value.

    Args:
      key_name: The name of the key.
      key_value: The value of the key.

    Returns:
      The parsed value.

    Raises:
      errors.PreProcessFail: if the value cannot be parsed.
    """
    if isinstance(key_value, (list, tuple)):
      key_value = key_value[0]
    _, _, keyboard_layout = key_value.rpartition(u'.')

    return keyboard_layout


class MacOSXTimeZone(interface.PreprocessPlugin):
  """Gather timezone information from a Mac OS X system."""

  ATTRIBUTE = u'time_zone_str'
  SUPPORTED_OS = [u'MacOSX']

  WEIGHT = 1

  ZONE_FILE_PATH = u'/private/etc/localtime'

  def GetValue(self, searcher, unused_knowledge_base):
    """Determines the local time zone settings.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      knowledge_base: A knowledge base object (instance of KnowledgeBase),
                      which contains information from the source data needed
                      for parsing.

    Returns:
      The local timezone settings.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    path = self.ZONE_FILE_PATH
    file_entry = self._FindFileEntry(searcher, path)
    if not file_entry:
      raise errors.PreProcessFail(
          u'Unable to find file: {0:s}'.format(path))

    if not file_entry.link:
      raise errors.PreProcessFail(
          u'Unable to retrieve timezone information from: {0:s}.'.format(path))

    _, _, zone = file_entry.link.partition(u'zoneinfo/')
    return zone


class MacOSXUsers(PlistPreprocessPlugin):
  """Get information about user accounts on a Mac OS X system."""

  SUPPORTED_OS = [u'MacOSX']
  ATTRIBUTE = u'users'
  WEIGHT = 1

  # Define the path to the user account information.
  USER_PATH = u'/private/var/db/dslocal/nodes/Default/users/[^_].+.plist'

  _KEYS = frozenset([u'name', u'uid', u'home', u'realname'])

  def _GetKeysDefaultEmpty(self, top_level, keys, depth=1):
    """Return keys nested in a plist dict, defaulting to an empty value.

    The method GetKeys fails if the supplied key does not exist within the
    plist object. This alternate method behaves the same way as GetKeys
    except that instead of raising an error if the key doesn't exist it will
    assign an empty string value ('') to the field.

    Args:
      top_level: Plist in dictionary form.
      keys: A list of keys that should be returned.
      depth: Defines how many levels deep to check for a match.

    Returns:
      A dictionary with just the keys requested.
    """
    keys = set(keys)
    match = {}

    if depth == 1:
      for key in keys:
        value = top_level.get(key, None)
        if value is not None:
          match[key] = value
    else:
      for _, parsed_key, parsed_value in plist_interface.RecurseKey(
          top_level, depth=depth):
        if parsed_key in keys:
          match[parsed_key] = parsed_value
          if set(match.keys()) == keys:
            return match
    return match

  def GetValue(self, searcher, unused_knowledge_base):
    """Determines the user accounts.

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
    path_specs = self._FindPathSpecs(searcher, self.USER_PATH)
    if not path_specs:
      raise errors.PreProcessFail(u'Unable to find user plist files.')

    users = []
    for path_spec in path_specs:
      file_entry = searcher.GetFileEntryByPathSpec(path_spec)

      root_key = self._GetPlistRootKey(file_entry)
      if not root_key:
        location = getattr(path_spec, u'location', u'')
        logging.warning(u'Missing root key in plist: {0:s}'.format(location))
        continue

      try:
        match = self._GetKeysDefaultEmpty(root_key, self._KEYS)
      except KeyError as exception:
        location = getattr(path_spec, u'location', u'')
        logging.warning(
            u'Unable to read user plist file: {0:s} with error: {1:s}'.format(
                location, exception))
        continue

      # TODO: as part of artifacts, create a proper object for this.
      user = {
          u'uid': match.get(u'uid', [-1])[0],
          u'path': match.get(u'home', [u'<not set>'])[0],
          u'name': match.get(u'name', [u'<not set>'])[0],
          u'realname': match.get(u'realname', [u'N/A'])[0]}
      users.append(user)

    if not users:
      raise errors.PreProcessFail(u'Unable to find any users on the system.')

    return users


manager.PreprocessPluginsManager.RegisterPlugins([
    MacOSXBuild, MacOSXHostname, MacOSXKeyboard, MacOSXTimeZone, MacOSXUsers])
