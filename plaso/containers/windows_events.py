# -*- coding: utf-8 -*-
"""This file contains the Windows specific event object classes."""

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import eventdata


class WindowsDistributedLinkTrackingCreationEvent(time_events.UUIDTimeEvent):
  """Convenience class for a Windows distributed link creation event.

  Attributes:
    origin: a string containing the origin of the event (event source).
            E.g. the path of the corresponding LNK file or file reference
            MFT entry with the corresponding NTFS $OBJECT_ID attribute.
  """

  DATA_TYPE = u'windows:distributed_link_tracking:creation'

  def __init__(self, uuid, origin):
    """Initializes an event object.

    Args:
      uuid: an uuid object (instance of uuid.UUID).
      origin: a string containing the origin of the event (event source).
              E.g. the path of the corresponding LNK file or file reference
              MFT entry with the corresponding NTFS $OBJECT_ID attribute.
    """
    super(WindowsDistributedLinkTrackingCreationEvent, self).__init__(
        uuid, eventdata.EventTimestamp.CREATION_TIME)

    # TODO: replace origin with something machine readable.
    self.origin = origin


class WindowsRegistryInstallationEventData(events.EventData):
  """Windows installation event data.

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
  """Windows Registry event data.

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
  """Windows Registry list event data e.g. MRU.

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
  """Windows Registry service event data.

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


class WindowsVolumeCreationEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows volume creation event.

  Attributes:
    device_path: a string containing the volume device path.
    origin: a string containing the origin of the event (event source).
            E.g. corresponding Prefetch file name.
    serial_number: a string containing the volume serial number.
  """
  DATA_TYPE = u'windows:volume:creation'

  def __init__(self, filetime, device_path, serial_number, origin):
    """Initializes an event object.

    Args:
      filetime: an integer containing the FILETIME timestamp value.
      device_path: a string containing the volume device path.
      origin: a string containing the origin of the event (event source).
              E.g. corresponding Prefetch file name.
      serial_number: a string containing the volume serial number.
    """
    super(WindowsVolumeCreationEvent, self).__init__(
        filetime, eventdata.EventTimestamp.CREATION_TIME)

    self.device_path = device_path
    self.origin = origin
    self.serial_number = serial_number
