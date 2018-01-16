# -*- coding: utf-8 -*-
"""Software update plist plugin."""

from __future__ import unicode_literals

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface



class SoftwareUpdatePlugin(interface.PlistPlugin):
  """Basic plugin to extract the MacOS update status.

  Further details about the extracted fields:
    LastFullSuccessfulDate:
      timestamp when MacOS was full update.
    LastSuccessfulDate:
      timestamp when MacOS was partially update.
  """

  NAME = 'maxos_software_update'
  DESCRIPTION = 'Parser for MacOS software update plist files.'

  PLIST_PATH = 'com.apple.SoftwareUpdate.plist'
  PLIST_KEYS = frozenset([
      'LastFullSuccessfulDate', 'LastSuccessfulDate',
      'LastAttemptSystemVersion', 'LastUpdatesAvailable',
      'LastRecommendedUpdatesAvailable', 'RecommendedUpdates'])

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant MacOS update entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    version = match.get('LastAttemptSystemVersion', 'N/A')
    pending = match.get('LastUpdatesAvailable', None)

    event_data = plist_event.PlistTimeEventData()
    event_data.desc = 'Last MacOS {0:s} full update.'.format(version)
    event_data.key = ''
    event_data.root = '/'

    datetime_value = match.get('LastFullSuccessfulDate', None)
    if datetime_value:
      event = time_events.PythonDatetimeEvent(
          datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    datetime_value = match.get('LastSuccessfulDate', None)
    if datetime_value and pending:
      software = []
      for update in match.get('RecommendedUpdates', []):
        identifier = update.get('Identifier', '<IDENTIFIER>')
        product_key = update.get('Product Key', '<PRODUCT_KEY>')

        software.append('{0:s}({1:s})'.format(identifier, product_key))

      if not software:
        return

      software = ','.join(software)
      event_data.desc = (
          'Last Mac OS {0!s} partially update, pending {1!s}: '
          '{2:s}.').format(version, pending, software)

      event = time_events.PythonDatetimeEvent(
          datetime_value, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(SoftwareUpdatePlugin)
