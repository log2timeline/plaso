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
"""Parse your Windows Registry files using preg.

preg is a simple Windows Registry parser using the plaso Registry plugins and
image parsing capabilities. It uses the back-end libraries of plaso to read
raw image files and extract Registry files from VSS and restore points and then
runs the Registry plugins of plaso against the Registry hive and presents it
in a textual format.
"""

import argparse
import binascii
import logging
import os
import re
import sys
import textwrap

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

try:
  # Support version 1.X of IPython.
  # pylint: disable=no-name-in-module
  from IPython.terminal.embed import InteractiveShellEmbed
except ImportError:
  # pylint: disable=no-name-in-module
  from IPython.frontend.terminal.embed import InteractiveShellEmbed

from IPython.core import magic

from plaso import preprocessors

# Import the winreg formatter to register it, adding the option
# to print event objects using the default formatter.
# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter

from plaso.frontend import frontend
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import winreg_plugins    # pylint: disable=unused-import
from plaso.parsers.winreg_plugins import interface as winreg_interface
from plaso.preprocessors import interface as preprocess_interface
from plaso.winreg import cache
from plaso.winreg import path_expander as winreg_path_expander
from plaso.winreg import winregistry


class RegCache(object):
  """Cache for current hive and Registry key."""

  # Attributes that are cached.
  cur_key = ''
  hive = None
  hive_type = 'UNKNOWN'
  pre_obj = None
  path_expander = None
  reg_cache = None
  file_entry = None
  events_from_last_parse = []

  REG_TYPES = {
      'NTUSER': ('\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer',),
      'SOFTWARE': ('\\Microsoft\\Windows\\CurrentVersion\\App Paths',),
      'SECURITY': ('\\Policy\\PolAdtEv',),
      'SYSTEM': ('\\Select',),
      'SAM': ('\\SAM\\Domains\\Account\\Users',),
      'UNKNOWN': (),
  }

  @classmethod
  def SetHiveType(cls):
    """Guess the type of the current hive in the cache."""
    # Detect Registry type.
    registry_type = 'UNKNOWN'
    for reg_type in cls.REG_TYPES:
      if reg_type == 'UNKNOWN':
        continue
      found = True
      for reg_key in cls.REG_TYPES[reg_type]:
        if not RegCache.hive.GetKeyByPath(reg_key):
          found = False
          break
      if found:
        registry_type = reg_type
        break

    cls.hive_type = registry_type

  @classmethod
  def BuildCache(cls):
    """Build the Registry cache."""
    # Calculate the Registry cache.
    cls.reg_cache = cache.WinRegistryCache()
    cls.reg_cache.BuildCache(cls.hive, cls.hive_type)
    cls.path_expander = winreg_path_expander.WinRegistryKeyPathExpander(
        cls.pre_obj, cls.reg_cache)

  @classmethod
  def GetHiveName(cls):
    """Return the name of the Registry hive file."""
    if not hasattr(cls, 'hive'):
      return 'N/A'

    return getattr(cls.hive, 'name', 'N/A')


