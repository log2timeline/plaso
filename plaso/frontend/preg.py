# -*- coding: utf-8 -*-
"""The preg front-end."""

import logging

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.dfwinreg import definitions as dfwinreg_definitions
from plaso.dfwinreg import registry as dfwinreg_registry
from plaso.engine import queue
from plaso.engine import single_process
from plaso.frontend import extraction_frontend
from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import manager as parsers_manager
from plaso.parsers import winreg_plugins    # pylint: disable=unused-import
from plaso.preprocessors import manager as preprocess_manager


class PregItemQueueConsumer(queue.ItemQueueConsumer):
  """Class that implements a list event object queue consumer."""

  def __init__(self, event_queue):
    """Initializes the list event object queue consumer.

    Args:
      event_queue: the event object queue (instance of Queue).
    """
    super(PregItemQueueConsumer, self).__init__(event_queue)
    self._event_objects = []

  def _ConsumeItem(self, event_object, **unused_kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self._event_objects.append(event_object)

  def GetItems(self):
    """Retrieves the consumed event objects.

    Yields:
      Event objects (instance of EventObject)
    """
    if not self._event_objects:
      raise StopIteration

    event_object = self._event_objects.pop(0)
    while event_object:
      yield event_object
      if not self._event_objects:
        break
      event_object = self._event_objects.pop(0)


class PregFrontend(extraction_frontend.ExtractionFrontend):
  """Class that implements the preg front-end.

  Attributes:
    knowledge_base_object: the knowledge base object (instance
                           of KnowledgeBase).
  """

  def __init__(self):
    """Initializes the front-end object."""
    super(PregFrontend, self).__init__()
    self._mount_path_spec = None
    self._parse_restore_points = False
    self._preprocess_completed = False
    self._registry_files = []
    self._registry_plugin_list = (
        parsers_manager.ParsersManager.GetWindowsRegistryPlugins())
    self._searcher = None
    self._single_file = False
    self._source_path = None
    self._source_path_specs = []

    self.knowledge_base_object = None

  @property
  def registry_plugin_list(self):
    """The Windows Registry plugin list (instance of PluginList)."""
    return self._registry_plugin_list

  # TODO: clean up this function as part of dfvfs find integration.
  def _FindRegistryPaths(self, searcher, pattern):
    """Return a list of Windows Registry file path specifications.

    Args:
      searcher: the file system searcher object (instance of
                dfvfs.FileSystemSearcher).
      pattern: the pattern to find.

    Returns:
      A list of path specification objects (instance of PathSpec).
    """
    # TODO: optimize this in one find.
    registry_file_paths = []
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
      return registry_file_paths

    for path_spec in path_specs:
      directory_location = getattr(path_spec, u'location', None)
      if not directory_location:
        raise errors.PreProcessFail(
            u'Missing directory location for: {0:s}'.format(file_path))

      # The path is split in segments to make it path segment separator
      # independent (and thus platform independent).
      path_segments = searcher.SplitPath(directory_location)
      path_segments.append(file_name)

      # Remove mount part if OS mount path is set.
      # TODO: Instead of using an absolute path spec, use a mount point one.
      if self._mount_path_spec:
        mount_point_location = getattr(self._mount_path_spec, u'location', u'')
        mount_point_segments = mount_point_location.split(u'/')
        if not mount_point_segments[0]:
          mount_point_segments = mount_point_segments[1:]

        remove_mount_point = True
        for index in range(0, len(mount_point_segments)):
          mount_point_segment = mount_point_segments[index]
          if mount_point_segment != path_segments[index]:
            remove_mount_point = False
        if remove_mount_point:
          path_segments = path_segments[len(mount_point_segments):]

      find_spec = file_system_searcher.FindSpec(
          location_regex=path_segments, case_sensitive=False)
      fh_path_specs = list(searcher.Find(find_specs=[find_spec]))

      if not fh_path_specs:
        logging.debug(u'File: {0:s} not found in directory: {1:s}'.format(
            file_name, directory_location))
        continue

      registry_file_paths.extend(fh_path_specs)

    return registry_file_paths

  def _GetRegistryHelperFromPath(self, path, codepage):
    """Return a Registry helper object from a path.

    Given a path to a Registry file this function goes through
    all the discovered source path specifications (instance of PathSpec)
    and extracts Registry helper objects based on the supplied
    path.

    Args:
      path: the path filter to a Registry file.
      codepage: the codepage used for the Registry file. The default is cp1252.

    Yields:
      A Registry helper object (instance of PregRegistryHelper).
    """
    for source_path_spec in self._source_path_specs:
      type_indicator = source_path_spec.TYPE_INDICATOR
      if type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(source_path_spec)
        if file_entry.IsFile():
          yield PregRegistryHelper(
              file_entry=file_entry, collector_name=u'OS', codepage=codepage)
          continue
        # TODO: Change this into an actual mount point path spec.
        self._mount_path_spec = source_path_spec

      collector_name = type_indicator
      parent_path_spec = getattr(source_path_spec, u'parent', None)
      if parent_path_spec:
        parent_type_indicator = parent_path_spec.TYPE_INDICATOR
        if parent_type_indicator == dfvfs_definitions.TYPE_INDICATOR_VSHADOW:
          vss_store = getattr(parent_path_spec, u'store_index', 0)
          collector_name = u'VSS Store: {0:d}'.format(vss_store)

      searcher = self._GetSearcher()
      for registry_file_path in self._FindRegistryPaths(searcher, path):
        file_entry = searcher.GetFileEntryByPathSpec(registry_file_path)
        yield PregRegistryHelper(
            file_entry=file_entry, collector_name=collector_name,
            codepage=codepage)

  def _GetRegistryTypes(self, plugin_name):
    """Retrieves the Windows Registry types based on a filter string.

    Args:
      plugin_name: string containing the name of the plugin or an empty
                   string for all types.

    Returns:
      A list of Windows Registry types.
    """
    types = set()
    for plugin in self.GetRegistryPlugins(plugin_name):
      for key_plugin_class in self._registry_plugin_list.GetAllKeyPlugins():
        if plugin.NAME == key_plugin_class.NAME:
          types.add(key_plugin_class.REG_TYPE)
          break

    return list(types)

  def _GetRegistryTypesFromPlugins(self, plugin_names):
    """Return a list of Registry types extracted from a list of plugin names.

    Args:
      plugin_names: a list of plugin names.

    Returns:
      A list of Registry types extracted from the supplied plugins.
    """
    if not plugin_names:
      return []

    plugins_list = self._registry_plugin_list
    registry_types = set()

    for plugin_name in plugin_names:
      for plugin_class in plugins_list.GetAllKeyPlugins():
        if plugin_name == plugin_class.NAME.lower():
          # If a plugin is available for every Registry type
          # we need to make sure all Registry files are included.
          if plugin_class.REG_TYPE == u'any':
            registry_types.extend(dfwinreg_definitions.REGISTRY_TYPES)

          else:
            registry_types.add(plugin_class.REG_TYPE)

    return list(registry_types)

  def _GetSearcher(self):
    """Retrieve a searcher for the first source path specification.

    Returns:
      A file system searcher object (instance of dfvfs.FileSystemSearcher)
      for the first discovered source path specification, or None if there are
      no discovered source path specifications.
    """
    if not self._source_path_specs:
      return

    if self._searcher:
      return self._searcher

    file_system, mount_point = self._GetSourceFileSystem(
        self._source_path_specs[0])
    self._searcher = file_system_searcher.FileSystemSearcher(
        file_system, mount_point)

    # TODO: close file_system after usage.
    return self._searcher

  # TODO: refactor, this is a duplicate of the function in engine.
  def _GetSourceFileSystem(self, source_path_spec, resolver_context=None):
    """Retrieves the file system of the source.

    The mount point path specification refers to either a directory or
    a volume on storage media device or image. It is needed by the dfVFS
    file system searcher (instance of FileSystemSearcher) to indicate
    the base location of the file system.

    Args:
      source_path_spec: The source path specification (instance of
                        dfvfs.PathSpec) of the file system.
      resolver_context: Optional resolver context (instance of dfvfs.Context).
                        The default is None. Note that every thread or process
                        must have its own resolver context.

    Returns:
      A tuple of the file system (instance of dfvfs.FileSystem) and
      the mount point path specification (instance of path.PathSpec).

    Raises:
      RuntimeError: if source path specification is not set.
    """
    if not source_path_spec:
      raise RuntimeError(u'Missing source.')

    file_system = path_spec_resolver.Resolver.OpenFileSystem(
        source_path_spec, resolver_context=resolver_context)

    type_indicator = source_path_spec.type_indicator
    if path_spec_factory.Factory.IsSystemLevelTypeIndicator(type_indicator):
      mount_point = source_path_spec
    else:
      mount_point = source_path_spec.parent

    return file_system, mount_point

  def CreateParserMediator(self, event_queue=None):
    """Create a parser mediator object.

    Args:
      event_queue: an optional event queue object (instance of Queue).
                   The default is None.

    Returns:
      A parser mediator object (instance of parsers_mediator.ParserMediator).
    """
    if event_queue is None:
      event_queue = single_process.SingleProcessQueue()
    event_queue_producer = queue.ItemQueueProducer(event_queue)

    parse_error_queue = single_process.SingleProcessQueue()
    parse_error_queue_producer = queue.ItemQueueProducer(parse_error_queue)

    return parsers_mediator.ParserMediator(
        event_queue_producer, parse_error_queue_producer,
        self.knowledge_base_object)

  def ExpandKeysRedirect(self, keys):
    """Expands a list of Registry key paths with their redirect equivalents.

    Args:
      keys: a list of Windows Registry key paths.
    """
    for key in keys:
      if key.startswith(u'\\Software') and u'Wow6432Node' not in key:
        _, first, second = key.partition(u'\\Software')
        keys.append(u'{0:s}\\Wow6432Node{1:s}'.format(first, second))

  def GetRegistryFilePaths(self, plugin_name=None, registry_type=None):
    """Returns a list of Registry paths from a configuration object.

    Args:
      plugin_name: optional string containing the name of the plugin or an empty
                   string or None for all the types. The default is None.
      registry_type: optional Registry type string. The default is None.

    Returns:
      A list of path names for Registry files.
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
      if reg_type == dfwinreg_definitions.REGISTRY_TYPE_NTUSER:
        paths.append(u'/Documents And Settings/.+/NTUSER.DAT')
        paths.append(u'/Users/.+/NTUSER.DAT')
        if restore_path:
          paths.append(u'{0:s}/_REGISTRY_USER_NTUSER.+'.format(restore_path))

      elif reg_type == dfwinreg_definitions.REGISTRY_TYPE_SAM:
        paths.append(u'{sysregistry}/SAM')
        if restore_path:
          paths.append(u'{0:s}/_REGISTRY_MACHINE_SAM'.format(restore_path))

      elif reg_type == dfwinreg_definitions.REGISTRY_TYPE_SECURITY:
        paths.append(u'{sysregistry}/SECURITY')
        if restore_path:
          paths.append(u'{0:s}/_REGISTRY_MACHINE_SECURITY'.format(restore_path))

      elif reg_type == dfwinreg_definitions.REGISTRY_TYPE_SOFTWARE:
        paths.append(u'{sysregistry}/SOFTWARE')
        if restore_path:
          paths.append(u'{0:s}/_REGISTRY_MACHINE_SOFTWARE'.format(restore_path))

      elif reg_type == dfwinreg_definitions.REGISTRY_TYPE_SYSTEM:
        paths.append(u'{sysregistry}/SYSTEM')
        if restore_path:
          paths.append(u'{0:s}/_REGISTRY_MACHINE_SYSTEM'.format(restore_path))

      elif reg_type == dfwinreg_definitions.REGISTRY_TYPE_USRCLASS:
        paths.append(u'/Users/.+/AppData/Local/Microsoft/Windows/UsrClass.dat')

    # Expand all the paths.
    win_registry = dfwinreg_registry.WinRegistry()

    # TODO: deprecate usage of pre_obj.
    path_attributes = self.knowledge_base_object.pre_obj.__dict__

    expanded_key_paths = []
    for key_path in paths:
      try:
        expanded_key_path = win_registry.ExpandKeyPath(
            key_path, path_attributes)
        expanded_key_paths.append(expanded_key_path)

      except KeyError as exception:
        logging.error(
            u'Unable to expand key path: {0:s} with error: {1:s}'.format(
                key_path, exception))

    return expanded_key_paths

  def GetRegistryHelpers(
      self, registry_types=None, plugin_names=None, codepage=u'cp1252'):
    """Returns a list of discovered Registry helpers.

    Args:
      registry_types: optional list of Registry types, eg: NTUSER, SAM, etc
                      that should be included. The default is None.
      plugin_names: optional list of strings containing the name of the
                    plugin(s) or an empty string for all the types. The default
                    is None.
      codepage: the codepage used for the Registry file. The default is cp1252.

    Returns:
      A list of Registry helper objects (instance of PregRegistryHelper).

    Raises:
      ValueError: If neither registry_types nor plugin name is passed
                  as a parameter.
    """
    if registry_types is None and plugin_names is None:
      raise ValueError(
          u'Missing Registry_types or plugin_name value.')

    if plugin_names is None:
      plugin_names = []
    else:
      plugin_names = [plugin_name.lower() for plugin_name in plugin_names]

    # TODO: use non-preprocess collector with filter to collect Registry files.
    if not self._single_file and not self._preprocess_completed:
      file_system, mount_point = self._GetSourceFileSystem(
          self._source_path_specs[0])
      preprocess_manager.PreprocessPluginsManager.RunPlugins(
          u'Windows', file_system, mount_point, self.knowledge_base_object)
      self._preprocess_completed = True
      file_system.Close()

    if registry_types is None:
      registry_types = []

    types_from_plugins = self._GetRegistryTypesFromPlugins(plugin_names)
    registry_types.extend(types_from_plugins)

    paths = []
    if self._single_file:
      paths = [self._source_path]
    elif registry_types:
      for registry_type in registry_types:
        paths.extend(self.GetRegistryFilePaths(
            registry_type=registry_type.upper()))
    else:
      for plugin_name in plugin_names:
        paths.extend(self.GetRegistryFilePaths(plugin_name=plugin_name))

    self.knowledge_base_object.SetDefaultCodepage(codepage)
    registry_helpers = []

    for path in paths:
      registry_helpers.extend([
          helper for helper in self._GetRegistryHelperFromPath(path, codepage)])
    return registry_helpers

  def GetRegistryPlugins(self, plugin_name):
    """Retrieves the Windows Registry plugins based on a filter string.

    Args:
      plugin_name: string containing the name of the plugin or an empty
                   string for all the plugins.

    Returns:
      A list of Windows Registry plugins (instance of RegistryPlugin).
    """
    key_plugins = {}
    for plugin in self._registry_plugin_list.GetAllKeyPlugins():
      key_plugins[plugin.NAME] = plugin

    if not plugin_name:
      return key_plugins.values()

    plugin_name = plugin_name.lower()

    plugins_to_run = []
    for key_plugin_name, key_plugin in iter(key_plugins.items()):
      if plugin_name in key_plugin_name.lower():
        plugins_to_run.append(key_plugin)

    return plugins_to_run

  def GetRegistryPluginsFromRegistryType(self, registry_type):
    """Retrieves the Windows Registry plugins based on a Registry type.

    Args:
      registry_type: string containing the Registry type.

    Returns:
      A list of Windows Registry plugins (instance of RegistryPlugin).
    """
    key_plugins = {}
    for plugin in self._registry_plugin_list.GetAllKeyPlugins():
      key_plugins.setdefault(plugin.REG_TYPE.lower(), []).append(plugin)

    if not registry_type:
      return key_plugins.values()

    registry_type = registry_type.lower()

    plugins_to_run = []
    for key_plugin_type, key_plugin_list in iter(key_plugins.items()):
      if registry_type == key_plugin_type:
        plugins_to_run.extend(key_plugin_list)
      elif key_plugin_type == u'any':
        plugins_to_run.extend(key_plugin_list)

    return plugins_to_run

  def ParseRegistryFile(
      self, registry_helper, key_paths=None, use_plugins=None):
    """Extracts events from a Registry file.

    This function takes a Registry helper object (instance of
    PregRegistryHelper) and information about either Registry plugins or keys.
    The function then opens up the Registry file and runs the plugins defined
    (or all if no plugins are defined) against all the keys supplied to it.

    Args:
      registry_helper: Registry helper object (instance of PregRegistryHelper)
      key_paths: optional list of Registry keys paths that are to be parsed.
                 The default is None, which results in no keys parsed.
      use_plugins: optional list of plugins used to parse the key. The
                   default is None, in which case all plugins are used.

    Returns:
      A dict that contains the following structure:
          key_path:
              key: a Registry key (instance of WinRegKey)
              subkeys: a list of Registry keys (instance of WinRegKey).
              data:
                plugin: a plugin object (instance of RegistryPlugin)
                  event_objects: List of event objects extracted.

          key_path 2:
              ...
      Or an empty dict on error.
    """
    if not registry_helper:
      return {}

    try:
      registry_helper.Open()
    except IOError as exception:
      logging.error(u'Unable to parse Registry file, with error: {0:s}'.format(
          exception))
      return {}

    return_dict = {}
    if key_paths is None:
      key_paths = []

    for key_path in key_paths:
      key = registry_helper.GetKeyByPath(key_path)
      return_dict[key_path] = {u'key': key}

      if not key:
        continue

      return_dict[key_path][u'subkeys'] = list(key.GetSubkeys())

      return_dict[key_path][u'data'] = self.ParseRegistryKey(
          key=key, registry_helper=registry_helper, use_plugins=use_plugins)

    return return_dict

  def ParseRegistryKey(
      self, key, registry_helper, use_plugins=None):
    """Parse a single Registry key and return parsed information.

    Parses the Registry key either using the supplied plugin or trying against
    all available plugins.

    Args:
      key: the Registry key to parse, WinRegKey object or a string.
      registry_helper: Registry helper object (instance of PregRegistryHelper)
      use_plugins: optional list of plugin names to use. The default is None
                   which uses all available plugins.

    Returns:
      A dictionary with plugin objects as keys and extracted event objects from
      each plugin as values or an empty dict on error.
    """
    return_dict = {}
    if not registry_helper:
      return return_dict

    if isinstance(key, basestring):
      key = registry_helper.GetKeyByPath(key)

    if not key:
      return return_dict

    registry_type = registry_helper.type

    plugins = {}
    plugins_list = self._registry_plugin_list

    # Compile a list of plugins we are about to use.
    for weight in plugins_list.GetWeights():
      plugin_list = plugins_list.GetWeightPlugins(weight, registry_type)
      plugins[weight] = []
      for plugin in plugin_list:
        if use_plugins:
          plugin_obj = plugin(reg_cache=registry_helper.reg_cache)
          if plugin_obj.NAME in use_plugins:
            plugins[weight].append(plugin_obj)
        else:
          plugins[weight].append(plugin(
              reg_cache=registry_helper.reg_cache))

    event_queue = single_process.SingleProcessQueue()
    event_queue_consumer = PregItemQueueConsumer(event_queue)

    parser_mediator = self.CreateParserMediator(event_queue)
    parser_mediator.SetFileEntry(registry_helper.file_entry)

    for weight in plugins:
      for plugin in plugins[weight]:
        plugin.Process(parser_mediator, key=key)
        event_queue_consumer.ConsumeItems()
        event_objects = [
            event_object for event_object in event_queue_consumer.GetItems()]
        if event_objects:
          return_dict[plugin] = event_objects

    return return_dict

  def SetSingleFile(self, single_file=False):
    """Sets the single file processing parameter.

    Args:
      single_file: boolean value, if set to True the tool treats the
                   source as a single file input, otherwise as a storage
                   media format. The default is False.
    """
    self._single_file = single_file

  def SetSourcePath(self, source_path):
    """Sets the source path.

    Args:
      source_path: the filesystem path to the disk image.
    """
    self._source_path = source_path

  def SetSourcePathSpecs(self, source_path_specs):
    """Sets the source path resolver.

    Args:
      source_path_specs: list of source path specifications (instance
                         of PathSpec).
    """
    self._source_path_specs = source_path_specs

  def SetKnowledgeBase(self, knowledge_base_object):
    """Sets the knowledge base object for the front end.

    Args:
      knowledge_base_object: the knowledge base object (instance
                             of KnowledgeBase).
    """
    self.knowledge_base_object = knowledge_base_object


class PregRegistryHelper(object):
  """Class that defines few helper functions for Registry operations.

  Attributes:
    file_entry: file entry object (instance of dfvfs.FileEntry).
    reg_cache: Registry objects cache (instance of WinRegistryCache).
  """

  def __init__(self, file_entry, collector_name, codepage=u'cp1252'):
    """Initialize the Registry helper.

    Args:
      file_entry: file entry object (instance of dfvfs.FileEntry).
      collector_name: the name of the collector, eg. TSK.
      codepage: the codepage used for the Registry file. The default is cp1252.
    """
    self._Reset()
    self._codepage = codepage
    self._collector_name = collector_name
    self._win_registry = dfwinreg_registry.WinRegistry(
        backend=dfwinreg_registry.WinRegistry.BACKEND_PYREGF)

    self.file_entry = file_entry
    self.reg_cache = None

  def __enter__(self):
    """Make usable with "with" statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.Close()

  @property
  def collector_name(self):
    """The name of the collector used to discover the Registry file."""
    return self._collector_name

  @property
  def name(self):
    """The name of the Registry file."""
    return getattr(self._registry_file, u'name', u'N/A')

  @property
  def path(self):
    """The file path of the Registry file."""
    path_spec = getattr(self.file_entry, u'path_spec', None)
    if not path_spec:
      return u'N/A'

    return getattr(path_spec, u'location', u'N/A')

  @property
  def root_key(self):
    """The root key of the Registry file."""
    if self._registry_file:
      return self._registry_file.GetKeyByPath(u'\\')

  @property
  def type(self):
    """The Registry type."""
    return self._registry_type

  def _Reset(self):
    """Reset all attributes of the Registry helper."""
    self._currently_loaded_registry_key = u''
    self._registry_file = None
    self._registry_type = dfwinreg_definitions.REGISTRY_TYPE_UNKNOWN

    self.reg_cache = None

  def Close(self):
    """Closes the helper."""
    self._Reset()

  def ExpandKeyPath(self, key_path, path_attributes):
    """Expand a Registry key path based on path attributes.

     A Registry key path may contain path attributes. A path attribute is
     defined as anything within a curly bracket, e.g.
     "\\System\\{my_attribute}\\Path\\Keyname".

     If the path attribute my_attribute is defined it's value will be replaced
     with the attribute name, e.g. "\\System\\MyValue\\Path\\Keyname".

     If the Registry path needs to have curly brackets in the path then
     they need to be escaped with another curly bracket, e.g.
     "\\System\\{my_attribute}\\{{123-AF25-E523}}\\KeyName". In this
     case the {{123-AF25-E523}} will be replaced with "{123-AF25-E523}".

    Args:
      key_path: the Registry key path before being expanded.
      path_attributes: a dictionary containing the path attributes.

    Returns:
      A Registry key path that's expanded based on attribute values.
    """
    return self._win_registry.ExpandKeyPath(key_path, path_attributes)

  def GetCurrentRegistryKey(self):
    """Return the currently loaded Registry key."""
    return self._currently_loaded_registry_key

  def GetCurrentRegistryPath(self):
    """Return the loaded Registry key path or None if no key is loaded."""
    key = self._currently_loaded_registry_key
    if not key:
      return

    return key.path

  def GetKeyByPath(self, key_path):
    """Retrieves a specific key defined by the Registry key path.

    Args:
      key_path: the Registry key path.

    Returns:
      The key (instance of WinRegKey) if available or None otherwise.
    """
    if not key_path:
      return

    try:
      # TODO: remove cache in follow up winreg refactor step.
      expanded_key_path = self._win_registry.ExpandKeyPath(
          key_path, self.reg_cache.attributes)
    except KeyError:
      expanded_key_path = key_path

    key = self._registry_file.GetKeyByPath(expanded_key_path)
    if not key:
      return

    self._currently_loaded_registry_key = key
    return key

  def Open(self):
    """Open the Registry file."""
    if self._registry_file:
      raise IOError(u'Registry file already open.')

    try:
      self._registry_file = self._win_registry.OpenFileEntry(
          self.file_entry, codepage=self._codepage)
    except IOError:
      logging.error(
          u'Unable to open Registry file: {0:s} [{1:s}]'.format(
              self.path, self._collector_name))
      self.Close()
      raise

    self._registry_type = self._win_registry.DetectRegistryType(
        self._registry_file)
    self.reg_cache = self._win_registry.CreateCache(
        self._registry_file, self._registry_type)

    # Retrieve the Registry file root key because the Registry helper
    # expects self._currently_loaded_registry_key to be set after
    # the Registry file is opened.
    self.GetKeyByPath(u'\\')
