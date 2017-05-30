# -*- coding: utf-8 -*-
"""Software update plist plugin."""

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

  NAME = u'maxos_software_update'
  DESCRIPTION = u'Parser for Mac OS X software update plist files.'

  PLIST_PATH = u'com.apple.SoftwareUpdate.plist'
  PLIST_KEYS = frozenset([
      u'LastFullSuccessfulDate', u'LastSuccessfulDate',
      u'LastAttemptSystemVersion', u'LastUpdatesAvailable',
      u'LastRecommendedUpdatesAvailable', u'RecommendedUpdates'])

  def GetEntries(self, parser_mediator, match=None, **unused_kwargs):
    """Extracts relevant Mac OS X update entries.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      match (Optional[dict[str: object]]): keys extracted from PLIST_KEYS.
    """
    version = match.get(u'LastAttemptSystemVersion', u'N/A')
    pending = match.get(u'LastUpdatesAvailable', None)

    event_data = plist_event.PlistTimeEventData()
    event_data.desc = u'Last Mac OS X {0:s} full update.'.format(version)
    event_data.key = u''
    event_data.root = u'/'

    datetime_value = match.get(u'LastFullSuccessfulDate', None)
    if datetime_value:
      timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    datetime_value = match.get(u'LastSuccessfulDate', None)
    if datetime_value and pending:
      software = []
      for update in match.get(u'RecommendedUpdates', []):
        identifier = update.get(u'Identifier', u'<IDENTIFIER>')
        product_key = update.get(u'Product Key', u'<PRODUCT_KEY>')

        software.append(u'{0:s}({1:s})'.format(identifier, product_key))

      if not software:
        return

      software = u','.join(software)
      event_data.desc = (
          u'Last Mac OS {0!s} partially update, pending {1!s}: '
          u'{2:s}.').format(version, pending, software)

      timestamp = timelib.Timestamp.FromPythonDatetime(datetime_value)
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(SoftwareUpdatePlugin)
