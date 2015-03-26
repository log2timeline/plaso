# -*- coding: utf-8 -*-
"""This file contains a default plist plugin in Plaso."""

from plaso.events import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class BluetoothPlugin(interface.PlistPlugin):
  """Basic plugin to extract interesting Bluetooth related keys."""

  NAME = 'plist_bluetooth'
  DESCRIPTION = u'Parser for Bluetooth plist files.'

  PLIST_PATH = 'com.apple.bluetooth.plist'
  PLIST_KEYS = frozenset(['DeviceCache', 'PairedDevices'])

  # LastInquiryUpdate = Device connected via Bluetooth Discovery.  Updated
  #   when a device is detected in discovery mode.  E.g. BT headphone power
  #   on.  Pairing is not required for a device to be discovered and cached.
  #
  # LastNameUpdate = When the human name was last set.  Usually done only once
  #   during initial setup.
  #
  # LastServicesUpdate = Time set when device was polled to determine what it
  #   is.  Usually done at setup or manually requested via advanced menu.

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant BT entries.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      match: Optional dictionary containing extracted keys from PLIST_KEYS.
             The default is None.
    """
    root = '/DeviceCache'

    for device, value in match['DeviceCache'].items():
      name = value.get('Name', '')
      if name:
        name = u''.join(('Name:', name))

      if device in match['PairedDevices']:
        desc = 'Paired:True {0:s}'.format(name)
        key = device
        if 'LastInquiryUpdate' in value:
          event_object = plist_event.PlistEvent(
              root, key, value['LastInquiryUpdate'], desc)
          parser_mediator.ProduceEvent(event_object)

      if value.get('LastInquiryUpdate'):
        desc = u' '.join(filter(None, ('Bluetooth Discovery', name)))
        key = u''.join((device, '/LastInquiryUpdate'))
        event_object = plist_event.PlistEvent(
            root, key, value['LastInquiryUpdate'], desc)
        parser_mediator.ProduceEvent(event_object)

      if value.get('LastNameUpdate'):
        desc = u' '.join(filter(None, ('Device Name Set', name)))
        key = u''.join((device, '/LastNameUpdate'))
        event_object = plist_event.PlistEvent(
            root, key, value['LastNameUpdate'], desc)
        parser_mediator.ProduceEvent(event_object)

      if value.get('LastServicesUpdate'):
        desc = desc = u' '.join(filter(None, ('Services Updated', name)))
        key = ''.join((device, '/LastServicesUpdate'))
        event_object = plist_event.PlistEvent(
            root, key, value['LastServicesUpdate'], desc)
        parser_mediator.ProduceEvent(event_object)


plist.PlistParser.RegisterPlugin(BluetoothPlugin)
