#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""The Windows Registry plugin objects interface."""

import abc
import logging

from plaso.parsers import plugins
from plaso.winreg import path_expander as winreg_path_expander


class RegistryPlugin(plugins.BasePlugin):
  """Class that defines the Windows Registry plugin object interface."""

  __abstract = True

  NAME = 'winreg'

  # Indicate the type of hive this plugin belongs to (eg. NTUSER, SOFTWARE).
  REG_TYPE = 'any'

  # The URLS should contain a list of URL's with additional information about
  # this key or value.
  URLS = []

  # WEIGHT is a simple integer value representing the priority of this plugin.
  # The weight can be used by some parser implementation to prioritize the
  # order in which plugins are run against the Windows Registry keys.
  # By default no the Windows Registry plugin should overwrite this value,
  # it should only be defined in interfaces extending the base class, providing
  # higher level of prioritization to Windows Registry plugins.
  WEIGHT = 3

  def __init__(self, pre_obj=None, reg_cache=None):
    """Initializes Windows Registry plugin object.

    Args:
      pre_obj: Optional preprocessing object that contains information gathered
               during preprocessing of data. The default is None.
      reg_cache: Optional Windows Registry objects cache (instance of
                 WinRegistryCache). The default is None.
    """
    super(RegistryPlugin, self).__init__(pre_obj)
    self._pre_obj = pre_obj

    # TODO: Clean this up, this value is stored but not used.
    self._reg_cache = reg_cache

  @abc.abstractmethod
  def GetEntries(self, key=None, codepage='cp1252', **kwargs):
    """Extracts event objects from the Windows Registry key."""

  def Process(self, key=None, unused_codepage='cp1252', **kwargs):
    """Processes a Windows Registry key or value.

    Args:
      key: The Registry key (instance of winreg.WinRegKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.

    Raises:
      ValueError: If the key value is not set.
    """
    if key is None:
      raise ValueError(u'Key is not set.')

    super(RegistryPlugin, self).Process(**kwargs)


class KeyPlugin(RegistryPlugin):
  """Class that defines the Windows Registry key-based plugin interface."""

  __abstract = True

  # A list of all the Windows Registry key paths this plugins supports.
  # Each of these key paths can contain a path that needs to be expanded,
  # such as {current_control_set}, etc.
  REG_KEYS = []

  WEIGHT = 1

  def __init__(self, pre_obj=None, reg_cache=None):
    """Initializes key-based Windows Registry plugin object.

    Args:
      pre_obj: Optional preprocessing object that contains information gathered
               during preprocessing of data. The default is None.
      reg_cache: Optional Windows Registry objects cache (instance of
                 WinRegistryCache). The default is None.
    """
    super(KeyPlugin, self).__init__(pre_obj=pre_obj, reg_cache=reg_cache)
    self._path_expander = winreg_path_expander.WinRegistryKeyPathExpander(
        pre_obj, reg_cache)

    # Build a list of expanded keys this plugin supports.
    self.expanded_keys = []
    for registry_key in self.REG_KEYS:
      key_fixed = u''
      try:
        key_fixed = self._path_expander.ExpandPath(registry_key)
        self.expanded_keys.append(key_fixed)
      except KeyError as exception:
        logging.debug((
            u'Unable to use registry key {0:s} for plugin {1:s}, error '
            u'message: {1:s}').format(
                registry_key, self.plugin_name, exception))
        continue

      if not key_fixed:
        continue
      # Special case of Wow6432 Windows Registry redirection.
      # URL:  http://msdn.microsoft.com/en-us/library/windows/desktop/\
      # ms724072%28v=vs.85%29.aspx
      if key_fixed.startswith('\\Software'):
        _, first, second = key_fixed.partition('\\Software')
        self.expanded_keys.append(u'{0:s}\\Wow6432Node{1:s}'.format(
            first, second))
      if self.REG_TYPE == 'SOFTWARE' or self.REG_TYPE == 'any':
        self.expanded_keys.append(u'\\Wow6432Node{:s}'.format(key_fixed))

  @abc.abstractmethod
  def GetEntries(self, key=None, codepage='cp1252', **kwargs):
    """Extracts event objects from the Windows Registry key."""

  def Process(self, key=None, codepage='cp1252', **kwargs):
    """Processes a Windows Registry key.

    Args:
      key: The Registry key (instance of winreg.WinRegKey).
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    if not key:
      return

    super(KeyPlugin, self).Process(key=key, **kwargs)

    if key.path in self.expanded_keys:
      return self.GetEntries(key=key, codepage=codepage)


class ValuePlugin(RegistryPlugin):
  """Class that defines the Windows Registry value-based plugin interface."""

  __abstract = True

  # REG_VALUES should be defined as a frozenset.
  REG_VALUES = frozenset()

  WEIGHT = 2

  @abc.abstractmethod
  def GetEntries(self, key=None, codepage='cp1252', **kwargs):
    """Extracts event objects from the Windows Registry key."""

  def Process(self, key=None, codepage='cp1252', **kwargs):
    """Processes a Windows Registry value.

    Args:
      key: The Registry key (instance of winreg.WinRegKey) in which the value
           is stored.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    super(ValuePlugin, self).Process(key=key, **kwargs)

    values = frozenset([val.name for val in key.GetValues()])
    if self.REG_VALUES.issubset(values):
      return self.GetEntries(key=key, codepage=codepage)
