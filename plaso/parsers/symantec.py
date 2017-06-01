# -*- coding: utf-8 -*-
"""This file contains a Symantec parser in plaso."""

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser

import pytz  # pylint: disable=wrong-import-order


__author__ = 'David Nides (david.nides@gmail.com)'


class SymantecEventData(events.EventData):
  """Symantec event data.

  Attributes:
    access (str): access.
    action0 (str): action0.
    action1 (str): action1.
    action1_status (str): action1 status.
    action2 (str): action2.
    action2_status (str): action2 status.
    address (str): address.
    backup_id (str): backup id.
    cat (str): cat.
    cleaninfo (str): cleaninfo.
    clientgroup (str): clientgroup.
    compressed (str): compressed.
    computer (str): computer.
    definfo (str): definfo.
    defseqnumber (str): defseqnumber.
    deleteinfo (str): deleteinfo.
    depth (str): depth.
    description (str): description.
    domain_guid (str): domain guid.
    domainname (str): domainname.
    err_code (str): err code.
    event_data (str): event data.
    event (str): event.
    extra (str): extra.
    file (str): file.
    flags (str): flags.
    groupid (str): groupid.
    guid (str): guid.
    license_expiration_dt (str): license expiration dt.
    license_feature_name (str): license feature name.
    license_feature_ver (str): license feature ver.
    license_fulfillment_id (str): license fulfillment id.
    license_lifecycle (str): license lifecycle.
    license_seats_delta (str): license seats delta.
    license_seats (str): license seats.
    license_seats_total (str): license seats total.
    license_serial_num (str): license serial num.
    license_start_dt (str): license start dt.
    logger (str): logger.
    login_domain (str): login domain.
    log_session_guid (str): log session guid.
    macaddr (str): macaddr.
    new_ext (str): new ext.
    ntdomain (str): ntdomain.
    offset (str): offset.
    parent (str): parent.
    quarfwd_status (str): quarfwd status.
    remote_machine_ip (str): remote machine ip.
    remote_machine (str): remote machine.
    scanid (str): scanid.
    snd_status (str): snd status.
    status (str): status.
    still_infected (str): still infected.
    time (str): time.
    user (str): user.
    vbin_id (str): vbin id.
    vbin_session_id (str): vbin session id.
    version (str): version.
    virus_id (str): virus id.
    virus (str): virus.
    virustype (str): virustype.
  """

  DATA_TYPE = u'av:symantec:scanlog'

  def __init__(self):
    """Initializes event data."""
    super(SymantecEventData, self).__init__(data_type=self.DATA_TYPE)
    self.access = None
    self.action0 = None
    self.action1 = None
    self.action1_status = None
    self.action2 = None
    self.action2_status = None
    self.address = None
    self.backup_id = None
    self.cat = None
    self.cleaninfo = None
    self.clientgroup = None
    self.compressed = None
    self.computer = None
    self.definfo = None
    self.defseqnumber = None
    self.deleteinfo = None
    self.depth = None
    self.description = None
    self.domain_guid = None
    self.domainname = None
    self.err_code = None
    self.event_data = None
    self.event = None
    self.extra = None
    self.file = None
    self.flags = None
    self.groupid = None
    self.guid = None
    self.license_expiration_dt = None
    self.license_feature_name = None
    self.license_feature_ver = None
    self.license_fulfillment_id = None
    self.license_lifecycle = None
    self.license_seats_delta = None
    self.license_seats = None
    self.license_seats_total = None
    self.license_serial_num = None
    self.license_start_dt = None
    self.logger = None
    self.login_domain = None
    self.log_session_guid = None
    self.macaddr = None
    self.new_ext = None
    self.ntdomain = None
    self.offset = None
    self.parent = None
    self.quarfwd_status = None
    self.remote_machine_ip = None
    self.remote_machine = None
    self.scanid = None
    self.snd_status = None
    self.status = None
    self.still_infected = None
    self.time = None
    self.user = None
    self.vbin_id = None
    self.vbin_session_id = None
    self.version = None
    self.virus_id = None
    self.virus = None
    self.virustype = None