class PregFrontend(frontend.ExtractionFrontend):
  """Class that implements the preg front-end."""

  def __init__(self, output_writer):
    """Initializes the front-end object."""
    input_reader = frontend.StdinFrontendInputReader()

    super(PregFrontend, self).__init__(input_reader, output_writer)

  def ParseOptions(self, options, unused_source):
    """Parses the options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the option are invalid.
    """
    if not options:
      raise errors.BadConfigOption(u'Missing options.')

    if not options.image and not options.regfile:
      raise errors.BadConfigOption(u'Not enough parameters to proceed.')

    if options.image:
      return

    # TODO: move this?
    if options.regfile and not os.path.isfile(options.regfile):
      raise errors.BadConfigOption(
          u'Registry file: {0:s} does not exist.'.format(options.regfile))

  # TODO: clean up this function as part of dfvfs find integration.
  # TODO: a duplicate of this function exists in class: WinRegistryPreprocess
  # method: GetValue; merge them.
  def _FindRegistryPaths(self, searcher, pattern):
    """Return a list of Windows Registry file paths.

    Args:
      searcher: The file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      pattern: The pattern to find.
    """
    # TODO: optimize this in one find.
    hive_paths = []
    file_path, _, file_name = pattern.rpartition(u'/')

    # The path is split in segments to make it path segement separator
    # independent (and thus platform independent).
    path_segments = file_path.split(u'/')
    if not path_segments[0]:
      path_segments = path_segments[1:]

    find_spec = file_system_searcher.FindSpec(
        location_regex=path_segments, case_sensitive=False)
    path_specs = list(searcher.Find(find_specs=[find_spec]))

    if not path_specs:
      logging.debug(u'Directory: {0:s} not found'.format(file_path))
      return hive_paths

    for path_spec in path_specs:
      directory_location = getattr(path_spec, 'location', None)
      if not directory_location:
        raise errors.PreProcessFail(
            u'Missing directory location for: {0:s}'.format(file_path))

      # The path is split in segments to make it path segement separator
      # independent (and thus platform independent).
      path_segments = searcher.SplitPath(directory_location)
      path_segments.append(file_name)

      find_spec = file_system_searcher.FindSpec(
          location_regex=path_segments, case_sensitive=False)
      fh_path_specs = list(searcher.Find(find_specs=[find_spec]))

      if not fh_path_specs:
        logging.debug(u'File: {0:s} not found in directory: {1:s}'.format(
            file_name, directory_location))
        continue

      hive_paths.extend(fh_path_specs)

    return hive_paths

  def _GetSearchersForImage(self, volume_path_spec, options):
    """Retrieves the file systems searchers for searching the image.

    Args:
      volume_path_spec: The path specification of the volume containing
                        the file system (instance of dfvfs.PathSpec).
      options: the command line arguments (instance of argparse.Namespace).

    Returns:
      A list of tuples containing the a string identifying the file system
      searcher and a file system searcher object (instance of
      dfvfs.FileSystemSearcher).
    """
    searchers = []

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
    searcher = file_system_searcher.FileSystemSearcher(
        file_system, volume_path_spec)

    searchers.append((u'', searcher))

    # TODO: Remove this option parsing and rely on self._vss_stores instead.
    vss_stores = getattr(options, 'vss_stores', [])
    if vss_stores is None:
      vss_stores = []

    if not vss_stores and self._vss_stores:
      vss_stores = self._vss_stores

    for store_index in vss_stores:
      vss_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW, store_index=store_index - 1,
          parent=volume_path_spec)
      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
          parent=vss_path_spec)

      file_system = path_spec_resolver.Resolver.OpenFileSystem(path_spec)
      searcher = file_system_searcher.FileSystemSearcher(
          file_system, vss_path_spec)

      searchers.append((
          u':VSS Store {0:d}'.format(store_index + 1), searcher))

    return searchers

  def ExpandKeysRedirect(self, keys):
    """Expand a key list with Registry redirect keys."""
    for key in keys:
      if key.startswith('\\Software') and 'Wow6432Node' not in key:
        _, first, second = key.partition('\\Software')
        keys.append(u'{0:s}\\Wow6432Node{1:s}'.format(first, second))

  def GetHivesAndCollectors(self, options):
    """Returns a list of discovered Registry hives and collectors.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    # TODO: use non-preprocess collector with filter to collect hives.

    # TODO: rewrite to always use collector or equiv.
    if options.image:
      # TODO: move to ParseOptions?
      try:
        self._source_path = getattr(options, 'image', '')
        self.ScanSource(options)
      except errors.FileSystemScannerError as exception:
        raise errors.BadConfigOption((
            u'Unable to scan for a supported filesystem with error: {0:s}.\n'
            u'Most likely the image format is not supported by the '
            u'tool.').format(exception))

      searchers = self._GetSearchersForImage(
          self._source_path_spec.parent, options)
      _, searcher = searchers[0]

      # Run preprocessing on image.
      RegCache.pre_obj = event.PreprocessObject()

      pre_plugin_list = preprocessors.PreProcessList(RegCache.pre_obj)
      guessed_os = preprocess_interface.GuessOS(searcher)
      for weight in pre_plugin_list.GetWeightList(guessed_os):
        for plugin in pre_plugin_list.GetWeight(guessed_os, weight):
          try:
            plugin.Run(searcher)
          except (IOError, errors.PreProcessFail) as exception:
            logging.warning(
                u'Unable to run plugin: {0:s} with error: {1:s}'.format(
                    plugin.plugin_name, exception))

      # Find all the Registry paths we need to check.
      if options.regfile:
        paths = self.GetRegistryFilePaths(options, options.regfile.upper())
      else:
        paths = self.GetRegistryFilePaths(options)

      hives = []
      for path in paths:
        hives.extend(self._FindRegistryPaths(searcher, path))
    else:
      hives = [options.regfile]
      searchers = [(u'', None)]

    return hives, searchers

  def GetRegistryFilePaths(self, options, registry_type=None):
    """Returns a list of Registry paths from a configuration object.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      registry_type: optional Registry type string. None by default.
    """
    if options.restore_points:
      restore_path = u'/System Volume Information/_restor.+/RP[0-9]+/snapshot/'
    else:
      restore_path = u''

    if registry_type:
      types = [registry_type]
    else:
      types = self.GetRegistryTypes(options)

    # Gather the Registry files to fetch.
    paths = []

    for reg_type in types:
      if reg_type == 'NTUSER':
        paths.append('/Documents And Settings/.+/NTUSER.DAT')
        paths.append('/Users/.+/NTUSER.DAT')
        if restore_path:
          paths.append('{0:s}/_REGISTRY_USER_NTUSER.+'.format(restore_path))

      elif reg_type == 'SOFTWARE':
        paths.append('{sysregistry}/SOFTWARE')
        if restore_path:
          paths.append('{0:s}/_REGISTRY_MACHINE_SOFTWARE'.format(restore_path))

      elif reg_type == 'SYSTEM':
        paths.append('{sysregistry}/SYSTEM')
        if restore_path:
          paths.append('{0:s}/_REGISTRY_MACHINE_SYSTEM'.format(restore_path))

      elif reg_type == 'SECURITY':
        paths.append('{sysregistry}/SECURITY')
        if restore_path:
          paths.append('{0:s}/_REGISTRY_MACHINE_SECURITY'.format(restore_path))

      elif reg_type == 'SAM':
        paths.append('{sysregistry}/SAM')
        if restore_path:
          paths.append('{0:s}/_REGISTRY_MACHINE_SAM'.format(restore_path))

    # Expand all the paths.
    expander = winreg_path_expander.WinRegistryKeyPathExpander(
        RegCache.pre_obj, None)
    try:
      paths = map(expander.ExpandPath, paths)
    except KeyError as exception:
      logging.error(u'Unable to expand all keys, with error: {0:s}'.format(
          exception))

    return paths

  def GetRegistryKeysFromType(self, options, registry_type):
    """Return a list of all key plugins for a given Registry type.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      registry_type: the Registry type string.
    """
    keys = []
    for reg_plugin in options.plugins.GetAllKeyPlugins():
      temp_obj = reg_plugin(
          pre_obj=RegCache.pre_obj, reg_cache=RegCache.reg_cache)
      if temp_obj.REG_TYPE == registry_type:
        keys.extend(temp_obj.expanded_keys)

    return keys

  def GetRegistryTypes(self, options):
    """Return back a list of all available Registry types.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    types = []
    for plugin in GetRegistryPlugins(options):
      for reg_plugin in options.plugins.GetAllKeyPlugins():
        temp_obj = reg_plugin(None, None)
        if plugin is temp_obj.plugin_name:
          if temp_obj.REG_TYPE not in types:
            types.append(temp_obj.REG_TYPE)
          break

    return types

  def RunModeRegistryKey(self, options):
    """Run against a specific Registry key.

    Finds and opens all Registry hives as configured in the configuration
    object and tries to open the Registry key that is stored in the
    configuration object for every detected hive file and parses it using
    all available plugins.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    hives, hive_collectors = self.GetHivesAndCollectors(options)

    # Get the Registry key.
    keys = [options.key]

    # Expand the keys if there is a need (due to Windows redirect).
    self.ExpandKeysRedirect(keys)

    for hive in hives:
      self._output_writer.Write(ParseHive(
          hive, hive_collectors, keys, None, options.verbose))

  def RunModeRegistryPlugin(self, options):
    """Run against a set of Registry plugins.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    hives, hive_collectors = self.GetHivesAndCollectors(options)

    if not hives:
      return

    plugin_list = GetRegistryPlugins(options)

    # In order to get all the Registry keys we need to expand
    # them, but to do so we need to open up one hive so that we
    # create the reg_cache object, which is necessary to fully
    # expand all keys.
    _, hive_collector = hive_collectors[0]
    OpenHive(hives[0], hive_collector)

    # Get all the appropriate keys from these plugins.
    key_plugins_all = options.plugins.GetAllKeyPlugins()
    key_plugins = []
    for key_plugin in key_plugins_all:
      temp_obj = key_plugin(
          pre_obj=RegCache.pre_obj, reg_cache=RegCache.reg_cache)
      if temp_obj.plugin_name in plugin_list:
        key_plugins.append(temp_obj)

    registry_keys = []
    for key_plugin in key_plugins:
      for registry_key in key_plugin.expanded_keys:
        if registry_key not in registry_keys:
          registry_keys.append(registry_key)

    for hive in hives:
      self._output_writer.Write(ParseHive(
          hive, hive_collectors, registry_keys, plugin_list, options.verbose))

  def RunModeRegistryFile(self, options):
    """Run against a Registry file.

    Finds and opens all Registry hives as configured in the configuration
    object and determines the type of Registry file opened. Then it will
    load up all the Registry plugins suitable for that particular registry
    file, find all Registry keys they are able to parse and run through
    them, one by one.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
    """
    # Get all the hives and collectors.
    hives, hive_collectors = self.GetHivesAndCollectors(options)

    for hive in hives:
      for _, hive_collector in hive_collectors:
        OpenHive(hive, hive_collector)
        options.plugin_name = RegCache.hive_type
        keys = self.GetRegistryKeysFromType(options, options.plugin_name)
        self.ExpandKeysRedirect(keys)
        plugins_to_run = GetRegistryPlugins(options)
        self._output_writer.Write(ParseHive(
            hive, hive_collectors, keys, plugins_to_run, options.verbose))


