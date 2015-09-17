# -*- coding: utf-8 -*-
"""This file contains the Windows specific event object classes."""

from plaso.events import time_events
from plaso.lib import eventdata


class WindowsDistributedLinkTrackingCreationEvent(time_events.UUIDTimeEvent):
  """Convenience class for a Windows distributed link creation event."""

  DATA_TYPE = 'windows:distributed_link_tracking:creation'

  def __init__(self, uuid, origin):
    """Initializes an event object.

    Args:
      uuid: A uuid object (instance of uuid.UUID).
      origin: A string containing the origin of the event (event source).
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
      values_dict: Dictionary object containing values of the key.
      usage: Optional description of the usage of the time value.
             The default is None.
      offset: Optional (data) offset of the Registry key or value.
              The default is None.
      registry_file_type: Optional string containing the Windows Registry file
                          type, e.g. NTUSER, SOFTWARE. The default is None.
      source_append: Optional string to append to the source_long of the event.
                     The default is None.
      urls: Optional list of URLs. The default is None.
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


class WindowsRegistryServiceEvent(WindowsRegistryEvent):
  """Convenience class for service entries retrieved from the registry."""
  DATA_TYPE = 'windows:registry:service'


class WindowsVolumeCreationEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows volume creation event."""

  DATA_TYPE = 'windows:volume:creation'

  def __init__(self, filetime, device_path, serial_number, origin):
    """Initializes an event object.

    Args:
      filetime: The FILETIME timestamp value.
      device_path: A string containing the volume device path.
      serial_number: A string containing the volume serial number.
      origin: A string containing the origin of the event (event source).
    """
    super(WindowsVolumeCreationEvent, self).__init__(
        filetime, eventdata.EventTimestamp.CREATION_TIME)

    self.device_path = device_path
    self.serial_number = serial_number
    self.origin = origin
