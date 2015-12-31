# -*- coding: utf-8 -*-
"""The preg front-end."""

import logging

from dfvfs.helpers import file_system_searcher
from dfvfs.helpers import windows_path_resolver
from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.dfwinreg import registry as dfwinreg_registry
from plaso.engine import queue
from plaso.engine import single_process
from plaso.frontend import extraction_frontend
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import manager as parsers_manager
from plaso.parsers import winreg
from plaso.parsers import winreg_plugins  # pylint: disable=unused-import
from plaso.preprocessors import manager as preprocess_manager


# The Registry (file) types.
REGISTRY_FILE_TYPE_NTUSER = u'NTUSER'
REGISTRY_FILE_TYPE_SAM = u'SAM'
REGISTRY_FILE_TYPE_SECURITY = u'SECURITY'
REGISTRY_FILE_TYPE_SOFTWARE = u'SOFTWARE'
REGISTRY_FILE_TYPE_SYSTEM = u'SYSTEM'
REGISTRY_FILE_TYPE_UNKNOWN = u'UNKNOWN'
REGISTRY_FILE_TYPE_USRCLASS = u'USRCLASS'

REGISTRY_FILE_TYPES = frozenset([
    REGISTRY_FILE_TYPE_NTUSER,
    REGISTRY_FILE_TYPE_SAM,
    REGISTRY_FILE_TYPE_SECURITY,
    REGISTRY_FILE_TYPE_SOFTWARE,
    REGISTRY_FILE_TYPE_SYSTEM,
    REGISTRY_FILE_TYPE_USRCLASS])


