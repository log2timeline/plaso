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


def BuildHostDict(storage_object):
  """Return a dict object from a StorageFile object.

  Build a dict object based on the preprocess objects stored inside
  a storage file.

  Args:
    storage_object: The StorageFile object that stores all the EventObjects.

  Returns:
    A dict object that has the store number as a key and the hostname
    as the value to that key.
  """
  host_dict = {}
  if not storage_object:
    return host_dict

  if not hasattr(storage_object, 'GetStorageInformation'):
    return host_dict

  for info in storage_object.GetStorageInformation():
    if hasattr(info, 'store_range') and hasattr(info, 'hostname'):
      for store_number in range(info.store_range[0], info.store_range[1]):
        # TODO: A bit wasteful, if the range is large we are wasting keys.
        # Rewrite this logic into a more optimal one.
        host_dict[store_number] = info.hostname

  return host_dict
