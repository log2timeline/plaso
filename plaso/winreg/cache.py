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
"""Interface and plugins for caching of Windows Registry objects."""

import abc

from plaso.lib import errors
from plaso.lib import registry


class WinRegistryCache(object):
  """Class that implements the Windows Registry objects cache.

     There are some values that are valid for the duration of an entire run
     against an image, such as code_page, etc.

     However there are other values that should only be valid for each
     Windows Registry file, such as a current_control_set. The Windows Registry
     objects cache is designed to store those short lived cache values, so they
     can be calculated once for each Windows Registry file, yet do not live
     across all files parsed within an image.
  """

  def __init__(self):
    """Initialize the cache object."""
    super(WinRegistryCache, self).__init__()
    self.attributes = {}

  def BuildCache(self, hive, reg_type):
    """Builds up the cache.

    Args:
      hive: The WinRegistry object.
      reg_type: The Registry type, eg. "SYSTEM", "NTUSER".
    """
    for _, cl in WinRegCachePlugin.classes.items():
      try:
        plugin = cl(reg_type)
        value = plugin.Process(hive)
        if value:
          self.attributes[plugin.ATTRIBUTE] = value
      except errors.WrongPlugin:
        pass


class WinRegCachePlugin(object):
  """Class that implement the Window Registry cache plugin interface."""

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  # Define the needed attributes.
  ATTRIBUTE = ''

  REG_TYPE = ''
  REG_KEY = ''

  def __init__(self, reg_type):
    """Initialize the plugin.

    Args:
      reg_type: The detected Windows Registry type. This value should match
                the REG_TYPE value defined by the plugins.
    """
    super(WinRegCachePlugin, self).__init__()
    if self.REG_TYPE.lower() != reg_type.lower():
      raise errors.WrongPlugin(u'Not the correct Windows Registry type.')

  def Process(self, hive):
    """Extract the correct key and get the value.

    Args:
      hive: The Windows Registry hive object (instance of WinRegistry).
    """
    if not self.REG_KEY:
      return

    key = hive.GetKeyByPath(self.REG_KEY)

    if not key:
      return

    return self.GetValue(key)

  @abc.abstractmethod
  def GetValue(self, key):
    """Extract the attribute from the provided key."""


class CurrentControl(WinRegCachePlugin):
  """Fetch information about the current control set."""

  ATTRIBUTE = 'current_control_set'

  REG_TYPE = 'SYSTEM'
  REG_KEY = '\\Select'

  def GetValue(self, key):
    """Extract current control set information."""
    value = key.GetValue('Current')

    if not value and not value.DataIsInteger():
      return None

    key_number = value.data

    # If the value is Zero then we need to check
    # other keys.
    # The default behavior is:
    #   1. Use the "Current" value.
    #   2. Use the "Default" value.
    #   3. Use the "LastKnownGood" value.
    if key_number == 0:
      default_value = key.GetValue('Default')
      lastgood_value = key.GetValue('LastKnownGood')

      if default_value and default_value.DataIsInteger():
        key_number = default_value.data

      if not key_number:
        if lastgood_value and lastgood_value.DataIsInteger():
          key_number = lastgood_value.data

    if key_number <= 0 or key_number > 999:
      return None

    return u'ControlSet{0:03d}'.format(key_number)
