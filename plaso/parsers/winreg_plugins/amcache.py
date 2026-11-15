"""Windows Registry plugin to parse the AMCache.hve Root key."""

import re

from dfdatetime import definitions as dfdatetime_definitions
from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import time_elements as dfdatetime_time_elements

from dfwinreg import errors as dfwinreg_errors

from plaso.containers import events
from plaso.parsers import winreg_parser
from plaso.parsers.winreg_plugins import interface


class AMCacheApplicationEventData(events.EventData):
    """AMCache application inventory event data.

    Attributes:
      bundle_manifest_path (str): path of the bundle manifest of the application.
      entry_source (str): source of the entry, for example AddRemoveProgram,
          AppxPackage or Msi.
      entry_type (str): type of entry, for example Application.
      installation_os_version (str): version of the operating system at the time
          the application was installed.
      installation_time (dfdatetime.DateTimeValues): installation date and time.
      is_hidden (bool): True if the application is hidden in Add/Remove Programs.
      is_inbox_modern_application (bool): True if the application is a modern
          application that is part of the operating system.
      language_code (int): language code of the application.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      manifest_path (str): path of the manifest of the application.
      msi_installation_time (dfdatetime.DateTimeValues): MSI installation date and
          time.
      msi_package_code (str): MSI package code of the application.
      msi_product_code (str): MSI product code of the application.
      name (str): name of the application.
      package_full_name (str): full name of the application package.
      program_identifier (str): identifier of the application.
      program_instance_identifier (str): identifier of the application instance.
      publisher (str): publisher of the application.
      registry_key_path (str): path of the uninstall Windows Registry key of
          the application.
      root_directory_path (str): path of the root directory of the application.
      store_application_type (str): type of store application.
      uninstall_string (str): command to uninstall the application.
      version (str): version of the application.
    """

    DATA_TYPE = "windows:registry:amcache:application"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.bundle_manifest_path = None
        self.entry_source = None
        self.entry_type = None
        self.installation_os_version = None
        self.installation_time = None
        self.is_hidden = None
        self.is_inbox_modern_application = None
        self.language_code = None
        self.last_written_time = None
        self.manifest_path = None
        self.msi_installation_time = None
        self.msi_package_code = None
        self.msi_product_code = None
        self.name = None
        self.package_full_name = None
        self.program_identifier = None
        self.program_instance_identifier = None
        self.publisher = None
        self.registry_key_path = None
        self.root_directory_path = None
        self.store_application_type = None
        self.uninstall_string = None
        self.version = None


class AMCacheApplicationShortcutEventData(events.EventData):
    """AMCache application shortcut inventory event data.

    Attributes:
      application_user_model_identifier (str): application user model identifier
          (AUMID) of the shortcut.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      program_identifier (str): identifier of the application the shortcut
          belongs to.
      shortcut_path (str): path of the shortcut (LNK) file.
      target_path (str): path of the target of the shortcut.
    """

    DATA_TYPE = "windows:registry:amcache:application_shortcut"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.application_user_model_identifier = None
        self.last_written_time = None
        self.program_identifier = None
        self.shortcut_path = None
        self.target_path = None


class AMCacheDeviceContainerEventData(events.EventData):
    """AMCache device container inventory event data.

    Attributes:
      categories (str): categories of the device container.
      container_identifier (str): identifier (GUID) of the device container.
      discovery_method (str): method used to discover the device container.
      friendly_name (str): friendly name of the device container.
      icon (str): icon of the device container.
      is_active (bool): True if the device container is active.
      is_connected (bool): True if the device container is connected.
      is_machine_container (bool): True if the device container represents
          the machine itself.
      is_networked (bool): True if the device container is networked.
      is_paired (bool): True if the device container is paired.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      manufacturer (str): manufacturer of the device container.
      model_identifier (str): identifier (GUID) of the model.
      model_name (str): name of the model.
      model_number (str): number of the model.
      primary_category (str): primary category of the device container.
      state (int): state of the device container.
    """

    DATA_TYPE = "windows:registry:amcache:device_container"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.categories = None
        self.container_identifier = None
        self.discovery_method = None
        self.friendly_name = None
        self.icon = None
        self.is_active = None
        self.is_connected = None
        self.is_machine_container = None
        self.is_networked = None
        self.is_paired = None
        self.last_written_time = None
        self.manufacturer = None
        self.model_identifier = None
        self.model_name = None
        self.model_number = None
        self.primary_category = None
        self.state = None


class AMCacheDevicePnpEventData(events.EventData):
    """AMCache Plug and Play device inventory event data.

    Attributes:
      bus_reported_description (str): description of the device as reported by
          the bus.
      class_identifier (str): identifier (GUID) of the device setup class.
      compatible_identifiers (str): compatible identifiers of the device.
      container_identifier (str): identifier (GUID) of the device container.
      description (str): description of the device.
      device_class (str): device setup class.
      device_instance_identifier (str): device instance identifier.
      device_state (int): state of the device.
      driver_identifier (str): identifier of the driver binary.
      driver_name (str): name of the driver binary.
      driver_package_strong_name (str): strong name of the driver package.
      driver_version (str): version of the driver.
      driver_version_time (dfdatetime.DateTimeValues): date of the driver version.
      enumerator (str): enumerator of the device.
      first_installation_time (dfdatetime.DateTimeValues): date the device was
          first installed.
      hardware_identifiers (str): hardware identifiers of the device.
      inf_name (str): name of the driver information (INF) file.
      install_state (int): installation state of the device.
      installation_time (dfdatetime.DateTimeValues): date the device was last
          installed.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      location_paths (str): location paths of the device.
      manufacturer (str): manufacturer of the device.
      matching_identifier (str): identifier used to match the device with
          the driver.
      model (str): model of the device.
      parent_identifier (str): device instance identifier of the parent device.
      problem_code (int): problem code of the device.
      provider (str): provider of the driver.
      service (str): name of the service of the driver.
      stack_identifiers (str): identifiers of the drivers in the device stack.
    """

    DATA_TYPE = "windows:registry:amcache:device_pnp"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.bus_reported_description = None
        self.class_identifier = None
        self.compatible_identifiers = None
        self.container_identifier = None
        self.description = None
        self.device_class = None
        self.device_instance_identifier = None
        self.device_state = None
        self.driver_identifier = None
        self.driver_name = None
        self.driver_package_strong_name = None
        self.driver_version = None
        self.driver_version_time = None
        self.enumerator = None
        self.first_installation_time = None
        self.hardware_identifiers = None
        self.inf_name = None
        self.install_state = None
        self.installation_time = None
        self.last_written_time = None
        self.location_paths = None
        self.manufacturer = None
        self.matching_identifier = None
        self.model = None
        self.parent_identifier = None
        self.problem_code = None
        self.provider = None
        self.service = None
        self.stack_identifiers = None