class SymantecParser(text_parser.TextCSVParser):
  """Parse Symantec AV Corporate Edition and Endpoint Protection log files."""

  NAME = u'symantec_scanlog'
  DESCRIPTION = u'Parser for Symantec Anti-Virus log files.'

  # Define the columns that make up the structure of a Symantec log file.
  # http://www.symantec.com/docs/TECH100099
  COLUMNS = [
      u'time', u'event', u'cat', u'logger', u'computer', u'user',
      u'virus', u'file', u'action1', u'action2', u'action0', u'virustype',
      u'flags', u'description', u'scanid', u'new_ext', u'groupid',
      u'event_data', u'vbin_id', u'virus_id', u'quarfwd_status',
      u'access', u'snd_status', u'compressed', u'depth', u'still_infected',
      u'definfo', u'defseqnumber', u'cleaninfo', u'deleteinfo',
      u'backup_id', u'parent', u'guid', u'clientgroup', u'address',
      u'domainname', u'ntdomain', u'macaddr', u'version:',
      u'remote_machine', u'remote_machine_ip', u'action1_status',
      u'action2_status', u'license_feature_name', u'license_feature_ver',
      u'license_serial_num', u'license_fulfillment_id', u'license_start_dt',
      u'license_expiration_dt', u'license_lifecycle', u'license_seats_total',
      u'license_seats', u'err_code', u'license_seats_delta', u'status',
      u'domain_guid', u'log_session_guid', u'vbin_session_id',
      u'login_domain', u'extra']

  def _ConvertToTimestamp(self, date_time_values, timezone=pytz.UTC):
    """Converts the given parsed date and time values to a timestamp.

    The date and time values consist of six hexadecimal octets.
    They represent the following:
      First octet: Number of years since 1970
      Second octet: Month, where January = 0
      Third octet: Day
      Fourth octet: Hour
      Fifth octet: Minute
      Sixth octet: Second

    For example, 200A13080122 represents November 19, 2002, 8:01:34 AM.

    Args:
      date_time_values: The hexadecimal encoded date and time values.
      timezone: Optional timezone (instance of pytz.timezone).

    Returns:
      A timestamp value, contains the number of micro seconds since
      January 1, 1970, 00:00:00 UTC.
    """
    if not date_time_values:
      return timelib.Timestamp.NONE_TIMESTAMP

    year, month, day, hours, minutes, seconds = (
        int(hexdigit[0] + hexdigit[1], 16) for hexdigit in zip(
            date_time_values[::2], date_time_values[1::2]))

    return timelib.Timestamp.FromTimeParts(
        year + 1970, month + 1, day, hours, minutes, seconds, timezone=timezone)

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a row and extract event objects.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): line number of the row.
      row (dict[str, str]): row of the fields specified in COLUMNS.
    """
    try:
      timestamp = self._ConvertToTimestamp(
          row[u'time'], timezone=parser_mediator.timezone)
    except (TypeError, ValueError, errors.TimestampError) as exception:
      timestamp = timelib.Timestamp.NONE_TIMESTAMP
      parser_mediator.ProduceExtractionError(
          u'unable to determine timestamp with error: {0:s}'.format(
              exception))

    # TODO: remove unused attributes.
    event_data = SymantecEventData()
    event_data.access = row.get(u'access', None)
    event_data.action0 = row.get(u'action0', None)
    event_data.action1 = row.get(u'action1', None)
    event_data.action1_status = row.get(u'action1_status', None)
    event_data.action2 = row.get(u'action2', None)
    event_data.action2_status = row.get(u'action2_status', None)
    event_data.address = row.get(u'address', None)
    event_data.backup_id = row.get(u'backup_id', None)
    event_data.cat = row.get(u'cat', None)
    event_data.cleaninfo = row.get(u'cleaninfo', None)
    event_data.clientgroup = row.get(u'clientgroup', None)
    event_data.compressed = row.get(u'compressed', None)
    event_data.computer = row.get(u'computer', None)
    event_data.definfo = row.get(u'definfo', None)
    event_data.defseqnumber = row.get(u'defseqnumber', None)
    event_data.deleteinfo = row.get(u'deleteinfo', None)
    event_data.depth = row.get(u'depth', None)
    event_data.description = row.get(u'description', None)
    event_data.domain_guid = row.get(u'domain_guid', None)
    event_data.domainname = row.get(u'domainname', None)
    event_data.err_code = row.get(u'err_code', None)
    event_data.event_data = row.get(u'event_data', None)
    event_data.event = row.get(u'event', None)
    event_data.extra = row.get(u'extra', None)
    event_data.file = row.get(u'file', None)
    event_data.flags = row.get(u'flags', None)
    event_data.groupid = row.get(u'groupid', None)
    event_data.guid = row.get(u'guid', None)
    event_data.license_expiration_dt = row.get(u'license_expiration_dt', None)
    event_data.license_feature_name = row.get(u'license_feature_name', None)
    event_data.license_feature_ver = row.get(u'license_feature_ver', None)
    event_data.license_fulfillment_id = row.get(u'license_fulfillment_id', None)
    event_data.license_lifecycle = row.get(u'license_lifecycle', None)
    event_data.license_seats_delta = row.get(u'license_seats_delta', None)
    event_data.license_seats = row.get(u'license_seats', None)
    event_data.license_seats_total = row.get(u'license_seats_total', None)
    event_data.license_serial_num = row.get(u'license_serial_num', None)
    event_data.license_start_dt = row.get(u'license_start_dt', None)
    event_data.logger = row.get(u'logger', None)
    event_data.login_domain = row.get(u'login_domain', None)
    event_data.log_session_guid = row.get(u'log_session_guid', None)
    event_data.macaddr = row.get(u'macaddr', None)
    event_data.new_ext = row.get(u'new_ext', None)
    event_data.ntdomain = row.get(u'ntdomain', None)
    event_data.offset = row_offset
    event_data.parent = row.get(u'parent', None)
    event_data.quarfwd_status = row.get(u'quarfwd_status', None)
    event_data.remote_machine_ip = row.get(u'remote_machine_ip', None)
    event_data.remote_machine = row.get(u'remote_machine', None)
    event_data.scanid = row.get(u'scanid', None)
    event_data.snd_status = row.get(u'snd_status', None)
    event_data.status = row.get(u'status', None)
    event_data.still_infected = row.get(u'still_infected', None)
    event_data.time = row.get(u'time', None)
    event_data.user = row.get(u'user', None)
    event_data.vbin_id = row.get(u'vbin_id', None)
    event_data.vbin_session_id = row.get(u'vbin_session_id', None)
    event_data.version = row.get(u'version:', None)
    event_data.virus_id = row.get(u'virus_id', None)
    event_data.virus = row.get(u'virus', None)
    event_data.virustype = row.get(u'virustype', None)

    event = time_events.TimestampEvent(
        timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyRow(self, parser_mediator, row):
    """Verify a single line of a Symantec log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): row of the fields specified in COLUMNS.

    Returns:
      bool: True if the row is in the expected format, False if not.
    """
    try:
      timestamp = self._ConvertToTimestamp(
          row[u'time'], timezone=parser_mediator.timezone)
    except (TypeError, ValueError, errors.TimestampError):
      return False

    if not timestamp:
      return False

    # Check few entries.
    try:
      my_event = int(row[u'event'])
    except (TypeError, ValueError):
      return False

    if my_event < 1 or my_event > 77:
      return False

    try:
      category = int(row[u'cat'])
    except (TypeError, ValueError):
      return False

    if category < 1 or category > 4:
      return False

    return True


manager.ParsersManager.RegisterParser(SymantecParser)
