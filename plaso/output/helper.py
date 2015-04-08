# -*- coding: utf-8 -*-

from plaso.lib import eventdata


def GetLegacy(evt):
  """Return a legacy MACB representation of the event."""
  # TODO: Fix this function when the MFT parser has been implemented.
  # The filestat parser is somewhat limited.
  # Also fix this when duplicate entries have been implemented so that
  # the function actually returns more than a single entry (as in combined).
  if evt.data_type.startswith('fs:'):
    letter = evt.timestamp_desc[0]

    if letter == 'm':
      return 'M...'
    elif letter == 'a':
      return '.A..'
    elif letter == 'c':
      if evt.timestamp_desc[1] == 'r':
        return '...B'

      return '..C.'
    else:
      return '....'

  # Access time.
  if evt.timestamp_desc in [
      eventdata.EventTimestamp.ACCESS_TIME,
      eventdata.EventTimestamp.ACCOUNT_CREATED,
      eventdata.EventTimestamp.PAGE_VISITED,
      eventdata.EventTimestamp.LAST_VISITED_TIME,
      eventdata.EventTimestamp.START_TIME,
      eventdata.EventTimestamp.LAST_SHUTDOWN,
      eventdata.EventTimestamp.LAST_LOGIN_TIME,
      eventdata.EventTimestamp.LAST_PASSWORD_RESET,
      eventdata.EventTimestamp.LAST_CONNECTED,
      eventdata.EventTimestamp.LAST_RUNTIME,
      eventdata.EventTimestamp.LAST_PRINTED]:
    return '.A..'

  # Content modification.
  if evt.timestamp_desc in [
      eventdata.EventTimestamp.MODIFICATION_TIME,
      eventdata.EventTimestamp.WRITTEN_TIME,
      eventdata.EventTimestamp.DELETED_TIME]:
    return 'M...'

  # Content creation time.
  if evt.timestamp_desc in [
      eventdata.EventTimestamp.CREATION_TIME,
      eventdata.EventTimestamp.ADDED_TIME,
      eventdata.EventTimestamp.FILE_DOWNLOADED,
      eventdata.EventTimestamp.FIRST_CONNECTED]:
    return '...B'

  # Metadata modification.
  if evt.timestamp_desc in [
      eventdata.EventTimestamp.CHANGE_TIME,
      eventdata.EventTimestamp.ENTRY_MODIFICATION_TIME]:
    return '..C.'

  return '....'