def CdCompleter(unused_self, unused_event):
  """Completer function for the cd command, returning back sub keys."""
  return_list = []
  for key in RegCache.cur_key.GetSubkeys():
    return_list.append(key.name)

  return return_list


def PluginCompleter(unused_self, event_object):
  """Completer function that returns a list of available plugins."""
  ret_list = []

  if not IsLoaded():
    return ret_list

  if not '-h' in event_object.line:
    ret_list.append('-h')

  plugin_obj = winreg_interface.GetRegistryPlugins()

  for plugin_cls in plugin_obj.GetKeyPlugins(RegCache.hive_type):
    plugin_obj = plugin_cls(
        pre_obj=RegCache.pre_obj, reg_cache=RegCache.reg_cache)

    plugin_name = plugin_obj.plugin_name
    if plugin_name.startswith('winreg'):
      plugin_name = plugin_name[7:]

    if plugin_name == 'default':
      continue
    ret_list.append(plugin_name)

  return ret_list


def VerboseCompleter(unused_self, event_object):
  """Completer function that suggests simple verbose settings."""
  if '-v' in event_object.line:
    return []
  else:
    return ['-v']


@magic.magics_class
class MyMagics(magic.Magics):
  """A simple class holding all magic functions for console."""

  EXPANSION_KEY_OPEN = r'{'
  EXPANSION_KEY_CLOSE = r'}'

  # Match against one instance, not two of the expansion key.
  EXPANSION_RE = re.compile(r'{0:s}{{1}}[^{1:s}]+?{1:s}'.format(
      EXPANSION_KEY_OPEN, EXPANSION_KEY_CLOSE))

  output_writer = sys.stdout

  @magic.line_magic
  def redirect_output(self, output_object):
    """Change the output writer to redirect plugin output to a file."""

    if isinstance(output_object, basestring):
      output_object = open(output_object, 'wb')

    if hasattr(output_object, 'write'):
      self.output_writer = output_object

  # Lowercase name since this is used inside the python console shell.
  @magic.line_magic
  def plugin(self, line):
    """Parse a Registry key using a specific plugin."""
    if not IsLoaded():
      print u'No hive loaded, unable to parse.'
      return

    if not line:
      print u'No plugin name added.'
      return

    plugin_name = line
    if '-h' in line:
      items = line.split()
      if len(items) != 2:
        print u'Wrong usage: plugin [-h] PluginName'
        return
      if items[0] == '-h':
        plugin_name = items[1]
      else:
        plugin_name = items[0]

    if not plugin_name.startswith('winreg'):
      plugin_name = u'winreg_{0:s}'.format(plugin_name)

    plugin_obj = winreg_interface.GetRegistryPlugins()
    plugin_found = False
    for plugin_cls in plugin_obj.GetKeyPlugins(RegCache.hive_type):
      plugin = plugin_cls(
          pre_obj=RegCache.pre_obj, reg_cache=RegCache.reg_cache)
      if plugin.plugin_name == plugin_name:
        # If we found the correct plugin.
        plugin_found = True
        break

    if not plugin_found:
      print u'No plugin named: {0:s} available for Registry type {1:s}'.format(
          plugin_name, RegCache.hive_type)
      return

    if not hasattr(plugin, 'REG_KEYS'):
      print u'Plugin: {0:s} has no key information.'.format(line)
      return

    if '-h' in line:
      print frontend_utils.FormatHeader(plugin_name)
      print frontend_utils.FormatOutputString('Description', plugin.__doc__)
      print u''
      for registry_key in plugin.expanded_keys:
        print frontend_utils.FormatOutputString('Registry Key', registry_key)
      return

    for registry_key in plugin.expanded_keys:
      key = RegCache.hive.GetKeyByPath(registry_key)
      if not key:
        print u'Key: {0:s} not found'.format(registry_key)
        continue

      # Move the current location to the key to be parsed.
      self.cd(registry_key)
      # Parse the key.
      print_strings = ParseKey(
          RegCache.cur_key, verbose=False, use_plugins=[plugin_name])
      self.output_writer.write(u'\n'.join(print_strings))
    self.output_writer.flush()

  # Lowercase name since this is used inside the python console shell.
  @magic.line_magic
  def parse(self, line):
    """Parse the current key."""
    if 'true' in line.lower():
      verbose = True
    elif '-v' in line.lower():
      verbose = True
    else:
      verbose = False

    if not IsLoaded():
      return

    print_strings = ParseKey(RegCache.cur_key, verbose=verbose)
    self.output_writer.write(u'\n'.join(print_strings))

    # Print out a hex dump of all binary values.
    if verbose:
      header_shown = False
      for value in RegCache.cur_key.GetValues():
        if value.DataIsBinaryData():
          if not header_shown:
            header_shown = True
            print frontend_utils.FormatHeader('Hex Dump')
          # Print '-' 80 times.
          self.output_writer.write(u'-'*80)
          self.output_writer.write(u'\n')
          self.output_writer.write(
              frontend_utils.FormatOutputString('Attribute', value.name))
          self.output_writer.write(u'-'*80)
          self.output_writer.write(u'\n')
          self.output_writer.write(
              frontend_utils.OutputWriter.GetHexDump(value.data))
          self.output_writer.write(u'\n')
          self.output_writer.write(u'+-'*40)
          self.output_writer.write(u'\n')

    self.output_writer.flush()

  # Lowercase name since this is used inside the python console shell.
  @magic.line_magic
  def cd(self, key):
    """Change between Registry keys, like a directory tree.

    The key path can either be an absolute path or a relative one.
    Absolute paths can use '.' and '..' to denote current and parent
    directory/key path.

    Args:
      key: The path to the key to traverse to.
    """
    registry_key = None
    key_path = key

    if not key:
      self.cd('\\')

    # Check if we need to expand environment attributes.
    match = self.EXPANSION_RE.search(key)
    if match and u'{0:s}{0:s}'.format(
        self.EXPANSION_KEY_OPEN) not in match.group(0):
      try:
        key = RegCache.path_expander.ExpandPath(key)
      except (KeyError, IndexError):
        pass

    if key.startswith('\\'):
      registry_key = RegCache.hive.GetKeyByPath(key)
    elif key == '.':
      return
    elif key.startswith('.\\'):
      current_path = RegCache.hive.cur_key.path
      _, _, key_path = key.partition('\\')
      registry_key = RegCache.hive.GetKeyByPath(u'{0:s}\\{1:s}'.format(
          current_path, key_path))
    elif key.startswith('..'):
      parent_path, _, _ = RegCache.cur_key.path.rpartition('\\')
      _, _, key_path = key.partition('\\')
      if parent_path:
        if key_path:
          path = u'{0:s}\\{1:s}'.format(parent_path, key_path)
        else:
          path = parent_path
        registry_key = RegCache.hive.GetKeyByPath(path)
      else:
        registry_key = RegCache.hive.GetKeyByPath(u'\\{0:s}'.format(key_path))

    else:
      # Check if key is not set at all, then assume traversal from root.
      if not RegCache.cur_key:
        RegCache.cur_key = RegCache.hive.GetKeyByPath('\\')

      if RegCache.cur_key.name == RegCache.hive.GetKeyByPath('\\').name:
        key_path = u'\\{0:s}'.format(key)
      else:
        key_path = u'{0:s}\\{1:s}'.format(RegCache.cur_key.path, key)
      registry_key = RegCache.hive.GetKeyByPath(key_path)

    if registry_key:
      if key_path == '\\':
        path = '\\'
      else:
        path = registry_key.path

      # Set the Registry key and the prompt.
      RegCache.cur_key = registry_key
      ip = get_ipython()    # pylint: disable=undefined-variable
      ip.prompt_manager.in_template = u'{0:s}->{1:s} [\\#] '.format(
          StripCurlyBrace(RegCache.GetHiveName()),
          StripCurlyBrace(path).replace('\\', '\\\\'))
    else:
      print u'Unable to change to: {0:s}'.format(key_path)

  # Lowercase name since this is used inside the python console shell.
  @magic.line_magic
  def pwd(self, unused_line):
    """Print the current path."""
    if not IsLoaded():
      return

    print RegCache.cur_key.path

  # Lowercase name since this is used inside the python console shell.
  @magic.line_magic
  def ls(self, line):
    """List all subkeys and values of the current key."""
    if not IsLoaded():
      return

    if 'true' in line.lower():
      verbose = True
    elif '-v' in line.lower():
      verbose = True
    else:
      verbose = False


    sub = []
    for key in RegCache.cur_key.GetSubkeys():
      # TODO: move this construction into a separate function in OutputWriter.
      timestamp, _, _ = frontend_utils.OutputWriter.GetDateTimeString(
          key.last_written_timestamp).partition('.')

      sub.append((u'{0:>19s} {1:>15s}  {2:s}'.format(
          timestamp.replace('T', ' '), '[KEY]',
          key.name), True))

    for value in RegCache.cur_key.GetValues():
      if not verbose:
        sub.append((u'{0:>19s} {1:>14s}]  {2:s}'.format(
            u'', '[' + value.data_type_string, value.name), False))
      else:
        if value.DataIsString():
          value_string = u'{0:s}'.format(value.data)
        elif value.DataIsInteger():
          value_string = u'{0:d}'.format(value.data)
        elif value.DataIsMultiString():
          value_string = u'{0:s}'.format(u''.join(value.data))
        elif value.DataIsBinaryData():
          hex_string = binascii.hexlify(value.data)
          # We'll just print the first few bytes, but we need to pad them
          # to make it fit in a single line if shorter.
          if len(hex_string) % 32:
            breakpoint = len(hex_string) / 32
            leftovers = hex_string[breakpoint:]
            pad = ' ' * (32 - len(leftovers))
            hex_string += pad

          value_string = frontend_utils.OutputWriter.GetHexDumpLine(
              hex_string, 0)
        else:
          value_string = u''

        sub.append((
            u'{0:>19s} {1:>14s}]  {2:<25s}  {3:s}'.format(
                u'', '[' + value.data_type_string, value.name, value_string),
            False))

    for entry, subkey in sorted(sub):
      if subkey:
        print u'dr-xr-xr-x {0:s}'.format(entry)
      else:
        print u'-r-xr-xr-x {0:s}'.format(entry)