# TODO: add tests for this class.
class PluginList(object):
  """A simple class that stores information about Windows Registry plugins."""

  def __init__(self):
    """Initializes the plugin list object."""
    super(PluginList, self).__init__()
    self._plugins = {}

  def __iter__(self):
    """Return an iterator of all Windows Registry plugins."""
    ret = []
    _ = map(ret.extend, self._plugins.values())
    for item in ret:
      yield item

  def _GetPluginsByType(self, plugins_dict, registry_file_type):
    """Retrieves the Windows Registry plugins of a specific type.

    Args:
      plugins_dict: Dictionary containing the Windows Registry plugins
                    by plugin type.
      registry_file_type: String containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.

    Returns:
      A list containing the Windows Registry plugins (instances of
      RegistryPlugin) for the specific plugin type.
    """
    return plugins_dict.get(
        registry_file_type, []) + plugins_dict.get(u'any', [])

  def AddPlugin(self, plugin_class):
    """Add a Windows Registry plugin to the plugin list.

    Only plugins with full Windows Registry key paths are registered.

    Args:
      plugin_class: The plugin class that is being registered.
    """
    key_paths = []
    registry_file_types = set()
    for registry_key_filter in plugin_class.FILTERS:
      plugin_key_paths = getattr(registry_key_filter, u'key_paths', [])
      for plugin_key_path in plugin_key_paths:
        if plugin_key_path not in key_paths:
          key_paths.append(plugin_key_path)

          if plugin_key_path.startswith(u'HKEY_CURRENT_USER'):
            registry_file_types.add(u'NTUSER')
          elif plugin_key_path.startswith(u'HKEY_LOCAL_MACHINE\\SAM'):
            registry_file_types.add(u'SAM')
          elif plugin_key_path.startswith(u'HKEY_LOCAL_MACHINE\\Software'):
            registry_file_types.add(u'SOFTWARE')
          elif plugin_key_path.startswith(u'HKEY_LOCAL_MACHINE\\System'):
            registry_file_types.add(u'SYSTEM')

    if len(registry_file_types) == 1:
      plugin_type = registry_file_types.pop()
    else:
      plugin_type = u'any'

    if key_paths:
      self._plugins.setdefault(plugin_type, []).append(plugin_class)

  def GetAllPlugins(self):
    """Return all key plugins as a list."""
    ret = []
    _ = map(ret.extend, self._plugins.values())
    return ret

  def GetKeyPaths(self, plugin_names=None):
    """Retrieves a list of Windows Registry key paths.

    Args:
      plugin_names: Optional list of plugin names, if defined only keys from
                    these plugins will be expanded. The default is None which
                    means all key plugins will get expanded keys.

    Returns:
      A set of Windows Registry key paths.
    """
    key_paths = set()
    for plugin_cls in self.GetAllPlugins():
      plugin_object = plugin_cls()

      if plugin_names and plugin_object.NAME not in plugin_names:
        continue

      for key_path in plugin_object.GetKeyPaths():
        key_paths.add(key_path)

    return key_paths

  def GetPluginObjectByName(self, registry_file_type, plugin_name):
    """Creates a new instance of a specific Windows Registry plugin.

    Args:
      registry_file_type: String containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.
      plugin_name: the name of the plugin.

    Returns:
      The Windows Registry plugin (instance of RegistryPlugin) or None.
    """
    # TODO: make this a dict lookup instead of a list iteration.
    for plugin_cls in self.GetPlugins(registry_file_type):
      if plugin_cls.NAME == plugin_name:
        return plugin_cls()

  def GetPluginObjects(self, registry_file_type):
    """Creates new instances of a specific type of Windows Registry plugins.

    Args:
      registry_file_type: String containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.

    Returns:
      A list of Windows Registry plugins (instances of RegistryPlugin).
    """
    return [plugin_cls() for plugin_cls in self.GetPlugins(registry_file_type)]

  def GetPlugins(self, registry_file_type):
    """Retrieves the Windows Registry key-based plugins of a specific type.

    Args:
      registry_file_type: String containing the Windows Registry file type,
                          e.g. NTUSER, SOFTWARE.

    Returns:
      A list containing the Windows Registry plugins (types of
      RegistryPlugin) for the specific plugin type.
    """
    return self._GetPluginsByType(self._plugins, registry_file_type)

  def GetRegistryPlugins(self, filter_string):
    """Retrieves the Windows Registry plugins based on a filter string.

    Args:
      filter_string: string containing the name of the plugin or an empty
                     string for all the plugins.

    Returns:
      A list of Windows Registry plugins (instance of RegistryPlugin).
    """
    if filter_string:
      filter_string = filter_string.lower()

    plugins_to_run = []
    for plugins_per_type in iter(self._plugins.values()):
      for plugin in plugins_per_type:
        # Note that this method also matches on parts of the plugin name.
        if not filter_string or filter_string in plugin.NAME.lower():
          plugins_to_run.append(plugin)

    return plugins_to_run

  def GetRegistryTypes(self, filter_string):
    """Retrieves the Windows Registry types based on a filter string.

    Args:
      filter_string: string containing the name of the plugin or an empty
                     string for all the plugins.

    Returns:
      A list of Windows Registry types.
    """
    if filter_string:
      filter_string = filter_string.lower()

    registry_file_types = set()
    for plugin_type, plugins_per_type in iter(self._plugins.items()):
      for plugin in plugins_per_type:
        if not filter_string or filter_string == plugin.NAME.lower():
          if plugin_type == u'any':
            registry_file_types.update(REGISTRY_FILE_TYPES)

          else:
            registry_file_types.add(plugin_type)

    return list(registry_file_types)

  def GetRegistryTypesFromPlugins(self, plugin_names):
    """Return a list of Registry types extracted from a list of plugin names.

    Args:
      plugin_names: a list of plugin names.

    Returns:
      A list of Registry types extracted from the supplied plugins.
    """
    if not plugin_names:
      return []

    registry_file_types = set()
    for plugin_type, plugins_per_type in iter(self._plugins.items()):
      for plugin in plugins_per_type:
        if plugin.NAME.lower() in plugin_names:
          # If a plugin is available for every Registry type
          # we need to make sure all Registry files are included.
          if plugin_type == u'any':
            registry_file_types.update(REGISTRY_FILE_TYPES)

          else:
            registry_file_types.add(plugin_type)

    return list(registry_file_types)

  def GetRegistryPluginsFromRegistryType(self, registry_file_type):
    """Retrieves the Windows Registry plugins based on a Registry type.

    Args:
      registry_file_type: the Windows Registry files type string or an empty
                          string for all the plugins.

    Returns:
      A list of Windows Registry plugins (instance of RegistryPlugin).
    """
    if registry_file_type:
      registry_file_type = registry_file_type.upper()

    plugins_to_run = []
    for plugin_type, plugins_per_type in iter(self._plugins.items()):
      if not registry_file_type or plugin_type in [u'any', registry_file_type]:
        plugins_to_run.extend(plugins_per_type)

    return plugins_to_run


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
    self._registry_plugin_list = self.GetWindowsRegistryPlugins()
    self._single_file = False
    self._source_path = None
    self._source_path_specs = []

    self.knowledge_base_object = None

  @property
  def registry_plugin_list(self):
    """The Windows Registry plugin list (instance of PluginList)."""
    return self._registry_plugin_list

  def _GetRegistryHelperFromPath(self, path, codepage):
    """Return a Registry helper object from a path.

    Given a path to a Registry file this function goes through
    all the discovered source path specifications (instance of PathSpec)
    and extracts Registry helper objects based on the supplied
    path.

    Args:
      path: the path filter to a Registry file.
      codepage: the codepage used for the Registry file.

    Yields:
      A Registry helper object (instance of PregRegistryHelper).
    """
    # TODO: deprecate usage of pre_obj.
    path_attributes = self.knowledge_base_object.pre_obj.__dict__

    for source_path_spec in self._source_path_specs:
      if source_path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
        file_entry = path_spec_resolver.Resolver.OpenFileEntry(source_path_spec)
        if file_entry.IsFile():
          yield PregRegistryHelper(
              file_entry, u'OS', self.knowledge_base_object, codepage=codepage)
          continue

        # TODO: Change this into an actual mount point path spec.
        self._mount_path_spec = source_path_spec

      collector_name = source_path_spec.type_indicator
      parent_path_spec = getattr(source_path_spec, u'parent', None)
      if parent_path_spec and parent_path_spec.type_indicator == (
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW):
        vss_store = getattr(parent_path_spec, u'store_index', 0)
        collector_name = u'VSS Store: {0:d}'.format(vss_store)

      file_system, mount_point = self._GetSourceFileSystem(source_path_spec)

      try:
        path_resolver = windows_path_resolver.WindowsPathResolver(
            file_system, mount_point)

        if path.startswith(u'%UserProfile%\\'):
          searcher = file_system_searcher.FileSystemSearcher(
              file_system, mount_point)

          user_profiles = []
          # TODO: determine the users path properly instead of relying on
          # common defaults. Note that these paths are language dependent.
          for user_path in (u'/Documents and Settings/.+', u'/Users/.+'):
            find_spec = file_system_searcher.FindSpec(
                location_regex=user_path, case_sensitive=False)
            for path_spec in searcher.Find(find_specs=[find_spec]):
              location = getattr(path_spec, u'location', None)
              if location:
                if location.startswith(u'/'):
                  location = u'\\'.join(location.split(u'/'))
                user_profiles.append(location)

          for user_profile in user_profiles:
            path_resolver.SetEnvironmentVariable(u'UserProfile', user_profile)

            path_spec = path_resolver.ResolvePath(path)
            if not path_spec:
              continue

            file_entry = file_system.GetFileEntryByPathSpec(path_spec)
            if not file_entry:
              continue

            yield PregRegistryHelper(
                file_entry, collector_name, self.knowledge_base_object,
                codepage=codepage)
        else:
          path_attribute_value = path_attributes.get(u'systemroot', None)
          if path_attribute_value:
            path_resolver.SetEnvironmentVariable(
                u'SystemRoot', path_attribute_value)

          path_spec = path_resolver.ResolvePath(path)
          if not path_spec:
            continue

          file_entry = file_system.GetFileEntryByPathSpec(path_spec)
          if not file_entry:
            continue

          yield PregRegistryHelper(
              file_entry, collector_name, self.knowledge_base_object,
              codepage=codepage)

      finally:
        file_system.Close()

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
                        The default is None which will use the built in context
                        which is not multi process safe. Note that every thread
                        or process must have its own resolver context.

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

  def GetRegistryFilePaths(self, registry_file_types):
    """Returns a list of Windows Registry file paths.

    If the Windows Registry file type is not set this functions attempts
    to determine it based on the presence of specific Registry keys.

    Args:
      registry_file_types: a set of Windows Registry file type strings.

    Returns:
      A list of path of Windows Registry files.
    """
    if self._parse_restore_points:
      restore_path = (
          u'\\System Volume Information\\_restore.+\\RP[0-9]+\\snapshot\\')
    else:
      restore_path = u''

    paths = []
    for registry_file_type in registry_file_types:
      if registry_file_type == REGISTRY_FILE_TYPE_NTUSER:
        paths.append(u'%UserProfile%\\NTUSER.DAT')
        if restore_path:
          paths.append(u'{0:s}\\_REGISTRY_USER_NTUSER_.+'.format(restore_path))

      elif registry_file_type == REGISTRY_FILE_TYPE_SAM:
        paths.append(u'%SystemRoot%\\System32\\config\\SAM')
        if restore_path:
          paths.append(u'{0:s}\\_REGISTRY_MACHINE_SAM'.format(restore_path))

      elif registry_file_type == REGISTRY_FILE_TYPE_SECURITY:
        paths.append(u'%SystemRoot%\\System32\\config\\SECURITY')
        if restore_path:
          paths.append(
              u'{0:s}\\_REGISTRY_MACHINE_SECURITY'.format(restore_path))

      elif registry_file_type == REGISTRY_FILE_TYPE_SOFTWARE:
        paths.append(u'%SystemRoot%\\System32\\config\\SOFTWARE')
        if restore_path:
          paths.append(
              u'{0:s}\\_REGISTRY_MACHINE_SOFTWARE'.format(restore_path))

      elif registry_file_type == REGISTRY_FILE_TYPE_SYSTEM:
        paths.append(u'%SystemRoot%\\System32\\config\\SYSTEM')
        if restore_path:
          paths.append(u'{0:s}\\_REGISTRY_MACHINE_SYSTEM'.format(restore_path))

      elif registry_file_type == REGISTRY_FILE_TYPE_USRCLASS:
        paths.append(
            u'%UserProfile%\\AppData\\Local\\Microsoft\\Windows\\UsrClass.dat')
        if restore_path:
          paths.append(
              u'{0:s}\\_REGISTRY_USER_USRCLASS_.+'.format(restore_path))

    return paths

  # TODO: refactor this function. Current implementation is too complex.
  def GetRegistryHelpers(
      self, registry_file_types=None, plugin_names=None, codepage=u'cp1252'):
    """Returns a list of discovered Registry helpers.

    Args:
      registry_file_types: optional list of Windows Registry file types,
                           e.g.: NTUSER, SAM, etc that should be included.
      plugin_names: optional list of strings containing the name of the
                    plugin(s) or an empty string for all the types. The default
                    is None.
      codepage: the codepage used for the Registry file.

    Returns:
      A list of Registry helper objects (instance of PregRegistryHelper).

    Raises:
      ValueError: If neither registry_file_types nor plugin name is passed
                  as a parameter.
    """
    if registry_file_types is None and plugin_names is None:
      raise ValueError(
          u'Missing registry_file_types or plugin_name value.')

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

    # TODO: fix issue handling Windows paths
    if registry_file_types is None:
      registry_file_types = []

    types_from_plugins = (
        self._registry_plugin_list.GetRegistryTypesFromPlugins(plugin_names))
    registry_file_types.extend(types_from_plugins)

    if self._single_file:
      paths = [self._source_path]

    else:
      types = set()
      if registry_file_types:
        for registry_file_type in registry_file_types:
          types.add(registry_file_type.upper())
      else:
        for plugin_name in plugin_names:
          types.extend(self._registry_plugin_list.GetRegistryTypes(plugin_name))

      paths = self.GetRegistryFilePaths(types)

    self.knowledge_base_object.SetDefaultCodepage(codepage)

    registry_helpers = []
    for path in paths:
      for helper in self._GetRegistryHelperFromPath(path, codepage):
        registry_helpers.append(helper)

    return registry_helpers

  # TODO: remove after refactoring.
  def GetRegistryPlugins(self, filter_string):
    """Retrieves the Windows Registry plugins based on a filter string.

    Args:
      filter_string: string containing the name of the plugin or an empty
                     string for all the plugins.

    Returns:
      A list of Windows Registry plugins (instance of RegistryPlugin).
    """
    return self._registry_plugin_list.GetRegistryPlugins(filter_string)

  # TODO: remove after refactoring.
  def GetRegistryPluginsFromRegistryType(self, registry_file_type):
    """Retrieves the Windows Registry plugins based on a Registry type.

    Args:
      registry_file_type: the Windows Registry files type string.

    Returns:
      A list of Windows Registry plugins (instance of RegistryPlugin).
    """
    return self._registry_plugin_list.GetRegistryPluginsFromRegistryType(
        registry_file_type)

  def GetRegistryTypes(self, filter_string):
    """Retrieves the Windows Registry types based on a filter string.

    Args:
      filter_string: string containing the name of the plugin or an empty
                     string for all the plugins.

    Returns:
      A list of Windows Registry types.
    """
    return self._registry_plugin_list.GetRegistryTypes(filter_string)

  def GetWindowsRegistryPlugins(self):
    """Build a list of all available Windows Registry plugins.

    Returns:
      A plugins list (instance of PluginList).
    """
    winreg_parser = parsers_manager.ParsersManager.GetParserObjectByName(
        u'winreg')
    if not winreg_parser:
      return

    plugins_list = PluginList()
    for _, plugin_class in winreg_parser.GetPlugins():
      plugins_list.AddPlugin(plugin_class)
    return plugins_list

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
              key: a Registry key (instance of dfwinreg.WinRegistryKey)
              subkeys: a list of Registry keys (instance of
                       dfwinreg.WinRegistryKey).
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
      registry_key = registry_helper.GetKeyByPath(key_path)
      return_dict[key_path] = {u'key': registry_key}

      if not registry_key:
        continue

      return_dict[key_path][u'subkeys'] = list(registry_key.GetSubkeys())

      return_dict[key_path][u'data'] = self.ParseRegistryKey(
          registry_key, registry_helper, use_plugins=use_plugins)

    return return_dict

  def ParseRegistryKey(self, registry_key, registry_helper, use_plugins=None):
    """Parse a single Registry key and return parsed information.

    Parses the Registry key either using the supplied plugin or trying against
    all available plugins.

    Args:
      registry_key: the Registry key to parse (instance of
                    dfwinreg.WinRegistryKey or a string containing key path).
      registry_helper: the Registry helper object (instance of
                       PregRegistryHelper).
      use_plugins: optional list of plugin names to use. The default is None
                   which uses all available plugins.

    Returns:
      A dictionary with plugin objects as keys and extracted event objects from
      each plugin as values or an empty dict on error.
    """
    if not registry_helper:
      return {}

    if isinstance(registry_key, basestring):
      registry_key = registry_helper.GetKeyByPath(registry_key)

    if not registry_key:
      return {}

    event_queue = single_process.SingleProcessQueue()
    event_queue_consumer = PregItemQueueConsumer(event_queue)

    parser_mediator = self.CreateParserMediator(event_queue)
    parser_mediator.SetFileEntry(registry_helper.file_entry)

    return_dict = {}
    found_matching_plugin = False
    for plugin_object in self._registry_plugin_list.GetPluginObjects(
        registry_helper.file_type):
      if use_plugins and plugin_object.NAME not in use_plugins:
        continue

      # Check if plugin should be processed.
      can_process = False
      for filter_object in plugin_object.FILTERS:
        if filter_object.Match(registry_key):
          can_process = True
          break

      if not can_process:
        continue

      found_matching_plugin = True
      plugin_object.Process(parser_mediator, registry_key)
      event_queue_consumer.ConsumeItems()
      event_objects = [
          event_object for event_object in event_queue_consumer.GetItems()]
      if event_objects:
        return_dict[plugin_object] = event_objects

    if not found_matching_plugin:
      winreg_parser = parsers_manager.ParsersManager.GetParserObjectByName(
          u'winreg')
      if not winreg_parser:
        return
      default_plugin_object = winreg_parser.GetPluginObjectByName(
          u'winreg_default')

      default_plugin_object.Process(parser_mediator, registry_key)
      event_queue_consumer.ConsumeItems()
      event_objects = [
          event_object for event_object in event_queue_consumer.GetItems()]
      if event_objects:
        return_dict[default_plugin_object] = event_objects

    return return_dict

  def SetSingleFile(self, single_file=False):
    """Sets the single file processing parameter.

    Args:
      single_file: boolean value, if set to True the tool treats the
                   source as a single file input, otherwise as a storage
                   media format.
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
  """

  _KEY_PATHS_PER_REGISTRY_TYPE = {
      REGISTRY_FILE_TYPE_NTUSER: frozenset([
          u'\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer']),
      REGISTRY_FILE_TYPE_SAM: frozenset([
          u'\\SAM\\Domains\\Account\\Users']),
      REGISTRY_FILE_TYPE_SECURITY: frozenset([
          u'\\Policy\\PolAdtEv']),
      REGISTRY_FILE_TYPE_SOFTWARE: frozenset([
          u'\\Microsoft\\Windows\\CurrentVersion\\App Paths']),
      REGISTRY_FILE_TYPE_SYSTEM: frozenset([
          u'\\Select']),
      REGISTRY_FILE_TYPE_USRCLASS: frozenset([
          u'\\Local Settings\\Software\\Microsoft\\Windows\\CurrentVersion']),
  }

  def __init__(
      self, file_entry, collector_name, knowledge_base_object,
      codepage=u'cp1252'):
    """Initialize the Registry helper.

    Args:
      file_entry: file entry object (instance of dfvfs.FileEntry).
      collector_name: the name of the collector, eg. TSK.
      knowledge_base_object: A knowledge base object (instance of
                             KnowledgeBase), which contains information from
                             the source data needed for parsing.
      codepage: optional codepage value used for the Registry file. The default
                is cp1252.
    """
    super(PregRegistryHelper, self).__init__()
    self._codepage = codepage
    self._collector_name = collector_name
    self._currently_registry_key = None
    self._key_path_prefix = None
    self._knowledge_base_object = knowledge_base_object
    self._registry_file = None
    self._registry_file_name = None
    self._registry_file_type = REGISTRY_FILE_TYPE_UNKNOWN
    self._win_registry = None

    self.file_entry = file_entry

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
  def file_type(self):
    """The Registry file type."""
    return self._registry_file_type

  @property
  def name(self):
    """The name of the Registry file."""
    return self._registry_file_name

  @property
  def path(self):
    """The file path of the Registry file."""
    path_spec = getattr(self.file_entry, u'path_spec', None)
    if not path_spec:
      return u'N/A'

    return getattr(path_spec, u'location', u'N/A')

  @property
  def root_key(self):
    """The root key of the Registry file or None."""
    if self._registry_file:
      return self._registry_file.GetRootKey()

  def _Reset(self):
    """Reset all attributes of the Registry helper."""
    self._currently_registry_key = None
    self._key_path_prefix = None
    self._registry_file = None
    self._registry_file_name = None
    self._registry_file_type = REGISTRY_FILE_TYPE_UNKNOWN

  def ChangeKeyByPath(self, key_path):
    """Changes the current key defined by the Registry key path.

    Args:
      key_path: string containing an absolute or relative Registry key path.

    Returns:
      The key (instance of dfwinreg.WinRegistryKey) if available or
      None otherwise.
    """
    if key_path == u'.':
      return self._currently_registry_key

    path_segments = []

    # If the key path is relative to the root key add the key path prefix.
    if not key_path or key_path.startswith(u'\\'):
      path_segments.append(self._key_path_prefix)

      # If no key path was provided then change to the root key.
      if not key_path:
        path_segments.append(u'\\')

    else:
      key_path_upper = key_path.upper()
      if not key_path_upper.startswith(u'HKEY_'):
        current_path = getattr(self._currently_registry_key, u'path', None)
        if current_path:
          path_segments.append(current_path)

    path_segments.append(key_path)

    # Split all the path segments based on the path (segment) separator.
    path_segments = [
        segment.split(u'\\') for segment in path_segments]

    # Flatten the sublists into one list.
    path_segments = [
        element for sublist in path_segments for element in sublist]

    # Remove empty and current ('.') path segments.
    path_segments = [
        segment for segment in path_segments
        if segment not in [None, u'', u'.']]

    # Remove parent ('..') path segments.
    index = 0
    while index < len(path_segments):
      if path_segments[index] == u'..':
        path_segments.pop(index)
        index -= 1

        if index > 0:
          path_segments.pop(index)
          index -= 1

      index += 1

    key_path = u'\\'.join(path_segments)
    return self.GetKeyByPath(key_path)

  def Close(self):
    """Closes the helper."""
    self._Reset()

  def GetCurrentRegistryKey(self):
    """Return the currently Registry key."""
    return self._currently_registry_key

  def GetCurrentRegistryPath(self):
    """Return the Registry key path or None."""
    return getattr(self._currently_registry_key, u'path', None)

  def GetKeyByPath(self, key_path):
    """Retrieves a specific key defined by the Registry key path.

    Args:
      key_path: a Windows Registry key path relative to the root key of
                the file or relative to the root of the Windows Registry.

    Returns:
      The key (instance of dfwinreg.WinRegistryKey) if available or
      None otherwise.
    """
    registry_key = self._win_registry.GetKeyByPath(key_path)
    if not registry_key:
      return

    self._currently_registry_key = registry_key
    return registry_key

  def GetRegistryFileType(self, registry_file):
    """Determines the Windows Registry type based on keys present in the file.

    Args:
      registry_file: the Windows Registry file object (instance of
                     WinRegistryFile).

    Returns:
      The Windows Registry file type, e.g. NTUSER, SOFTWARE.
    """
    registry_file_type = REGISTRY_FILE_TYPE_UNKNOWN
    for registry_file_type, key_paths in iter(
        self._KEY_PATHS_PER_REGISTRY_TYPE.items()):

      # If all key paths are found we consider the file to match a certain
      # Registry type.
      match = True
      for key_path in key_paths:
        registry_key = registry_file.GetKeyByPath(key_path)
        if not registry_key:
          match = False

      if match:
        break

    return registry_file_type

  def Open(self):
    """Opens a Windows Registry file.

    Raises:
      IOError: if the Windows Registry file cannot be opened.
    """
    if self._registry_file:
      raise IOError(u'Registry file already open.')

    file_object = self.file_entry.GetFileObject()
    if not file_object:
      logging.error(
          u'Unable to open Registry file: {0:s} [{1:s}]'.format(
              self.path, self._collector_name))
      raise IOError(u'Unable to open Registry file.')

    win_registry_reader = winreg.FileObjectWinRegistryFileReader()
    self._registry_file = win_registry_reader.Open(file_object)
    if not self._registry_file:
      file_object.close()

      logging.error(
          u'Unable to open Registry file: {0:s} [{1:s}]'.format(
              self.path, self._collector_name))
      raise IOError(u'Unable to open Registry file.')

    self._win_registry = dfwinreg_registry.WinRegistry()
    self._key_path_prefix = self._win_registry.GetRegistryFileMapping(
        self._registry_file)
    self._win_registry.MapFile(self._key_path_prefix, self._registry_file)

    self._registry_file_name = self.file_entry.name
    self._registry_file_type = self.GetRegistryFileType(self._registry_file)

    # Retrieve the Registry file root key because the Registry helper
    # expects self._currently_registry_key to be set after
    # the Registry file is opened.
    self._currently_registry_key = self._registry_file.GetRootKey()