class AMCacheDriverBinaryEventData(events.EventData):
    """AMCache driver binary inventory event data.

    Attributes:
      checksum (int): checksum of the driver binary.
      company_name (str): name of the company that created the driver binary.
      driver_identifier (str): identifier of the driver binary (SHA-1 of
          the driver binary, preceded by "0000").
      driver_package_strong_name (str): strong name of the driver package.
      driver_type (int): type of the driver.
      driver_version (str): version of the driver binary.
      file_modification_time (dfdatetime.DateTimeValues): driver binary file
          entry last modification date and time.
      filename (str): name of the driver binary.
      image_size (int): size of the image of the driver binary in bytes.
      inf_name (str): name of the driver information (INF) file.
      is_in_box (bool): True if the driver binary is part of the operating system.
      is_kernel_mode (bool): True if the driver binary runs in kernel mode.
      is_signed (bool): True if the driver binary is signed.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      link_time (dfdatetime.DateTimeValues): link date and time.
      path (str): path of the driver binary.
      product_name (str): product name the driver binary belongs to.
      product_version (str): version of the product.
      service (str): name of the service of the driver.
      wdf_version (str): version of the Windows Driver Frameworks (WDF).
    """

    DATA_TYPE = "windows:registry:amcache:driver_binary"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.checksum = None
        self.company_name = None
        self.driver_identifier = None
        self.driver_package_strong_name = None
        self.driver_type = None
        self.driver_version = None
        self.file_modification_time = None
        self.filename = None
        self.image_size = None
        self.inf_name = None
        self.is_in_box = None
        self.is_kernel_mode = None
        self.is_signed = None
        self.last_written_time = None
        self.link_time = None
        self.path = None
        self.product_name = None
        self.product_version = None
        self.service = None
        self.wdf_version = None


class AMCacheDriverPackageEventData(events.EventData):
    """AMCache driver package inventory event data.

    Attributes:
      class_identifier (str): identifier (GUID) of the device setup class.
      device_class (str): device setup class.
      directory (str): path of the directory of the driver package.
      driver_package_strong_name (str): strong name of the driver package.
      driver_version (str): version of the driver.
      driver_version_time (dfdatetime.DateTimeValues): date of the driver version.
      hardware_identifiers (str): hardware identifiers supported by the driver
          package.
      inf_name (str): name of the driver information (INF) file.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and
          time.
      provider (str): provider of the driver package.
      submission_identifier (str): identifier of the hardware submission of
          the driver package.
      system_file (str): name of the driver binary of the driver package.
    """

    DATA_TYPE = "windows:registry:amcache:driver_package"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.class_identifier = None
        self.device_class = None
        self.directory = None
        self.driver_package_strong_name = None
        self.driver_version = None
        self.driver_version_time = None
        self.hardware_identifiers = None
        self.inf_name = None
        self.last_written_time = None
        self.provider = None
        self.submission_identifier = None
        self.system_file = None


class AMCacheFileEventData(events.EventData):
    """AMCache file event data.

    Attributes:
      application_key_last_written_time (dfdatetime.DateTimeValues): last written date
          and time of the application key.
      company_name (str): company name that created product file belongs to.
      file_creation_time (dfdatetime.DateTimeValues): file entry creation date and time.
      file_description (str): description of file.
      file_identifier (str): identifier of file (SHA-1 of the first 30 MiB (31457280
          bytes) of file, preceded by "0000").
      file_modification_time (dfdatetime.DateTimeValues): file entry last modification
          date and time.
      file_reference (str): file system file reference, for example 9-1 (MFT entry -
          sequence number).
      file_size (int): size of file in bytes.
      file_version (str): version of file.
      filename (str): name of the file.
      full_path (str): full path of file.
      installation_time (dfdatetime.DateTimeValues): installation date and time.
      language_code (int): language code of file.
      last_written_time (dfdatetime.DateTimeValues): entry last written date and time.
      link_time (dfdatetime.DateTimeValues): link date and time.
      msi_installation_time (dfdatetime.DateTimeValues): MSI installation date and time.
      product_name (str): product name file belongs to.
      program_identifier (str): GUID of entry under Root/Program key file belongs to.
      sha1 (str): SHA-1.
    """

    DATA_TYPE = "windows:registry:amcache"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.application_key_last_written_time = None
        self.company_name = None
        self.file_creation_time = None
        self.file_description = None
        self.file_identifier = None
        self.file_modification_time = None
        self.file_reference = None
        self.file_size = None
        self.file_version = None
        self.filename = None
        self.full_path = None
        self.installation_time = None
        self.language_code = None
        self.last_written_time = None
        self.link_time = None
        self.msi_installation_time = None
        self.product_name = None
        self.program_identifier = None
        self.sha1 = None


