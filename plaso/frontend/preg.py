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

import IPython
from IPython.config.loader import Config
from IPython.core import magic

from plaso.artifacts import knowledge_base
from plaso.engine import queue
from plaso.engine import single_process

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
from plaso.parsers import context as parsers_context
from plaso.parsers import manager as parsers_manager
from plaso.parsers import winreg as winreg_parser
from plaso.parsers import winreg_plugins    # pylint: disable=unused-import
from plaso.preprocessors import interface as preprocess_interface
from plaso.preprocessors import manager as preprocess_manager
from plaso.winreg import cache
from plaso.winreg import path_expander as winreg_path_expander
from plaso.winreg import winregistry


if IPython.version_info < (1, 2, 1):
  raise ImportWarning(
      'Preg requires at least IPython version 1.2.1.')


class ConsoleConfig(object):
  """Class that contains functions to configure console actions."""

  @classmethod
  def GetConfig(cls):
    """Retrieves the iPython config.

    Returns:
      The IPython config object (instance of
      IPython.terminal.embed.InteractiveShellEmbed)
    """
    try:
      # The "get_ipython" function does not exist except within an IPython
      # session.
      return get_ipython()  # pylint: disable-msg=undefined-variable
    except NameError:
      return Config()

  @classmethod
  def SetPrompt(
      cls, hive_path=None, config=None, prepend_string=None):
    """Sets the prompt string on the console.

    Args:
      hive_path: The hive name or path as a string, this is optional name or
                 location of the loaded hive. If not defined the name is derived
                 from a default string.
      config: The IPython configuration object (instance of
              IPython.terminal.embed.InteractiveShellEmbed), this is optional
              and is automatically derived if not used.
      prepend_string: An optional string that can be injected into the prompt
                      just prior to the command count.
    """
    if hive_path is None:
      path_string = u'Unknown hive loaded'
    else:
      path_string = hive_path

    prompt_strings = [
        r'[{color.LightBlue}\T{color.Normal}]',
        r'{color.LightPurple} ',
        path_string,
        r'\n{color.Normal}']
    if prepend_string is not None:
      prompt_strings.append(u'{0:s} '.format(prepend_string))
    prompt_strings.append(r'[{color.Red}\#{color.Normal}] \$ ')

    if config is None:
      ipython_config = cls.GetConfig()
    else:
      ipython_config = config

    try:
      ipython_config.PromptManager.in_template = r''.join(prompt_strings)
    except AttributeError:
      ipython_config.prompt_manager.in_template = r''.join(prompt_strings)


class PregCache(object):
  """Cache storage used for iPython and other aspects of preg."""

  events_from_last_parse = []

  knowledge_base_object = knowledge_base.KnowledgeBase()

  # Parser context, used when parsing Registry keys.
  parser_context = None

  hive_storage = None
  shell_helper = None


