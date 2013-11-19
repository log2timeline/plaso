#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from plaso.lib import plist_interface
from plaso.lib import preprocess
from plaso.lib import utils

from binplist import binplist


class OSXBuild(preprocess.MacXMLPlistPreprocess):
  """Fetches build information about a Mac OS X system."""

  ATTRIBUTE = 'build'
  PLIST_PATH = '/System/Library/CoreServices/SystemVersion.plist'

  PLIST_KEYS = ['ProductUserVisibleVersion']


class OSXUsers(preprocess.PreprocessPlugin):
  """Get information about user accounts on a Mac OS X system."""

  SUPPORTED_OS = ['MacOSX']
  ATTRIBUTE = 'users'
  WEIGHT = 1

  # Define the path to the user account information.
  USER_PATH = '/private/var/db/dslocal/nodes/Default/users/[^_].+.plist'

  def OpenPlistFile(self, filename):
    """Open a Plist file given a path and returns a plist top level object."""
    try:
      filehandle = self._collector.OpenFile(filename)
    except IOError as e:
      raise errors.PreProcessFail(
          u'Unable to open file:{} [{}]'.format(
              filename, utils.GetUnicodeString(e)))

    try:
      plist_file = binplist.BinaryPlist(filehandle)
      top_level_object = plist_file.Parse()
    except binplist.FormatError as e:
      raise errors.PreProcessFail(
          u'File is not a plist:{}'.format(utils.GetUnicodeString(e)))
    except OverflowError as e:
      raise errors.PreProcessFail(
          u'Error processing:{} Error:{}'.format(filehandle.display_name, e))

    if not plist_file:
      raise errors.PreProcessFail(
          u'File is not a plist:{}'.format(utils.GetUnicodeString(
              filehandle.display_name)))

    return top_level_object

  def GetValue(self):
    """Return the value for discovered user accounts, as a list of users."""
    users = []

    try:
      user_plists = self._collector.FindPaths(self.USER_PATH)
    except errors.PathNotFound:
      return users

    for plist in user_plists:
      top_level_object = self.OpenPlistFile(plist)

      try:
        match = plist_interface.GetKeysDefaultEmpty(
            top_level_object, frozenset(['name', 'uid', 'home', 'realname']))
      except KeyError as e:
        user, _, _ = plist.partition('.')
        logging.warning(u'Unable to read in data [{}] for user: {}'.format(
            e, user))
        continue

      user = {
          'sid': match.get('uid', [-1])[0],
          'path': match.get('home', ['<not set>'])[0],
          'name': match.get('name', ['<not set>'])[0],
          'realname': match.get('realname', ['N/A'])[0]}
      users.append(user)

    return users


class OSXHostname(preprocess.MacXMLPlistPreprocess):
  """Fetches hostname information about a Mac OS X system."""

  ATTRIBUTE = 'hostname'
  PLIST_PATH = '/Library/Preferences/SystemConfiguration/preferences.plist'

  PLIST_KEYS = ['ComputerName', 'LocalHostName']


class OSXTimeZone(preprocess.PreprocessPlugin):
  """Gather timezone information from a Mac OS X system."""

  ATTRIBUTE = 'time_zone_str'
  SUPPORTED_OS = ['MacOSX']

  WEIGHT = 1

  ZONE_FILE_PATH = u'/private/etc/localtime'

  def GetValue(self):
    """Extract and return the value of the time zone settings."""
    # TODO: This needs to be completely rewritten once PyVFS is
    # implemented.
    # Also this only works currently for the common case of symbolic
    # links in the /private/etc directory. Other cases exist that need
    # to be supported as well.
    try:
      _ = self._collector.FindPaths(self.ZONE_FILE_PATH)
    except errors.PathNotFound:
      raise errors.PreProcessFail(u'Zonefile does not exist.')

    # TODO: This only works against an image file, need to support
    # other use cases as well (again something fixed with PyVFS).
    if not isinstance(
        self._collector, preprocess.TSKFileCollector):
      raise errors.PreProcessFail(
          u'Currently only works against an image file.')

    # Try to open file.
    try:
      # We need to access the fs object directly, remove this
      # once PyVFS is completed.
      # pylint: disable-msg=protected-access
      zone_file = self._collector._fs_obj.fs.open(
          self.ZONE_FILE_PATH)
    except IOError:
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


class OSXKeyboard(preprocess.MacPlistPreprocess):
  """Fetches keyboard information from a Mac OS X system."""

  ATTRIBUTE = 'keyboard_layout'
  PLIST_PATH = '/Library/Preferences/com.apple.HIToolbox.plist'

  PLIST_KEYS = ['AppleCurrentKeyboardLayoutInputSourceID']

  def ParseKey(self, key, key_name):
    """Return the key value."""
    value = super(OSXKeyboard, self).ParseKey(key, key_name)
    _, _, ret = value.rpartition('.')

    return ret
