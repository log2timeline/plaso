# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) time helper."""

from dfdatetime import apfs_time as dfdatetime_apfs_time

from plaso.lib.aul import constants
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
      # ARM processors.
      if (
          ts.timebase_numerator == constants.ARM_TIMEBASE_NUMERATOR
          and ts.timebase_denominator == constants.ARM_TIMEBASE_DENOMINATOR
      ):
        ts.adjustment = (
            constants.ARM_TIMEBASE_NUMERATOR
            / constants.ARM_TIMEBASE_DENOMINATOR
        )
      return ts
  logger.error("Could not find boot uuid {} in Timesync!".format(uuid))
  return None


def FindClosestTimesyncItemInList(sync_records,
                                  continuous_time,
                                  return_first=False):
  """Returns the closest timesync item from the provided list without going over

  Args:
    sync_records (List[timesync_sync_record]): List of timesync boot records.
    continuous_time (int): The timestamp we're looking for.
    return_first (bool): Whether to return the first largest record.

  Returns:
    timesync_boot_record or None if not available.
  """
  if not sync_records:
    return None

  i = 1
  closest_tsi = None
  for item in sync_records:
    if item.kernel_continuous_timestamp > continuous_time:
      if return_first and i == 1:
        closest_tsi = item
      break
    i += 1
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
        timestamp=int(time)).CopyToDateTimeString()
  return time_string