def StripCurlyBrace(string):
  """Return a format "safe" string."""
  return string.replace('}', '}}').replace('{', '{{')


def IsLoaded():
  """Checks if a Windows Registry Hive is loaded."""
  if hasattr(RegCache.cur_key, 'path'):
    return True

  if RegCache.GetHiveName() != 'N/A':
    return True

  print u'No hive loaded, cannot complete action. Use OpenHive to load a hive.'
  return False


# TODO: Refactor this function or add another helper that makes opening up other
# hives simpler (and to find other hives within the image, eg I open SYSTEM and
# then I realize I need SOFTWARE, etc). Also to allow opening NTUSER based on
# usernames.
def OpenHive(filename_or_path_spec, hive_collector, codepage='cp1252'):
  """Open a Registry hive based on a collector or a filename."""
  if isinstance(filename_or_path_spec, basestring):
    filename = filename_or_path_spec
    path_spec = None
  else:
    filename = filename_or_path_spec.location
    path_spec = filename_or_path_spec

  if not hive_collector:
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=filename)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
  else:
    file_entry = hive_collector.GetFileEntryByPathSpec(path_spec)

  use_codepage = getattr(RegCache.pre_obj, 'code_page', codepage)

  win_registry = winregistry.WinRegistry(
      winregistry.WinRegistry.BACKEND_PYREGF)

  try:
    RegCache.hive = win_registry.OpenFile(file_entry, codepage=use_codepage)
  except IOError:
    if filename is not None:
      filename_string = filename
    elif path_spec:
      filename_string = path_spec.location
    else:
      filename_string = u'unknown file path'
    logging.error(
        u'Unable to open Registry hive: {0:s}'.format(filename_string))
    sys.exit(1)
  RegCache.SetHiveType()
  RegCache.file_entry = file_entry
  RegCache.BuildCache()
  RegCache.cur_key = RegCache.hive.GetKeyByPath('\\')


