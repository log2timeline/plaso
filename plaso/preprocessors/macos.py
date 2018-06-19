# -*- coding: utf-8 -*-
"""This file contains preprocessors for MacOS."""

from __future__ import unicode_literals

import abc

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.lib import plist
from plaso.parsers.plist_plugins import interface as plist_interface
from plaso.preprocessors import interface
from plaso.preprocessors import manager


class PlistFileArtifactPreprocessorPlugin(
    interface.FileArtifactPreprocessorPlugin):
  """Plist file artifact preprocessor plugin interface.

  Retrieves values from a plist file artifact using names of keys defined
  in _PLIST_KEYS.
  """

  # The key that's value should be returned back. It is an ordered list
  # of preference. If the first value is found it will be returned and no
  # others will be searched.
  _PLIST_KEYS = ['']

  def _FindKeys(self, key, names, matches):
    """Searches the plist key hierarchy for keys with matching names.

    If a match is found a tuple of the key name and value is added to
    the matches list.

    Args:
      key (dict[str, object]): plist key.
      names (list[str]): names of the keys to match.
      matches (list[str]): keys with matching names.
    """
    for name, subkey in iter(key.items()):
      if name in names:
        matches.append((name, subkey))

      if isinstance(subkey, dict):
        self._FindKeys(subkey, names, matches)

  def _ParseFileData(self, knowledge_base, file_object):
    """Parses file content (data) for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      file_object (dfvfs.FileIO): file-like object that contains the artifact
          value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    plist_file = plist.PlistFile()

    try:
      plist_file.Read(file_object)

    except IOError as exception:
      raise errors.PreProcessFail(
          'Unable to read: {0:s} with error: {1!s}'.format(
              self.ARTIFACT_DEFINITION_NAME, exception))

    if not plist_file.root_key:
      raise errors.PreProcessFail((
          'Unable to read: {0:s} with error: missing root key').format(
              self.ARTIFACT_DEFINITION_NAME))

    matches = []

    self._FindKeys(plist_file.root_key, self._PLIST_KEYS, matches)
    if not matches:
      raise errors.PreProcessFail(
          'Unable to read: {0:s} with error: no such keys: {1:s}.'.format(
              self.ARTIFACT_DEFINITION_NAME, ', '.join(self._PLIST_KEYS)))

    name = None
    value = None
    for name, value in matches:
      if value:
        break

    if value is None:
      raise errors.PreProcessFail((
          'Unable to read: {0:s} with error: no values found for keys: '
          '{1:s}.').format(
              self.ARTIFACT_DEFINITION_NAME, ', '.join(self._PLIST_KEYS)))

    self._ParsePlistKeyValue(knowledge_base, name, value)

  @abc.abstractmethod
  def _ParsePlistKeyValue(self, knowledge_base, name, value):
    """Parses a plist key value.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """


class MacOSHostnamePlugin(PlistFileArtifactPreprocessorPlugin):
  """MacOS hostname plugin."""

  ARTIFACT_DEFINITION_NAME = 'MacOSSystemConfigurationPreferencesPlistFile'

  _PLIST_KEYS = ['ComputerName', 'LocalHostName']

  def _ParsePlistKeyValue(self, knowledge_base, name, value):
    """Parses a plist key value.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """
    if not knowledge_base.GetHostname():
      if name in self._PLIST_KEYS:
        hostname_artifact = artifacts.HostnameArtifact(name=value)
        knowledge_base.SetHostname(hostname_artifact)


class MacOSKeyboardLayoutPlugin(PlistFileArtifactPreprocessorPlugin):
  """MacOS keyboard layout plugin."""

  ARTIFACT_DEFINITION_NAME = 'MacOSKeyboardLayoutPlistFile'

  _PLIST_KEYS = ['AppleCurrentKeyboardLayoutInputSourceID']

  def _ParsePlistKeyValue(self, knowledge_base, name, value):
    """Parses a plist key value.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """
    if not knowledge_base.GetValue('keyboard_layout'):
      if name in self._PLIST_KEYS:
        if isinstance(value, (list, tuple)):
          value = value[0]

        _, _, keyboard_layout = value.rpartition('.')

        knowledge_base.SetValue('keyboard_layout', keyboard_layout)


class MacOSSystemVersionPlugin(PlistFileArtifactPreprocessorPlugin):
  """MacOS system version information plugin."""

  ARTIFACT_DEFINITION_NAME = 'MacOSSystemVersionPlistFile'

  _PLIST_KEYS = ['ProductUserVisibleVersion']

  def _ParsePlistKeyValue(self, knowledge_base, name, value):
    """Parses a plist key value.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """
    if not knowledge_base.GetValue('operating_system_version'):
      if name in self._PLIST_KEYS:
        knowledge_base.SetValue('operating_system_version', value)


class MacOSTimeZonePlugin(interface.FileEntryArtifactPreprocessorPlugin):
  """MacOS time zone plugin."""

  ARTIFACT_DEFINITION_NAME = 'MacOSLocalTime'

  def _ParseFileEntry(self, knowledge_base, file_entry):
    """Parses artifact file system data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      file_entry (dfvfs.FileEntry): file entry that contains the artifact
          value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    if not file_entry or not file_entry.link:
      raise errors.PreProcessFail(
          'Unable to read: {0:s} with error: not a symbolic link'.format(
              self.ARTIFACT_DEFINITION_NAME))

    _, _, time_zone = file_entry.link.partition('zoneinfo/')
    # TODO: check if time zone is set in knowledge base.
    if time_zone:
      try:
        knowledge_base.SetTimeZone(time_zone)
      except ValueError:
        # TODO: add and store preprocessing errors.
        pass