class PregEventObjectQueueConsumer(queue.EventObjectQueueConsumer):
  """Class that implements a list event object queue consumer."""

  def __init__(self, event_queue):
    """Initializes the list event object queue consumer.

    Args:
      event_queue: the event object queue (instance of Queue).
    """
    super(PregEventObjectQueueConsumer, self).__init__(event_queue)
    self.event_objects = []

  def _ConsumeEventObject(self, event_object, **unused_kwargs):
    """Consumes an event object callback for ConsumeEventObjects.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self.event_objects.append(event_object)


class PregFrontend(frontend.ExtractionFrontend):
  """Class that implements the preg front-end."""

  def __init__(self, output_writer):
    """Initializes the front-end object."""
    input_reader = frontend.StdinFrontendInputReader()

    super(PregFrontend, self).__init__(input_reader, output_writer)
    self._key_path = None
    self._parse_restore_points = False
    self._verbose_output = False
    self.plugins = None

  def GetListOfAllPlugins(self):
    """Returns information about the supported plugins."""
    return_strings = []
    # TODO: replace frontend_utils.FormatHeader by frontend function.
    return_strings.append(frontend_utils.FormatHeader(u'Supported Plugins'))
    all_plugins = parsers_manager.ParsersManager.GetWindowsRegistryPlugins()

    return_strings.append(frontend_utils.FormatHeader(u'Key Plugins'))
    for plugin_obj in all_plugins.GetAllKeyPlugins():
      return_strings.append(frontend_utils.FormatOutputString(
          plugin_obj.NAME[7:], plugin_obj.DESCRIPTION))

    return_strings.append(frontend_utils.FormatHeader(u'Value Plugins'))
    for plugin_obj in all_plugins.GetAllValuePlugins():
      return_strings.append(frontend_utils.FormatOutputString(
          plugin_obj.NAME[7:], plugin_obj.DESCRIPTION))

    return u'\n'.join(return_strings)

  def ParseHive(
      self, hive_path_or_path_spec, hive_collectors, shell_helper,
      key_paths=None, use_plugins=None, verbose=False):
    """Opens a hive file, and returns information about parsed keys.

    This function takes a path to a hive and a list of collectors (or
    none if the Registry file is passed to the tool).

    The function then opens up the hive inside each collector and runs
    the plugins defined (or all if no plugins are defined) against all
    the keys supplied to it.

    Args:
      hive_path: Full path to the hive file in question.
      hive_collectors: A list of collectors to use (instance of
                       dfvfs.helpers.file_system_searcher.FileSystemSearcher)
      shell_helper: A helper object (instance of PregHelper).
      key_paths: A list of Registry keys paths that are to be parsed.
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

    if key_paths is None:
      key_paths = []

    print_strings = []
    for name, hive_collector in hive_collectors:
      # Printing '*' 80 times.
      print_strings.append(u'*' * 80)
      print_strings.append(
          u'{0:>15} : {1:s}{2:s}'.format(u'Hive File', hive_path, name))
      if hive_path_spec:
        current_hive = shell_helper.OpenHive(hive_path_spec, hive_collector)
      else:
        current_hive = shell_helper.OpenHive(hive_path, hive_collector)

      if not current_hive:
        continue

      for key_path in key_paths:
        key_texts = []
        key_dict = {}
        if current_hive.reg_cache:
          key_dict.update(current_hive.reg_cache.attributes.items())

        if PregCache.knowledge_base_object.pre_obj:
          key_dict.update(
              PregCache.knowledge_base_object.pre_obj.__dict__.items())

        key = current_hive.GetKeyByPath(key_path)
        key_texts.append(u'{0:>15} : {1:s}'.format(u'Key Name', key_path))
        if not key:
          key_texts.append(u'Unable to open key: {0:s}'.format(key_path))
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

        output_string = ParseKey(
            key=key, shell_helper=shell_helper, verbose=verbose,
            use_plugins=use_plugins, hive_helper=current_hive)
        key_texts.extend(output_string)

        print_strings.extend(key_texts)

    return u'\n'.join(print_strings)

  def ParseOptions(self, options, source_option='source'):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      source_option: optional name of the source option. The default is source.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    if not options:
      raise errors.BadConfigOption(u'Missing options.')

    image = getattr(options, 'image', None)
    regfile = getattr(options, 'regfile', None)

    if not image and not regfile:
      raise errors.BadConfigOption(u'Not enough parameters to proceed.')

    if image:
      self._source_path = image

    if regfile:
      if not image and not os.path.isfile(regfile):
        raise errors.BadConfigOption(
            u'Registry file: {0:s} does not exist.'.format(regfile))

    self._key_path = getattr(options, 'key', None)
    self._parse_restore_points = getattr(options, 'restore_points', False)

    self._verbose_output = getattr(options, 'verbose', False)

    self.plugins = parsers_manager.ParsersManager.GetWindowsRegistryPlugins()

  def _ExpandKeysRedirect(self, keys):
    """Expands a list of Registry key paths with their redirect equivalents.

    Args:
      keys: a list of Windows Registry key paths.
    """
    for key in keys:
      if key.startswith('\\Software') and 'Wow6432Node' not in key:
        _, first, second = key.partition('\\Software')
        keys.append(u'{0:s}\\Wow6432Node{1:s}'.format(first, second))

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

      # The path is split in segments to make it path segment separator
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

  def _GetRegistryFilePaths(self, plugin_name=None, registry_type=None):
    """Returns a list of Registry paths from a configuration object.

    Args:
      plugin_name: optional string containing the name of the plugin or an empty
                   string or None for all the types. Defaults to None.
      registry_type: optional Registry type string. None by default.

    Returns:
      A list of path names for registry files.
    """
    if self._parse_restore_points:
      restore_path = u'/System Volume Information/_restor.+/RP[0-9]+/snapshot/'
    else:
      restore_path = u''

    if registry_type:
      types = [registry_type]
    else:
      types = self._GetRegistryTypes(plugin_name)

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
    expanded_paths = []
    expander = winreg_path_expander.WinRegistryKeyPathExpander()
    for path in paths:
      try:
        expanded_paths.append(expander.ExpandPath(
            path, pre_obj=PregCache.knowledge_base_object.pre_obj))

      except KeyError as exception:
        logging.error(u'Unable to expand keys with error: {0:s}'.format(
            exception))

    return expanded_paths

  def _GetRegistryKeysFromHive(self, hive_helper, parser_context):
    """Retrieves a list of all key plugins for a given Registry type.

    Args:
      hive_helper: A hive object (instance of PregHiveHelper).
      parser_context: A parser context object (instance of ParserContext).

    Returns:
      A list of Windows Registry keys.
    """
    keys = []
    if not hive_helper:
      return
    for key_plugin_cls in self.plugins.GetAllKeyPlugins():
      temp_obj = key_plugin_cls(reg_cache=hive_helper.reg_cache)
      if temp_obj.REG_TYPE == hive_helper.type:
        temp_obj.ExpandKeys(parser_context)
        keys.extend(temp_obj.expanded_keys)

    return keys

  def _GetRegistryPlugins(self, plugin_name):
    """Retrieves the Windows Registry plugins based on a filter string.

    Args:
      plugin_name: string containing the name of the plugin or an empty
                   string for all the plugins.

    Returns:
      A list of Windows Registry plugins.
    """
    key_plugin_names = []
    for plugin in self.plugins.GetAllKeyPlugins():
      temp_obj = plugin(None)
      key_plugin_names.append(temp_obj.plugin_name)

    if not plugin_name:
      return key_plugin_names

    plugin_name = plugin_name.lower()
    if not plugin_name.startswith('winreg'):
      plugin_name = u'winreg_{0:s}'.format(plugin_name)

    plugins_to_run = []
    for key_plugin in key_plugin_names:
      if plugin_name in key_plugin.lower():
        plugins_to_run.append(key_plugin)

    return plugins_to_run

  def _GetRegistryTypes(self, plugin_name):
    """Retrieves the Windows Registry types based on a filter string.

    Args:
      plugin_name: string containing the name of the plugin or an empty
                   string for all the types.

    Returns:
      A list of Windows Registry types.
    """
    reg_cache = cache.WinRegistryCache()
    types = []
    for plugin in self._GetRegistryPlugins(plugin_name):
      for key_plugin_cls in self.plugins.GetAllKeyPlugins():
        temp_obj = key_plugin_cls(reg_cache=reg_cache)
        if plugin is temp_obj.plugin_name:
          if temp_obj.REG_TYPE not in types:
            types.append(temp_obj.REG_TYPE)
          break

    return types

  def _GetSearchersForImage(self, volume_path_spec):
    """Retrieves the file systems searchers for searching the image.

    Args:
      volume_path_spec: The path specification of the volume containing
                        the file system (instance of dfvfs.PathSpec).

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
          u':VSS Store {0:d}'.format(store_index), searcher))

    return searchers

  def GetHivesAndCollectors(
      self, options, registry_types=None, plugin_names=None):
    """Returns a list of discovered Registry hives and collectors.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      registry_types: an optional list of Registry types, eg: NTUSER, SAM, etc
                      that should be included. Defaults to None.
      plugin_names: an optional list of strings containing the name of the
                    plugin(s) or an empty string for all the types. Defaults to
                    None.

    Returns:
      A tuple of hives and searchers, where hives is a list that contains
      either a string (location of a Registry hive) or path specs (instance of
      dfvfs.path.path_spec.PathSpec). The searchers is a list of tuples that
      contain the name of the searcher and a searcher object (instance of
      dfvfs.helpers.file_system_searcher.FileSystemSearcher) or None (if no
      searcher is required).

    Raises:
      ValueError: If neither registry_types nor plugin name is passed
                  as a parameter.
    """
    if registry_types is None and plugin_names is None:
      raise ValueError(
          u'Missing registry_types or plugin_name value.')

    if plugin_names is None:
      plugin_names = []
    else:
      plugin_names = [plugin_name.lower() for plugin_name in plugin_names]

    # TODO: use non-preprocess collector with filter to collect hives.

    # TODO: rewrite to always use collector or equiv.
    if not self._source_path:
      searchers = [(u'', None)]
      return registry_types, searchers

    try:
      self.ScanSource(options)
    except errors.SourceScannerError as exception:
      raise errors.BadConfigOption((
          u'Unable to scan for a supported filesystem with error: {0:s}\n'
          u'Most likely the image format is not supported by the '
          u'tool.').format(exception))

    searchers = self._GetSearchersForImage(self.GetSourcePathSpec().parent)
    _, searcher = searchers[0]

    # Run preprocessing on image.
    platform = preprocess_interface.GuessOS(searcher)

    preprocess_manager.PreprocessPluginsManager.RunPlugins(
        platform, searcher, PregCache.knowledge_base_object)

    # Create the keyword list if plugins are used.
    plugins_list = parsers_manager.ParsersManager.GetWindowsRegistryPlugins()
    if plugin_names:
      if registry_types is None:
        registry_types = []
      for plugin_name in plugin_names:
        if not plugin_name.startswith('winreg_'):
          plugin_name = u'winreg_{0:s}'.format(plugin_name)
        for plugin_cls in plugins_list.GetAllKeyPlugins():
          if plugin_name == plugin_cls.NAME.lower():
            if plugin_cls.REG_TYPE not in registry_types:
              registry_types.append(plugin_cls.REG_TYPE)

    # Find all the Registry paths we need to check.
    paths = []
    if registry_types:
      for registry_type in registry_types:
        paths.extend(self._GetRegistryFilePaths(
            registry_type=registry_type.upper()))
    else:
      for plugin_name in plugin_names:
        paths.extend(self._GetRegistryFilePaths(plugin_name=plugin_name))

    hives = []
    for path in paths:
      hives.extend(self._FindRegistryPaths(searcher, path))

    return hives, searchers

  def RunModeRegistryKey(self, options, plugin_names):
    """Run against a specific Registry key.

    Finds and opens all Registry hives as configured in the configuration
    object and tries to open the Registry key that is stored in the
    configuration object for every detected hive file and parses it using
    all available plugins.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      plugin_names: a list of strings containing the name of the plugin(s) or
                    an empty list for all the types.
    """
    regfile = getattr(options, 'regfile', u'')

    hives, hive_collectors = self.GetHivesAndCollectors(
        options, registry_types=[regfile],
        plugin_names=plugin_names)

    key_paths = [self._key_path]

    # Expand the keys paths if there is a need (due to Windows redirect).
    self._ExpandKeysRedirect(key_paths)

    hive_storage = PregStorage()
    shell_helper = PregHelper(options, self, hive_storage)

    if hives is None:
      hives = [regfile]

    for hive in hives:
      output_string = self.ParseHive(
          hive, hive_collectors, shell_helper,
          key_paths=key_paths, verbose=self._verbose_output)
      self._output_writer.Write(output_string)

  def RunModeRegistryPlugin(self, options, plugin_names):
    """Run against a set of Registry plugins.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      plugin_names: a list of strings containing the name of the plugin(s) or
                    an empty string for all the types.
    """
    # TODO: Add support for splitting the output to separate files based on
    # each plugin name.
    hives, hive_collectors = self.GetHivesAndCollectors(
        options, plugin_names=plugin_names)

    if hives is None:
      hives = [getattr(options, 'regfile', None)]

    plugin_list = []
    for plugin_name in plugin_names:
      plugin_list.extend(self._GetRegistryPlugins(plugin_name))

    # In order to get all the Registry keys we need to expand
    # them, but to do so we need to open up one hive so that we
    # create the reg_cache object, which is necessary to fully
    # expand all keys.
    _, hive_collector = hive_collectors[0]
    hive_storage = PregStorage()
    shell_helper = PregHelper(options, self, hive_storage)
    hive_helper = shell_helper.OpenHive(hives[0], hive_collector)
    parser_context = shell_helper.BuildParserContext()

    # Get all the appropriate keys from these plugins.
    key_paths = self.plugins.GetExpandedKeyPaths(
        parser_context, reg_cache=hive_helper.reg_cache,
        plugin_names=plugin_list)

    for hive in hives:
      output_string = self.ParseHive(
          hive, hive_collectors, shell_helper,
          key_paths=key_paths, use_plugins=plugin_list,
          verbose=self._verbose_output)
      self._output_writer.Write(output_string)

  def RunModeRegistryFile(self, options, regfile):
    """Run against a Registry file.

    Finds and opens all Registry hives as configured in the configuration
    object and determines the type of Registry file opened. Then it will
    load up all the Registry plugins suitable for that particular Registry
    file, find all Registry keys they are able to parse and run through
    them, one by one.

    Args:
      options: the command line arguments (instance of argparse.Namespace).
      regfile: A string containing either full path to the Registry hive or
               a keyword to match it.
    """
    # Get all the hives and collectors.
    hives, hive_collectors = self.GetHivesAndCollectors(
        options, registry_types=[regfile])

    hive_storage = PregStorage()
    shell_helper = PregHelper(options, self, hive_storage)
    parser_context = shell_helper.BuildParserContext()

    for hive in hives:
      for collector_name, hive_collector in hive_collectors:
        hive_helper = shell_helper.OpenHive(
            hive, hive_collector=hive_collector,
            hive_collector_name=collector_name)
        hive_type = hive_helper.type

        key_paths = self._GetRegistryKeysFromHive(hive_helper, parser_context)
        self._ExpandKeysRedirect(key_paths)

        plugins_to_run = self._GetRegistryPlugins(hive_type)
        output_string = self.ParseHive(
            hive, hive_collectors, shell_helper, key_paths=key_paths,
            use_plugins=plugins_to_run, verbose=self._verbose_output)
        self._output_writer.Write(output_string)


class PregHelper(object):
  """Class that defines various helper functions.

  The purpose of this class is to bridge the plaso generated objects
  with the IPython objects, making it easier to create magic classes
  and provide additional helper functions to the IPython shell.
  """

  def __init__(self, tool_options, tool_front_end, hive_storage):
    """Initialize the helper object.

    Args:
      tool_options: A configuration object.
      tool_front_end: A front end object (instance of PregFrontend).
      hive_storage: A hive storage object (instance of PregStorage).
    """
    super(PregHelper, self).__init__()
    self.tool_options = tool_options
    self.tool_front_end = tool_front_end
    self.hive_storage = hive_storage

  def BuildParserContext(self, event_queue=None):
    """Build the parser object.

    Args:
      event_queue: An event queue object (instance of Queue). This is
                   optional and if a queue is not provided a default
                   one will be provided.

    Returns:
      A parser context object (instance of parsers_context.ParserContext).
    """
    if event_queue is None:
      event_queue = single_process.SingleProcessQueue()
    event_queue_producer = queue.ItemQueueProducer(event_queue)

    parse_error_queue = single_process.SingleProcessQueue()
    parse_error_queue_producer = queue.ItemQueueProducer(parse_error_queue)

    return parsers_context.ParserContext(
        event_queue_producer, parse_error_queue_producer,
        PregCache.knowledge_base_object)

  def OpenHive(
      self, filename_or_path_spec, hive_collector, hive_collector_name=None,
      codepage='cp1252'):
    """Open a Registry hive based on a collector or a filename.

    Args:
      filename_or_path_spec: file path to the hive as a string or a path spec
                             object (instance of dfvfs.path.path_spec.PathSpec)
      hive_collector: the collector to use (instance of
                      dfvfs.helpers.file_system_searcher.FileSystemSearcher)
      hive_collector_name: optional string denoting the name of the collector
                           used. The default value is None.
      codepage: the default codepage, default is cp1252.

    Returns:
      A hive helper object (instance of PregHiveHelper).
    """
    PregCache.knowledge_base_object.SetDefaultCodepage(codepage)

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

    win_registry = winregistry.WinRegistry(
        winregistry.WinRegistry.BACKEND_PYREGF)

    try:
      hive_object = win_registry.OpenFile(
          file_entry, codepage=PregCache.knowledge_base_object.codepage)
    except IOError:
      if filename is not None:
        filename_string = filename
      elif path_spec:
        filename_string = path_spec.location
      else:
        filename_string = u'unknown file path'
      logging.error(
          u'Unable to open Registry hive: {0:s} [{1:s}]'.format(
              filename_string, hive_collector_name))
      return

    return PregHiveHelper(
        hive_object, file_entry=file_entry, collector_name=hive_collector_name)

  def Scan(self, registry_types):
    """Scan for available hives using keyword.

    Args:
      registry_types: A list of keywords to scan for, eg: "NTUSER",
                      "SOFTWARE", etc.
    """
    if not registry_types:
      print (
          u'Unable to scan for an empty keyword. Please specify a keyword, '
          u'eg: NTUSER, SOFTWARE, etc')
      return

    hives, collectors = self.tool_front_end.GetHivesAndCollectors(
        self.tool_options, registry_types=registry_types)

    if not hives:
      print u'No new discovered hives.'
      return

    if type(hives) in (list, tuple):
      for hive in hives:
        for name, collector in collectors:
          hive_helper = self.OpenHive(
              hive, hive_collector=collector, hive_collector_name=name)
          if hive_helper:
            self.hive_storage.AppendHive(hive_helper)
    else:
      for name, collector in collectors:
        hive_helper = self.OpenHive(
              hives, hive_collector=collector, hive_collector_name=name)
        if hive_helper:
          self.hive_storage.AppendHive(hive_helper)


class PregHiveHelper(object):
  """Class that defines few helper functions for Registry operations."""

  _currently_loaded_registry_key = ''
  _hive = None
  _hive_type = u'UNKNOWN'

  collector_name = None
  file_entry = None
  path_expander = None
  reg_cache = None

  REG_TYPES = {
      u'NTUSER': ('\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer',),
      u'SOFTWARE': ('\\Microsoft\\Windows\\CurrentVersion\\App Paths',),
      u'SECURITY': ('\\Policy\\PolAdtEv',),
      u'SYSTEM': ('\\Select',),
      u'SAM': ('\\SAM\\Domains\\Account\\Users',),
      u'UNKNOWN': (),
  }

  @property
  def name(self):
    """Return the name of the hive."""
    return getattr(self._hive, 'name', u'N/A')

  @property
  def path(self):
    """Return the file path of the hive."""
    path_spec = getattr(self.file_entry, 'path_spec', None)
    if not path_spec:
      return u'N/A'

    return getattr(path_spec, 'location', u'N/A')

  @property
  def root_key(self):
    """Return the root key of the Registry hive."""
    return self._hive.GetKeyByPath(u'\\')

  @property
  def type(self):
    """Return the hive type."""
    return self._hive_type

  def __init__(self, hive, file_entry, collector_name):
    """Initialize the Registry hive helper.

    Args:
      hive: A hive object (instance of WinPyregfFile).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      collector_name: Name of the collector used as a string.
    """
    self._hive = hive
    self.file_entry = file_entry
    self.collector_name = collector_name

    # Determine type and build cache.
    self._SetHiveType()
    self._BuildHiveCache()

    # Initialize the hive to the root key.
    _ = self.GetKeyByPath(u'\\')

  def _BuildHiveCache(self):
    """Calculate the Registry cache."""
    self.reg_cache = cache.WinRegistryCache()
    self.reg_cache.BuildCache(self._hive, self._hive_type)
    self.path_expander = winreg_path_expander.WinRegistryKeyPathExpander(
        reg_cache=self.reg_cache)

  def _SetHiveType(self):
    """Detect and set the hive type."""
    get_key_by_path = self._hive.GetKeyByPath
    for reg_type in self.REG_TYPES:
      if reg_type == u'UNKNOWN':
        continue

      # For a hive to be considered a specific type all of the keys need to
      # be found.
      found = True
      for reg_key in self.REG_TYPES[reg_type]:
        if not get_key_by_path(reg_key):
          found = False
          break

      if found:
        self._hive_type = reg_type
        return

  def GetCurrentRegistryKey(self):
    """Return the currently loaded Registry key."""
    return self._currently_loaded_registry_key

  def GetCurrentRegistryPath(self):
    """Return the loaded Registry key path or None if no key is loaded."""
    key = self._currently_loaded_registry_key
    if not key:
      return

    return key.path

  def GetKeyByPath(self, path):
    """Retrieves a specific key defined by the Registry path.

    Args:
      path: the Registry path.

    Returns:
      The key (instance of WinRegKey) if available or None otherwise.
    """
    if not path:
      return

    key = self._hive.GetKeyByPath(path)
    if not key:
      return

    self._currently_loaded_registry_key = key
    return key


class PregStorage(object):
  """Class for storing discovered hives."""

  # Index number of the currently loaded Registry hive.
  _current_index = -1
  _currently_loaded_hive = None

  _hive_list = []

  @property
  def loaded_hive(self):
    """Return the currently loaded hive or None if no hive loaded."""
    if not self._currently_loaded_hive:
      return

    return self._currently_loaded_hive

  def __len__(self):
    """Return the number of available hives."""
    return len(self._hive_list)

  def AppendHive(self, hive_helper):
    """Append a hive object to the Registry hive storage.

    Args:
      hive_helper: A hive object (instance of PregHiveHelper)
    """
    self._hive_list.append(hive_helper)

  def AppendHives(self, hive_helpers):
    """Append hives to the Registry hive storage.

    Args:
      hive_helpers: A list of hive objects (instance of PregHiveHelper)
    """
    if type(hive_helpers) not in (list, tuple):
      hive_helpers = [hive_helpers]

    self._hive_list.extend(hive_helpers)

  def ListHives(self):
    """Return a string with a list of all available hives and collectors.

    Returns:
      A string with a list of all available hives and collectors. If there are
      no loaded hives None will be returned.
    """
    if not self._hive_list:
      return

    return_strings = [u'Index Hive [collector]']
    for index, hive in enumerate(self._hive_list):
      collector = hive.collector_name
      if not collector:
        collector = u'Currently Allocated'

      if self._current_index == index:
        star = u'*'
      else:
        star = u''
      return_strings.append(u'{0:<5d} {1:s}{2:s} [{3:s}]'.format(
          index, star, hive.path, collector))

    return u'\n'.join(return_strings)

  def SetOpenHive(self, hive_index):
    """Set the current open hive.

    Args:
      hive_index: An index (integer) into the hive list.
    """
    if not self._hive_list:
      return

    index = hive_index
    if isinstance(hive_index, basestring):
      try:
        index = int(hive_index, 10)
      except ValueError:
        print u'Wrong hive index, value should be decimal.'
        return

    try:
      hive_helper = self._hive_list[index]
    except IndexError:
      print u'Hive not found, index out of range?'
      return

    self._current_index = index
    self._currently_loaded_hive = hive_helper


def CdCompleter(unused_self, unused_event):
  """Completer function for the cd command, returning back sub keys."""
  return_list = []
  current_hive = PregCache.hive_storage.loaded_hive
  current_key = current_hive.GetCurrentRegistryKey()
  for key in current_key.GetSubkeys():
    return_list.append(key.name)

  return return_list


def PluginCompleter(unused_self, event_object):
  """Completer function that returns a list of available plugins."""
  ret_list = []

  if not IsLoaded():
    return ret_list

  if not '-h' in event_object.line:
    ret_list.append('-h')

  plugins_list = parsers_manager.ParsersManager.GetWindowsRegistryPlugins()

  current_hive = PregCache.hive_storage.loaded_hive
  hive_type = current_hive.type

  for plugin_cls in plugins_list.GetKeyPlugins(hive_type):
    plugins_list = plugin_cls(reg_cache=current_hive.reg_cache)

    plugin_name = plugins_list.plugin_name
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

  @magic.line_magic('cd')
  def ChangeDirectory(self, key):
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
      self.ChangeDirectory('\\')

    loaded_hive = PregCache.hive_storage.loaded_hive

    if not loaded_hive:
      return

    # Check if we need to expand environment attributes.
    match = self.EXPANSION_RE.search(key)
    if match and u'{0:s}{0:s}'.format(
        self.EXPANSION_KEY_OPEN) not in match.group(0):
      try:
        key = loaded_hive.path_expander.ExpandPath(
            key, pre_obj=PregCache.knowledge_base_object.pre_obj)
      except (KeyError, IndexError):
        pass

    if key.startswith(u'\\'):
      registry_key = loaded_hive.GetKeyByPath(key)
    elif key == '.':
      return
    elif key.startswith(u'.\\'):
      current_path = loaded_hive.GetCurrentRegistryPath()
      _, _, key_path = key.partition(u'\\')
      registry_key = loaded_hive.GetKeyByPath(u'{0:s}\\{1:s}'.format(
          current_path, key_path))
    elif key.startswith(u'..'):
      parent_path, _, _ = loaded_hive.GetCurrentRegistryPath().rpartition(u'\\')
      # We know the path starts with a "..".
      if len(key) == 2:
        key_path = u''
      else:
        key_path = key[3:]
      if parent_path:
        if key_path:
          path = u'{0:s}\\{1:s}'.format(parent_path, key_path)
        else:
          path = parent_path
        registry_key = loaded_hive.GetKeyByPath(path)
      else:
        registry_key = loaded_hive.GetKeyByPath(u'\\{0:s}'.format(key_path))

    else:
      # Check if key is not set at all, then assume traversal from root.
      if not loaded_hive.GetCurrentRegistryPath():
        _ = loaded_hive.GetKeyByPath(u'\\')

      current_key = loaded_hive.GetCurrentRegistryKey()
      if current_key.name == loaded_hive.root_key.name:
        key_path = u'\\{0:s}'.format(key)
      else:
        key_path = u'{0:s}\\{1:s}'.format(current_key.path, key)
      registry_key = loaded_hive.GetKeyByPath(key_path)

    if registry_key:
      if key_path == '\\':
        path = '\\'
      else:
        path = registry_key.path

      ConsoleConfig.SetPrompt(
          hive_path=loaded_hive.path,
          prepend_string=StripCurlyBrace(path).replace('\\', '\\\\'))
    else:
      print u'Unable to change to: {0:s}'.format(key_path)

  @magic.line_magic('hive')
  def HiveActions(self, line):
    """Define the hive command on the console prompt."""
    if line.startswith('list'):
      print PregCache.hive_storage.ListHives()

      print u''
      print u'To open a hive, use: hive_open INDEX'
    elif line.startswith('open ') or line.startswith('load '):
      PregCache.hive_storage.SetOpenHive(line[5:])
      hive_helper = PregCache.hive_storage.loaded_hive
      print u'Opening hive: {0:s} [{1:s}]'.format(
          hive_helper.path, hive_helper.collector_name)
      ConsoleConfig.SetPrompt(hive_path=hive_helper.path)
    elif line.startswith('scan'):
      items = line.split()
      if len(items) < 2:
        print (
            u'Unable to scan for an empty keyword. Please specify a keyword, '
            u'eg: NTUSER, SOFTWARE, etc')
        return

      PregCache.hive_storage.Scan(items[1:])

  @magic.line_magic('ls')
  def ListDirectoryContent(self, line):
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
    current_hive = PregCache.hive_storage.loaded_hive
    if not current_hive:
      return

    current_key = current_hive.GetCurrentRegistryKey()
    for key in current_key.GetSubkeys():
      # TODO: move this construction into a separate function in OutputWriter.
      timestamp, _, _ = frontend_utils.OutputWriter.GetDateTimeString(
          key.last_written_timestamp).partition('.')

      sub.append((u'{0:>19s} {1:>15s}  {2:s}'.format(
          timestamp.replace('T', ' '), '[KEY]',
          key.name), True))

    for value in current_key.GetValues():
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
        self.output_writer.write(u'dr-xr-xr-x {0:s}\n'.format(entry))
      else:
        self.output_writer.write(u'-r-xr-xr-x {0:s}\n'.format(entry))

  @magic.line_magic('parse')
  def ParseCurrentKey(self, line):
    """Parse the current key."""
    if 'true' in line.lower():
      verbose = True
    elif '-v' in line.lower():
      verbose = True
    else:
      verbose = False

    if not IsLoaded():
      return

    current_hive = PregCache.hive_storage.loaded_hive
    if not current_hive:
      return

    # Clear the last results from parse key.
    PregCache.events_from_last_parse = []

    print_strings = ParseKey(
        key=current_hive.GetCurrentRegistryKey(), hive_helper=current_hive,
        shell_helper=PregCache.shell_helper, verbose=verbose)
    self.output_writer.write(u'\n'.join(print_strings))

    # Print out a hex dump of all binary values.
    if verbose:
      header_shown = False
      for value in current_hive.GetCurrentRegistryKey().GetValues():
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

  @magic.line_magic('plugin')
  def ParseWithPlugin(self, line):
    """Parse a Registry key using a specific plugin."""
    if not IsLoaded():
      print u'No hive loaded, unable to parse.'
      return

    current_hive = PregCache.hive_storage.loaded_hive
    if not current_hive:
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

    hive_type = current_hive.type
    plugins_list = parsers_manager.ParsersManager.GetWindowsRegistryPlugins()
    plugin_found = False
    for plugin_cls in plugins_list.GetKeyPlugins(hive_type):
      plugin = plugin_cls(reg_cache=current_hive.reg_cache)
      if plugin.plugin_name == plugin_name:
        # If we found the correct plugin.
        plugin_found = True
        break

    if not plugin_found:
      print u'No plugin named: {0:s} available for Registry type {1:s}'.format(
          plugin_name, hive_type)
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

    if not plugin.expanded_keys:
      plugin.ExpandKeys(PregCache.parser_context)

    # Clear the last results from parse key.
    PregCache.events_from_last_parse = []

    # Defining outside of for loop for optimization.
    get_key_by_path = current_hive.GetKeyByPath
    for registry_key in plugin.expanded_keys:
      key = get_key_by_path(registry_key)
      if not key:
        print u'Key: {0:s} not found'.format(registry_key)
        continue

      # Move the current location to the key to be parsed.
      self.ChangeDirectory(registry_key)
      # Parse the key.
      print_strings = ParseKey(
          key=current_hive.GetCurrentRegistryKey(), hive_helper=current_hive,
          shell_helper=PregCache.shell_helper, verbose=False,
          use_plugins=[plugin_name])
      self.output_writer.write(u'\n'.join(print_strings))
    self.output_writer.flush()

  @magic.line_magic('pwd')
  def PrintCurrentWorkingDirectory(self, unused_line):
    """Print the current path."""
    if not IsLoaded():
      return

    current_hive = PregCache.hive_storage.loaded_hive
    if not current_hive:
      return

    self.output_writer.write(u'{0:s}\n'.format(
        current_hive.GetCurrentRegistryPath()))

  @magic.line_magic('redirect_output')
  def RedirectOutput(self, output_object):
    """Change the output writer to redirect plugin output to a file."""

    if isinstance(output_object, basestring):
      output_object = open(output_object, 'wb')

    if hasattr(output_object, 'write'):
      self.output_writer = output_object


def StripCurlyBrace(string):
  """Return a format "safe" string."""
  return string.replace('}', '}}').replace('{', '{{')


def IsLoaded():
  """Checks if a Windows Registry Hive is loaded."""
  current_hive = PregCache.hive_storage.loaded_hive
  if not current_hive:
    return False

  current_key = current_hive.GetCurrentRegistryKey()
  if hasattr(current_key, 'path'):
    return True

  if current_hive.name != 'N/A':
    return True

  print (
      u'No hive loaded, cannot complete action. Use "hive list" '
      u'and "hive open" to load a hive.')
  return False


def GetValue(value_name):
  """Return a value object from the currently loaded Registry key.

  Args:
    value_name: A string containing the name of the value to be retrieved.

  Returns:
    The Registry value (instance of WinPyregfValue) if it exists, None if
    either there is no currently loaded Registry key or if the value does
    not exist.
  """
  current_hive = PregCache.hive_storage.loaded_hive
  current_key = current_hive.GetCurrentRegistryKey()

  if not current_key:
    return

  return current_key.GetValue(value_name)


def GetValueData(value_name):
  """Return the value data from a value in the currently loaded Registry key.

  Args:
    value_name: A string containing the name of the value to be retrieved.

  Returns:
    The data from a Registry value if it exists, None if either there is no
    currently loaded Registry key or if the value does not exist.
  """
  value = GetValue(value_name)

  if not value:
    return

  return value.data


def GetCurrentKey():
  """Return the currently loaded Registry key (instance of WinPyregfKey).

  Returns:
    The currently loaded Registry key (instance of WinPyregfKey) or None
    if there is no loaded key.
  """
  current_hive = PregCache.hive_storage.loaded_hive
  return current_hive.GetCurrentRegistryKey()


def GetFormatString(event_object):
  """Return back a format string that can be used for a given event object."""
  # Assign a default value to font align length.
  align_length = 15

  # Go through the attributes and see if there is an attribute
  # value that is longer than the default font align length, and adjust
  # it accordingly if found.
  if hasattr(event_object, 'regvalue'):
    attributes = event_object.regvalue.keys()
  else:
    attributes = event_object.GetAttributes().difference(
        event_object.COMPARE_EXCLUDE)

  for attribute in attributes:
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
  if hasattr(event_object, 'keyname'):
    ret_strings.append(format_string.format(u'Key Path', event_object.keyname))
  if event_object.timestamp_desc != eventdata.EventTimestamp.WRITTEN_TIME:
    ret_strings.append(format_string.format(
        u'Description', event_object.timestamp_desc))

  ret_strings.append(frontend_utils.FormatHeader(u'Data', u'-'))

  return ret_strings


def GetEventBody(event_object, file_entry=None, show_hex=False):
  """Returns a list of strings containing information from an event.

  Args:
    event_object: An event object (instance of event.EventObject).
    file_entry: An optional file entry object (instance of dfvfs.FileEntry) that
                the event originated from. Default is None.
    show_hex: A boolean, if set to True hex dump of the value is included in
              the output. The default value is False.

  Returns:
    A list of strings containing the event body.
  """
  format_string = GetFormatString(event_object)

  ret_strings = []

  timestamp_description = getattr(
      event_object, 'timestamp_desc', eventdata.EventTimestamp.WRITTEN_TIME)

  if timestamp_description != eventdata.EventTimestamp.WRITTEN_TIME:
    ret_strings.append(u'<{0:s}>'.format(timestamp_description))

  if hasattr(event_object, 'regvalue'):
    attributes = event_object.regvalue
  else:
    # TODO: Add a function for this to avoid repeating code.
    keys = event_object.GetAttributes().difference(
        event_object.COMPARE_EXCLUDE)
    keys.discard('offset')
    keys.discard('timestamp_desc')
    attributes = {}
    for key in keys:
      attributes[key] = getattr(event_object, key)

  for attribute, value in attributes.items():
    ret_strings.append(format_string.format(attribute, value))

  if show_hex and file_entry:
    event_object.pathspec = file_entry.path_spec
    ret_strings.append(frontend_utils.FormatHeader(
        u'Hex Output From Event.', '-'))
    ret_strings.append(
        frontend_utils.OutputWriter.GetEventDataHexDump(event_object))

  return ret_strings


def GetRangeForAllLoadedHives():
  """Return a range or a list of all loaded hives."""
  return range(0, GetTotalNumberOfLoadedHives())


def GetTotalNumberOfLoadedHives():
  """Return the total number of Registy hives that are loaded."""
  return len(PregCache.hive_storage)


def ParseKey(key, shell_helper, hive_helper, verbose=False, use_plugins=None):
  """Parse a single Registry key and return parsed information.

  Parses the Registry key either using the supplied plugin or trying against
  all avilable plugins.

  Args:
    key: The Registry key to parse, WinRegKey object or a string.
    shell_helper: A shell helper object (instance of PregHelper).
    hive_helper: A hive object (instance of PregHiveHelper).
    verbose: Print additional information, such as a hex dump.
    use_plugins: A list of plugin names to use, or none if all should be used.

  Returns:
    A list of strings.
  """
  print_strings = []
  if not hive_helper:
    return

  if isinstance(key, basestring):
    key = hive_helper.GetKeyByPath(key)

  if not key:
    return

  # Detect Registry type.
  registry_type = hive_helper.type

  plugins = {}
  plugins_list = parsers_manager.ParsersManager.GetWindowsRegistryPlugins()

  # Compile a list of plugins we are about to use.
  for weight in plugins_list.GetWeights():
    plugin_list = plugins_list.GetWeightPlugins(weight, registry_type)
    plugins[weight] = []
    for plugin in plugin_list:
      if use_plugins:
        plugin_obj = plugin(reg_cache=hive_helper.reg_cache)
        if plugin_obj.NAME in use_plugins:
          plugins[weight].append(plugin_obj)
      else:
        plugins[weight].append(plugin(
            reg_cache=hive_helper.reg_cache))

  event_queue = single_process.SingleProcessQueue()
  event_queue_consumer = PregEventObjectQueueConsumer(event_queue)

  # Build a parser context.
  parser_context = shell_helper.BuildParserContext(event_queue)

  # Run all the plugins in the correct order of weight.
  for weight in plugins:
    for plugin in plugins[weight]:
      plugin.Process(parser_context, key=key)
      event_queue_consumer.ConsumeEventObjects()
      if not event_queue_consumer.event_objects:
        continue

      print_strings.append(u'')
      print_strings.append(
          u'{0:^80}'.format(u' ** Plugin : {0:s} **'.format(
              plugin.plugin_name)))
      print_strings.append(u'')
      print_strings.append(u'[{0:s}] {1:s}'.format(
          plugin.REG_TYPE, plugin.DESCRIPTION))
      print_strings.append(u'')
      if plugin.URLS:
        print_strings.append(u'Additional information can be found here:')

        for url in plugin.URLS:
          print_strings.append(u'{0:>17s} {1:s}'.format(u'URL :', url))
        print_strings.append(u'')

      # TODO: move into the event queue consumer.
      event_objects_and_timestamps = {}
      event_object = event_queue_consumer.event_objects.pop(0)
      while event_object:
        PregCache.events_from_last_parse.append(event_object)
        event_objects_and_timestamps.setdefault(
            event_object.timestamp, []).append(event_object)

        if event_queue_consumer.event_objects:
          event_object = event_queue_consumer.event_objects.pop(0)
        else:
          event_object = None

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
          print_strings.extend(GetEventBody(
              event_object, hive_helper.file_entry, verbose))

      print_strings.append(u'')

  # Printing '*' 80 times.
  print_strings.append(u'*'*80)
  print_strings.append(u'')

  return print_strings


def RunModeConsole(front_end, options):
  """Open up an iPython console.

  Args:
    options: the command line arguments (instance of argparse.Namespace).
  """
  namespace = {}

  function_name_length = 23
  banners = []
  banners.append(frontend_utils.FormatHeader(
      u'Welcome to PREG - home of the Plaso Windows Registry Parsing.'))
  banners.append(u'')
  banners.append(u'Some of the commands that are available for use are:')
  banners.append(u'')
  banners.append(frontend_utils.FormatOutputString(
      u'cd key', u'Navigate the Registry like a directory structure.',
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      u'ls [-v]', (
          u'List all subkeys and values of a Registry key. If called as '
          u'ls True then values of keys will be included in the output.'),
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      u'parse -[v]', u'Parse the current key using all plugins.',
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      u'pwd', u'Print the working "directory" or the path of the current key.',
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      u'plugin [-h] plugin_name', (
          u'Run a particular key-based plugin on the loaded hive. The correct '
          u'Registry key will be loaded, opened and then parsed.'),
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      u'get_value value_name', (
          u'Get a value from the currently loaded Registry key.')))
  banners.append(frontend_utils.FormatOutputString(
      u'get_value_data value_name', (
          u'Get a value data from a value stored in the currently loaded '
          u'Registry key.')))
  banners.append(frontend_utils.FormatOutputString(
      u'get_key', u'Return the currently loaded Registry key.'))

  banners.append(u'')

  # Build the global cache and prepare the tool.
  hive_storage = PregStorage()
  shell_helper = PregHelper(options, front_end, hive_storage)
  parser_context = shell_helper.BuildParserContext()

  PregCache.parser_context = parser_context
  PregCache.shell_helper = shell_helper
  PregCache.hive_storage = hive_storage

  registry_types = getattr(options, 'regfile', None)
  if isinstance(registry_types, basestring):
    registry_types = registry_types.split(u',')

  if not registry_types:
    registry_types = ['NTUSER', 'SOFTWARE', 'SYSTEM', 'SAM', 'SECURITY']
  PregCache.shell_helper.Scan(registry_types)

  if len(PregCache.hive_storage) == 1:
    PregCache.hive_storage.SetOpenHive(0)
    hive_helper = PregCache.hive_storage.loaded_hive
    banners.append(
        u'Opening hive: {0:s} [{1:s}]'.format(
            hive_helper.path, hive_helper.collector_name))
    ConsoleConfig.SetPrompt(hive_path=hive_helper.path)

  loaded_hive = PregCache.hive_storage.loaded_hive

  if loaded_hive and loaded_hive.name != u'N/A':
    banners.append(
        u'Registry hive: {0:s} is available and loaded.'.format(
            loaded_hive.name))
  else:
    banners.append(u'More than one Registry file ready for use.')
    banners.append(u'')
    banners.append(PregCache.hive_storage.ListHives())
    banners.append(u'')
    banners.append((
        u'Use "hive open INDEX" to load a hive and "hive list" to see a '
        u'list of available hives.'))

  banners.append(u'')
  banners.append(u'Happy command line console fu-ing.')

  # Adding variables in scope.
  namespace.update(globals())
  namespace.update({
      'get_current_key': GetCurrentKey,
      'get_key': GetCurrentKey,
      'get_value': GetValue,
      'get_value_data': GetValueData,
      'number_of_hives': GetTotalNumberOfLoadedHives,
      'range_of_hives': GetRangeForAllLoadedHives,
      'options': options})

  ipshell_config = ConsoleConfig.GetConfig()
  if loaded_hive:
    ConsoleConfig.SetPrompt(
        hive_path=loaded_hive.name, config=ipshell_config)
  else:
    ConsoleConfig.SetPrompt(hive_path=u'NO HIVE LOADED', config=ipshell_config)

  # Starting the shell.
  ipshell = InteractiveShellEmbed(
      user_ns=namespace, config=ipshell_config, banner1=u'\n'.join(banners),
      exit_msg='')
  ipshell.confirm_exit = False
  # Adding "magic" functions.
  ipshell.register_magics(MyMagics)
  # Set autocall to two, making parenthesis not necessary when calling
  # function names (although they can be used and are necessary sometimes,
  # like in variable assignements, etc).
  ipshell.autocall = 2
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
preg is a simple Windows Registry parser using the plaso Registry
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
      '-p', '--plugins', dest='plugin_names', action='append', default=[],
      type=unicode, metavar='PLUGIN_NAME',
      help=(
          u'Substring match of the Registry plugin to be used, this'
          u'parameter can be repeated to create a list of plugins to be '
          u'run against, eg: "-p userassist -p rdp" or "-p userassist".'))

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

  if options.info:
    print front_end.GetListOfAllPlugins()
    return True

  try:
    front_end.ParseOptions(options, source_option='image')
  except errors.BadConfigOption as exception:
    arg_parser.print_help()
    print u''
    logging.error('{0:s}'.format(exception))
    return False

  # Run the tool, using the run mode according to the options passed
  # to the tool.
  if options.console:
    RunModeConsole(front_end, options)
  # TODO: merge the following run functions.
  elif options.key and options.regfile:
    front_end.RunModeRegistryKey(options, options.plugin_names)
  elif options.plugin_names:
    front_end.RunModeRegistryPlugin(options, options.plugin_names)
  elif options.regfile:
    front_end.RunModeRegistryFile(options, options.regfile)
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