def GetFormatString(event_object):
  """Return back a format string that can be used for a given event object."""
  # Assign a default value to font align length.
  align_length = 15

  # Go through the attributes and see if there is an attribute
  # value that is longer than the default font align length, and adjust
  # it accordingly if found.
  for attribute in event_object.regvalue:
    attribute_len = len(attribute)
    if attribute_len > align_length and attribute_len < 30:
      align_length = len(attribute)

  # Create the format string that will be used, using variable length
  # font align length (calculated in the prior step).
  return u'{{0:>{0:d}s}} : {{1!s}}'.format(align_length)


def GetEventHeader(event_object, descriptions, exclude_timestamp):
  """Returns a list of strings that contains a header for the event.

  Args:
    event_object: An event object (instance of event.EventObject).
    descriptions: A list of strings describing the value of the header
                  timestamp.
    exclude_timestamp: A boolean. If it is set to True the method
                       will not include the timestamp in the header.

  Returns:
    A list of strings containing header information for the event.
  """
  format_string = GetFormatString(event_object)

  # Create the strings to return.
  ret_strings = []
  ret_strings.append(u'Key information.')
  if not exclude_timestamp:
    for description in descriptions:
      ret_strings.append(format_string.format(
          description, timelib.Timestamp.CopyToIsoFormat(
              event_object.timestamp)))
  ret_strings.append(format_string.format(u'Key Path', event_object.keyname))
  if event_object.timestamp_desc != eventdata.EventTimestamp.WRITTEN_TIME:
    ret_strings.append(format_string.format(
        u'Description', event_object.timestamp_desc))

  ret_strings.append(frontend_utils.FormatHeader(u'Data', u'-'))

  return ret_strings


