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

  def __init__(self, reg_cache=None):
    """Initializes Windows Registry plugin object.

    Args:
      reg_cache: Optional Windows Registry objects cache (instance of
                 WinRegistryCache). The default is None.
    """
    super(RegistryPlugin, self).__init__()
    # TODO: Clean this up, this value is stored but not used.
    self._reg_cache = reg_cache

  @abc.abstractmethod
  def GetEntries(
      self, parser_context, file_entry=None, key=None, registry_type=None,
      codepage='cp1252', **kwargs):
    """Extracts event objects from the Windows Registry key.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """

  def Process(self, parser_context, key=None, **kwargs):
    """Processes a Windows Registry key or value.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.

    Raises:
      ValueError: If the key value is not set.
    """
    if key is None:
      raise ValueError(u'Key is not set.')

    del kwargs['file_entry']
    del kwargs['registry_type']
    del kwargs['codepage']

    # This will raise if unhandled keyword arguments are passed.
    super(RegistryPlugin, self).Process(parser_context, **kwargs)


class KeyPlugin(RegistryPlugin):
  """Class that defines the Windows Registry key-based plugin interface."""

  __abstract = True

  # A list of all the Windows Registry key paths this plugins supports.
  # Each of these key paths can contain a path that needs to be expanded,
  # such as {current_control_set}, etc.
  REG_KEYS = []

  WEIGHT = 1

  def __init__(self, reg_cache=None):
    """Initializes key-based Windows Registry plugin object.

    Args:
      reg_cache: Optional Windows Registry objects cache (instance of
                 WinRegistryCache). The default is None.
    """
    super(KeyPlugin, self).__init__(reg_cache=reg_cache)
    self._path_expander = winreg_path_expander.WinRegistryKeyPathExpander(
        reg_cache=reg_cache)
    self.expanded_keys = None

  def ExpandKeys(self, parser_context):
    """Builds a list of expanded keys this plugin supports.

    Args:
      parser_context: A parser context object (instance of ParserContext).
    """
    self.expanded_keys = []
    for registry_key in self.REG_KEYS:
      expanded_key = u''
      try:
        # TODO: deprecate direct use of pre_obj.
        expanded_key = self._path_expander.ExpandPath(
            registry_key, pre_obj=parser_context.knowledge_base.pre_obj)
      except KeyError as exception:
        logging.debug((
            u'Unable to expand Registry key {0:s} for plugin {1:s} with '
            u'error: {1:s}').format(registry_key, self.plugin_name, exception))
        continue

      if not expanded_key:
        continue

      self.expanded_keys.append(expanded_key)

      # Special case of Wow6432 Windows Registry redirection.
      # URL: http://msdn.microsoft.com/en-us/library/windows/desktop/\
      # ms724072%28v=vs.85%29.aspx
      if expanded_key.startswith('\\Software'):
        _, first, second = expanded_key.partition('\\Software')
        self.expanded_keys.append(u'{0:s}\\Wow6432Node{1:s}'.format(
            first, second))

      if self.REG_TYPE == 'SOFTWARE' or self.REG_TYPE == 'any':
        self.expanded_keys.append(u'\\Wow6432Node{0:s}'.format(expanded_key))

  @abc.abstractmethod
  def GetEntries(
      self, parser_context, file_entry=None, key=None, registry_type=None,
      codepage='cp1252', **kwargs):
    """Extracts event objects from the Windows Registry key.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """

  def Process(
      self, parser_context, file_entry=None, key=None, registry_type=None,
      codepage='cp1252', **kwargs):
    """Processes a Windows Registry key.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    if self.expanded_keys is None:
      self.ExpandKeys(parser_context)

    super(KeyPlugin, self).Process(
        parser_context, file_entry=file_entry, key=key,
        registry_type=registry_type, codepage=codepage, **kwargs)

    if key and key.path in self.expanded_keys:
      self.GetEntries(
          parser_context, file_entry=file_entry, key=key,
          registry_type=registry_type, codepage=codepage, **kwargs)


class ValuePlugin(RegistryPlugin):
  """Class that defines the Windows Registry value-based plugin interface."""

  __abstract = True

  # REG_VALUES should be defined as a frozenset.
  REG_VALUES = frozenset()

  WEIGHT = 2

  @abc.abstractmethod
  def GetEntries(
      self, parser_context, file_entry=None, key=None, registry_type=None,
      codepage='cp1252', **kwargs):
    """Extracts event objects from the Windows Registry key.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """

  def Process(
      self, parser_context, file_entry=None, key=None, registry_type=None,
      codepage='cp1252', **kwargs):
    """Processes a Windows Registry value.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      key: Optional Registry key (instance of winreg.WinRegKey).
           The default is None.
      registry_type: Optional Registry type string. The default is None.
      codepage: Optional extended ASCII string codepage. The default is cp1252.
    """
    super(ValuePlugin, self).Process(
        parser_context, file_entry=file_entry, key=key,
        registry_type=registry_type, codepage=codepage, **kwargs)

    values = frozenset([val.name for val in key.GetValues()])
    if self.REG_VALUES.issubset(values):
      self.GetEntries(
          parser_context, file_entry=file_entry, key=key,
          registry_type=registry_type, codepage=codepage, **kwargs)
