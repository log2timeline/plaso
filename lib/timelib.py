# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains functions and variables used for time manipulations.

This file should contain common methods that can be used in Plaso to convert
timestamps in various formats into the standard micro seconds precision integer
Epoch UTC time that is used internally to store timestamps in Plaso.

The file can also contain common functions to change the default timestamp into
a more human readable one.
"""

import calendar

MONTH_DICT = {
    'jan': 1,
    'feb': 2,
    'mar': 3,
    'apr': 4,
    'may': 5,
    'jun': 6,
    'jul': 7,
    'aug': 8,
    'sep': 9,
    'oct': 10,
    'nov': 11,
    'dec': 12}

MICROSEC_MULTIPLIER = 1000000


def WinFiletime2Unix(timestamp):
  """Return a micro second second precision timestamp from a Windows FILETIME.

  Windows FILETIME is represented in UTC on the form of:
    1601-01-01 00:00:00, resolution 100ns

  While UNIX 64-bit epoch is:
    1970-01-01 00:00:00, resolution 1 micro second.

  Args:
    timestamp: The timestamp as an "unsigned long long"
    ("<Q" in struct.unpack).

  Returns:
    An integer, representing the micro seconds since UNIX Epoch.
  """
  if not timestamp:
    return 0

  return int(timestamp / 10 - (11644473600 * 1e6))


def Timetuple2Timestamp(time_tuple):
  """Return a micro second precision timestamp from a timetuple."""
  if type(time_tuple) != tuple:
    return 0

  return int(calendar.timegm(time_tuple))

