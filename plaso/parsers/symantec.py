# -*- coding: utf-8 -*-
"""Symantec AV Corporate Edition and Endpoint Protection log file parser."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import dsv_parser
from plaso.parsers import manager


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
    backup_id (str): backup identifier.
    cat (str): category.
    cleaninfo (str): clean information.
    clientgroup (str): client group.
    compressed (str): compressed.
    computer (str): computer.
    definfo (str): definfo.
    defseqnumber (str): def sequence number.
    deleteinfo (str): delete information.
    depth (str): depth.
    description (str): description.
    domain_guid (str): domain identifier (GUID).
    domainname (str): domain name.
    err_code (str): error code.
    event_data (str): event data.
    event (str): event.
    extra (str): extra.
    file (str): file.
    flags (str): flags.
    groupid (str): group identifier.
    guid (str): guid.
    last_written_time (dfdatetime.DateTimeValues): entry last written date and
        time.
    license_expiration_dt (str): license expiration date.
    license_feature_name (str): license feature name.
    license_feature_ver (str): license feature ver.
    license_fulfillment_id (str): license fulfillment identifier.
    license_lifecycle (str): license lifecycle.
    license_seats_delta (str): license seats delta.
    license_seats (str): license seats.
    license_seats_total (str): license seats total.
    license_serial_num (str): license serial number.
    license_start_dt (str): license start date.
    logger (str): logger.
    login_domain (str): login domain.
    log_session_guid (str): log session identifier (GUID).
    macaddr (str): MAC address.
    new_ext (str): new ext.
    ntdomain (str): ntdomain.
    offset (str): offset.
    parent (str): parent.
    quarfwd_status (str): quarfwd status.
    remote_machine_ip (str): remote machine IP address.
    remote_machine (str): remote machine.
    scanid (str): scan identifier.
    snd_status (str): snd status.
    status (str): status.
    still_infected (str): still infected.
    time (str): time.
    user (str): user.
    vbin_id (str): vbin identifier.
    vbin_session_id (str): vbin session identifier.
    version (str): version.
    virus_id (str): virus identifier.
    virus (str): virus.
    virustype (str): virustype.
  """

  DATA_TYPE = 'av:symantec:scanlog'

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
    self.last_written_time = None
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


