# -*- coding: utf-8 -*-
"""Software update plist plugin."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class SoftwareUpdatePlugin(interface.PlistPlugin):
  """Basic plugin to extract the Mac OS X update status.

  Further details about the extracted fields:
    LastFullSuccessfulDate:
      timestamp when Mac OS X was full update.
    LastSuccessfulDate:
      timestamp when Mac OS X was partially update.
  """

  NAME = 'maxos_software_update'
  DESCRIPTION = 'Parser for Mac OS X software update plist files.'

  PLIST_PATH = 'com.apple.SoftwareUpdate.plist'
  PLIST_KEYS = frozenset([
      'LastFullSuccessfulDate', 'LastSuccessfulDate',
      'LastAttemptSystemVersion', 'LastUpdatesAvailable',
      'LastRecommendedUpdatesAvailable', 'RecommendedUpdates'])

  # pylint: disable=arguments-differ
  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Mac OS X update entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    version = match.get('LastAttemptSystemVersion', 'N/A')
    pending = match.get('LastUpdatesAvailable', None)

    event_data = plist_event.PlistTimeEventData()
    event_data.desc = 'Last Mac OS X {0:s} full update.'.format(version)
    event_data.key = ''
    event_data.root = '/'

    datetime_value = match.get('LastFullSuccessfulDate', None)
    if datetime_value:
      timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
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

      timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(SoftwareUpdatePlugin)
