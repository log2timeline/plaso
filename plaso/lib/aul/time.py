# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) time helper."""

from dfdatetime import apfs_time as dfdatetime_apfs_time

from plaso.parsers import logger

def GetBootUuidTimeSync(records, uuid):
  """Retrieves the timesync for a specific boot identifier.

  Args:
      records (List[timesync_boot_record]): List of Timesync records.
      uuid (uuid): boot identifier.

  Returns:
    timesync_boot_record or None if not available.
  """
  for ts in records:
    if ts.boot_uuid == uuid:
      ts.adjustment = 1
      if ts.timebase_numerator == 125 and ts.timebase_denominator == 3:
        ts.adjustment = 125 / 3
      return ts
  logger.error("Could not find boot uuid {} in Timesync!".format(uuid))
  return None

def FindClosestTimesyncItemInList(sync_records, continuous_time):
  """Returns the closest timesync item from the provided list

  Args:
    sync_records (List[timesync_sync_record]): List of timesync boot records.
    continuous_time (int): The timestamp we're looking for.

  Returns:
    timesync_boot_record or None if not available.
  """
  if not sync_records:
    return None

  closest_tsi = sync_records[0]
  for item in sync_records:
    if item.kernel_continuous_timestamp > continuous_time:
      break
    closest_tsi = item
  return closest_tsi

def TimestampFromContTime(boot_uuid_ts_list, ct):
  """Converts a continuous time into a Date Time string.

  Args:
    boot_uuid_ts_list (List[timesync_sync_record]): List of
      timesync boot records.
    ct (int): A continuous time stamp.

  Returns:
    string
  """
  ts = FindClosestTimesyncItemInList(boot_uuid_ts_list, ct)
  time_string = 'N/A'
  if ts is not None:
    time = ts.wall_time + ct - ts.kernel_continuous_timestamp
    time_string = dfdatetime_apfs_time.APFSTime(
      timestamp=time).CopyToDateTimeString()
  return time_string
