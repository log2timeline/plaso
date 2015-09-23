# -*- coding: utf-8 -*-
"""This file contains the Windows specific event object classes."""

from plaso.events import time_events
from plaso.lib import eventdata


class WindowsDistributedLinkTrackingCreationEvent(time_events.UUIDTimeEvent):
  """Convenience class for a Windows distributed link creation event.

  Attributes:
    origin: a string containing the origin of the event (event source).
            E.g. the path of the corresponding LNK file or file reference
            MFT entry with the corresponding NTFS $OBJECT_ID attribute.
  """

  DATA_TYPE = 'windows:distributed_link_tracking:creation'

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

    self.origin = origin


class WindowsRegistryEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows Registry-based event."""

  DATA_TYPE = 'windows:registry:key_value'

  def __init__(
      self, filetime, key_path, values_dict, usage=None, offset=None,
      registry_file_type=None, source_append=None, urls=None):
    """Initializes a Windows registry event.

    Args:
      filetime: the FILETIME timestamp value.
      key_path: the Windows Registry key path.
      values_dict: dictionary object containing values of the key.
      usage: optional description of the usage of the time value.
      offset: optional (data) offset of the Registry key or value.
      registry_file_type: optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE.
      source_append: optional string to append to the source_long of the event.
      urls: optional list of URLs.
    """
    if usage is None:
      usage = eventdata.EventTimestamp.WRITTEN_TIME

    super(WindowsRegistryEvent, self).__init__(filetime, usage)

    if key_path:
      # TODO: rename keyname to key_path
      self.keyname = key_path

    self.regvalue = values_dict

    if offset or isinstance(offset, (int, long)):
      self.offset = offset

    if registry_file_type:
      self.registry_file_type = registry_file_type

    if source_append:
      self.source_append = source_append

    if urls:
      self.url = u' - '.join(urls)


class WindowsRegistryInstallationEvent(time_events.PosixTimeEvent):
  """Convenience class for a Windows installation event.

  Attributes:
    key_path: the Windows Registry key path.
    owner: string containing the owner.
    product_name: string containing the produce name.
    service_pack: string containing service pack.
    version: string containing the version.
  """
  DATA_TYPE = 'windows:registry:installation'

  def __init__(
      self, posix_time, key_path, owner, product_name, service_pack, version):
    """Initializes an event object.

    Args:
      posix_time: the POSIX time value.
      key_path: the Windows Registry key path.
      owner: string containing the owner.
      product_name: string containing the produce name.
      service_pack: string containing service pack.
      version: string containing the version.
    """
    super(WindowsRegistryInstallationEvent, self).__init__(
        posix_time, eventdata.EventTimestamp.INSTALLATION_TIME)

    self.key_path = key_path
    self.owner = owner
    self.product_name = product_name
    self.service_pack = service_pack
    self.version = version


class WindowsRegistryListEvent(time_events.FiletimeEvent):
  """Convenience class for a list retrieved from the Registry e.g. MRU.

  Attributes:
    key_path: string containing the Windows Registry key path.
    list_name: string containing the name of the list.
    list_values: string containing the list values.
    value_name: string containing the Windows Registry value name.
  """
  DATA_TYPE = 'windows:registry:list'

  def __init__(
      self, filetime, key_path, list_name, list_values,
      timestamp_description=None, value_name=None):
    """Initializes a Windows registry event.

    Args:
      filetime: the FILETIME timestamp value.
      key_path: string containing the Windows Registry key path.
      list_name: string containing the name of the list.
      list_values: string containing the list values.
      timestamp_description: optional usage string for the timestamp value.
      value_name: optional string containing the Windows Registry value name.
    """
    if timestamp_description is None:
      timestamp_description = eventdata.EventTimestamp.WRITTEN_TIME

    super(WindowsRegistryListEvent, self).__init__(
        filetime, timestamp_description)

    self.key_path = key_path
    self.list_name = list_name
    self.list_values = list_values
    self.value_name = value_name


class WindowsRegistryServiceEvent(WindowsRegistryEvent):
  """Convenience class for service information retrieved from the Registry."""
  DATA_TYPE = 'windows:registry:service'


class WindowsVolumeCreationEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows volume creation event.

  Attributes:
    device_path: a string containing the volume device path.
    serial_number: a string containing the volume serial number.
    origin: a string containing the origin of the event (event source).
            E.g. corresponding Prefetch file name.
  """
  DATA_TYPE = 'windows:volume:creation'

  def __init__(self, filetime, device_path, serial_number, origin):
    """Initializes an event object.

    Args:
      filetime: the FILETIME timestamp value.
      device_path: a string containing the volume device path.
      serial_number: a string containing the volume serial number.
      origin: a string containing the origin of the event (event source).
              E.g. corresponding Prefetch file name.
    """
    super(WindowsVolumeCreationEvent, self).__init__(
        filetime, eventdata.EventTimestamp.CREATION_TIME)

    self.device_path = device_path
    self.serial_number = serial_number
    self.origin = origin
