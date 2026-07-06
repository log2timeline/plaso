"""Windows EventLog resources database reader."""

import collections
import os

from acstore import sqlite_store
from acstore.containers import interface as containers_interface

from plaso.engine import path_helper
from plaso.helpers.windows import languages
from plaso.helpers.windows import resource_files
from plaso.output import logger


class WinevtResourcesEventLogProvider(containers_interface.AttributeContainer):
    """Windows Event Log provider.

    Attributes:
      additional_identifier (str): additional identifier of the provider,
          contains a GUID.
      category_message_files (set[str]): paths of the category message files.
      event_message_files (set[str]): paths of the event message files.
      identifier (str): identifier of the provider, contains a GUID.
      log_sources (list[str]): names of the corresponding Event Log sources.
      log_types (list[str]): Windows Event Log types.
      name (str): name of the provider.
      parameter_message_files (set[str]): paths of the parameter message
          files.
      windows_version (str): Windows version.
    """

    CONTAINER_TYPE = "winevtrc_eventlog_provider"

    SCHEMA = {
        "additional_identifier": "str",
        "category_message_files": "List[str]",
        "event_message_files": "List[str]",
        "identifier": "str",
        "log_sources": "List[str]",
        "log_types": "List[str]",
        "name": "str",
        "parameter_message_files": "List[str]",
        "windows_version": "str",
    }

    def __init__(self):
        """Initializes the Windows Event Log provider."""
        super().__init__()
        self.additional_identifier = None
        self.category_message_files = set()
        self.event_message_files = set()
        self.identifier = None
        self.log_sources = []
        self.log_types = []
        self.name = None
        self.parameter_message_files = set()
        self.windows_version = None


class WinevtResourcesMessageFile(containers_interface.AttributeContainer):
    """Windows Event Log message file.

    Attributes:
      file_version (str): file version.
      product_version (str): product version.
      windows_path (str): path as defined by the Window Event Log provider.
      windows_version (str): Windows version.
    """

    CONTAINER_TYPE = "winevtrc_message_file"

    SCHEMA = {
        "file_version": "str",
        "product_version": "str",
        "windows_path": "str",
        "windows_version": "str",
    }

    def __init__(
        self,
        file_version=None,
        product_version=None,
        windows_path=None,
        windows_version=None,
    ):
        """Initializes a Windows Event Log message file.

        Args:
          file_version (Optional[str]): file version.
          product_version (Optional[str]): product version.
          windows_path (Optional[str]): path as defined by the Window Event Log
              provider.
          windows_version (Optional[str]): Windows version.
        """
        super().__init__()
        self.file_version = file_version
        self.product_version = product_version
        self.windows_path = windows_path
        self.windows_version = windows_version


class WinevtResourcesMessageString(containers_interface.AttributeContainer):
    """Windows Event Log message string.

    Attributes:
      identifier (int): message identifier.
      text (str): message text.
    """

    CONTAINER_TYPE = "winevtrc_message_string"

    SCHEMA = {
        "_message_table_identifier": "AttributeContainerIdentifier",
        "language_identifier": "str",
        "message_identifier": "int",
        "text": "str",
    }

    _SERIALIZABLE_PROTECTED_ATTRIBUTES = ["_message_table_identifier"]

    def __init__(self, message_identifier=None, text=None):
        """Initializes a Windows Event Log message string.

        Args:
          message_identifier (Optional[int]): message identifier.
          text (Optional[int]): message text.
        """
        super().__init__()
        self._message_table_identifier = None
        self.message_identifier = message_identifier
        self.text = text

    def GetMessageTableIdentifier(self):
        """Retrieves the identifier of the associated message table.

        Returns:
          AttributeContainerIdentifier: message table identifier or None when not
              set.
        """
        return self._message_table_identifier

    def SetMessageTableIdentifier(self, message_table_identifier):
        """Sets the identifier of the associated message table.

        Args:
          message_table_identifier (AttributeContainerIdentifier): message table
              identifier.
        """
        self._message_table_identifier = message_table_identifier


