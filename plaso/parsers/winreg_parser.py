"""Parser for Windows NT Registry (REGF) files."""

import os

from dfvfs.path import factory as path_spec_factory

from dfwinreg import errors as dfwinreg_errors
from dfwinreg import regf as dfwinreg_regf
from dfwinreg import registry as dfwinreg_registry
from dfwinreg import registry_searcher as dfwinreg_registry_searcher

from plaso.engine import artifact_filters
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.filters import path_filter
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class WinRegistryParser(interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
    """Parses Windows NT Registry (REGF) files."""

    NAME = "winreg"
    DATA_FORMAT = "Windows NT Registry (REGF) file"

    _plugin_classes = {}

    _DEFINITION_FILE = os.path.join(os.path.dirname(__file__), "winreg_parser.yaml")

    _FILE_TYPE_PRIMARY = 0

    _TRANSACTION_LOG_FILE_SUFFIXES = (".LOG1", ".LOG2")

    _ARTIFACTS_FILTER_HELPER = artifact_filters.ArtifactDefinitionsFiltersHelper

    _AMCACHE_ROOT_KEY_NAMES = frozenset(
        [
            "{11517b7c-e79d-4e20-961b-75a811715add}",
            "{356c48f6-2fee-e7ef-2a64-39f59ec3be22}",
        ]
    )

    _CONTROL_SET_PREFIX = ("HKEY_LOCAL_MACHINE\\System\\ControlSet").lower()

    _NORMALIZED_CONTROL_SET_PREFIX = (
        "HKEY_LOCAL_MACHINE\\System\\CurrentControlSet"
    ).lower()

    def __init__(self):
        """Initializes a parser."""
        super().__init__()
        self._path_filter = None
        self._plugins_per_key_path = {}
        self._plugins_without_key_paths = []

    def _CanProcessKeyWithPlugin(self, registry_key, plugin):
        """Determines if a plugin can process a Windows Registry key or its values.

        Args:
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          plugin (WindowsRegistryPlugin): Windows Registry plugin.

        Returns:
          bool: True if the Registry key can be processed with the plugin.
        """
        for registry_key_filter in plugin.FILTERS:
            # Skip filters that define key paths since they are already
            # checked by the path filter.
            if getattr(registry_key_filter, "key_paths", []):
                continue

            if registry_key_filter.Match(registry_key):
                return True

        return False

    def EnablePlugins(self, plugin_includes):
        """Enables parser plugins.

        Args:
          plugin_includes (set[str]): names of the plugins to enable, where
              set(['*']) represents all plugins. Note the default plugin, if
              it exists, is always enabled and cannot be disabled.
        """
        self._plugins_per_name = {}
        self._plugins_per_key_path = {}
        self._plugins_without_key_paths = []

        if not self._plugin_classes:
            return

        key_paths = []

        for plugin_name, plugin_class in self._plugin_classes.items():
            if plugin_name == self._default_plugin_name:
                self._default_plugin = plugin_class()
                continue

            if (
                plugin_includes != self.ALL_PLUGINS
                and plugin_name not in plugin_includes
            ):
                continue

            plugin_object = plugin_class()
            self._plugins_per_name[plugin_name] = plugin_object

            for registry_key_filter in plugin_object.FILTERS:
                plugin_key_paths = getattr(registry_key_filter, "key_paths", [])
                if (
                    not plugin_key_paths
                    and plugin_object not in self._plugins_without_key_paths
                ):
                    self._plugins_without_key_paths.append(plugin_object)
                    continue

                for plugin_key_path in plugin_key_paths:
                    lookup_path = plugin_key_path.lower()

                    existing_plugin = self._plugins_per_key_path.get(lookup_path)
                    if existing_plugin:
                        logger.warning(
                            f"Windows Registry key path: {plugin_key_path:s} defined "
                            f"by plugin: {plugin_object.NAME:s} already set by plugin: "
                            f"{existing_plugin.NAME:s}"
                        )
                        continue

                    self._plugins_per_key_path[lookup_path] = plugin_object

                    key_paths.append(lookup_path)

        self._path_filter = path_filter.PathFilterScanTree(
            key_paths, case_sensitive=False, path_segment_separator="\\"
        )

    @classmethod
    def GetFormatSpecification(cls):
        """Retrieves the format specification."""
        format_specification = specification.FormatSpecification(cls.NAME)
        format_specification.AddNewSignature(b"regf", offset=0)
        return format_specification

    def _ParseKeyWithPlugin(self, parser_mediator, win_registry, registry_key, plugin):
        """Parses the Registry key with a specific plugin.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          win_registry (dfwinreg.WinRegistry): Windows Registry.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          plugin (WindowsRegistryPlugin): Windows Registry plugin.
        """
        kwargs = {}
        for attribute_name, context_key_path in plugin.CONTEXT_KEYS.items():
            kwargs[attribute_name] = win_registry.GetKeyByPath(context_key_path)

        try:
            plugin.UpdateChainAndProcess(parser_mediator, registry_key, **kwargs)
        except (OSError, dfwinreg_errors.WinRegistryValueError) as exception:
            parser_mediator.ProduceWarning(
                f"in key: {registry_key.path:s} error: {exception!s}"
            )

    def _GetTransactionLogFileNames(self, parser_mediator):
        """Retrieves the names of the transaction log files of the Registry file.

        Args:
          parser_mediator (ParserMediator): parser mediator.

        Returns:
          list[str]: names of the transaction log files that exist next to the
              Windows Registry file.
        """
        transaction_log_file_names = []

        file_entry = parser_mediator.GetFileEntry()
        if not file_entry:
            return transaction_log_file_names

        path_spec = file_entry.path_spec
        location = getattr(path_spec, "location", None)
        if not path_spec or not location:
            return transaction_log_file_names

        file_system = file_entry.GetFileSystem()

        for suffix in self._TRANSACTION_LOG_FILE_SUFFIXES:
            transaction_log_path_spec = path_spec_factory.Factory.NewPathSpec(
                file_system.type_indicator,
                location=f"{location:s}{suffix:s}",
                parent=path_spec.parent,
            )
            if file_system.FileEntryExistsByPathSpec(transaction_log_path_spec):
                transaction_log_file_names.append(f"{file_entry.name:s}{suffix:s}")

        return transaction_log_file_names

    def _NormalizeKeyPath(self, key_path):
        """Normalizes a Windows Registry key path.

        Args:
          key_path (str): Windows Registry key path.

        Returns:
          str: normalized Windows Registry key path.
        """
        normalized_key_path = key_path.lower()
        # The Registry key path should start with:
        # HKEY_LOCAL_MACHINE\System\ControlSet followed by 3 digits
        # which makes 39 characters.
        if len(normalized_key_path) < 39 or not normalized_key_path.startswith(
            self._CONTROL_SET_PREFIX
        ):
            return normalized_key_path

        # Key paths that contain ControlSet### must be normalized to
        # CurrentControlSet.
        return "".join([self._NORMALIZED_CONTROL_SET_PREFIX, normalized_key_path[39:]])

    def _ParseKey(self, parser_mediator, win_registry, registry_key):
        """Parses the Registry key with a specific plugin.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          win_registry (dfwinreg.WinRegistry): Windows Registry.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        matching_plugin = None

        logger.debug(f"Parsing Windows Registry key: {registry_key.path:s}")

        normalized_key_path = self._NormalizeKeyPath(registry_key.path)
        if self._path_filter and self._path_filter.CheckPath(normalized_key_path):
            matching_plugin = self._plugins_per_key_path[normalized_key_path]
        else:
            for plugin in self._plugins_without_key_paths:
                profiling_name = "/".join([self.NAME, plugin.NAME])

                parser_mediator.SampleFormatCheckStartTiming(profiling_name)

                try:
                    if self._CanProcessKeyWithPlugin(registry_key, plugin):
                        matching_plugin = plugin
                        break

                finally:
                    parser_mediator.SampleFormatCheckStopTiming(profiling_name)

        if not matching_plugin:
            matching_plugin = self._default_plugin

        if matching_plugin:
            self._ParseKeyWithPlugin(
                parser_mediator, win_registry, registry_key, matching_plugin
            )

    def _ParseRecurseKeys(self, parser_mediator, win_registry, registry_key):
        """Parses the Registry keys recursively.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          win_registry (dfwinreg.WinRegistry): Windows Registry.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        # Note that we do not use dfWinReg generators here to be able to catch
        # exceptions raised by corrupt files.

        self._ParseKey(parser_mediator, win_registry, registry_key)

        for subkey_index in range(registry_key.number_of_subkeys):
            if parser_mediator.abort:
                break

            try:
                subkey = registry_key.GetSubkeyByIndex(subkey_index)
                self._ParseRecurseKeys(parser_mediator, win_registry, subkey)

            except OSError as exception:
                parser_mediator.ProduceWarning(
                    f"in key: {registry_key.path:s} error: {exception!s}"
                )

    def _ParseKeysFromFindSpecs(self, parser_mediator, win_registry, find_specs):
        """Parses the Registry keys from FindSpecs.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          win_registry (dfwinreg.WinRegistry): Windows Registry.
          find_specs (dfwinreg.FindSpecs): Keys to search for.
        """
        searcher = dfwinreg_registry_searcher.WinRegistrySearcher(win_registry)
        for registry_key_path in searcher.Find(find_specs=find_specs):
            if parser_mediator.abort:
                break

            registry_key = searcher.GetKeyByPath(registry_key_path)
            self._ParseKey(parser_mediator, win_registry, registry_key)

    def _ProduceDirtyFileWarning(self, parser_mediator, file_header):
        """Produces a warning if the Windows Registry file is dirty.

        A primary Windows Registry file is dirty when its primary and secondary
        sequence numbers differ, which means that changes stored in transaction
        log files have not been applied to the file.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          file_header (regf_file_header): file header.
        """
        if file_header.file_type != self._FILE_TYPE_PRIMARY:
            return

        primary_sequence_number = file_header.primary_sequence_number
        secondary_sequence_number = file_header.secondary_sequence_number
        if primary_sequence_number == secondary_sequence_number:
            return

        message = (
            f"Windows Registry file is dirty (primary sequence number: "
            f"{primary_sequence_number:d}, secondary sequence number: "
            f"{secondary_sequence_number:d}), transaction logs were not applied "
            f"and recent changes may be missing"
        )

        transaction_log_file_names = self._GetTransactionLogFileNames(parser_mediator)
        if transaction_log_file_names:
            file_names = ", ".join(transaction_log_file_names)
            message = f"{message:s}, transaction log files: {file_names:s}"

        parser_mediator.ProduceWarning(message)

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses a Windows Registry file-like object.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          file_object (dfvfs.FileIO): a file-like object.
        """
        file_header_map = self._GetDataTypeMap("regf_file_header")

        try:
            file_header, _ = self._ReadStructureFromFileObject(
                file_object, 0, file_header_map
            )
        except (ValueError, errors.ParseError) as exception:
            logger.debug(f"Unable to parse file header with error: {exception!s}")
            file_header = None

        code_page = parser_mediator.GetCodePage()

        registry_file = dfwinreg_regf.REGFWinRegistryFile(ascii_codepage=code_page)

        try:
            registry_file.Open(file_object)
        except OSError as exception:
            parser_mediator.ProduceWarning(
                f"unable to open Windows Registry file with error: {exception!s}"
            )
            return

        if file_header:
            self._ProduceDirtyFileWarning(parser_mediator, file_header)

        try:
            win_registry = dfwinreg_registry.WinRegistry()

            key_path_prefix = win_registry.GetRegistryFileMapping(registry_file)
            registry_file.SetKeyPathPrefix(key_path_prefix)
            root_key = registry_file.GetRootKey()
            if root_key:
                # For now treat AMCache.hve separately.
                if root_key.name.lower() in self._AMCACHE_ROOT_KEY_NAMES:
                    self._ParseRecurseKeys(parser_mediator, win_registry, root_key)

                elif not parser_mediator.registry_find_specs:
                    self._ParseRecurseKeys(parser_mediator, win_registry, root_key)

                elif not self._ARTIFACTS_FILTER_HELPER.CheckKeyCompatibility(
                    key_path_prefix
                ):
                    logger.warning(
                        f"Artifacts filters are not supported for Windows Registry "
                        f'file with key path prefix: "{key_path_prefix:s}".'
                    )
                else:
                    win_registry.MapFile(key_path_prefix, registry_file)
                    # Note that win_registry will close the mapped registry_file.
                    registry_file = None

                    self._ParseKeysFromFindSpecs(
                        parser_mediator,
                        win_registry,
                        parser_mediator.registry_find_specs,
                    )

        except OSError as exception:
            parser_mediator.ProduceWarning(f"{exception!s}")

        finally:
            if registry_file:
                registry_file.Close()


manager.ParsersManager.RegisterParser(WinRegistryParser)
