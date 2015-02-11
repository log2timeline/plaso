# -*- coding: utf-8 -*-
"""This file contains preprocessors for Mac OS X."""

import logging

from binplist import binplist
from dfvfs.helpers import file_system_searcher
from xml.etree import ElementTree

from plaso.lib import errors
from plaso.lib import utils
from plaso.parsers.plist_plugins import interface as plist_interface
from plaso.preprocessors import interface
from plaso.preprocessors import manager


class PlistPreprocessPlugin(interface.PreprocessPlugin):
  """Class that defines the plist preprocess plugin object."""

  SUPPORTED_OS = ['MacOSX']
  WEIGHT = 2

  # Path to the plist file to be parsed, can depend on paths discovered
  # in previous preprocessors.
  PLIST_PATH = ''

  # The key that's value should be returned back. It is an ordered list
  # of preference. If the first value is found it will be returned and no
  # others will be searched.
  PLIST_KEYS = ['']

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

    file_object = file_entry.GetFileObject()
    value = self.ParseFile(file_entry, file_object)
    file_object.close()

    return value

  def ParseFile(self, file_entry, file_object):
    """Parses the plist file and returns the parsed key.

    Args:
      file_entry: The file entry (instance of dfvfs.FileEntry).
      file_object: The file-like object.

    Returns:
      The value of the first key defined by PLIST_KEYS that is found.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    try:
      plist_file = binplist.BinaryPlist(file_object)
      top_level_object = plist_file.Parse()

    except binplist.FormatError as exception:
      raise errors.PreProcessFail(
          u'File is not a plist: {0:s} with error: {1:s}'.format(
              file_entry.path_spec.comparable, exception))

    except OverflowError as exception:
      raise errors.PreProcessFail(
          u'Unable to process plist: {0:s} with error: {1:s}'.format(
              file_entry.path_spec.comparable, exception))

    if not plist_file:
      raise errors.PreProcessFail(
          u'File is not a plist: {0:s}'.format(file_entry.path_spec.comparable))

    match = None
    key_name = ''
    for plist_key in self.PLIST_KEYS:
      try:
        match = plist_interface.GetKeys(
            top_level_object, frozenset([plist_key]))
      except KeyError:
        continue
      if match:
        key_name = plist_key
        break

    if not match:
      raise errors.PreProcessFail(
          u'Keys not found inside plist file: {0:s}.'.format(
              u','.join(self.PLIST_KEYS)))

    return self.ParseKey(match, key_name)

  def ParseKey(self, key, key_name):
    """Retrieves a specific value from the key.

    Args:
      key: The key object (instance of dict).
      key_name: The name of the key.

    Returns:
      The value of the key defined by key_name.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    value = key.get(key_name, None)
    if not value:
      raise errors.PreProcessFail(
          u'Value of key: {0:s} not found.'.format(key_name))

    return value


