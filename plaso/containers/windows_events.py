"""Windows event data attribute containers."""

from dfdatetime import uuid_time as dfdatetime_uuid_time

from plaso.containers import events


class WindowsDistributedLinkTrackingEventData(events.EventData):
    """Windows distributed link event data attribute container.

    Attributes:
      creation_time (dfdatetime.DateTimeValues): file entry creation date
          and time.
      mac_address (str): MAC address stored in the UUID.
      origin (str): origin of the event (event source).
          E.g. the path of the corresponding LNK file or file reference
          MFT entry with the corresponding NTFS $OBJECT_ID attribute.
      uuid (str): UUID.
    """

    DATA_TYPE = "windows:distributed_link_tracking:creation"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.creation_time = None
        self.mac_address = None
        # TODO: replace origin my something machine readable.
        self.origin = None
        self.uuid = None

    @classmethod
    def CreateFromUUID(cls, uuid_object, origin):
        """Creates event data from a distributed link tracking identifier.

        Args:
          uuid_object (uuid.UUID): UUID of the distributed link tracking identifier.
          origin (str): origin of the event (event source).
              E.g. the path of the corresponding LNK file or file reference
              MFT entry with the corresponding NTFS $OBJECT_ID attribute.

        Returns:
          WindowsDistributedLinkTrackingEventData: event data.

        Raises:
          ValueError: if the UUID version is not supported.
        """
        if uuid_object.version != 1:
            raise ValueError("Unsupported UUID version.")

        mac_address = (
            f"{uuid_object.hex[20:22]:s}:{uuid_object.hex[22:24]:s}:"
            f"{uuid_object.hex[24:26]:s}:{uuid_object.hex[26:28]:s}:"
            f"{uuid_object.hex[28:30]:s}:{uuid_object.hex[30:32]:s}"
        )

        event_data = cls()
        event_data.creation_time = dfdatetime_uuid_time.UUIDTime(
            timestamp=uuid_object.time
        )
        event_data.mac_address = mac_address
        event_data.origin = origin
        event_data.uuid = f"{uuid_object!s}"

        return event_data


class WindowsRegistryEventData(events.EventData):
    """Windows Registry event data attribute container.

    Attributes:
      key_path (str): Windows Registry key path.
      last_written_time (dfdatetime.DateTimeValues): key last written date and
          time.
      values (list[tuple[str, str, str]]): name, data type and data of the values
          in the key.
    """

    DATA_TYPE = "windows:registry:key_value"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.key_path = None
        self.last_written_time = None
        self.values = None


class WindowsShellItemFileEntryEventData(events.EventData):
    """Windows shell item file entry event data attribute container.

    Attributes:
      access_time (dfdatetime.DateTimeValues): file entry last access date
          and time.
      creation_time (dfdatetime.DateTimeValues): file entry creation date
          and time.
      file_reference (str): NTFS file reference, in the format:
          "MTF entry - sequence number".
      localized_name (str): localized name of the file entry shell item.
      long_name (str): long name of the file entry shell item.
      modification_time (dfdatetime.DateTimeValues): file entry last modification
          date and time.
      name (str): name of the file entry shell item.
      origin (str): origin of the event.
      shell_item_path (str): shell item path.
    """

    DATA_TYPE = "windows:shell_item:file_entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.access_time = None
        self.creation_time = None
        self.file_reference = None
        self.localized_name = None
        self.long_name = None
        self.modification_time = None
        self.name = None
        self.origin = None
        self.shell_item_path = None


class WindowsVolumeEventData(events.EventData):
    """Windows volume event data attribute container.

    Attributes:
      creation_time (dfdatetime.DateTimeValues): volume creation date and time.
      device_path (str): volume device path.
      origin (str): origin of the event (event source), for example
          the corresponding Prefetch file name.
      serial_number (str): volume serial number.
    """

    DATA_TYPE = "windows:volume:creation"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.creation_time = None
        self.device_path = None
        # TODO: replace origin with something machine readable.
        self.origin = None
        self.serial_number = None
