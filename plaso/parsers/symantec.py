#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
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
"""This file contains a Symantec parser in plaso."""
import re

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib

__author__ = 'David Nides (david.nides@gmail.com)'


class SymantecEvent(event.TextEvent):
  """Convenience class for a Symantec line event."""
  DATA_TYPE = 'av:symantec:scanlog'


class Symantec(parser.TextCSVParser):
  """Parse Symantec AV Corporate Edition and Endpoint Protection log files."""

  # Define the columns that make up the structure of a Symantec log file.
  # http://www.symantec.com/docs/TECH100099
  COLUMNS = [
      'time','event','cat','logger','computer','user',
      'virus','file','action1','action2','action0','virustype',
      'flags','description','scanid','new_ext','groupid',
      'event_data','vbin_id','virus_id','quarfwd_status',
      'access','snd_status','compressed','depth','still_infected',
      'definfo','defseqnumber','cleaninfo','deleteinfo',
      'backup_id','parent','guid','clientgroup','address',
      'domainname','ntdomain','macaddr','version:',
      'remote_machine','remote_machine_ip','action1_status',
      'action2_status','license_feature_name','license_feature_ver',
      'license_serial_num','license_fulfillment_id','license_start_dt',
      'license_expiration_dt','license_lifecycle','license_seats_total',
      'license_seats','err_code','license_seats_delta','status',
      'domain_guid','log_session_guid','vbin_session_id',
      'login_domain', 'extra']

  def VerifyRow(self, row):
    """Verify a single line of a Symantec log file."""

    try:
      timestamp = self.GetTimestamp(row['time'])
    except (TypeError, ValueError) as e:
      return False

    if not timestamp:
      return False

    # Check few entries.
    try:
      event = int(row['event'])
    except TypeError:
      return False

    if event < 1 or event > 77:
      return False

    try:
      category = int(row['cat'])
    except TypeError:
      return False

    if category < 1 or category > 4:
      return False

    return True

  def GetTimestamp(self, timestamp_raw):
    """Return a 64-bit signed timestamp value in micro seconds since Epoch.

     The timestamp consists of six hexadecimal octets.
     They represent the following:
       First octet: Number of years since 1970
       Second octet: Month, where January = 0
       Third octet: Day
       Fourth octet: Hour
       Fifth octet: Minute
       Sixth octet: Second

     For example, 200A13080122 represents November 19, 2002, 8:01:34 AM.

     Args:
       timestamp_raw: The hexadecimal encoded timestamp value.

     Returns:
       A plaso timestamp value, micro seconds since Epoch in UTC.
    """
    if timestamp_raw == '':
      return 0

    year, month, day, hour, minute, sec = (
        int(x[0] + x[1], 16) for x in zip(
            timestamp_raw[::2], timestamp_raw[1::2]))

    timestamp = timelib.FromTimeParts(
        year + 1970, month + 1, day, hour, minute, sec, 0, self._pre_obj.zone)

    return timestamp

  def ParseRow(self, row):
    """Parse a single line from the symantec log file."""
    epoch = self.GetTimestamp(row['time'])
    # TODO: Create new dict object that only contains valuable attributes.
    yield SymantecEvent(epoch, row)
