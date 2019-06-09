# -*- coding: utf-8 -*-
"""Windows event data attribute containers."""

from __future__ import unicode_literals

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

  DATA_TYPE = 'windows:distributed_link_tracking:creation'

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
      raise ValueError('Unsupported UUID version.')

    mac_address = '{0:s}:{1:s}:{2:s}:{3:s}:{4:s}:{5:s}'.format(
        uuid.hex[20:22], uuid.hex[22:24], uuid.hex[24:26], uuid.hex[26:28],
        uuid.hex[28:30], uuid.hex[30:32])

    super(WindowsDistributedLinkTrackingEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.mac_address = mac_address
    # TODO: replace origin my something machine readable.
    self.origin = origin
    self.uuid = '{0!s}'.format(uuid)


class WindowsRegistryEventData(events.EventData):
  """Windows Registry event data attribute container.

  Attributes:
    key_path (str): Windows Registry key path.
    values (str): names and data of the values in the key.
  """

  DATA_TYPE = 'windows:registry:key_value'

  def __init__(self):
    """Initializes event data."""
    super(WindowsRegistryEventData, self).__init__(data_type=self.DATA_TYPE)
    self.key_path = None
    self.values = None


class WindowsVolumeEventData(events.EventData):
  """Windows volume event data attribute container.

  Attributes:
    device_path (str): volume device path.
    origin (str): origin of the event (event source), for example
        the corresponding Prefetch file name.
    serial_number (str): volume serial number.
  """
  DATA_TYPE = 'windows:volume:creation'

  def __init__(self):
    """Initializes event data."""
    super(WindowsVolumeEventData, self).__init__(data_type=self.DATA_TYPE)
    self.device_path = None
    # TODO: replace origin with something machine readable.
    self.origin = None
    self.serial_number = None