class XMLPlistPreprocessPlugin(PlistPreprocessPlugin):
  """Class that defines the Mac OS X XML plist preprocess plugin object."""

  def _GetKeys(self, xml_root, key_name):
    """Return a dict with the requested keys."""
    match = {}

    generator = xml_root.iter()
    for key in generator:
      if 'key' in key.tag and key_name in key.text:
        value_key = generator.next()
        value = ''
        for subkey in value_key.iter():
          if 'string' in subkey.tag:
            value = subkey.text
        match[key.text] = value

    # Now we need to go over the match dict and retrieve values.
    return match

  def ParseFile(self, file_entry, file_object):
    """Parse the file and return parsed key.

    Args:
      file_entry: The file entry (instance of dfvfs.FileEntry).
      file_object: The file-like object.

    Returns:
      The value of the first key defined by PLIST_KEYS that is found.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    # TODO: Move to defusedxml for safer XML parsing.
    try:
      xml = ElementTree.parse(file_object)
    except ElementTree.ParseError:
      raise errors.PreProcessFail(u'File is not a XML file.')
    except IOError:
      raise errors.PreProcessFail(u'File is not a XML file.')

    xml_root = xml.getroot()
    key_name = ''
    match = None
    for key in self.PLIST_KEYS:
      match = self._GetKeys(xml_root, key)
      if match:
        key_name = key
        break

    if not match:
      raise errors.PreProcessFail(
          u'Keys not found inside plist file: {0:s}.'.format(
              u','.join(self.PLIST_KEYS)))

    return self.ParseKey(match, key_name)


class MacOSXBuild(XMLPlistPreprocessPlugin):
  """Fetches build information about a Mac OS X system."""

  ATTRIBUTE = 'build'
  PLIST_PATH = '/System/Library/CoreServices/SystemVersion.plist'

  PLIST_KEYS = ['ProductUserVisibleVersion']


class MacOSXHostname(XMLPlistPreprocessPlugin):
  """Fetches hostname information about a Mac OS X system."""

  ATTRIBUTE = 'hostname'
  PLIST_PATH = '/Library/Preferences/SystemConfiguration/preferences.plist'

  PLIST_KEYS = ['ComputerName', 'LocalHostName']


class MacOSXKeyboard(PlistPreprocessPlugin):
  """Fetches keyboard information from a Mac OS X system."""

  ATTRIBUTE = 'keyboard_layout'
  PLIST_PATH = '/Library/Preferences/com.apple.HIToolbox.plist'

  PLIST_KEYS = ['AppleCurrentKeyboardLayoutInputSourceID']

  def ParseKey(self, key, key_name):
    """Determines the keyboard layout."""
    value = super(MacOSXKeyboard, self).ParseKey(key, key_name)
    if type(value) in (list, tuple):
      value = value[0]
    _, _, keyboard_layout = value.rpartition('.')

    return keyboard_layout


class MacOSXTimeZone(interface.PreprocessPlugin):
  """Gather timezone information from a Mac OS X system."""

  ATTRIBUTE = 'time_zone_str'
  SUPPORTED_OS = ['MacOSX']

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


class MacOSXUsers(interface.PreprocessPlugin):
  """Get information about user accounts on a Mac OS X system."""

  SUPPORTED_OS = ['MacOSX']
  ATTRIBUTE = 'users'
  WEIGHT = 1

  # Define the path to the user account information.
  USER_PATH = '/private/var/db/dslocal/nodes/Default/users/[^_].+.plist'

  _KEYS = frozenset(['name', 'uid', 'home', 'realname'])

  def _OpenPlistFile(self, searcher, path_spec):
    """Open a Plist file given a path and returns a plist top level object.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      path_spec: The path specification (instance of dfvfs.PathSpec)
                 of the plist file.

    Raises:
      errors.PreProcessFail: if the preprocessing fails.
    """
    plist_file_location = getattr(path_spec, 'location', u'')
    file_entry = searcher.GetFileEntryByPathSpec(path_spec)
    file_object = file_entry.GetFileObject()

    try:
      plist_file = binplist.BinaryPlist(file_object)
      top_level_object = plist_file.Parse()

    except binplist.FormatError as exception:
      exception = utils.GetUnicodeString(exception)
      raise errors.PreProcessFail(
          u'File is not a plist: {0:s}'.format(exception))

    except OverflowError as exception:
      raise errors.PreProcessFail(
          u'Error processing: {0:s} with error: {1:s}'.format(
              plist_file_location, exception))

    if not plist_file:
      raise errors.PreProcessFail(
          u'File is not a plist: {0:s}'.format(plist_file_location))

    return top_level_object

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
    find_spec = file_system_searcher.FindSpec(
        location_regex=self.USER_PATH, case_sensitive=False)

    path_specs = list(searcher.Find(find_specs=[find_spec]))
    if not path_specs:
      raise errors.PreProcessFail(u'Unable to find user plist files.')

    users = []
    for path_spec in path_specs:
      plist_file_location = getattr(path_spec, 'location', u'')
      if not plist_file_location:
        raise errors.PreProcessFail(u'Missing user plist file location.')

      try:
        top_level_object = self._OpenPlistFile(searcher, path_spec)
      except IOError:
        logging.warning(u'Unable to parse user plist file: {0:s}'.format(
            plist_file_location))
        continue

      try:
        match = plist_interface.GetKeysDefaultEmpty(
            top_level_object, self._KEYS)
      except KeyError as exception:
        logging.warning(
            u'Unable to read user plist file: {0:s} with error: {1:s}'.format(
                plist_file_location, exception))
        continue

      # TODO: as part of artifacts, create a proper object for this.
      user = {
          'uid': match.get('uid', [-1])[0],
          'path': match.get('home', [u'<not set>'])[0],
          'name': match.get('name', [u'<not set>'])[0],
          'realname': match.get('realname', [u'N/A'])[0]}
      users.append(user)

    if not users:
      raise errors.PreProcessFail(u'Unable to find any users on the system.')

    return users


manager.PreprocessPluginsManager.RegisterPlugins([
    MacOSXBuild, MacOSXHostname, MacOSXKeyboard, MacOSXTimeZone, MacOSXUsers])
