# -*- coding: utf-8 -*-
"""This file contains preprocessors for Mac OS X."""

import abc
import plistlib

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.lib import plist
from plaso.parsers.plist_plugins import interface as plist_interface
from plaso.preprocessors import interface
from plaso.preprocessors import manager


class PlistPreprocessPlugin(interface.FileSystemPreprocessPlugin):
  """The plist preprocess plugin interface."""

  _PLIST_PATH = u''

  def _GetPlistRootKey(self, file_entry):
    """Opens a plist file entry.

    Args:
      file_entry (dfvfs.FileEntry): file entry of the plist.

    Returns:
      plistlib._InternalDict: plist root key.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    file_object = file_entry.GetFileObject()

    try:
      plist_file = plist.PlistFile()
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
  def Run(self, searcher, knowledge_base):
    """Determines the value of the preprocessing attributes.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
    """


class PlistKeyPreprocessPlugin(PlistPreprocessPlugin):
  """The plist key preprocess plugin interface.

  The plist key preprocess plugin retieves values from key names,
  defined in _PLIST_KEYS, from a specific plist file, defined in
  _PLIST_PATH.
  """

  # The key that's value should be returned back. It is an ordered list
  # of preference. If the first value is found it will be returned and no
  # others will be searched.
  _PLIST_KEYS = [u'']

  def _FindKeys(self, key, names, matches):
    """Searches the plist key hierarchy for keys with matching names.

    If a match is found a tuple of the key name and value is added to
    the matches list.

    Args:
      key (plistlib._InternalDict): plist key.
      names (list[str]): names of the keys to match.
      matches (list[str]): keys with matching names.
    """
    for name, subkey in iter(key.items()):
      if name in names:
        matches.append((name, subkey))

      # pylint: disable=protected-access
      if isinstance(subkey, plistlib._InternalDict):
        self._FindKeys(subkey, names, matches)

  @abc.abstractmethod
  def _ParseValue(self, knowledge_base, name, value):
    """Parses a plist key value.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """

  def Run(self, searcher, knowledge_base):
    """Determines the value of the preprocessing attributes.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    file_entry = self._FindFileEntry(searcher, self._PLIST_PATH)
    if not file_entry:
      return

    root_key = self._GetPlistRootKey(file_entry)
    if not root_key:
      location = getattr(file_entry.path_spec, u'location', u'')
      raise errors.PreProcessFail(
          u'Missing root key in plist: {0:s}'.format(location))

    matches = []

    self._FindKeys(root_key, self._PLIST_KEYS, matches)
    if not matches:
      raise errors.PreProcessFail(u'No such keys: {0:s}.'.format(
          u', '.join(self._PLIST_KEYS)))

    name = None
    value = None
    for name, value in matches:
      if value:
        break

    if value is None:
      raise errors.PreProcessFail(u'No values found for keys: {0:s}.'.format(
          u', '.join(self._PLIST_KEYS)))

    self._ParseValue(knowledge_base, name, value)


class MacOSXHostnamePreprocessPlugin(PlistKeyPreprocessPlugin):
  """Mac OS X hostname preprocessing plugin."""

  _PLIST_PATH = u'/Library/Preferences/SystemConfiguration/preferences.plist'
  _PLIST_KEYS = [u'ComputerName', u'LocalHostName']

  def _ParseValue(self, knowledge_base, name, value):
    """Parses a plist key value.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """
    if name not in self._PLIST_KEYS:
      return

    hostname_artifact = artifacts.HostnameArtifact(name=value)
    knowledge_base.SetHostname(hostname_artifact)


class MacOSXKeyboardLayoutPreprocessPlugin(PlistKeyPreprocessPlugin):
  """Mac OS X keyboard layout preprocessing plugin."""

  _PLIST_PATH = u'/Library/Preferences/com.apple.HIToolbox.plist'
  _PLIST_KEYS = [u'AppleCurrentKeyboardLayoutInputSourceID']

  def _ParseValue(self, knowledge_base, name, value):
    """Parses a plist key value.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """
    if name not in self._PLIST_KEYS:
      return

    if isinstance(value, (list, tuple)):
      value = value[0]

    _, _, keyboard_layout = value.rpartition(u'.')

    knowledge_base.SetValue(u'keyboard_layout', keyboard_layout)