def GetEventBody(event_object, show_hex=False):
  """Returns a list of strings containing information from an event.

  Args:
    event_object: An event object (instance of event.EventObject).
    show_hex: A boolean, if set to True hex dump of the value is included in
              the output. The default value is False.

  Returns:
    A list of strings containing the event body.
  """
  format_string = GetFormatString(event_object)

  ret_strings = []
  for attribute, value in event_object.regvalue.items():
    ret_strings.append(format_string.format(attribute, value))

  if show_hex:
    event_object.pathspec = RegCache.file_entry.path_spec
    ret_strings.append(frontend_utils.FormatHeader(
        u'Hex Output From Event.', '-'))
    ret_strings.append(
        frontend_utils.OutputWriter.GetEventDataHexDump(event_object))

  return ret_strings


def ParseHive(
    hive_path_or_path_spec, hive_collectors, keys, use_plugins, verbose):
  """Opens a hive file, and returns information about parsed keys.

  This function takes a path to a hive and a list of collectors (or
  none if the Registry file is passed to the tool).

  The function then opens up the hive inside each collector and runs
  the plugins defined (or all if no plugins are defined) against all
  the keys supplied to it.

  Args:
    hive_path: Full path to the hive file in question.
    hive_collectors: A list of collectors to use.
    keys: A list of Registry keys (strings) that are to be parsed.
    use_plugins: A list of plugins used to parse the key, None if all
    plugins should be used.
    verbose: Print more verbose content, like hex dump of extracted events.

  Returns:
    A string containing extracted information.
  """
  if isinstance(hive_path_or_path_spec, basestring):
    hive_path_spec = None
    hive_path = hive_path_or_path_spec
  else:
    hive_path_spec = hive_path_or_path_spec
    hive_path = hive_path_spec.location

  print_strings = []
  for name, hive_collector in hive_collectors:
    # Printing '*' 80 times.
    print_strings.append(u'*'*80)
    print_strings.append(
        u'{0:>15} : {1:s}{2:s}'.format(u'Hive File', hive_path, name))
    if hive_path_spec:
      OpenHive(hive_path_spec, hive_collector)
    else:
      OpenHive(hive_path, hive_collector)

    for key_str in keys:
      key_texts = []
      key_dict = {}
      if RegCache.reg_cache:
        key_dict.update(RegCache.reg_cache.attributes.items())

      if RegCache.pre_obj:
        key_dict.update(RegCache.pre_obj.__dict__.items())

      key = RegCache.hive.GetKeyByPath(key_str)
      key_texts.append(u'{0:>15} : {1:s}'.format(u'Key Name', key_str))
      if not key:
        key_texts.append(u'Unable to open key: {0:s}'.format(key_str))
        if verbose:
          print_strings.extend(key_texts)
        continue
      key_texts.append(
          u'{0:>15} : {1:d}'.format(u'Subkeys', key.number_of_subkeys))
      key_texts.append(u'{0:>15} : {1:d}'.format(
          u'Values', key.number_of_values))
      key_texts.append(u'')

      if verbose:
        key_texts.append(u'{0:-^80}'.format(u' SubKeys '))
        for subkey in key.GetSubkeys():
          key_texts.append(
              u'{0:>15} : {1:s}'.format(u'Key Name', subkey.path))

      key_texts.append(u'')
      key_texts.append(u'{0:-^80}'.format(u' Plugins '))
      key_texts.extend(
          ParseKey(key, verbose=verbose, use_plugins=use_plugins))
      print_strings.extend(key_texts)

  return u'\n'.join(print_strings)


def ParseKey(key, verbose=False, use_plugins=None):
  """Parse a single Registry key and return parsed information.

  Parses the Registry key either using the supplied plugin or trying against
  all avilable plugins.

  Args:
    key: The Registry key to parse, WinRegKey object or a string.
    verbose: Print additional information, such as a hex dump.
    use_plugins: A list of plugin names to use, or none if all should be used.

  Returns:
    A list of strings.
  """
  print_strings = []
  # Check if hive is set.
  if not RegCache.hive:
    return

  if type(key) in (unicode, str):
    key = RegCache.hive.GetKeyByPath(key)

  if not key:
    return

  # Detect Registry type.
  registry_type = RegCache.hive_type

  # Clear the last results from parse key.
  RegCache.events_from_last_parse = []

  plugins = {}
  regplugins = winreg_interface.GetRegistryPlugins()
  # Compile a list of plugins we are about to use.
  for weight in regplugins.GetWeights():
    plugin_list = regplugins.GetWeightPlugins(weight, registry_type)
    plugins[weight] = []
    for plugin in plugin_list:
      if use_plugins:
        plugin_obj = plugin(
            pre_obj=RegCache.pre_obj, reg_cache=RegCache.reg_cache)
        if plugin_obj.plugin_name in use_plugins:
          plugins[weight].append(plugin_obj)
      else:
        plugins[weight].append(plugin(
            pre_obj=RegCache.pre_obj, reg_cache=RegCache.reg_cache))

  # Run all the plugins in the correct order of weight.
  for weight in plugins:
    for plugin in plugins[weight]:
      call_back = plugin.Process(key)
      if call_back:
        print_strings.append(u'')
        print_strings.append(
            u'{0:^80}'.format(u' ** Plugin : {0:s} **'.format(
                plugin.plugin_name)))
        print_strings.append(u'')
        print_strings.append(u'[{0:s}] {1:s}'.format(
            plugin.REG_TYPE, plugin.__doc__.partition('\n')[0]))
        print_strings.append(u'')
        if plugin.URLS:
          print_strings.append(u'Additional information can be found here:')

          for url in plugin.URLS:
            print_strings.append(u'{0:>17s} {1:s}'.format(u'URL :', url))
          print_strings.append(u'')

        event_objects_and_timestamps = {}
        for event_object in call_back:
          RegCache.events_from_last_parse.append(event_object)
          event_objects_and_timestamps.setdefault(
              event_object.timestamp, []).append(event_object)

        if not event_objects_and_timestamps:
          continue

        # If there is only a single timestamp then we'll include it in the
        # header, otherwise each event will have it's own timestamp.
        if len(event_objects_and_timestamps) > 1:
          exclude_timestamp_in_header = True
        else:
          exclude_timestamp_in_header = False

        first = True
        for event_timestamp in sorted(event_objects_and_timestamps):
          if first:
            first_event = event_objects_and_timestamps[event_timestamp][0]
            descriptions = set()
            for event_object in event_objects_and_timestamps[event_timestamp]:
              descriptions.add(getattr(event_object, 'timestamp_desc', u''))
            print_strings.extend(GetEventHeader(
                first_event, list(descriptions), exclude_timestamp_in_header))
            first = False

          if exclude_timestamp_in_header:
            print_strings.append(u'')
            print_strings.append(u'[{0:s}]'.format(
                timelib.Timestamp.CopyToIsoFormat(event_timestamp)))

          for event_object in event_objects_and_timestamps[event_timestamp]:
            print_strings.append(u'')
            print_strings.extend(GetEventBody(event_object, verbose))

        print_strings.append(u'')

  # Printing '*' 80 times.
  print_strings.append(u'*'*80)
  print_strings.append(u'')

  return print_strings