class WinevtResourcesMessageStringMapping(containers_interface.AttributeContainer):
    """Windows Event Log message string mapping.

    Attributes:
      event_identifier (int): event identifier.
      event_version (int): event version.
      message_identifier (int): message identifier.
      provider_identifier (str): Event Log provider identifier.
    """

    CONTAINER_TYPE = "winevtrc_message_string_mapping"

    SCHEMA = {
        "_message_file_identifier": "AttributeContainerIdentifier",
        "event_identifier": "int",
        "event_version": "int",
        "message_identifier": "int",
        "provider_identifier": "str",
    }

    _SERIALIZABLE_PROTECTED_ATTRIBUTES = ["_message_file_identifier"]

    def __init__(
        self,
        event_identifier=None,
        event_version=None,
        message_identifier=None,
        provider_identifier=None,
    ):
        """Initializes a Windows Event Log message string mapping.

        Args:
          event_identifier (Optional[int]): event identifier.
          event_version (Optional[int]): event version.
          message_identifier (Optional[int]): message identifier.
          provider_identifier (Optional[str]): Event Log provider identifier.
        """
        super().__init__()
        self._message_file_identifier = None
        self.event_identifier = event_identifier
        self.event_version = event_version
        self.message_identifier = message_identifier
        self.provider_identifier = provider_identifier

    def GetMessageFileIdentifier(self):
        """Retrieves the identifier of the associated message file.

        Returns:
          AttributeContainerIdentifier: message file identifier or None when
              not set.
        """
        return self._message_file_identifier

    def SetMessageFileIdentifier(self, message_file_identifier):
        """Sets the identifier of the associated message file.

        Args:
          message_file_identifier (AttributeContainerIdentifier): message file
              identifier.
        """
        self._message_file_identifier = message_file_identifier


class WinevtResourcesMessageTable(containers_interface.AttributeContainer):
    """Windows Event Log message table.

    Attributes:
      language_identifier (int): language identifier (LCID).
    """

    CONTAINER_TYPE = "winevtrc_message_table"

    SCHEMA = {
        "_message_file_identifier": "AttributeContainerIdentifier",
        "language_identifier": "int",
    }

    _SERIALIZABLE_PROTECTED_ATTRIBUTES = ["_message_file_identifier"]

    def __init__(self, language_identifier=None):
        """Initializes a Windows Event Log message table descriptor.

        Args:
          language_identifier (Optional[int]): language identifier (LCID).
        """
        super().__init__()
        self._message_file_identifier = None
        self.language_identifier = language_identifier

    def GetMessageFileIdentifier(self):
        """Retrieves the identifier of the associated message file.

        Returns:
          AttributeContainerIdentifier: message file identifier or None when not
              set.
        """
        return self._message_file_identifier

    def SetMessageFileIdentifier(self, message_file_identifier):
        """Sets the identifier of the associated message file.

        Args:
          message_file_identifier (AttributeContainerIdentifier): message file
              identifier.
        """
        self._message_file_identifier = message_file_identifier


