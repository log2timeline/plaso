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
"""Interface and plugins for registry caching."""
import abc

from plaso.lib import errors
from plaso.lib import registry


class WinRegistryCache(object):
  """Stores calculated registry cache object.

  There are some values that are valid for the duration
  of an entire run against an image, such as code_page, etc.

  However there are other values that should only be valid for each
  registry file, such as a current_control_set. This registry cache
  object is designed to store those short lived cache values, so they
  can be calculated once for each registry file, yet do not live
  across all files parsed within an image.
  """

  def __init__(self, hive, reg_type):
    """Initialize the registry cache object.

    Args:
      hive: The WinRegistry object.
      reg_type: The registry type, eg. "SYSTEM", "NTUSER".
    """
    self._reg_type = reg_type
    self._hive = hive
    self.attributes = {}

  def BuildCache(self):
    """Builds up the cache."""
    for _, cl in WinRegCachePlugin.classes.items():
      try:
        plugin = cl(self._hive, self._reg_type)
        value = plugin.Process()
        if value:
          self.attributes[plugin.ATTRIBUTE] = value
      except errors.WrongPlugin:
        pass


class WinRegCachePlugin(object):
  """A registry cache plugin interface."""

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  # Define the needed attributes.
  ATTRIBUTE = ''

  REG_TYPE = ''
  REG_KEY = ''

  def __init__(self, hive, reg_type):
    """Initialize the plugin.

    Args:
      hive: The registry hive object (WinRegistry).
      reg_type: The detected registry type, should match this plugins type.
    """
    if self.REG_TYPE.lower() != reg_type.lower():
      raise errors.WrongPlugin(u'Not the correct registry type.')

    self._hive = hive

  def Process(self):
    """Extract the correct key and get the value."""
    if not self.REG_KEY:
      return

    key = self._hive.GetKey(self.REG_KEY)

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
    if not value:
      return

    return 'ControlSet%.3d' % value.GetData()