class MacOSXSystemVersionPreprocessPlugin(PlistKeyPreprocessPlugin):
  """Mac OS X system version information preprocessing plugin."""

  _PLIST_PATH = u'/System/Library/CoreServices/SystemVersion.plist'
  _PLIST_KEYS = [u'ProductUserVisibleVersion']

  def _ParseValue(self, knowledge_base, name, value):
    """Parses a plist key value.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """
    if name not in self._PLIST_KEYS:
      return

    knowledge_base.SetValue(u'operating_system_version', value)


class MacOSXTimeZonePreprocessPlugin(interface.FileSystemPreprocessPlugin):
  """Mac OS X time zone preprocessing plugin."""

  _PATH = u'/private/etc/localtime'

  def Run(self, searcher, knowledge_base):
    """Determines the value of the preprocessing attributes.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    file_entry = self._FindFileEntry(searcher, self._PATH)
    if not file_entry:
      return

    if not file_entry.link:
      raise errors.PreProcessFail(
          u'Unable to retrieve time zone information from: {0:s}.'.format(
              self._PATH))

    _, _, time_zone = file_entry.link.partition(u'zoneinfo/')
    if not time_zone:
      return

    try:
      knowledge_base.SetTimeZone(time_zone)
    except ValueError:
      # TODO: add and store preprocessing errors.
      pass


class MacOSXUserAccountsPreprocessPlugin(PlistPreprocessPlugin):
  """Mac OS X user accouns preprocessing plugin."""

  ATTRIBUTE = u'users'

  # Define the path to the user account information.
  _PLIST_PATH_REGEX = (
      u'/private/var/db/dslocal/nodes/Default/users/[^_].+.plist')

  _KEYS = frozenset([u'gid', 'home', u'name', u'realname', u'shell', u'uid'])

  def _GetKeysDefaultEmpty(self, top_level, keys, depth=1):
    """Return keys nested in a plist dict, defaulting to an empty value.

    The method GetKeys fails if the supplied key does not exist within the
    plist object. This alternate method behaves the same way as GetKeys
    except that instead of raising an error if the key doesn't exist it will
    assign an empty string value ('') to the field.

    Args:
      top_level (plistlib._InternalDict): top level plist object.
      keys (set[str]): names of keys that should be returned.
      depth (int): depth within the plist, where 1 is top level.

    Returns:
      dict[str,str]: values of the requested keys.
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

  def _ParsePlistFileEntry(self, knowledge_base, file_entry):
    """Parses an user account plist file.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      file_entry (dfvfs.FileNetry): file entry of the user account plist file.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    root_key = self._GetPlistRootKey(file_entry)
    if not root_key:
      location = getattr(file_entry.path_spec, u'location', u'')
      raise errors.PreProcessFail(
          u'Missing root key in plist: {0:s}'.format(location))

    try:
      match = self._GetKeysDefaultEmpty(root_key, self._KEYS)
    except KeyError as exception:
      location = getattr(file_entry.path_spec, u'location', u'')
      raise errors.PreProcessFail(
          u'Unable to read user plist file: {0:s} with error: {1:s}'.format(
              location, exception))

    name = match.get(u'name', [None])[0]
    uid = match.get(u'uid', [None])[0]

    if not name or not uid:
      # TODO: add and store preprocessing errors.
      return

    user_account = artifacts.UserAccountArtifact(
        identifier=uid, username=name)
    user_account.group_identifier = match.get(u'gid', [None])[0]
    user_account.full_name = match.get(u'realname', [None])[0]
    user_account.shell = match.get(u'shell', [None])[0]
    user_account.user_directory = match.get(u'home', [None])[0]

    try:
      knowledge_base.AddUserAccount(user_account)
    except KeyError:
      # TODO: add and store preprocessing errors.
      pass

  def Run(self, searcher, knowledge_base):
    """Determines the value of the preprocessing attributes.

    Args:
      searcher (dfvfs.FileSystemSearcher): file system searcher.
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
    """
    path_specs = self._FindPathSpecs(searcher, self._PLIST_PATH_REGEX)
    if not path_specs:
      return

    for path_spec in path_specs:
      file_entry = searcher.GetFileEntryByPathSpec(path_spec)
      self._ParsePlistFileEntry(knowledge_base, file_entry)


manager.PreprocessPluginsManager.RegisterPlugins([
    MacOSXHostnamePreprocessPlugin, MacOSXKeyboardLayoutPreprocessPlugin,
    MacOSXSystemVersionPreprocessPlugin, MacOSXTimeZonePreprocessPlugin,
    MacOSXUserAccountsPreprocessPlugin])
