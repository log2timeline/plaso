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
"""Parser for Windows NT Registry (REGF) files."""

import logging
import os

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import winreg_plugins  # pylint: disable=unused-import
from plaso.winreg import cache
from plaso.winreg import winregistry


class WinRegistryParser(interface.BaseParser):
  """Parses Windows NT Registry (REGF) files."""

  NAME = 'winreg'

  # List of types Windows Registry types and required keys to identify each of
  # these types.
  REG_TYPES = {
      'NTUSER': ('\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer',),
      'SOFTWARE': ('\\Microsoft\\Windows\\CurrentVersion\\App Paths',),
      'SECURITY': ('\\Policy\\PolAdtEv',),
      'SYSTEM': ('\\Select',),
      'SAM': ('\\SAM\\Domains\\Account\\Users',),
      'UNKNOWN': (),
  }

  def __init__(self):
    """Initializes a parser object."""
    super(WinRegistryParser, self).__init__()
    self._plugins = manager.ParsersManager.GetWindowsRegistryPlugins()

  def _RecurseKey(self, key):
    """A generator that takes a key and yields every subkey of it."""
    # In the case of a Registry file not having a root key we will not be able
    # to traverse the Registry, in which case we need to return here.
    if not key:
      return

    yield key

    for subkey in key.GetSubkeys():
      for recursed_key in self._RecurseKey(subkey):
        yield recursed_key

  def Parse(self, parser_context, file_entry):
    """Extract data from a Windows Registry file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
    """
    # TODO: Remove this magic reads when the classifier has been
    # implemented, until then we need to make sure we are dealing with
    # a Windows NT Registry file before proceeding.
    magic = 'regf'

    file_object = file_entry.GetFileObject()
    file_object.seek(0, os.SEEK_SET)
    data = file_object.read(len(magic))
    file_object.close()

    if data != magic:
      raise errors.UnableToParseFile((
          u'[{0:s}] unable to parse file: {1:s} with error: invalid '
          u'signature.').format(self.parser_name, file_entry.name))

    registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    # Determine type, find all parsers
    try:
      winreg_file = registry.OpenFile(
          file_entry, codepage=parser_context.codepage)
    except IOError as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.parser_name, file_entry.name, exception))

    # Detect the Windows Registry file type.
    registry_type = 'UNKNOWN'
    for reg_type in self.REG_TYPES:
      if reg_type == 'UNKNOWN':
        continue

      # Check if all the known keys for a certain Registry file exist.
      known_keys_found = True
      for known_key_path in self.REG_TYPES[reg_type]:
        if not winreg_file.GetKeyByPath(known_key_path):
          known_keys_found = False
          break

      if known_keys_found:
        registry_type = reg_type
        break

    self._registry_type = registry_type
    logging.debug(
        u'Windows Registry file {0:s}: detected as: {1:s}'.format(
            file_entry.name, registry_type))

    registry_cache = cache.WinRegistryCache()
    registry_cache.BuildCache(winreg_file, registry_type)

    plugins = {}
    number_of_plugins = 0
    for weight in self._plugins.GetWeights():
      plist = self._plugins.GetWeightPlugins(weight, registry_type)
      plugins[weight] = []
      for plugin in plist:
        plugins[weight].append(plugin(reg_cache=registry_cache))
        number_of_plugins += 1

    logging.debug(
        u'Number of plugins for this Windows Registry file: {0:d}.'.format(
            number_of_plugins))

    # Recurse through keys in the file and apply the plugins in the order:
    # 1. file type specific key-based plugins.
    # 2. generic key-based plugins.
    # 3. file type specific value-based plugins.
    # 4. generic value-based plugins.
    root_key = winreg_file.GetKeyByPath(u'\\')

    for key in self._RecurseKey(root_key):
      for weight in plugins.iterkeys():
        # TODO: determine if the plugin matches the key and continue
        # to the next key.
        for plugin in plugins[weight]:
          plugin.Process(
              parser_context, file_entry=file_entry, key=key,
              registry_type=self._registry_type,
              codepage=parser_context.codepage)

    winreg_file.Close()
