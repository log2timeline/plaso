# -*- coding: utf-8 -*-
"""MacOS preprocessor plugins."""

import abc
import plistlib

from plaso.containers import artifacts
from plaso.lib import errors
from plaso.lib import plist
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
    for name, subkey in key.items():
      if name in names:
        matches.append((name, subkey))

      if isinstance(subkey, dict):
        self._FindKeys(subkey, names, matches)

  def _ParseFileData(self, mediator, file_object):
    """Parses file content (data) for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
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

    self._ParsePlistKeyValue(mediator, name, value)

  @abc.abstractmethod
  def _ParsePlistKeyValue(self, mediator, name, value):
    """Parses a plist key value.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """


class MacOSHostnamePlugin(PlistFileArtifactPreprocessorPlugin):
  """MacOS hostname plugin."""

  ARTIFACT_DEFINITION_NAME = 'MacOSSystemConfigurationPreferencesPlistFile'

  _PLIST_KEYS = ['ComputerName', 'LocalHostName']

  def _ParsePlistKeyValue(self, mediator, name, value):
    """Parses a plist key value.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """
    if name in self._PLIST_KEYS:
      hostname_artifact = artifacts.HostnameArtifact(name=value)
      mediator.AddHostname(hostname_artifact)


class MacOSKeyboardLayoutPlugin(PlistFileArtifactPreprocessorPlugin):
  """MacOS keyboard layout plugin."""

  ARTIFACT_DEFINITION_NAME = 'MacOSKeyboardLayoutPlistFile'

  _PLIST_KEYS = ['AppleCurrentKeyboardLayoutInputSourceID']

  def _ParsePlistKeyValue(self, mediator, name, value):
    """Parses a plist key value.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """
    if name in self._PLIST_KEYS:
      if isinstance(value, (list, tuple)):
        value = value[0]

      _, _, keyboard_layout = value.rpartition('.')

      mediator.SetValue('keyboard_layout', keyboard_layout)


class MacOSSystemVersionPlugin(PlistFileArtifactPreprocessorPlugin):
  """MacOS system version information plugin."""

  ARTIFACT_DEFINITION_NAME = 'MacOSSystemVersionPlistFile'

  _PLIST_KEYS = ['ProductUserVisibleVersion']

  def _ParsePlistKeyValue(self, mediator, name, value):
    """Parses a plist key value.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      name (str): name of the plist key.
      value (str): value of the plist key.
    """
    if name in self._PLIST_KEYS:
      mediator.SetValue('operating_system_version', value)


class MacOSTimeZonePlugin(interface.FileEntryArtifactPreprocessorPlugin):
  """MacOS time zone plugin."""

  ARTIFACT_DEFINITION_NAME = 'MacOSLocalTime'

  def _ParseFileEntry(self, mediator, file_entry):
    """Parses artifact file system data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
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
    if time_zone:
      try:
        mediator.SetTimeZone(time_zone)
      except ValueError:
        mediator.ProducePreprocessingWarning(
            self.ARTIFACT_DEFINITION_NAME,
            'Unable to set time zone in knowledge base.')


class MacOSUserAccountsPlugin(interface.FileEntryArtifactPreprocessorPlugin):
  """MacOS user accounts plugin."""

  ARTIFACT_DEFINITION_NAME = 'MacOSUserPasswordHashesPlistFiles'

  _KEYS = frozenset(['gid', 'home', 'name', 'realname', 'shell', 'uid'])

  def _GetTopLevelKeys(self, top_level, keys):
    """Retrieves top-level plist keys.

    Args:
      top_level (plistlib._InternalDict): top level plist object.
      keys (set[str]): names of the top-level keys that should be retrieved.

    Returns:
      dict[str, str]: values of the requested keys or an empty dictionary if
          no corresponding top-level keys were found.
    """
    match = {}
    for key in set(keys):
      value = top_level.get(key, None)
      if value is not None:
        match[key] = value

    return match

  def _ParseFileEntry(self, mediator, file_entry):
    """Parses artifact file system data for a preprocessing attribute.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage.
      file_entry (dfvfs.FileEntry): file entry that contains the artifact
          value data.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    file_object = file_entry.GetFileObject()

    try:
      plist_file = plist.PlistFile()
      plist_file.Read(file_object)
      match = self._GetTopLevelKeys(plist_file.root_key, self._KEYS)

    except (IOError, plistlib.InvalidFileException) as exception:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to read plist with error: {0!s}.'.format(exception))
      return

    name = match.get('name', [None])[0]
    uid = match.get('uid', [None])[0]

    if not name or not uid:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME, 'Missing name or user identifier')
      return

    user_account = artifacts.UserAccountArtifact(
        identifier=uid, username=name)
    user_account.group_identifier = match.get('gid', [None])[0]
    user_account.full_name = match.get('realname', [None])[0]
    user_account.shell = match.get('shell', [None])[0]
    user_account.user_directory = match.get('home', [None])[0]

    try:
      mediator.AddUserAccount(user_account)
    except KeyError:
      mediator.ProducePreprocessingWarning(
          self.ARTIFACT_DEFINITION_NAME,
          'Unable to add user account: {0:s} to knowledge base.'.format(name))


manager.PreprocessPluginsManager.RegisterPlugins([
    MacOSHostnamePlugin, MacOSKeyboardLayoutPlugin, MacOSSystemVersionPlugin,
    MacOSTimeZonePlugin, MacOSUserAccountsPlugin])