class WinevtResourcesAttributeContainerStore(
    sqlite_store.SQLiteAttributeContainerStore
):
    """Windows EventLog resources attribute container store.

    Attributes:
      format_version (int): storage format version.
      serialization_format (str): serialization format.
      string_format (str): string format.
    """

    _FORMAT_VERSION = 20240929
    _APPEND_COMPATIBLE_FORMAT_VERSION = 20240929
    _UPGRADE_COMPATIBLE_FORMAT_VERSION = 20240929
    _READ_COMPATIBLE_FORMAT_VERSION = 20240929

    def __init__(self, string_format="wrc"):
        """Initializes a message resource attribute container store.

        Args:
          string_format (Optional[str]): string format. The default is the Windows
              Resource (wrc) format.
        """
        super().__init__()
        self.string_format = string_format

        try:
            self._containers_manager.RegisterAttributeContainers(
                [
                    WinevtResourcesEventLogProvider,
                    WinevtResourcesMessageFile,
                    WinevtResourcesMessageString,
                    WinevtResourcesMessageStringMapping,
                    WinevtResourcesMessageTable,
                ]
            )
        except KeyError:
            pass

    def _ReadAndCheckStorageMetadata(self, check_readable_only=False):
        """Reads storage metadata and checks that the values are valid.

        Args:
          check_readable_only (Optional[bool]): whether the store should only be
              checked to see if it can be read. If False, the store will be checked
              to see if it can be read and written to.

        Raises:
          OSError: when there is an error querying the attribute container store.
        """
        metadata_values = self._ReadMetadata()

        self._CheckStorageMetadata(
            metadata_values, check_readable_only=check_readable_only
        )
        string_format = metadata_values.get("string_format")

        if string_format not in ("pep3101", "wrc"):
            raise OSError(f"Unsupported string format: {string_format:s}")

        self.format_version = metadata_values["format_version"]
        self.serialization_format = metadata_values["serialization_format"]
        self.string_format = metadata_values["string_format"]