def GetRegistryPlugins(options):
  """Return a list of Registry plugins by examining configuration object.

  Args:
    options: the command line arguments (instance of argparse.Namespace).
  """
  key_plugin_names = []
  for plugin in options.plugins.GetAllKeyPlugins():
    temp_obj = plugin(None, None)
    key_plugin_names.append(temp_obj.plugin_name)

  # Determine if we are running against a plugin or a key (behavior differs).
  plugins_to_run = []
  if options.plugin_name:
    plugin_name = options.plugin_name.lower()
    if not plugin_name.startswith('winreg'):
      plugin_name = u'winreg_{0:s}'.format(plugin_name)

    for key_plugin in key_plugin_names:
      if plugin_name in key_plugin.lower():
        plugins_to_run.append(key_plugin)
  else:
    plugins_to_run = key_plugin_names

  return plugins_to_run


def RunModeConsole(front_end, options):
  """Open up an iPython console.

  Args:
    options: the command line arguments (instance of argparse.Namespace).
  """
  namespace = {}
  hives, hive_collectors = front_end.GetHivesAndCollectors(options)

  function_name_length = 23
  banners = []
  banners.append(frontend_utils.FormatHeader(
      'Welcome to PREG - home of the Plaso Windows Registry Parsing.'))
  banners.append('')
  banners.append('Some of the commands that are available for use are:')
  banners.append('')
  banners.append(frontend_utils.FormatOutputString(
      'cd key', 'Navigate the Registry like a directory structure.',
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      'ls [-v]', (
          'List all subkeys and values of a Registry key. If called as '
          'ls True then values of keys will be included in the output.'),
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      'parse -[v]', 'Parse the current key using all plugins.',
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      'pwd', 'Print the working "directory" or the path of the current key.',
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      'plugin [-h] plugin_name', (
          'Run a particular key-based plugin on the loaded hive. The correct '
          'Registry key will be loaded, opened and then parsed.'),
      function_name_length))

  banners.append('')

  if len(hives) == 1:
    hive = hives[0]
    hives = []
  else:
    hive = None

  if len(hive_collectors) == 1:
    hive_collector = hive_collectors[0][1]
    hive_collectors = []
  else:
    hive_collector = None

  if hive and not hive_collectors:
    OpenHive(hive, hive_collector)

  if RegCache.hive and RegCache.GetHiveName() != 'N/A':
    banners.append(
        u'Registry hive: {0:s} is available and loaded.'.format(
            RegCache.GetHiveName()))
  elif hives:
    banners.append('More than one Registry file ready for use.')
    banners.append('')
    banners.append('Registry files discovered:')
    for number, hive in enumerate(hives):
      banners.append(' - {0:d}  {1:s}'.format(number, hive.location))
    banners.append('')
    banners.append('To load a hive use:')
    text = 'OpenHive(hives[NR], collector)'

    if hive_collectors:
      banners.append('')
      banners.append((
          'There is more than one collector available. To use any of them '
          'instead of the attribute "collector" in the OpenHive '
          'function use the collectors attribute.\nThe available collectors '
          'are:'))
      counter = 0
      for name, _ in hive_collectors:
        if not name:
          name = 'Current Value'
        banners.append(' {0:d} = {1:s}'.format(counter, name))
        counter += 1

      banners.append(
          'To use the collector use:\ncollector = collectors[NR][1]\nwhere '
          'NR is the number as listed above.')
    else:
      banners.append(frontend_utils.FormatOutputString(text, (
          'Collector is an available attribute and NR is a number ranging'
          ' from 0 to {0:d} (see above which files these numbers belong to).'
          ' To get the name of the loaded hive use RegCache.GetHiveName()'
          ' and RegCache.hive_type to get the '
          'type.').format(len(hives) + 1), len(text)))
  else:
    # We have a single hive but many collectors.
    banners.append(
        'There is more than one collector available for the hive that was '
        'discovered. To open up a hive use:\nOpenHive(hive, collectors[NR][1])'
        '\nWhere NR is one of the following values:')

    counter = 0
    for name, _ in hive_collectors:
      if not name:
        name = 'Current Value'
      banners.append(' {0:d} = {1:s}'.format(counter, name))
      counter += 1

  banners.append('')
  banners.append('Happy command line console fu-ing.')

  # Adding variables in scope.
  namespace.update(globals())
  namespace.update({
      'hives': hives,
      'hive': hive,
      'collector': hive_collector,
      'collectors': hive_collectors})

  # Starting the shell.
  ipshell = InteractiveShellEmbed(
      user_ns=namespace, banner1=u'\n'.join(banners), exit_msg='')
  ipshell.confirm_exit = False
  # Adding "magic" functions.
  ipshell.register_magics(MyMagics)
  # Registering command completion for the magic commands.
  ipshell.set_hook('complete_command', CdCompleter, str_key='%cd')
  ipshell.set_hook('complete_command', VerboseCompleter, str_key='%ls')
  ipshell.set_hook('complete_command', VerboseCompleter, str_key='%parse')
  ipshell.set_hook('complete_command', PluginCompleter, str_key='%plugin')
  ipshell()


