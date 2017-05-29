# -*- coding: utf-8 -*-
"""Windows event data attribute containers."""

from plaso.containers import events


class WindowsDistributedLinkTrackingEventData(events.EventData):
  """Windows distributed link event data attribute container.

  Attributes:
    mac_address (str): MAC address stored in the UUID.
    origin (str): origin of the event (event source).
        E.g. the path of the corresponding LNK file or file reference
        MFT entry with the corresponding NTFS $OBJECT_ID attribute.
    uuid (str): UUID.
  """

  DATA_TYPE = u'windows:distributed_link_tracking:creation'

  def __init__(self, uuid, origin):
    """Initializes an event object.

    Args:
      uuid (uuid.UUID): UUID.
      origin (str): origin of the event (event source).
          E.g. the path of the corresponding LNK file or file reference
          MFT entry with the corresponding NTFS $OBJECT_ID attribute.

    Raises:
      ValueError: if the UUID version is not supported.
    """
    if uuid.version != 1:
      raise ValueError(u'Unsupported UUID version.')

    mac_address = u'{0:s}:{1:s}:{2:s}:{3:s}:{4:s}:{5:s}'.format(
        uuid.hex[20:22], uuid.hex[22:24], uuid.hex[24:26], uuid.hex[26:28],
        uuid.hex[28:30], uuid.hex[30:32])

    super(WindowsDistributedLinkTrackingEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.mac_address = mac_address
    # TODO: replace origin my something machine readable.
    self.origin = origin
    self.uuid = u'{0!s}'.format(uuid)


class WindowsRegistryInstallationEventData(events.EventData):
  """Windows installation event data attribute container.

  Attributes:
    key_path (str): Windows Registry key path.
    owner (str): owner.
    product_name (str): product name.
    service_pack (str): service pack.
    version (str): version.
  """

  DATA_TYPE = u'windows:registry:installation'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryInstallationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.key_path = None
    self.owner = None
    self.product_name = None
    self.service_pack = None
    self.version = None


class WindowsRegistryEventData(events.EventData):
  """Windows Registry event data attribute container.

  Attributes:
    key_path (str): Windows Registry key path.
    regvalue (dict[str, object]): values in the key.
    source_append (str): text to append to the source_long of the event.
    urls (list[str]): URLs.
  """

  DATA_TYPE = u'windows:registry:key_value'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.key_path = None
    # TODO: deprecate regvalue.
    self.regvalue = None
    # TODO: deprecate source_append.
    self.source_append = None
    # TODO: deprecate urls.
    self.urls = None


class WindowsRegistryListEventData(events.EventData):
  """Windows Registry list event data attribute container.

  Windows Registry list event data is used to store a MRU.

  Attributes:
    key_path (str): Windows Registry key path.
    list_name (str): name of the list.
    list_values (str): values in the list.
    value_name (str): Windows Registry value name.
  """
  DATA_TYPE = u'windows:registry:list'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryListEventData, self).__init__(data_type=self.DATA_TYPE)
    self.key_path = None
    self.list_name = None
    self.list_values = None
    self.value_name = None


class WindowsRegistryServiceEventData(events.EventData):
  """Windows Registry service event data attribute container.

  Attributes:
    key_path (str): Windows Registry key path.
    offset (int): data offset of the Windows Registry key or value.
    regvalue (dict[str, str]): values of a key.
    urls (Optional[list[str]]): URLs.
  """

  DATA_TYPE = u'windows:registry:service'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryServiceEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.key_path = None
    # TODO: deprecate regvalue.
    self.regvalue = None
    # TODO: deprecate source_append.
    self.source_append = None
    # TODO: deprecate urls.
    self.urls = None


class WindowsVolumeEventData(events.EventData):
  """Windows volume event data attribute container.

  Attributes:
    device_path (str): volume device path.
    origin (str): origin of the event (event source), for example
        the corresponding Prefetch file name.
    serial_number (str): volume serial number.
  """
  DATA_TYPE = u'windows:volume:creation'

  def __init__(self):
    """Initializes event data."""
    super(WindowsVolumeEventData, self).__init__(data_type=self.DATA_TYPE)
    self.device_path = None
    # TODO: replace origin my something machine readable.
    self.origin = None
    self.serial_number = None
