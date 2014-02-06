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

from plaso.lib import errors
from plaso.lib import preprocess_interface
from plaso.lib import utils
from plaso.parsers.plist_plugins import interface
from plaso.pvfs import pfile

from binplist import binplist


class OSXBuild(preprocess_interface.MacXMLPlistPreprocess):
  """Fetches build information about a Mac OS X system."""

  ATTRIBUTE = 'build'
  PLIST_PATH = '/System/Library/CoreServices/SystemVersion.plist'

  PLIST_KEYS = ['ProductUserVisibleVersion']


class OSXUsers(preprocess_interface.PreprocessPlugin):
  """Get information about user accounts on a Mac OS X system."""

  SUPPORTED_OS = ['MacOSX']
  ATTRIBUTE = 'users'
  WEIGHT = 1

  # Define the path to the user account information.
  USER_PATH = '/private/var/db/dslocal/nodes/Default/users/[^_].+.plist'

  def OpenPlistFile(self, filename):
    """Open a Plist file given a path and returns a plist top level object."""
    file_entry = self._collector.OpenFileEntry(filename)
    file_object = file_entry.Open()

    try:
      plist_file = binplist.BinaryPlist(file_object)
      top_level_object = plist_file.Parse()
    except binplist.FormatError as e:
      raise IOError(
          u'File is not a plist:{}'.format(utils.GetUnicodeString(e)))
    except OverflowError as e:
      raise IOError(
          u'Error processing:{} Error:{}'.format(file_entry.display_name, e))

    if not plist_file:
      raise IOError(
          u'File is not a plist:{}'.format(utils.GetUnicodeString(
              file_entry.display_name)))

    return top_level_object

  def GetValue(self):
    """Return the value for discovered user accounts, as a list of users."""
    users = []

    try:
      user_plists = self._collector.FindPaths(self.USER_PATH)
    except errors.PathNotFound:
      raise errors.PreProcessFail(u'Unable to find user files.')

    for plist in user_plists:
      try:
        top_level_object = self.OpenPlistFile(plist)
      except IOError:
        logging.warning(u'Unable to parse userfile: {}'.format(plist))
        continue

      try:
        match = interface.GetKeysDefaultEmpty(
            top_level_object, frozenset(['name', 'uid', 'home', 'realname']))
      except KeyError as exception:
        user, _, _ = plist.partition('.')
        logging.warning(u'Unable to read in data [{}] for user: {}'.format(
            exception, user))
        continue

      user = {
          'sid': match.get('uid', [-1])[0],
          'path': match.get('home', ['<not set>'])[0],
          'name': match.get('name', ['<not set>'])[0],
          'realname': match.get('realname', ['N/A'])[0]}
      users.append(user)

    if not users:
      raise errors.PreProcessFail(u'Unable to find any users on the system.')

    return users


class OSXHostname(preprocess_interface.MacXMLPlistPreprocess):
  """Fetches hostname information about a Mac OS X system."""

  ATTRIBUTE = 'hostname'
  PLIST_PATH = '/Library/Preferences/SystemConfiguration/preferences.plist'

  PLIST_KEYS = ['ComputerName', 'LocalHostName']


class OSXTimeZone(preprocess_interface.PreprocessPlugin):
  """Gather timezone information from a Mac OS X system."""

  ATTRIBUTE = 'time_zone_str'
  SUPPORTED_OS = ['MacOSX']

  WEIGHT = 1

  ZONE_FILE_PATH = u'/private/etc/localtime'

  def GetValue(self):
    """Extract and return the value of the time zone settings."""
    # TODO: This needs to be completely rewritten once dfVFS is
    # implemented.
    # Also this only works currently for the common case of symbolic
    # links in the /private/etc directory. Other cases exist that need
    # to be supported as well.
    try:
      _ = self._collector.FindPaths(self.ZONE_FILE_PATH)
    except errors.PathNotFound:
      raise errors.PreProcessFail(u'Zonefile does not exist.')

    # TODO: This only works against an image file, need to support
    # other use cases as well (again something fixed with dfVFS).
    if not self._collector.ReadingFromImage():
      raise errors.PreProcessFail(
          u'Currently only works against an image file.')

    # Try to open file.
    try:
      # We need to access the fs object directly, remove this
      # once dfVFS is completed.
      # pylint: disable-msg=protected-access
      root_path_spec = pfile.PFileResolver.CopyPathToPathSpec(
          u'TSK', u'/', self._collector._source_path,
          image_offset=self._collector._GetImageByteOffset())
      file_system = pfile.PFileResolver.OpenFileSystem(root_path_spec)
      zone_file = file_system.tsk_fs.open(
          self.ZONE_FILE_PATH)
    except (IOError, errors.UnableToOpenFilesystem):
      raise errors.PreProcessFail(u'Unable to open zone file.')

    zone_info = zone_file.info

    if not zone_info:
      raise errors.PreProcessFail(u'No info object for zone file.')

    meta = zone_info.meta

    if not meta:
      raise errors.PreProcessFail(u'No meta object for zone file.')

    if meta.nlink == 1:
      zone_text = meta.link
      _, _, zone = zone_text.partition('zoneinfo/')
      return zone

    raise errors.PreProcessFail(u'Value not found.')


class OSXKeyboard(preprocess_interface.MacPlistPreprocess):
  """Fetches keyboard information from a Mac OS X system."""

  ATTRIBUTE = 'keyboard_layout'
  PLIST_PATH = '/Library/Preferences/com.apple.HIToolbox.plist'

  PLIST_KEYS = ['AppleCurrentKeyboardLayoutInputSourceID']

  def ParseKey(self, key, key_name):
    """Return the key value."""
    value = super(OSXKeyboard, self).ParseKey(key, key_name)
    _, _, ret = value.rpartition('.')

    return ret