class AMCacheProgramEventData(events.EventData):
    """AMCache programs event data.

    Attributes:
      entry_type (str): type of entry (usually AddRemoveProgram).
      file_paths (str): file paths of installed program.
      files (str): list of files belonging to program.
      installation_time (dfdatetime.DateTimeValues): installation date and time.
      language_code (int): language_code of program.
      msi_package_code (str): MSI package code of program.
      msi_product_code (str): MSI product code of program.
      name (str): name of installed program.
      package_code (str): package code of program.
      product_code (str): product code of program.
      publisher (str): publisher of program.
      uninstall_key (str): unicode string of uninstall registry key for program.
      version (str): version of program.
    """

    DATA_TYPE = "windows:registry:amcache:programs"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.entry_type = None
        self.file_paths = None
        self.files = None
        self.installation_time = None
        self.language_code = None
        self.msi_package_code = None
        self.msi_product_code = None
        self.name = None
        self.package_code = None
        self.product_code = None
        self.publisher = None
        self.uninstall_key = None
        self.version = None


class AMCachePlugin(interface.WindowsRegistryPlugin):
    """AMCache.hve Windows Registry plugin."""

    NAME = "amcache"
    DATA_FORMAT = "AMCache (AMCache.hve)"

    FILTERS = frozenset([interface.WindowsRegistryKeyPathFilter("\\Root")])

    # Contains: {value name: attribute name}
    _APPLICATION_SUB_KEY_VALUES = {
        "FileId": "file_identifier",
        "LowerCaseLongPath": "full_path",
        "Name": "filename",
        "ProductName": "product_name",
        "ProductVersion": "file_version",
        "ProgramId": "program_identifier",
        "Publisher": "company_name",
        "Size": "file_size",
    }

    _FILE_REFERENCE_KEY_VALUES = {
        "0": "product_name",
        "1": "company_name",
        "3": "language_code",
        "5": "file_version",
        "6": "file_size",
        "c": "file_description",
        "15": "full_path",
        "100": "program_identifier",
        "101": "sha1",
    }

    _INVENTORY_BOOLEAN_VALUES = {"0": False, "1": True, "false": False, "true": True}

    # Date and time strings formatted as: "MM/DD/YYYY hh:mm:ss", "MM-DD-YYYY" or
    # "YYYY-M-D", for example "01/14/2026 18:34:33", "06-21-2006" or "2016-5-25"
    _INVENTORY_DATE_TIME_RES = (
        re.compile(
            r"(?P<month>[0-9]{2})/(?P<day_of_month>[0-9]{2})/(?P<year>[0-9]{4}) "
            r"(?P<hours>[0-9]{2}):(?P<minutes>[0-9]{2}):(?P<seconds>[0-9]{2})"
        ),
        re.compile(
            r"(?P<month>[0-9]{2})-(?P<day_of_month>[0-9]{2})-(?P<year>[0-9]{4})"
        ),
        re.compile(
            r"(?P<year>[0-9]{4})-(?P<month>[0-9]{1,2})-(?P<day_of_month>[0-9]{1,2})"
        ),
    )

    _AMCACHE_LINK_TIME = "f"
    _AMCACHE_FILE_MODIFICATION_TIME = "11"
    _AMCACHE_FILE_CREATION_TIME = "12"
    _AMCACHE_ENTRY_WRITE_TIME = "17"

    _AMCACHE_P_INSTALLATION_TIME = "a"

    _AMCACHE_P_FILES = "Files"

    # Date and time string formatted as: "MM/DD/YYYY hh:mm:ss"
    # for example "04/07/2014 15:18:49"
    # TODO: determine if this is true for other locales.
    _LINK_DATE_TIME_RE = re.compile(
        r"([0-9][0-9])/([0-9][0-9])/([0-9][0-9][0-9][0-9]) "
        r"([0-9][0-9]):([0-9][0-9]):([0-9][0-9])"
    )

    _PRODUCT_KEY_VALUES = {
        "0": "name",
        "1": "version",
        "2": "publisher",
        "3": "language_code",
        "6": "entry_type",
        "7": "uninstall_key",
        "d": "file_paths",
        "f": "product_code",
        "10": "package_code",
        "11": "msi_product_code",
        "12": "msi_package_code",
    }

    def _GetInventoryBooleanValue(self, parser_mediator, registry_key, value_name):
        """Retrieves a boolean value of an inventory sub key.

        Depending on the Windows version the value data is a string, such as "0",
        "1" or "true", or an integer.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          value_name (str): name of the value.

        Returns:
          bool: value or None when the value data is empty or not supported.
        """
        value_data = self._GetInventoryValueData(
            parser_mediator, registry_key, value_name
        )
        if value_data is None:
            return None

        if isinstance(value_data, int):
            return bool(value_data)

        boolean_value = self._INVENTORY_BOOLEAN_VALUES.get(value_data.lower(), None)
        if boolean_value is None:
            parser_mediator.ProduceWarning(
                f"unsupported {value_name:s} value data in key: {registry_key.path:s}"
            )
        return boolean_value

    def _GetInventoryIntegerValue(self, parser_mediator, registry_key, value_name):
        """Retrieves an integer value of an inventory sub key.

        Depending on the Windows version the value data is a string or an integer.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          value_name (str): name of the value.

        Returns:
          int: value or None when the value data is empty or not supported.
        """
        value_data = self._GetInventoryValueData(
            parser_mediator, registry_key, value_name
        )
        if isinstance(value_data, str):
            try:
                value_data = int(value_data, 10)
            except ValueError:
                parser_mediator.ProduceWarning(
                    f"unsupported {value_name:s} value data in key: "
                    f"{registry_key.path:s}"
                )
                value_data = None

        return value_data

    def _GetInventoryStringValue(self, parser_mediator, registry_key, value_name):
        """Retrieves a string value of an inventory sub key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          value_name (str): name of the value.

        Returns:
          str: value or None when the value data is empty or not supported.
        """
        value_data = self._GetInventoryValueData(
            parser_mediator, registry_key, value_name
        )
        if isinstance(value_data, int):
            parser_mediator.ProduceWarning(
                f"unsupported {value_name:s} with an integer value data type in "
                f"key: {registry_key.path:s}"
            )
            value_data = None

        return value_data

    def _GetInventoryValueData(self, parser_mediator, registry_key, value_name):
        """Retrieves the data of a value of an inventory sub key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          value_name (str): name of the value.

        Returns:
          object: integer or string value data or None when the value is missing,
              the value data is empty or not supported.
        """
        registry_value = registry_key.GetValueByName(value_name)
        if not registry_value or not registry_value.data:
            return None

        value_data = None
        if registry_value.DataIsInteger() or registry_value.DataIsString():
            try:
                value_data = registry_value.GetDataAsObject()
            except dfwinreg_errors.WinRegistryValueError as exception:
                parser_mediator.ProduceWarning(
                    f"unable to retrieve {value_name:s} value data in key: "
                    f"{registry_key.path:s} with error: {exception!s}"
                )
                return None

        if isinstance(value_data, int):
            if value_data < 0:
                # dfwinreg represents integer value data as a signed integer.
                value_data += 1 << (8 * len(registry_value.data))

        elif not isinstance(value_data, str):
            parser_mediator.ProduceWarning(
                f"unsupported {value_name:s} with value data type: "
                f"{registry_value.data_type_string:s} in key: {registry_key.path:s}"
            )
            value_data = None

        elif not value_data:
            value_data = None

        return value_data

    def _GetValueDataAsObject(
        self, parser_mediator, key_path, value_name, registry_value
    ):
        """Retrieves the value data as an object from a Windows Registry value.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          key_path (str): key path.
          value_name (str): name of the value.
          registry_value (dfwinreg.WinRegistryValue): Windows Registry value.

        Returns:
          object: value data or None when the value data cannot be determined.
        """
        if registry_value.data is None:
            return "(empty)"

        try:
            value_object = registry_value.GetDataAsObject()

            if registry_value.DataIsMultiString():
                value_object = list(value_object)

            elif (
                not registry_value.DataIsInteger() and not registry_value.DataIsString()
            ):
                # Represent remaining types like REG_BINARY and
                # REG_RESOURCE_REQUIREMENT_LIST.
                value_object = registry_value.data

        except dfwinreg_errors.WinRegistryValueError as exception:
            parser_mediator.ProduceWarning(
                f"Unable to retrieve value data of type: "
                f"{registry_value.data_type_string:s} as object from value: "
                f"{value_name:s} in key: {key_path:s} with error: {exception!s}"
            )
            value_object = None

        return value_object

    def _ParseApplicationShortcutSubKey(self, parser_mediator, shortcut_sub_key):
        """Parses a Root\\InventoryApplicationShortcut\\%NAME%|%IDENTIFIER% key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          shortcut_sub_key (dfwinreg.WinRegistryKey): shortcut sub key of the
              InventoryApplicationShortcut Windows Registry key.
        """
        event_data = AMCacheApplicationShortcutEventData()
        event_data.last_written_time = shortcut_sub_key.last_written_time

        event_data.application_user_model_identifier = self._GetInventoryStringValue(
            parser_mediator, shortcut_sub_key, "ShortcutAumid"
        )
        event_data.program_identifier = self._GetInventoryStringValue(
            parser_mediator, shortcut_sub_key, "ShortcutProgramId"
        )
        event_data.shortcut_path = self._GetInventoryStringValue(
            parser_mediator, shortcut_sub_key, "ShortcutPath"
        )
        event_data.target_path = self._GetInventoryStringValue(
            parser_mediator, shortcut_sub_key, "ShortcutTargetPath"
        )
        parser_mediator.ProduceEventData(event_data)

    def _ParseApplicationSubKey(self, parser_mediator, application_sub_key):
        """Parses a Root\\InventoryApplicationFile\\%NAME%|%IDENTIFIER% key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          application_sub_key (dfwinreg.WinRegistryKey): application sub key of the
              InventoryApplicationFile Windows Registry key.
        """
        corrupted = False
        event_data = AMCacheFileEventData()

        for value_name, attribute_name in self._APPLICATION_SUB_KEY_VALUES.items():
            value = application_sub_key.GetValueByName(value_name)
            if value:
                value_data = self._GetValueDataAsObject(
                    parser_mediator, application_sub_key.path, value_name, value
                )
                setattr(event_data, attribute_name, value_data)

        install_date_value = application_sub_key.GetValueByName("InstallDate")
        if install_date_value:
            event_data.installation_time, value_corrupted = self._ParseDateStringValue(
                parser_mediator, application_sub_key.path, install_date_value
            )
            corrupted = corrupted or value_corrupted

        install_date_msi_value = application_sub_key.GetValueByName("InstallDateMsi")
        if install_date_msi_value:
            event_data.msi_installation_time, value_corrupted = (
                self._ParseDateStringValue(
                    parser_mediator, application_sub_key.path, install_date_msi_value
                )
            )
            corrupted = corrupted or value_corrupted

        link_date_value = application_sub_key.GetValueByName("LinkDate")
        if link_date_value:
            event_data.link_time, value_corrupted = self._ParseDateStringValue(
                parser_mediator, application_sub_key.path, link_date_value
            )
            corrupted = corrupted or value_corrupted

        event_data.application_key_last_written_time = (
            application_sub_key.last_written_time
        )
        parser_mediator.ProduceEventData(event_data, corrupted=corrupted)

    def _ParseDateStringValue(self, parser_mediator, key_path, registry_value):
        """Parses a date and time string value.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          key_path (str): key path.
          registry_value (dfwinreg.WinRegistryValue): Windows Registry value.

        Returns:
          tuple: containing:

              dfdatetime_time_elements.TimeElements: date and time value or None
                  if not available.
              bool: value to indicate the date and time string value was corrupted.
        """
        if not registry_value.DataIsString():
            parser_mediator.ProduceWarning(
                f"unsupported {registry_value.name:s} with value data type: "
                f"{registry_value.data_type_string:s} in key: {key_path:s}"
            )
            return None, False

        date_time_string = registry_value.GetDataAsObject()
        if not date_time_string:
            parser_mediator.ProduceWarning(
                f"missing {registry_value.name:s} value data in key: {key_path:s}"
            )
            return None, False

        re_match = self._LINK_DATE_TIME_RE.match(date_time_string)
        if not re_match:
            parser_mediator.ProduceWarning(
                f"unsupported {registry_value.name:s} value data: "
                f"{date_time_string!s} in key: {key_path:s}"
            )
            return None, False

        month, day_of_month, year, hours, minutes, seconds = re_match.groups()

        try:
            year = int(year, 10)
            month = int(month, 10)
            day_of_month = int(day_of_month, 10)
            hours = int(hours, 10)
            minutes = int(minutes, 10)
            seconds = int(seconds, 10)
        except (TypeError, ValueError):
            parser_mediator.ProduceWarning(
                f"invalid {registry_value.name:s} date time value: "
                f"{date_time_string!s} in key: {key_path:s}"
            )
            return None, True

        time_elements_tuple = (year, month, day_of_month, hours, minutes, seconds)

        try:
            date_time = dfdatetime_time_elements.TimeElements(
                time_elements_tuple=time_elements_tuple
            )
        except ValueError:
            parser_mediator.ProduceWarning(
                f"invalid {registry_value.name:s} date time value: "
                f"{time_elements_tuple!s} in key: {key_path:s}"
            )
            return None, True

        return date_time, False

    def _ParseDeviceContainerSubKey(self, parser_mediator, container_sub_key):
        """Parses a Root\\InventoryDeviceContainer\\%GUID% key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          container_sub_key (dfwinreg.WinRegistryKey): device container sub key of
              the InventoryDeviceContainer Windows Registry key.
        """
        event_data = AMCacheDeviceContainerEventData()
        event_data.container_identifier = container_sub_key.name
        event_data.last_written_time = container_sub_key.last_written_time

        event_data.categories = self._GetInventoryStringValue(
            parser_mediator, container_sub_key, "Categories"
        )
        event_data.discovery_method = self._GetInventoryStringValue(
            parser_mediator, container_sub_key, "DiscoveryMethod"
        )
        event_data.friendly_name = self._GetInventoryStringValue(
            parser_mediator, container_sub_key, "FriendlyName"
        )
        event_data.icon = self._GetInventoryStringValue(
            parser_mediator, container_sub_key, "Icon"
        )
        event_data.is_active = self._GetInventoryBooleanValue(
            parser_mediator, container_sub_key, "IsActive"
        )
        event_data.is_connected = self._GetInventoryBooleanValue(
            parser_mediator, container_sub_key, "IsConnected"
        )
        event_data.is_machine_container = self._GetInventoryBooleanValue(
            parser_mediator, container_sub_key, "IsMachineContainer"
        )
        event_data.is_networked = self._GetInventoryBooleanValue(
            parser_mediator, container_sub_key, "IsNetworked"
        )
        event_data.is_paired = self._GetInventoryBooleanValue(
            parser_mediator, container_sub_key, "IsPaired"
        )
        event_data.manufacturer = self._GetInventoryStringValue(
            parser_mediator, container_sub_key, "Manufacturer"
        )
        event_data.model_identifier = self._GetInventoryStringValue(
            parser_mediator, container_sub_key, "ModelId"
        )
        event_data.model_name = self._GetInventoryStringValue(
            parser_mediator, container_sub_key, "ModelName"
        )
        event_data.model_number = self._GetInventoryStringValue(
            parser_mediator, container_sub_key, "ModelNumber"
        )
        event_data.primary_category = self._GetInventoryStringValue(
            parser_mediator, container_sub_key, "PrimaryCategory"
        )
        event_data.state = self._GetInventoryIntegerValue(
            parser_mediator, container_sub_key, "State"
        )
        parser_mediator.ProduceEventData(event_data)

    def _ParseDevicePnpSubKey(self, parser_mediator, device_sub_key):
        """Parses a Root\\InventoryDevicePnp\\%DEVICE% key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          device_sub_key (dfwinreg.WinRegistryKey): device sub key of the
              InventoryDevicePnp Windows Registry key.
        """
        event_data = AMCacheDevicePnpEventData()
        # The name of the key is the device instance identifier with the path
        # segment separators replaced by a forward slash.
        event_data.device_instance_identifier = device_sub_key.name.replace("/", "\\")
        event_data.last_written_time = device_sub_key.last_written_time

        event_data.bus_reported_description = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "BusReportedDescription"
        )
        event_data.class_identifier = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "ClassGuid"
        )
        event_data.compatible_identifiers = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "COMPID"
        )
        event_data.container_identifier = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "ContainerId"
        )
        event_data.description = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "Description"
        )
        event_data.device_class = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "Class"
        )
        event_data.device_state = self._GetInventoryIntegerValue(
            parser_mediator, device_sub_key, "DeviceState"
        )
        event_data.driver_identifier = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "DriverId"
        )
        event_data.driver_name = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "DriverName"
        )
        event_data.driver_package_strong_name = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "DriverPackageStrongName"
        )
        event_data.driver_version = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "DriverVerVersion"
        )
        event_data.enumerator = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "Enumerator"
        )
        event_data.hardware_identifiers = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "HWID"
        )
        event_data.inf_name = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "Inf"
        )
        event_data.install_state = self._GetInventoryIntegerValue(
            parser_mediator, device_sub_key, "InstallState"
        )
        event_data.location_paths = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "LocationPaths"
        )
        event_data.manufacturer = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "Manufacturer"
        )
        event_data.matching_identifier = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "MatchingID"
        )
        event_data.model = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "Model"
        )
        event_data.parent_identifier = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "ParentId"
        )
        event_data.problem_code = self._GetInventoryIntegerValue(
            parser_mediator, device_sub_key, "ProblemCode"
        )
        event_data.provider = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "Provider"
        )
        event_data.service = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "Service"
        )
        event_data.stack_identifiers = self._GetInventoryStringValue(
            parser_mediator, device_sub_key, "STACKID"
        )
        event_data.driver_version_time, corrupted = self._ParseInventoryDateTimeValue(
            parser_mediator, device_sub_key, "DriverVerDate"
        )
        event_data.first_installation_time, value_corrupted = (
            self._ParseInventoryDateTimeValue(
                parser_mediator, device_sub_key, "FirstInstallDate"
            )
        )
        corrupted = corrupted or value_corrupted

        event_data.installation_time, value_corrupted = (
            self._ParseInventoryDateTimeValue(
                parser_mediator, device_sub_key, "InstallDate"
            )
        )
        corrupted = corrupted or value_corrupted

        parser_mediator.ProduceEventData(event_data, corrupted=corrupted)

    def _ParseDriverBinarySubKey(self, parser_mediator, driver_sub_key):
        """Parses a Root\\InventoryDriverBinary\\%DRIVER% key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          driver_sub_key (dfwinreg.WinRegistryKey): driver sub key of the
              InventoryDriverBinary Windows Registry key.
        """
        event_data = AMCacheDriverBinaryEventData()
        event_data.last_written_time = driver_sub_key.last_written_time

        event_data.checksum = self._GetInventoryIntegerValue(
            parser_mediator, driver_sub_key, "DriverCheckSum"
        )
        event_data.company_name = self._GetInventoryStringValue(
            parser_mediator, driver_sub_key, "DriverCompany"
        )
        event_data.driver_identifier = self._GetInventoryStringValue(
            parser_mediator, driver_sub_key, "DriverId"
        )
        # The name of the key is either the path of the driver binary, with
        # the path segment separators replaced by a forward slash, or the driver
        # identifier depending on the Windows version.
        if "/" in driver_sub_key.name:
            event_data.path = driver_sub_key.name.replace("/", "\\")
        elif not event_data.driver_identifier:
            event_data.driver_identifier = driver_sub_key.name

        event_data.driver_package_strong_name = self._GetInventoryStringValue(
            parser_mediator, driver_sub_key, "DriverPackageStrongName"
        )
        event_data.driver_type = self._GetInventoryIntegerValue(
            parser_mediator, driver_sub_key, "DriverType"
        )
        event_data.driver_version = self._GetInventoryStringValue(
            parser_mediator, driver_sub_key, "DriverVersion"
        )
        event_data.filename = self._GetInventoryStringValue(
            parser_mediator, driver_sub_key, "DriverName"
        )
        event_data.image_size = self._GetInventoryIntegerValue(
            parser_mediator, driver_sub_key, "ImageSize"
        )
        event_data.inf_name = self._GetInventoryStringValue(
            parser_mediator, driver_sub_key, "Inf"
        )
        event_data.is_in_box = self._GetInventoryBooleanValue(
            parser_mediator, driver_sub_key, "DriverInBox"
        )
        event_data.is_kernel_mode = self._GetInventoryBooleanValue(
            parser_mediator, driver_sub_key, "DriverIsKernelMode"
        )
        event_data.is_signed = self._GetInventoryBooleanValue(
            parser_mediator, driver_sub_key, "DriverSigned"
        )
        event_data.product_name = self._GetInventoryStringValue(
            parser_mediator, driver_sub_key, "Product"
        )
        event_data.product_version = self._GetInventoryStringValue(
            parser_mediator, driver_sub_key, "ProductVersion"
        )
        event_data.service = self._GetInventoryStringValue(
            parser_mediator, driver_sub_key, "Service"
        )
        event_data.wdf_version = self._GetInventoryStringValue(
            parser_mediator, driver_sub_key, "WdfVersion"
        )
        event_data.file_modification_time, corrupted = (
            self._ParseInventoryDateTimeValue(
                parser_mediator, driver_sub_key, "DriverLastWriteTime"
            )
        )
        timestamp = self._GetInventoryIntegerValue(
            parser_mediator, driver_sub_key, "DriverTimeStamp"
        )
        if timestamp is not None:
            event_data.link_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)

        parser_mediator.ProduceEventData(event_data, corrupted=corrupted)

    def _ParseDriverPackageSubKey(self, parser_mediator, package_sub_key):
        """Parses a Root\\InventoryDriverPackage\\%STRONG_NAME% key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          package_sub_key (dfwinreg.WinRegistryKey): driver package sub key of the
              InventoryDriverPackage Windows Registry key.
        """
        event_data = AMCacheDriverPackageEventData()
        event_data.driver_package_strong_name = package_sub_key.name
        event_data.last_written_time = package_sub_key.last_written_time

        event_data.class_identifier = self._GetInventoryStringValue(
            parser_mediator, package_sub_key, "ClassGuid"
        )
        event_data.device_class = self._GetInventoryStringValue(
            parser_mediator, package_sub_key, "Class"
        )
        event_data.directory = self._GetInventoryStringValue(
            parser_mediator, package_sub_key, "Directory"
        )
        event_data.driver_version = self._GetInventoryStringValue(
            parser_mediator, package_sub_key, "Version"
        )
        event_data.hardware_identifiers = self._GetInventoryStringValue(
            parser_mediator, package_sub_key, "Hwids"
        )
        event_data.inf_name = self._GetInventoryStringValue(
            parser_mediator, package_sub_key, "Inf"
        )
        event_data.provider = self._GetInventoryStringValue(
            parser_mediator, package_sub_key, "Provider"
        )
        event_data.submission_identifier = self._GetInventoryStringValue(
            parser_mediator, package_sub_key, "SubmissionId"
        )
        event_data.system_file = self._GetInventoryStringValue(
            parser_mediator, package_sub_key, "SYSFILE"
        )
        event_data.driver_version_time, corrupted = self._ParseInventoryDateTimeValue(
            parser_mediator, package_sub_key, "Date"
        )
        parser_mediator.ProduceEventData(event_data, corrupted=corrupted)

    def _ParseFileKey(self, parser_mediator, file_key):
        """Parses a Root\\File key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_key (dfwinreg.WinRegistryKey): the File Windows Registry key.
        """
        for volume_key in file_key.GetSubkeys():
            for file_reference_key in volume_key.GetSubkeys():
                self._ParseFileReferenceKey(parser_mediator, file_reference_key)

    def _ParseFileReferenceKey(self, parser_mediator, file_reference_key):
        """Parses a file reference key (sub key of Root\\File\\%VOLUME%) for events.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_reference_key (dfwinreg.WinRegistryKey): file reference Windows
              Registry key.
        """
        event_data = AMCacheFileEventData()

        try:
            if "0000" in file_reference_key.name:
                # A NTFS file reference is a combination of MFT entry and sequence
                # number.
                sequence_number, mft_entry = file_reference_key.name.split("0000")
                mft_entry = int(mft_entry, 16)
                sequence_number = int(sequence_number, 16)
                event_data.file_reference = f"{mft_entry:d}-{sequence_number:d}"
            else:
                # A FAT file reference is the offset of the corresponding directory
                # entry.
                file_reference = int(file_reference_key.name, 16)
                event_data.file_reference = f"{file_reference:d}"

        except (ValueError, TypeError):
            pass

        for value_name, attribute_name in self._FILE_REFERENCE_KEY_VALUES.items():
            value = file_reference_key.GetValueByName(value_name)
            if not value:
                continue

            value_data = self._GetValueDataAsObject(
                parser_mediator, file_reference_key.path, value_name, value
            )
            if attribute_name == "sha1" and value_data.startswith("0000"):
                # Strip off the 4 leading zero's from the sha1 hash.
                value_data = value_data[4:]

            setattr(event_data, attribute_name, value_data)

        write_time_value = file_reference_key.GetValueByName(
            self._AMCACHE_ENTRY_WRITE_TIME
        )
        if write_time_value:
            timestamp = write_time_value.GetDataAsObject()
            event_data.last_written_time = dfdatetime_filetime.Filetime(
                timestamp=timestamp
            )

        creation_time_value = file_reference_key.GetValueByName(
            self._AMCACHE_FILE_CREATION_TIME
        )
        if creation_time_value:
            timestamp = creation_time_value.GetDataAsObject()
            event_data.file_creation_time = dfdatetime_filetime.Filetime(
                timestamp=timestamp
            )

        modification_time_value = file_reference_key.GetValueByName(
            self._AMCACHE_FILE_MODIFICATION_TIME
        )
        if modification_time_value:
            timestamp = modification_time_value.GetDataAsObject()
            event_data.file_modification_time = dfdatetime_filetime.Filetime(
                timestamp=timestamp
            )

        link_time_value = file_reference_key.GetValueByName(self._AMCACHE_LINK_TIME)
        if link_time_value:
            timestamp = link_time_value.GetDataAsObject()
            event_data.link_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)

        parser_mediator.ProduceEventData(event_data)

    def _ParseInventoryApplicationFileKey(
        self, parser_mediator, inventory_application_file_key
    ):
        """Parses a Root\\InventoryApplicationFile key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          inventory_application_file_key (dfwinreg.WinRegistryKey): the
              InventoryApplicationFile Windows Registry key.
        """
        for application_sub_key in inventory_application_file_key.GetSubkeys():
            self._ParseApplicationSubKey(parser_mediator, application_sub_key)

    def _ParseInventoryApplicationSubKey(self, parser_mediator, application_sub_key):
        """Parses a Root\\InventoryApplication\\%IDENTIFIER% key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          application_sub_key (dfwinreg.WinRegistryKey): application sub key of the
              InventoryApplication Windows Registry key.
        """
        event_data = AMCacheApplicationEventData()
        event_data.last_written_time = application_sub_key.last_written_time

        event_data.bundle_manifest_path = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "BundleManifestPath"
        )
        event_data.entry_source = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "Source"
        )
        event_data.entry_type = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "Type"
        )
        event_data.installation_os_version = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "OSVersionAtInstallTime"
        )
        event_data.is_hidden = self._GetInventoryBooleanValue(
            parser_mediator, application_sub_key, "HiddenArp"
        )
        event_data.is_inbox_modern_application = self._GetInventoryBooleanValue(
            parser_mediator, application_sub_key, "InboxModernApp"
        )
        event_data.language_code = self._GetInventoryIntegerValue(
            parser_mediator, application_sub_key, "Language"
        )
        event_data.manifest_path = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "ManifestPath"
        )
        event_data.msi_package_code = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "MsiPackageCode"
        )
        event_data.msi_product_code = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "MsiProductCode"
        )
        event_data.name = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "Name"
        )
        event_data.package_full_name = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "PackageFullName"
        )
        event_data.program_identifier = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "ProgramId"
        )
        event_data.program_instance_identifier = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "ProgramInstanceId"
        )
        event_data.publisher = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "Publisher"
        )
        event_data.registry_key_path = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "RegistryKeyPath"
        )
        event_data.root_directory_path = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "RootDirPath"
        )
        event_data.store_application_type = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "StoreAppType"
        )
        event_data.uninstall_string = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "UninstallString"
        )
        event_data.version = self._GetInventoryStringValue(
            parser_mediator, application_sub_key, "Version"
        )
        event_data.installation_time, corrupted = self._ParseInventoryDateTimeValue(
            parser_mediator, application_sub_key, "InstallDate"
        )
        # The value is named InstallDateMsi or MsiInstallDate depending on
        # the Windows version.
        for value_name in ("InstallDateMsi", "MsiInstallDate"):
            date_time, value_corrupted = self._ParseInventoryDateTimeValue(
                parser_mediator, application_sub_key, value_name
            )
            corrupted = corrupted or value_corrupted
            if date_time:
                event_data.msi_installation_time = date_time

        parser_mediator.ProduceEventData(event_data, corrupted=corrupted)

    def _ParseInventoryDateTimeValue(self, parser_mediator, registry_key, value_name):
        """Parses a date and time string value of an inventory sub key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
          value_name (str): name of the value.

        Returns:
          tuple: containing:

              dfdatetime_time_elements.TimeElements: date and time value or None
                  if not available.
              bool: value to indicate the date and time string value was corrupted.
        """
        registry_value = registry_key.GetValueByName(value_name)
        if not registry_value:
            return None, False

        date_time_string = None
        if registry_value.DataIsMultiString() or registry_value.DataIsString():
            try:
                date_time_string = registry_value.GetDataAsObject()
            except dfwinreg_errors.WinRegistryValueError as exception:
                parser_mediator.ProduceWarning(
                    f"unable to retrieve {value_name:s} value data in key: "
                    f"{registry_key.path:s} with error: {exception!s}"
                )
                return None, False

            if registry_value.DataIsMultiString():
                # Older Windows versions store the date and time string in
                # a multi-string value, of which the first string is used.
                date_time_string = next(iter(date_time_string or []), None)

        else:
            parser_mediator.ProduceWarning(
                f"unsupported {value_name:s} with value data type: "
                f"{registry_value.data_type_string:s} in key: {registry_key.path:s}"
            )

        if not date_time_string:
            return None, False

        re_match = None
        for date_time_re in self._INVENTORY_DATE_TIME_RES:
            re_match = re_match or date_time_re.fullmatch(date_time_string)

        if not re_match:
            parser_mediator.ProduceWarning(
                f"unsupported {value_name:s} value data: {date_time_string!s} in "
                f"key: {registry_key.path:s}"
            )
            return None, False

        values = {name: int(value, 10) for name, value in re_match.groupdict().items()}

        precision = dfdatetime_definitions.PRECISION_1_DAY
        if "hours" in values:
            precision = dfdatetime_definitions.PRECISION_1_SECOND

        time_elements_tuple = (
            values["year"],
            values["month"],
            values["day_of_month"],
            values.get("hours", 0),
            values.get("minutes", 0),
            values.get("seconds", 0),
        )
        try:
            date_time = dfdatetime_time_elements.TimeElements(
                precision=precision, time_elements_tuple=time_elements_tuple
            )
        except ValueError:
            parser_mediator.ProduceWarning(
                f"invalid {value_name:s} date time value: "
                f"{time_elements_tuple!s} in key: {registry_key.path:s}"
            )
            return None, True

        return date_time, False

    def _ParseInventoryKey(self, parser_mediator, inventory_key, callback):
        """Parses the sub keys of a Root\\Inventory* key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          inventory_key (dfwinreg.WinRegistryKey): the inventory Windows Registry
              key.
          callback (function): method to parse a sub key of the inventory key.
        """
        for inventory_sub_key in inventory_key.GetSubkeys():
            callback(parser_mediator, inventory_sub_key)

    def _ParseProgramKey(self, parser_mediator, program_key):
        """Parses a program key (a sub key of Root\\Programs) for events.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          program_key (dfwinreg.WinRegistryKey): program Windows Registry key.
        """
        event_data = AMCacheProgramEventData()

        for value_name, attribute_name in self._PRODUCT_KEY_VALUES.items():
            value = program_key.GetValueByName(value_name)
            if value:
                value_data = self._GetValueDataAsObject(
                    parser_mediator, program_key.path, value_name, value
                )
                setattr(event_data, attribute_name, value_data)

        installation_time_value = program_key.GetValueByName(
            self._AMCACHE_P_INSTALLATION_TIME
        )
        if installation_time_value:
            timestamp = installation_time_value.GetDataAsObject()
            event_data.installation_time = dfdatetime_posix_time.PosixTime(
                timestamp=timestamp
            )

        parser_mediator.ProduceEventData(event_data)

    def _ParseProgramsKey(self, parser_mediator, programs_key):
        """Parses a Root\\Programs key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          programs_key (dfwinreg.WinRegistryKey): the Programs Windows Registry key.
        """
        for program_key in programs_key.GetSubkeys():
            self._ParseProgramKey(parser_mediator, program_key)

    def _ParseRootKey(self, parser_mediator, root_key):
        """Parses a Root key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          root_key (dfwinreg.WinRegistryKey): the Root Windows Registry key.
        """
        self._ProduceDefaultWindowsRegistryEvent(parser_mediator, root_key)

        for sub_key in root_key.GetSubkeys():
            self._ParseSubKey(parser_mediator, sub_key)

            if sub_key.name == "File":
                self._ParseFileKey(parser_mediator, sub_key)

            elif sub_key.name == "InventoryApplication":
                self._ParseInventoryKey(
                    parser_mediator, sub_key, self._ParseInventoryApplicationSubKey
                )

            elif sub_key.name == "InventoryApplicationFile":
                self._ParseInventoryApplicationFileKey(parser_mediator, sub_key)

            elif sub_key.name == "InventoryApplicationShortcut":
                self._ParseInventoryKey(
                    parser_mediator, sub_key, self._ParseApplicationShortcutSubKey
                )

            elif sub_key.name == "InventoryDeviceContainer":
                self._ParseInventoryKey(
                    parser_mediator, sub_key, self._ParseDeviceContainerSubKey
                )

            elif sub_key.name == "InventoryDevicePnp":
                self._ParseInventoryKey(
                    parser_mediator, sub_key, self._ParseDevicePnpSubKey
                )

            elif sub_key.name == "InventoryDriverBinary":
                self._ParseInventoryKey(
                    parser_mediator, sub_key, self._ParseDriverBinarySubKey
                )

            elif sub_key.name == "InventoryDriverPackage":
                self._ParseInventoryKey(
                    parser_mediator, sub_key, self._ParseDriverPackageSubKey
                )

            elif sub_key.name == "Programs":
                self._ParseProgramsKey(parser_mediator, sub_key)

    def _ParseSubKey(self, parser_mediator, registry_key):
        """Parses a sub key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): the Windows Registry key.
        """
        self._ProduceDefaultWindowsRegistryEvent(parser_mediator, registry_key)

        for sub_key in registry_key.GetSubkeys():
            self._ParseSubKey(parser_mediator, sub_key)

    def ExtractEvents(self, parser_mediator, registry_key, **kwargs):
        """Extracts events from a Windows Registry key.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          registry_key (dfwinreg.WinRegistryKey): Windows Registry key.
        """
        self._ParseRootKey(parser_mediator, registry_key)


winreg_parser.WinRegistryParser.RegisterPlugin(AMCachePlugin)
