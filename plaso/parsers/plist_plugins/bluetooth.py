# -*- coding: utf-8 -*-
"""This file contains a default plist plugin in Plaso."""

from plaso.events import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class BluetoothPlugin(interface.PlistPlugin):
  """Basic plugin to extract interesting Bluetooth related keys.

  Additional details about the fields.

  LastInquiryUpdate:
    Device connected via Bluetooth Discovery. Updated
    when a device is detected in discovery mode. E.g. BT headphone power
    on. Pairing is not required for a device to be discovered and cached.

  LastNameUpdate:
    When the human name was last set. Usually done only once during
    initial setup.

  LastServicesUpdate:
    Time set when device was polled to determine what it is. Usually
    done at setup or manually requested via advanced menu.
  """

  NAME = u'macosx_bluetooth'
  DESCRIPTION = u'Parser for Bluetooth plist files.'

  PLIST_PATH = u'com.apple.bluetooth.plist'
  PLIST_KEYS = frozenset([u'DeviceCache', u'PairedDevices'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant BT entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing extracted keys from PLIST_KEYS.
    """
    root = u'/DeviceCache'

    if u'DeviceCache' not in match:
      return

    for device, value in match[u'DeviceCache'].iteritems():
      name = value.get(u'Name', u'')
      if name:
        name = u''.join((u'Name:', name))

      if device in match.get(u'PairedDevices', []):
        desc = u'Paired:True {0:s}'.format(name)
        key = device
        if u'LastInquiryUpdate' in value:
          event_object = plist_event.PlistEvent(
              root, key, value[u'LastInquiryUpdate'], desc)
          parser_mediator.ProduceEvent(event_object)

      if value.get(u'LastInquiryUpdate', None):
        desc = u' '.join(filter(None, (u'Bluetooth Discovery', name)))
        key = u''.join((device, u'/LastInquiryUpdate'))
        event_object = plist_event.PlistEvent(
            root, key, value[u'LastInquiryUpdate'], desc)
        parser_mediator.ProduceEvent(event_object)

      if value.get(u'LastNameUpdate', None):
        desc = u' '.join(filter(None, (u'Device Name Set', name)))
        key = u''.join((device, u'/LastNameUpdate'))
        event_object = plist_event.PlistEvent(
            root, key, value[u'LastNameUpdate'], desc)
        parser_mediator.ProduceEvent(event_object)

      if value.get(u'LastServicesUpdate', None):
        desc = desc = u' '.join(filter(None, (u'Services Updated', name)))
        key = u''.join((device, u'/LastServicesUpdate'))
        event_object = plist_event.PlistEvent(
            root, key, value[u'LastServicesUpdate'], desc)
        parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(BluetoothPlugin)