def Main():
  """Run the tool."""
  output_writer = frontend.StdoutFrontendOutputWriter()
  front_end = PregFrontend(output_writer)

  epilog = textwrap.dedent("""

Example usage:

Parse the SOFTWARE hive from an image:
  {0:s} [--vss] [--vss-stores VSS_STORES] -i IMAGE_PATH [-o OFFSET] -c SOFTWARE

Parse an userassist key within an extracted hive:
  {0:s} -p userassist MYNTUSER.DAT

Parse the run key from all Registry keys (in vss too):
  {0:s} --vss -i IMAGE_PATH [-o OFFSET] -p run

Open up a console session for the SYSTEM hive inside an image:
  {0:s} -i IMAGE_PATH [-o OFFSET] -c SYSTEM
      """).format(os.path.basename(sys.argv[0]))

  description = textwrap.dedent("""
preg is a simple Windows Registry parser using the plaso registry
plugins and image parsing capabilities.

It uses the back-end libraries of plaso to read raw image files and
extract Registry files from VSS and restore points and then runs the
Registry plugins of plaso against the Registry hive and presents it
in a textual format.

      """)

  arg_parser = argparse.ArgumentParser(
      epilog=epilog, description=description, add_help=False,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  # Create the different argument groups.
  mode_options = arg_parser.add_argument_group(u'Run Mode Options')
  image_options = arg_parser.add_argument_group(u'Image Options')
  info_options = arg_parser.add_argument_group(u'Informational Options')
  additional_data = arg_parser.add_argument_group(u'Additional Options')

  mode_options.add_argument(
      '-c', '--console', dest='console', action='store_true', default=False,
      help=u'Drop into a console session Instead of printing output to STDOUT.')

  additional_data.add_argument(
      '-r', '--restore_points', dest='restore_points', action='store_true',
      default=False, help=u'Include restore points for hive locations.')

  image_options.add_argument(
      '-i', '--image', dest='image', action='store', type=unicode, default='',
      metavar='IMAGE_PATH',
      help=(u'If the Registry file is contained within a storage media image, '
            u'set this option to specify the path of image file.'))

  front_end.AddImageOptions(image_options)

  info_options.add_argument(
      '-v', '--verbose', dest='verbose', action='store_true', default=False,
      help=u'Print sub key information.')

  info_options.add_argument(
      '-h', '--help', action='help', help=u'Show this help message and exit.')

  front_end.AddVssProcessingOptions(additional_data)

  info_options.add_argument(
      '--info', dest='info', action='store_true', default=False,
      help=u'Print out information about supported plugins.')

  mode_options.add_argument(
      '-p', '--plugins', dest='plugin_name', action='store', default='',
      type=unicode, metavar='PLUGIN_NAME',
      help=u'Substring match of the Registry plugin to be used.')

  mode_options.add_argument(
      '-k', '--key', dest='key', action='store', default='', type=unicode,
      metavar='REGISTRY_KEYPATH',
      help=(u'A Registry key path that the tool should parse using all '
            u'available plugins.'))

  arg_parser.add_argument(
      'regfile', action='store', metavar='REGHIVE', nargs='?',
      help=(u'The Registry hive to read key from (not needed if running '
            u'using a plugin)'))

  # Parse the command line arguments.
  options = arg_parser.parse_args()

  options.plugins = winreg_interface.GetRegistryPlugins()

  # TODO: Move some of this logic to a separate function calls to make
  # GUI writing on top of this front-end simpler.

  # Run some common operations (common to all run modes)
  # Detect run mode and run appropriate method calls.
  if options.info:
    print frontend_utils.FormatHeader(u'Supported Plugins')
    key_plugin = options.plugins.GetAllKeyPlugins()[0]

    for plugin, obj in sorted(key_plugin.classes.items()):
      doc_string, _, _ = obj.__doc__.partition('\n')
      print frontend_utils.FormatOutputString(plugin, doc_string)
    return True

  try:
    front_end.ParseOptions(options, u'')
  except errors.BadConfigOption as exception:
    arg_parser.print_help()
    print u''
    logging.error('{0:s}'.format(exception))
    return False

  # Run the tool, using the run mode according to the options passed
  # to the tool.
  if options.console:
    RunModeConsole(front_end, options)
  elif options.key and options.regfile:
    front_end.RunModeRegistryKey(options)
  elif options.plugin_name:
    front_end.RunModeRegistryPlugin(options)
  elif options.regfile:
    front_end.RunModeRegistryFile(options)
  else:
    print (u'Incorrect usage. You\'ll need to define the path of either '
           u'a storage media image or a Windows Registry file.')
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