class WinevtResourcesHelper:
    """Windows EventLog resources helper."""

    # LCID 0x0409 is en-US.
    DEFAULT_LCID = 0x0409

    _DEFAULT_PARAMETER_MESSAGE_FILES = (
        "%SystemRoot%\\System32\\MsObjs.dll",
        "%SystemRoot%\\System32\\kernel32.dll",
    )

    # The maximum number of cached message strings
    _MAXIMUM_CACHED_MESSAGE_STRINGS = 64 * 1024

    _WINEVT_RC_DATABASE = "winevt-rc.db"

    def __init__(self, storage_reader, data_location, lcid):
        """Initializes Windows EventLog resources helper.

        Args:
          storage_reader (StorageReader): storage reader.
          data_location (str): data location of the winevt-rc database.
          lcid (int): Windows Language Code Identifier (LCID).
        """
        language_tag = languages.WindowsLanguageHelper.GetLanguageTagForLCID(
            lcid or self.DEFAULT_LCID
        )
        super().__init__()
        self._data_location = data_location
        self._environment_variables = None
        self._language_tag = language_tag.lower()
        self._lcid = lcid or self.DEFAULT_LCID
        self._message_string_cache = collections.OrderedDict()
        self._resouce_file_helper = resource_files.WindowsResourceFileHelper
        self._storage_reader = None
        self._windows_eventlog_message_files = None
        self._windows_eventlog_providers = None
        self._winevt_database_reader = None

        if storage_reader and storage_reader.HasAttributeContainers(
            "windows_eventlog_provider"
        ):
            self._storage_reader = storage_reader

    def _CacheMessageString(
        self,
        provider_identifier,
        log_source,
        message_identifier,
        event_version,
        message_string,
    ):
        """Caches a specific message string.

        Args:
          provider_identifier (str): EventLog provider identifier.
          log_source (str): EventLog source, such as "Application Error".
          message_identifier (int): message identifier.
          event_version (int): event version or None if not set.
          message_string (str): message string.
        """
        if len(self._message_string_cache) >= self._MAXIMUM_CACHED_MESSAGE_STRINGS:
            self._message_string_cache.popitem(last=True)

        if provider_identifier:
            lookup_key = f"{provider_identifier:s}:0x{message_identifier:08x}"
            if event_version is not None:
                lookup_key = f"{lookup_key:s}:{event_version:d}"
            self._message_string_cache[lookup_key] = message_string
            self._message_string_cache.move_to_end(lookup_key, last=False)

        if log_source:
            lookup_key = f"{log_source:s}:0x{message_identifier:08x}"
            if event_version is not None:
                lookup_key = f"{lookup_key:s}:{event_version:d}"
            self._message_string_cache[lookup_key] = message_string
            self._message_string_cache.move_to_end(lookup_key, last=False)

    def _GetCachedMessageString(
        self, provider_identifier, log_source, message_identifier, event_version
    ):
        """Retrieves a specific cached message string.

        Args:
          provider_identifier (str): EventLog provider identifier.
          log_source (str): EventLog source, such as "Application Error".
          message_identifier (int): message identifier.
          event_version (int): event version or None if not set.

        Returns:
          str: message string or None if not available.
        """
        lookup_key = None
        message_string = None

        if provider_identifier:
            lookup_key = f"{provider_identifier:s}:0x{message_identifier:08x}"
            if event_version is not None:
                lookup_key = f"{lookup_key:s}:{event_version:d}"
            message_string = self._message_string_cache.get(lookup_key)

        if not message_string and log_source:
            lookup_key = f"{log_source:s}:0x{message_identifier:08x}"
            if event_version is not None:
                lookup_key = f"{lookup_key:s}:{event_version:d}"
            message_string = self._message_string_cache.get(lookup_key)

        if message_string:
            self._message_string_cache.move_to_end(lookup_key, last=False)

        return message_string

    def _GetEventMessageFileIdentifiers(self, message_files):
        """Retrieves event message file identifiers.

        Args:
          message_files (list[str]): Windows EventLog message files.

        Returns:
          list[str]: message file identifiers.
        """
        message_file_identifiers = []
        for windows_path in message_files or []:
            path, filename = path_helper.PathHelper.GetWindowsSystemPath(
                windows_path, self._environment_variables
            )

            lookup_path = "\\".join([path, filename]).lower()
            message_file_identifier = self._windows_eventlog_message_files.get(
                lookup_path, None
            )
            if message_file_identifier:
                message_file_identifier = message_file_identifier.CopyToString()
                message_file_identifiers.append(message_file_identifier)

            mui_filename = f"{filename:s}.mui"
            lookup_path = "\\".join([path, self._language_tag, mui_filename]).lower()
            message_file_identifier = self._windows_eventlog_message_files.get(
                lookup_path, None
            )
            if message_file_identifier:
                message_file_identifier = message_file_identifier.CopyToString()
                message_file_identifiers.append(message_file_identifier)

        return message_file_identifiers

    def _GetMappedMessageIdentifier(
        self, storage_reader, provider_identifier, message_identifier, event_version
    ):
        """Retrieves a WEVT_TEMPLATE mapped message identifier if available.

        Args:
          storage_reader (StorageReader): storage reader.
          provider_identifier (str): EventLog provider identifier.
          message_identifier (int): message identifier.
          event_version (int): event version or None if not set.

        Returns:
          int: message identifier.
        """
        # Map the event identifier to a message identifier as defined by the
        # WEVT_TEMPLATE event definition.
        if provider_identifier and storage_reader.HasAttributeContainers(
            "windows_wevt_template_event"
        ):
            # TODO: add message_file_identifiers to filter_expression
            filter_expression = (
                f"provider_identifier == '{provider_identifier:s}' and "
                f"identifier == {message_identifier:d}"
            )
            if event_version is not None:
                filter_expression = (
                    f"{filter_expression:s} and version == {event_version:d}"
                )

            for event_definition in storage_reader.GetAttributeContainers(
                "windows_wevt_template_event", filter_expression=filter_expression
            ):
                logger.debug(
                    f"Message: 0x{message_identifier:08x} of provider: "
                    f"{provider_identifier:s} maps to: "
                    f"0x{event_definition.message_identifier:08x}"
                )
                return event_definition.message_identifier

        return message_identifier

    def _GetMessageStrings(
        self, storage_reader, message_file_identifiers, message_identifier
    ):
        """Retrieves message strings.

        Args:
          storage_reader (StorageReader): storage reader.
          message_file_identifiers (list[str]): message file identifiers.
          message_identifier (int): message identifier.

        Returns:
          list[str]: message strings.
        """
        message_strings = []

        # TODO: add message_file_identifiers to filter_expression
        filter_expression = (
            f"language_identifier == {self._lcid:d} and "
            f"message_identifier == {message_identifier:d}"
        )
        for message_string in storage_reader.GetAttributeContainers(
            "windows_eventlog_message_string", filter_expression=filter_expression
        ):
            identifier = message_string.GetMessageFileIdentifier()
            identifier = identifier.CopyToString()
            if identifier in message_file_identifiers:
                message_strings.append(message_string)

        return message_strings

    def _GetMessageStringsWithMessageTable(
        self, storage_reader, message_file_identifiers, message_identifier
    ):
        """Retrieves message strings.

        Args:
          storage_reader (StorageReader): storage reader.
          message_file_identifiers (list[str]): message file identifiers.
          message_identifier (int): message identifier.

        Returns:
          list[str]: message strings.
        """
        message_strings = []

        for message_file_identifier in message_file_identifiers:
            filter_expression = (
                f"_message_file_identifier == '{message_file_identifier:s}' and "
                f"language_identifier == {self._lcid:d}"
            )
            for message_table in storage_reader.GetAttributeContainers(
                "winevtrc_message_table", filter_expression=filter_expression
            ):
                if not message_table:
                    continue

                identifier = message_table.GetIdentifier()
                message_table_identifier = identifier.CopyToString()

                filter_expression = (
                    f"_message_table_identifier == '{message_table_identifier:s}' and "
                    f"message_identifier == {message_identifier:d}"
                )
                identifier = message_table.GetMessageFileIdentifier()
                message_file_identifier = identifier.CopyToString()

                for message_string in storage_reader.GetAttributeContainers(
                    "winevtrc_message_string", filter_expression=filter_expression
                ):
                    if message_file_identifier in message_file_identifiers:
                        message_strings.append(message_string)

        return message_strings

    def _GetWindowsEventLogProvider(self, provider_identifier, log_source):
        """Retrieves a Windows EventLog provider.

        Args:
          provider_identifier (str): EventLog provider identifier.
          log_source (str): EventLog source, such as "Application Error".

        Returns:
          tuple[WindowsEventLogProviderArtifact, str]: Windows EventLog provider
              or None if not available, and provider lookup key.
        """
        provider = None

        if provider_identifier:
            lookup_key = provider_identifier.lower()
            provider = self._windows_eventlog_providers.get(lookup_key)

        if not provider:
            lookup_key = log_source.lower()
            provider = self._windows_eventlog_providers.get(lookup_key)

        return provider, lookup_key

    def _GetWinevtRcDatabaseReader(self):
        """Opens the Windows EventLog resource database reader.

        Returns:
          WinevtResourcesAttributeContainerStore: Windows EventLog resource database
              reader or None.
        """
        if not self._winevt_database_reader and self._data_location:
            logger.warning(
                f"Falling back to {self._WINEVT_RC_DATABASE:s}. Please make sure "
                f"the Windows EventLog message strings in the database correspond "
                f"to those in the EventLog files."
            )
            database_path = os.path.join(self._data_location, self._WINEVT_RC_DATABASE)
            if not os.path.isfile(database_path):
                return None

            try:
                self._winevt_database_reader = WinevtResourcesAttributeContainerStore()
                # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
                self._winevt_database_reader.Open(path=database_path, read_only=True)
            except OSError:
                self._winevt_database_reader = None

        return self._winevt_database_reader

    def _GetWinevtRcDatabaseMessageString(
        self, provider_identifier, log_source, message_identifier, event_version
    ):
        """Retrieves a specific Windows EventLog resource database message string.

        Args:
          provider_identifier (str): EventLog provider identifier.
          log_source (str): EventLog source, such as "Application Error".
          message_identifier (int): message identifier.
          event_version (int): event version or None if not set.

        Returns:
          str: message string or None if not available.
        """
        database_reader = self._GetWinevtRcDatabaseReader()
        if not database_reader:
            return None

        if self._windows_eventlog_providers is None:
            self._ReadWindowsEventLogProviders(
                database_reader, container_type="winevtrc_eventlog_provider"
            )

        if self._windows_eventlog_message_files is None:
            self._ReadWindowsEventLogMessageFiles(
                database_reader,
                container_type="winevtrc_message_file",
                path_attribute="windows_path",
            )

        provider, provider_lookup_key = self._GetWindowsEventLogProvider(
            provider_identifier, log_source
        )
        if not provider:
            return None

        original_message_identifier = message_identifier

        # TODO: pass message_file_identifiers
        message_identifier = self._GetMappedMessageIdentifier(
            database_reader, provider_identifier, message_identifier, event_version
        )
        message_file_identifiers = self._GetEventMessageFileIdentifiers(
            provider.event_message_files
        )
        if not message_file_identifiers:
            logger.warning(
                f"No event message file for identifier: 0x{message_identifier:08x} "
                f"(original: 0x{original_message_identifier:08x}) "
                f"of provider: {provider_lookup_key:s}"
            )
            return None

        message_strings = self._GetMessageStringsWithMessageTable(
            database_reader, message_file_identifiers, message_identifier
        )
        if not message_strings:
            logger.warning(
                f"No message string for identifier: 0x{message_identifier:08x} "
                f"(original: 0x{original_message_identifier:08x}) "
                f"of provider: {provider_lookup_key:s}"
            )
            return None

        message_string = message_strings[0].text
        if database_reader.string_format == "wrc":
            message_string = self._resouce_file_helper.FormatMessageStringInPEP3101(
                message_string
            )

        return message_string

    def _GetWinevtRcDatabaseParameterMessageString(
        self,
        provider_identifier,
        log_source,
        message_identifier,
    ):
        """Retrieves a specific Windows EventLog resource database parameter string.

        Args:
          provider_identifier (str): EventLog provider identifier.
          log_source (str): EventLog source, such as "Application Error".
          message_identifier (int): message identifier.

        Returns:
          str: parameter message string or None if not available.
        """
        database_reader = self._GetWinevtRcDatabaseReader()
        if not database_reader:
            return None

        if self._windows_eventlog_providers is None:
            self._ReadWindowsEventLogProviders(
                database_reader, container_type="winevtrc_eventlog_provider"
            )

        if self._windows_eventlog_message_files is None:
            self._ReadWindowsEventLogMessageFiles(
                database_reader,
                container_type="winevtrc_message_file",
                path_attribute="windows_path",
            )

        provider, provider_lookup_key = self._GetWindowsEventLogProvider(
            provider_identifier, log_source
        )
        if not provider:
            return None

        message_files = provider.parameter_message_files
        if not message_files:
            # If no parameter message files are defined fallback to the event message
            # files and default parameter message files.
            message_files = list(provider.event_message_files)
            message_files.extend(self._DEFAULT_PARAMETER_MESSAGE_FILES)

        message_file_identifiers = self._GetEventMessageFileIdentifiers(message_files)
        if not message_file_identifiers:
            logger.warning(
                f"No parameter message file for identifier: "
                f"0x{message_identifier:08x} of provider: {provider_lookup_key:s}"
            )
            return None

        message_strings = self._GetMessageStringsWithMessageTable(
            database_reader, message_file_identifiers, message_identifier
        )
        if not message_strings:
            logger.warning(
                f"No parameter string for identifier: 0x{message_identifier:08x} "
                f"of provider: {provider_lookup_key:s}"
            )
            return None

        message_string = message_strings[0].text
        if database_reader.string_format == "wrc":
            message_string = self._resouce_file_helper.FormatMessageStringInPEP3101(
                message_string
            )

        return message_string

    def _ReadEnvironmentVariables(self, storage_reader):
        """Reads the environment variables.

        Args:
          storage_reader (StorageReader): storage reader.
        """
        # TODO: get environment variables related to the source.
        self._environment_variables = list(
            storage_reader.GetAttributeContainers("environment_variable")
        )

    def _ReadEventMessageString(
        self,
        storage_reader,
        provider_identifier,
        log_source,
        message_identifier,
        event_version,
    ):
        """Reads an event message string.

        Args:
          storage_reader (StorageReader): storage reader.
          provider_identifier (str): EventLog provider identifier.
          log_source (str): EventLog source, such as "Application Error".
          message_identifier (int): message identifier.
          event_version (int): event version or None if not set.

        Returns:
          str: message string or None if not available.
        """
        if self._environment_variables is None:
            self._ReadEnvironmentVariables(storage_reader)

        if self._windows_eventlog_providers is None:
            self._ReadWindowsEventLogProviders(storage_reader)

        if self._windows_eventlog_message_files is None:
            self._ReadWindowsEventLogMessageFiles(storage_reader)

        provider, provider_lookup_key = self._GetWindowsEventLogProvider(
            provider_identifier, log_source
        )
        if not provider:
            return None

        if not storage_reader.HasAttributeContainers("windows_eventlog_message_string"):
            return None

        original_message_identifier = message_identifier

        # TODO: pass message_file_identifiers
        message_identifier = self._GetMappedMessageIdentifier(
            storage_reader, provider_identifier, message_identifier, event_version
        )
        message_file_identifiers = self._GetEventMessageFileIdentifiers(
            provider.event_message_files
        )
        if not message_file_identifiers:
            logger.warning(
                f"No event message file for identifier: 0x{message_identifier:08x} "
                f"(original: 0x{original_message_identifier:08x}) "
                f"of provider: {provider_lookup_key:s}"
            )
            return None

        message_strings = self._GetMessageStrings(
            storage_reader, message_file_identifiers, message_identifier
        )
        if not message_strings:
            logger.warning(
                f"No message string for identifier: 0x{message_identifier:08x} "
                f"(original: 0x{original_message_identifier:08x}) "
                f"of provider: {provider_lookup_key:s}"
            )
            return None

        return message_strings[0].string

    def _ReadParameterMessageString(
        self, storage_reader, provider_identifier, log_source, message_identifier
    ):
        """Reads a parameter message string.

        Args:
          storage_reader (StorageReader): storage reader.
          provider_identifier (str): EventLog provider identifier.
          log_source (str): EventLog source, such as "Application Error".
          message_identifier (int): message identifier.

        Returns:
          str: parameter string or None if not available.
        """
        if self._environment_variables is None:
            self._ReadEnvironmentVariables(storage_reader)

        if self._windows_eventlog_providers is None:
            self._ReadWindowsEventLogProviders(storage_reader)

        if self._windows_eventlog_message_files is None:
            self._ReadWindowsEventLogMessageFiles(storage_reader)

        provider, provider_lookup_key = self._GetWindowsEventLogProvider(
            provider_identifier, log_source
        )
        if not provider:
            return None

        if not storage_reader.HasAttributeContainers("windows_eventlog_message_string"):
            return None

        message_files = provider.parameter_message_files
        if not message_files:
            # If no parameter message files are defined fallback to the event message
            # files and default parameter message files.
            message_files = list(provider.event_message_files)
            message_files.extend(self._DEFAULT_PARAMETER_MESSAGE_FILES)

        message_file_identifiers = self._GetEventMessageFileIdentifiers(message_files)
        if not message_file_identifiers:
            logger.warning(
                f"No parameter message file for identifier: "
                f"0x{message_identifier:08x} of provider: {provider_lookup_key:s}"
            )
            return None

        message_strings = self._GetMessageStrings(
            storage_reader, message_file_identifiers, message_identifier
        )
        if not message_strings:
            logger.warning(
                f"No parameter string for identifier: 0x{message_identifier:08x} "
                f"of provider: {provider_lookup_key:s}"
            )
            return None

        return message_strings[0].string

    def _ReadWindowsEventLogMessageFiles(
        self,
        attribute_store,
        container_type="windows_eventlog_message_file",
        path_attribute="path",
    ):
        """Reads the Windows EventLog message files.

        Args:
          attribute_store (AttributeContainerStore): attribute container store.
          container_type (Optional[str]): attribute container type.
          path_attribute (Optional[str]): name of the attribute containing the path.
        """
        # TODO: get windows eventlog message files related to the source.
        self._windows_eventlog_message_files = {}
        if attribute_store.HasAttributeContainers(container_type):
            for message_file in attribute_store.GetAttributeContainers(container_type):
                message_file_path = getattr(message_file, path_attribute, None)
                path, filename = path_helper.PathHelper.GetWindowsSystemPath(
                    message_file_path, self._environment_variables
                )
                lookup_path = "\\".join([path, filename]).lower()
                message_file_identifier = message_file.GetIdentifier()
                self._windows_eventlog_message_files[lookup_path] = (
                    message_file_identifier
                )

    def _ReadWindowsEventLogProviders(
        self, attribute_store, container_type="windows_eventlog_provider"
    ):
        """Reads Windows EventLog provider attribute containers.

        Args:
          attribute_store (AttributeContainerStore): attribute container store.
          container_type (Optional[str]): attribute container type.
        """
        self._windows_eventlog_providers = {}
        if attribute_store.HasAttributeContainers(container_type):
            for provider in attribute_store.GetAttributeContainers(container_type):
                if provider.identifier:
                    self._windows_eventlog_providers[provider.identifier] = provider

                for log_source in provider.log_sources:
                    log_source = log_source.lower()
                    self._windows_eventlog_providers[log_source] = provider

    def GetMessageString(
        self, provider_identifier, log_source, message_identifier, event_version
    ):
        """Retrieves a specific Windows EventLog message string.

        Args:
          provider_identifier (str): EventLog provider identifier.
          log_source (str): EventLog source, such as "Application Error".
          message_identifier (int): message identifier.
          event_version (int): event version or None if not set.

        Returns:
          str: message string or None if not available.
        """
        message_string = self._GetCachedMessageString(
            provider_identifier, log_source, message_identifier, event_version
        )
        if not message_string:
            if self._storage_reader:
                message_string = self._ReadEventMessageString(
                    self._storage_reader,
                    provider_identifier,
                    log_source,
                    message_identifier,
                    event_version,
                )
            else:
                message_string = self._GetWinevtRcDatabaseMessageString(
                    provider_identifier, log_source, message_identifier, event_version
                )

            if message_string:
                self._CacheMessageString(
                    provider_identifier,
                    log_source,
                    message_identifier,
                    event_version,
                    message_string,
                )

        return message_string

    def GetParameterString(self, provider_identifier, log_source, message_identifier):
        """Retrieves a specific Windows EventLog parameter string.

        Args:
          provider_identifier (str): EventLog provider identifier.
          log_source (str): EventLog source, such as "Application Error".
          message_identifier (int): parameter identifier.

        Returns:
          str: parameter string or None if not available.
        """
        message_string = self._GetCachedMessageString(
            provider_identifier, log_source, message_identifier, None
        )
        if not message_string:
            if self._storage_reader:
                message_string = self._ReadParameterMessageString(
                    self._storage_reader,
                    provider_identifier,
                    log_source,
                    message_identifier,
                )
            else:
                message_string = self._GetWinevtRcDatabaseParameterMessageString(
                    provider_identifier,
                    log_source,
                    message_identifier,
                )

            if message_string:
                self._CacheMessageString(
                    provider_identifier,
                    log_source,
                    message_identifier,
                    None,
                    message_string,
                )

        return message_string
