#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains preprocessors for Mac OS X."""

import logging

from binplist import binplist
from dfvfs.helpers import file_system_searcher

from plaso.lib import errors
from plaso.lib import utils
from plaso.parsers.plist_plugins import interface as plist_interface
from plaso.preprocessors import interface


class MacOSXBuild(interface.MacXMLPlistPreprocess):
  """Fetches build information about a Mac OS X system."""

  ATTRIBUTE = 'build'
  PLIST_PATH = '/System/Library/CoreServices/SystemVersion.plist'

  PLIST_KEYS = ['ProductUserVisibleVersion']


class MacOSXHostname(interface.MacXMLPlistPreprocess):
  """Fetches hostname information about a Mac OS X system."""

  ATTRIBUTE = 'hostname'
  PLIST_PATH = '/Library/Preferences/SystemConfiguration/preferences.plist'

  PLIST_KEYS = ['ComputerName', 'LocalHostName']


class MacOSXKeyboard(interface.MacPlistPreprocess):
  """Fetches keyboard information from a Mac OS X system."""

  ATTRIBUTE = 'keyboard_layout'
  PLIST_PATH = '/Library/Preferences/com.apple.HIToolbox.plist'

  PLIST_KEYS = ['AppleCurrentKeyboardLayoutInputSourceID']

  def ParseKey(self, key, key_name):
    """Determines the keyboard layout."""
    value = super(MacOSXKeyboard, self).ParseKey(key, key_name)
    _, _, keyboard_layout = value.rpartition('.')

    return keyboard_layout


class MacOSXTimeZone(interface.PreprocessPlugin):
  """Gather timezone information from a Mac OS X system."""

  ATTRIBUTE = 'time_zone_str'
  SUPPORTED_OS = ['MacOSX']

  WEIGHT = 1

  ZONE_FILE_PATH = u'/private/etc/localtime'

  def GetValue(self, searcher):
    """Determines the local time zone settings.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).

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

  def GetValue(self, searcher):
    """Determines the user accounts.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).

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
