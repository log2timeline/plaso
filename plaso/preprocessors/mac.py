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
from plaso.lib import errors
from plaso.lib import preprocess


class OSXBuild(preprocess.MacXMLPlistPreprocess):
  """Fetches build information about a Mac OS X system."""

  ATTRIBUTE = 'build'
  PLIST_PATH = '/System/Library/CoreServices/SystemVersion.plist'

  PLIST_KEY = 'ProductUserVisibleVersion'


class OSXHostname(preprocess.MacXMLPlistPreprocess):
  """Fetches hostname information about a Mac OS X system."""

  ATTRIBUTE = 'hostname'
  PLIST_PATH = '/Library/Preferences/SystemConfiguration/preferences.plist'

  PLIST_KEY = 'ComputerName'


class OSXKeyboard(preprocess.MacPlistPreprocess):
  """Fetches keyboard information from a Mac OS X system."""

  ATTRIBUTE = 'keyboard_layout'
  PLIST_PATH = '/Library/Preferences/com.apple.HIToolbox.plist'

  PLIST_KEY = 'AppleCurrentKeyboardLayoutInputSourceID'

  def ParseKey(self, key):
    """Return the key value."""
    value = super(OSXKeyboard, self).ParseKey(key)
    _, _, ret = value.rpartition('.')

    return ret