class MacOSUserAccountsPlugin(interface.FileEntryArtifactPreprocessorPlugin):
  """MacOS user accounts plugin."""

  ARTIFACT_DEFINITION_NAME = 'MacOSUserPasswordHashesPlistFiles'

  _KEYS = frozenset(['gid', 'home', 'name', 'realname', 'shell', 'uid'])

  def _GetKeysDefaultEmpty(self, top_level, keys, depth=1):
    """Retrieves plist keys, defaulting to empty values.

    Args:
      top_level (plistlib._InternalDict): top level plist object.
      keys (set[str]): names of keys that should be returned.
      depth (int): depth within the plist, where 1 is top level.

    Returns:
      dict[str, str]: values of the requested keys.
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

  def _GetPlistRootKey(self, file_entry):
    """Retrieves the root key of a plist file.

    Args:
      file_entry (dfvfs.FileEntry): file entry of the plist.

    Returns:
      dict[str, object]: plist root key.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    file_object = file_entry.GetFileObject()

    try:
      plist_file = plist.PlistFile()
      plist_file.Read(file_object)

    except IOError as exception:
      location = getattr(file_entry.path_spec, 'location', '')
      raise errors.PreProcessFail(
          'Unable to read plist file: {0:s} with error: {1!s}'.format(
              location, exception))

    finally:
      file_object.close()

    return plist_file.root_key

  def _ParseFileEntry(self, knowledge_base, file_entry):
    """Parses artifact file system data for a preprocessing attribute.

    Args:
      knowledge_base (KnowledgeBase): to fill with preprocessing information.
      file_entry (dfvfs.FileEntry): file entry that contains the artifact
          value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    root_key = self._GetPlistRootKey(file_entry)
    if not root_key:
      location = getattr(file_entry.path_spec, 'location', '')
      raise errors.PreProcessFail((
          'Unable to read: {0:s} plist: {1:s} with error: missing root '
          'key.').format(self.ARTIFACT_DEFINITION_NAME, location))

    try:
      match = self._GetKeysDefaultEmpty(root_key, self._KEYS)
    except KeyError as exception:
      location = getattr(file_entry.path_spec, 'location', '')
      raise errors.PreProcessFail(
          'Unable to read: {0:s} plist: {1:s} with error: {2!s}'.format(
              self.ARTIFACT_DEFINITION_NAME, location, exception))

    name = match.get('name', [None])[0]
    uid = match.get('uid', [None])[0]

    if not name or not uid:
      # TODO: add and store preprocessing errors.
      return

    user_account = artifacts.UserAccountArtifact(
        identifier=uid, username=name)
    user_account.group_identifier = match.get('gid', [None])[0]
    user_account.full_name = match.get('realname', [None])[0]
    user_account.shell = match.get('shell', [None])[0]
    user_account.user_directory = match.get('home', [None])[0]

    try:
      knowledge_base.AddUserAccount(user_account)
    except KeyError:
      # TODO: add and store preprocessing errors.
      pass


manager.PreprocessPluginsManager.RegisterPlugins([
    MacOSHostnamePlugin, MacOSKeyboardLayoutPlugin, MacOSSystemVersionPlugin,
    MacOSTimeZonePlugin, MacOSUserAccountsPlugin])
