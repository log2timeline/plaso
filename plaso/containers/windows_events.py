# -*- coding: utf-8 -*-
"""This file contains the Windows specific event object classes."""

from plaso.containers import time_events
from plaso.lib import eventdata
from plaso.lib import py2to3


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

    self.origin = origin


class WindowsRegistryEvent(time_events.FiletimeEvent):
  """Convenience class for a Windows Registry-based event.

  Attributes:
    key_path: a string containing the Windows Registry key path.
    offset: an integer containing the data offset of the Windows Registry
            key or value.
    regvalue: a dictionary containing the values of the key.
    urls: optional list of strings containing URLs.
  """

  DATA_TYPE = u'windows:registry:key_value'

  def __init__(
      self, filetime, key_path, values_dict, usage=None, offset=None,
      source_append=None, urls=None):
    """Initializes a Windows Registry event.

    Args:
      filetime: a FILETIME timestamp time object (instance of
                dfdatetime.Filetime).
      key_path: a string containing the Windows Registry key path.
      values_dict: dictionary object containing values of the key.
      usage: optional string containing the description of the usage of
             the filetime timestamp.
      offset: optional integer containing the data offset of the Windows
              Registry key or value.
      source_append: optional string to append to the source_long of the event.
      urls: optional list of strings containing URLs.
    """
    # TODO: remove this override any other meaning derived from the timestamp
    # should be done at the analysis phase.
    if usage is None:
      usage = eventdata.EventTimestamp.WRITTEN_TIME

    super(WindowsRegistryEvent, self).__init__(filetime.timestamp, usage)

    self.key_path = key_path
    # TODO: rename regvalue to ???.
    self.regvalue = values_dict

    # TODO: determine how should offset 0 be handled.
    if offset or isinstance(offset, py2to3.INTEGER_TYPES):
      self.offset = offset

    # TODO: deprecate and remove.
    if source_append:
      self.source_append = source_append

    if urls:
      self.urls = urls


class WindowsRegistryInstallationEvent(time_events.PosixTimeEvent):
  """Convenience class for a Windows installation event.

  Attributes:
    key_path: a string containing the Windows Registry key path.
    owner: a string containing the owner.
    product_name: a string containing the produce name.
    service_pack: a string containing service pack.
    version: a string containing the version.
  """
  DATA_TYPE = u'windows:registry:installation'

  def __init__(
      self, posix_time, key_path, owner, product_name, service_pack, version):
    """Initializes an event object.

    Args:
      posix_time: the POSIX time value.
      key_path: a string containing the Windows Registry key path.
      owner: a string containing the owner.
      product_name: a string containing the produce name.
      service_pack: a string containing service pack.
      version: a string containing the version.
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
    key_path: a string containing the Windows Registry key path.
    list_name: a string containing the name of the list.
    list_values: a string containing the list values.
    value_name: a string containing the Windows Registry value name.
  """
  DATA_TYPE = u'windows:registry:list'

  def __init__(
      self, filetime, key_path, list_name, list_values,
      timestamp_description=None, value_name=None):
    """Initializes a Windows Registry event.

    Args:
      filetime: a FILETIME timestamp time object (instance of
                dfdatetime.Filetime).
      key_path: a string containing the Windows Registry key path.
      list_name: a string containing the name of the list.
      list_values: a string containing the list values.
      timestamp_description: optional usage string for the timestamp value.
      value_name: optional string containing the Windows Registry value name.
    """
    super(WindowsRegistryListEvent, self).__init__(
        filetime.timestamp, eventdata.EventTimestamp.WRITTEN_TIME)
    self.key_path = key_path
    self.list_name = list_name
    self.list_values = list_values
    self.value_name = value_name


class WindowsRegistryServiceEvent(WindowsRegistryEvent):
  """Convenience class for service information retrieved from the Registry."""
  DATA_TYPE = u'windows:registry:service'


class WindowsRegistryNetworkEvent(time_events.SystemtimeEvent):
  """Convenience class for a Windows network event.

  Attributes:
    connection_type: a string containing the type of connection.
    default_gateway_mac: MAC address for the default gateway.
    description: a string containing the description of the wireless connection.
    dns_suffix: the DNS suffix.
    source_append: optional string to append to the source_long of the event.
    ssid: the SSID of the connection.
  """
  DATA_TYPE = u'windows:registry:network'

  def __init__(
      self, systemtime, timestamp_description, ssid, description,
      connection_type, default_gateway_mac, dns_suffix):
    """Initializes an event object.

    Args:
      systemtime: a bytestring containing the SYSTEMTIME timestamp value.
      timestamp_description: string containing timestamp description.
      ssid: the SSID of the connection.
      description: a string containing the description of the wireless
                   connection.
      connection_type: a string containing the type of connection.
      default_gateway_mac: MAC address for the default gateway.
      dns_suffix: the DNS suffix.
    """
    super(WindowsRegistryNetworkEvent, self).__init__(
        systemtime, timestamp_description)

    self.connection_type = connection_type
    self.default_gateway_mac = default_gateway_mac
    self.description = description
    self.dns_suffix = dns_suffix
    self.ssid = ssid


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
