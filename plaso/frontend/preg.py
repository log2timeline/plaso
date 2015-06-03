# -*- coding: utf-8 -*-
"""The preg front-end."""

import logging

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import knowledge_base
from plaso.engine import queue

# Import the winreg formatter to register it, adding the option
# to print event objects using the default formatter.
# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter

from plaso.frontend import extraction_frontend
from plaso.frontend import frontend
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import manager as parsers_manager
from plaso.parsers import winreg as winreg_parser
from plaso.parsers import winreg_plugins    # pylint: disable=unused-import
from plaso.preprocessors import interface as preprocess_interface
from plaso.preprocessors import manager as preprocess_manager
from plaso.winreg import cache
from plaso.winreg import path_expander as winreg_path_expander
from plaso.winreg import winregistry


# TODO: refactor this to be an instance not a singleton.
class PregCache(object):
  """Cache storage used for iPython and other aspects of preg."""

  events_from_last_parse = []

  knowledge_base_object = knowledge_base.KnowledgeBase()

  # Parser mediator, used when parsing Registry keys.
  parser_mediator = None

  hive_storage = None
  shell_helper = None

  @classmethod
  def GetLoadedHive(cls):
    """Retrieves the loaded hive.

    Returns:
      The loaded hive (an instance of TODO).
    """
    return cls.hive_storage.loaded_hive


class PregItemQueueConsumer(queue.ItemQueueConsumer):
  """Class that implements a list event object queue consumer."""

  def __init__(self, event_queue):
    """Initializes the list event object queue consumer.

    Args:
      event_queue: the event object queue (instance of Queue).
    """
    super(PregItemQueueConsumer, self).__init__(event_queue)
    self.event_objects = []

  def _ConsumeItem(self, event_object, **unused_kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self.event_objects.append(event_object)


class PregFrontend(extraction_frontend.ExtractionFrontend):
  """Class that implements the preg front-end."""

  def __init__(self):
    """Initializes the front-end object."""
    super(PregFrontend, self).__init__()
    self._parse_restore_points = False
    self._registry_plugin_list = (
        parsers_manager.ParsersManager.GetWindowsRegistryPlugins())

  def GetWindowsRegistryPlugins(self):
    """Build a list of all available Windows Registry plugins.

    Returns:
      A plugins list (instance of PluginList).
    """
    return self._registry_plugin_list

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

    # The path is split in segments to make it path segment separator
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

  def _GetRegistryTypes(self, plugin_name):
    """Retrieves the Windows Registry types based on a filter string.

    Args:
      plugin_name: string containing the name of the plugin or an empty
                   string for all the types.

    Returns:
      A list of Windows Registry types.
    """
    types = []
    for plugin in self.GetRegistryPlugins(plugin_name):
      for key_plugin_class in self._registry_plugin_list.GetAllKeyPlugins():
        if plugin == key_plugin_class.NAME:
          if key_plugin_class.REG_TYPE not in types:
            types.append(key_plugin_class.REG_TYPE)
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

    vss_stores = self.vss_stores

    if not vss_stores:
      return searchers

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

  def ExpandKeysRedirect(self, keys):
    """Expands a list of Registry key paths with their redirect equivalents.

    Args:
      keys: a list of Windows Registry key paths.
    """
    for key in keys:
      if key.startswith('\\Software') and 'Wow6432Node' not in key:
        _, first, second = key.partition('\\Software')
        keys.append(u'{0:s}\\Wow6432Node{1:s}'.format(first, second))

  def GetRegistryFilePaths(self, plugin_name=None, registry_type=None):
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

      elif reg_type == 'USRCLASS':
        paths.append('/Users/.+/AppData/Local/Microsoft/Windows/UsrClass.dat')

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

  def GetRegistryKeysFromHive(self, hive_helper, parser_mediator):
    """Retrieves a list of all key plugins for a given Registry type.

    Args:
      hive_helper: A hive object (instance of PregHiveHelper).
      parser_mediator: A parser mediator object (instance of ParserMediator).

    Returns:
      A list of Windows Registry keys.
    """
    keys = []
    if not hive_helper:
      return
    for key_plugin_class in self._registry_plugin_list.GetAllKeyPlugins():
      temp_obj = key_plugin_class(reg_cache=hive_helper.reg_cache)
      if temp_obj.REG_TYPE == hive_helper.type:
        temp_obj.ExpandKeys(parser_mediator)
        keys.extend(temp_obj.expanded_keys)

    return keys

  def GetRegistryPlugins(self, plugin_name):
    """Retrieves the Windows Registry plugins based on a filter string.

    Args:
      plugin_name: string containing the name of the plugin or an empty
                   string for all the plugins.

    Returns:
      A list of Windows Registry plugins.
    """
    key_plugin_names = [
        plugin.NAME for plugin in self._registry_plugin_list.GetAllKeyPlugins()]

    if not plugin_name:
      return key_plugin_names

    plugin_name = plugin_name.lower()

    plugins_to_run = []
    for key_plugin in key_plugin_names:
      if plugin_name in key_plugin.lower():
        plugins_to_run.append(key_plugin)

    return plugins_to_run

  def GetRegistryPluginsFromRegistryType(self, hive_type):
    """Retrieves the Windows Registry plugins based on a hive type.

    Args:
      hive_type: string containing the hive type.

    Returns:
      A list of Windows Registry plugins.
    """
    key_plugins = {}
    for plugin in self._registry_plugin_list.GetAllKeyPlugins():
      key_plugins[plugin.NAME.lower()] = plugin.REG_TYPE.lower()

    if not hive_type:
      return key_plugins.values()

    hive_type = hive_type.lower()

    plugins_to_run = []
    for key_plugin_name, key_plugin_type in key_plugins.iteritems():
      if hive_type == key_plugin_type:
        plugins_to_run.append(key_plugin_name)
      elif key_plugin_type == 'any':
        plugins_to_run.append(key_plugin_name)

    return plugins_to_run


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
      u'USRCLASS': (
          '\\Local Settings\\Software\\Microsoft\\Windows\\CurrentVersion',),
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
    if not isinstance(hive_helpers, (list, tuple)):
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