class SymantecParser(dsv_parser.DSVParser):
  """Parses Symantec AV Corporate Edition and Endpoint Protection log files."""

  NAME = 'symantec_scanlog'
  DATA_FORMAT = 'Symantec AV Corporate Edition and Endpoint Protection log file'

  # Define the columns that make up the structure of a Symantec log file.
  # http://www.symantec.com/docs/TECH100099
  COLUMNS = [
      'time', 'event', 'cat', 'logger', 'computer', 'user',
      'virus', 'file', 'action1', 'action2', 'action0', 'virustype',
      'flags', 'description', 'scanid', 'new_ext', 'groupid',
      'event_data', 'vbin_id', 'virus_id', 'quarfwd_status',
      'access', 'snd_status', 'compressed', 'depth', 'still_infected',
      'definfo', 'defseqnumber', 'cleaninfo', 'deleteinfo',
      'backup_id', 'parent', 'guid', 'clientgroup', 'address',
      'domainname', 'ntdomain', 'macaddr', 'version:',
      'remote_machine', 'remote_machine_ip', 'action1_status',
      'action2_status', 'license_feature_name', 'license_feature_ver',
      'license_serial_num', 'license_fulfillment_id', 'license_start_dt',
      'license_expiration_dt', 'license_lifecycle', 'license_seats_total',
      'license_seats', 'err_code', 'license_seats_delta', 'status',
      'domain_guid', 'log_session_guid', 'vbin_session_id',
      'login_domain', 'extra']

  def _ParseTimestamp(self, timestamp):
    """Parses a Symantec log timestamp.

    A Symantec log timestamp consist of six hexadecimal octets, that represent:
      First octet: Number of years since 1970
      Second octet: Month, where 0 represents January.
      Third octet: Day of the month
      Fourth octet: Number of hours
      Fifth octet: Number of minutes
      Sixth octet: Number of seconds

    For example, 200A13080122 represents November 19, 2002, 8:01:34 AM.

    Args:
      timestamp (str): hexadecimal encoded date and time values.

    Returns:
      dfdatetime.TimeElements: date and time value.

    Raises:
      ParseError: if a valid date and time value cannot be derived from
          the time elements.
    """
    try:
      year, month, day_of_month, hours, minutes, seconds = (
          int(hexdigit[0] + hexdigit[1], 16) for hexdigit in zip(
              timestamp[::2], timestamp[1::2]))

      time_elements_tuple = (
          1970 + year, month + 1, day_of_month, hours, minutes, seconds)

      date_time = dfdatetime_time_elements.TimeElements(
          time_elements_tuple=time_elements_tuple)
      date_time.is_local_time = True

      return date_time

    except (TypeError, ValueError) as exception:
      raise errors.ParseError(
          'Unable to parse time elements with error: {0!s}'.format(exception))

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): line number of the row.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    timestamp = row['time']

    # TODO: remove unused attributes.
    event_data = SymantecEventData()
    event_data.access = row.get('access', None)
    event_data.action0 = row.get('action0', None)
    event_data.action1 = row.get('action1', None)
    event_data.action1_status = row.get('action1_status', None)
    event_data.action2 = row.get('action2', None)
    event_data.action2_status = row.get('action2_status', None)
    event_data.address = row.get('address', None)
    event_data.backup_id = row.get('backup_id', None)
    event_data.cat = row.get('cat', None)
    event_data.cleaninfo = row.get('cleaninfo', None)
    event_data.clientgroup = row.get('clientgroup', None)
    event_data.compressed = row.get('compressed', None)
    event_data.computer = row.get('computer', None)
    event_data.definfo = row.get('definfo', None)
    event_data.defseqnumber = row.get('defseqnumber', None)
    event_data.deleteinfo = row.get('deleteinfo', None)
    event_data.depth = row.get('depth', None)
    event_data.description = row.get('description', None)
    event_data.domain_guid = row.get('domain_guid', None)
    event_data.domainname = row.get('domainname', None)
    event_data.err_code = row.get('err_code', None)
    event_data.event_data = row.get('event_data', None)
    event_data.event = row.get('event', None)
    event_data.extra = row.get('extra', None)
    event_data.file = row.get('file', None)
    event_data.flags = row.get('flags', None)
    event_data.groupid = row.get('groupid', None)
    event_data.guid = row.get('guid', None)
    event_data.last_written_time = self._ParseTimestamp(timestamp)
    event_data.license_expiration_dt = row.get('license_expiration_dt', None)
    event_data.license_feature_name = row.get('license_feature_name', None)
    event_data.license_feature_ver = row.get('license_feature_ver', None)
    event_data.license_fulfillment_id = row.get('license_fulfillment_id', None)
    event_data.license_lifecycle = row.get('license_lifecycle', None)
    event_data.license_seats_delta = row.get('license_seats_delta', None)
    event_data.license_seats = row.get('license_seats', None)
    event_data.license_seats_total = row.get('license_seats_total', None)
    event_data.license_serial_num = row.get('license_serial_num', None)
    event_data.license_start_dt = row.get('license_start_dt', None)
    event_data.logger = row.get('logger', None)
    event_data.login_domain = row.get('login_domain', None)
    event_data.log_session_guid = row.get('log_session_guid', None)
    event_data.macaddr = row.get('macaddr', None)
    event_data.new_ext = row.get('new_ext', None)
    event_data.ntdomain = row.get('ntdomain', None)
    event_data.offset = row_offset
    event_data.parent = row.get('parent', None)
    event_data.quarfwd_status = row.get('quarfwd_status', None)
    event_data.remote_machine_ip = row.get('remote_machine_ip', None)
    event_data.remote_machine = row.get('remote_machine', None)
    event_data.scanid = row.get('scanid', None)
    event_data.snd_status = row.get('snd_status', None)
    event_data.status = row.get('status', None)
    event_data.still_infected = row.get('still_infected', None)
    event_data.time = row.get('time', None)
    event_data.user = row.get('user', None)
    event_data.vbin_id = row.get('vbin_id', None)
    event_data.vbin_session_id = row.get('vbin_session_id', None)
    event_data.version = row.get('version:', None)
    event_data.virus_id = row.get('virus_id', None)
    event_data.virus = row.get('virus', None)
    event_data.virustype = row.get('virustype', None)

    parser_mediator.ProduceEventData(event_data)

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    timestamp = row['time']

    try:
      self._ParseTimestamp(timestamp)
    except errors.ParseError:
      return False

    try:
      my_event = int(row['event'], 10)
    except (TypeError, ValueError):
      return False

    if my_event < 1 or my_event > 77:
      return False

    try:
      category = int(row['cat'], 10)
    except (TypeError, ValueError):
      return False

    if category < 1 or category > 4:
      return False

    return True


manager.ParsersManager.RegisterParser(SymantecParser)
