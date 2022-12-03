# -*- coding: utf-8 -*-
"""Parser for the Microsoft User Access Logging (UAL) ESE database.

User Access Logging (UAL) is present in Windows Server editions starting with
Window Server 2012.

Also see:
  https://www.crowdstrike.com/blog/user-access-logging-ual-overview/
"""

import ipaddress
import uuid

from dfvfs.resolver import resolver as path_spec_resolver
from dfvfs.path import factory as path_spec_factory

from plaso.containers import events
from plaso.parsers import esedb
from plaso.parsers.esedb_plugins import interface


class UserAccessLoggingClientsEventsData(events.EventData):
  """Windows User Access Logging CLIENTS table event data.

  Attributes:
    access_time (dfdatetime.DateTimeValues): last access date and time.
    authenticated_username (str): domain/user account name
        performing the access.
    client_name (str): client name, use unknown.
    insert_time (dfdatetime.DateTimeValues): date and time the entry was
        first inserted into the table.
    role_identifier (str): identifier of the service accessed.
    role_name (str): Name of the service accessed.
    source_ip_address (str): source IP address.
    tenant_identifier (str): unique identifier of a tenant client.
    total_accesses (int): Count of accesses for the year.
  """

  DATA_TYPE = 'windows:user_access_logging:clients'

  def __init__(self):
    """Initializes event data."""
    super(UserAccessLoggingClientsEventsData, self).__init__(
        data_type=self.DATA_TYPE)
    self.access_time = None
    self.authenticated_username = None
    self.client_name = None
    self.insert_time = None
    self.role_identifier = None
    self.role_name = None
    self.source_ip_address = None
    self.tenant_identifier = None
    self.total_accesses = None


class UserAccessLoggingDNSEventData(events.EventData):
  """Windows User Access Logging DNS table event data.

  Attributes:
    hostname (str): hostname.
    ip_address (str): IP address.
    last_seen_time (dfdatetime.DateTimeValues): date and time the hostname to
        IP address mapping was last observed.
  """

  DATA_TYPE = 'windows:user_access_logging:dns'

  def __init__(self):
    """Initializes event data."""
    super(UserAccessLoggingDNSEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.hostname = None
    self.ip_address = None
    self.last_seen_time = None


class UserAccessLoggingRoleAccessEventsData(events.EventData):
  """Windows User Access Logging ROLE_ACCESS table event data.

  Attributes:
    first_seen_time (dfdatetime.DateTimeValues): date and time the role was
        first observed to be used.
    last_seen_time (dfdatetime.DateTimeValues): date and time the role was
        last observed to be used.
    role_identifier (str): identifier of the role.
    role_name (str): name of the role.
  """

  DATA_TYPE = 'windows:user_access_logging:role_access'

  def __init__(self):
    """Initializes event data."""
    super(UserAccessLoggingRoleAccessEventsData, self).__init__(
        data_type=self.DATA_TYPE)
    self.first_seen_time = None
    self.last_seen_time = None
    self.role_identifier = None
    self.role_name = None


class UserAccessLoggingSystemIdentityEventdata(events.EventData):
  """Windows User Access Logging SYSTEM_IDENTITY table event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): date and time the system
        identity was created.
    operating_system_build (int): operating system build.
    system_dns_hostname (str): System hostname.
    system_domain_name (str): System domain name.
  """

  DATA_TYPE = 'windows:user_access_logging:system_identity'

  def __init__(self):
    """Initializes event data."""
    super(UserAccessLoggingSystemIdentityEventdata, self).__init__(
        data_type=self.DATA_TYPE)
    self.creation_time = None
    self.operating_system_build = None
    self.system_dns_hostname = None
    self.system_domain_name = None


class UserAccessLoggingVirtualMachinesEventData(events.EventData):
  """Windows User Access Logging VIRTUALMACHINES table event data.

  Attributes:
    bios_identifier (str): BIOS identifier.
    creation_time (dfdatetime.DateTimeValues): date and time the virtual
        machine was created.
    last_active_time (dfdatetime.DateTimeValues): date and time the virtual
        machine was last observed to be active.
    serial_number (str): Serial number.
    vm_identifier (str): identifier of the virtual machine.
  """

  DATA_TYPE = 'windows:user_access_logging:virtual_machines'

  def __init__(self):
    """Initializes event data."""
    super(UserAccessLoggingVirtualMachinesEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.bios_identifier = None
    self.creation_time = None
    self.last_active_time = None
    self.serial_number = None
    self.vm_identifier = None


class UserAccessLoggingESEDBPlugin(interface.ESEDBPlugin):
  """Parses Windows User Access Logging ESE database file. """

  NAME = 'user_access_logging'
  DATA_FORMAT = 'Windows User Access Logging ESE database file'

  REQUIRED_TABLES = {
      'CLIENTS': 'ParseClientsTable',
      'DNS': 'ParseDNSTable',
      'ROLE_ACCESS': 'ParseRoleAccessTable',
      'VIRTUALMACHINES': 'ParseVirtualMachinesTable'}

  _CLIENTS_TABLE_VALUE_MAPPINGS = {
      'Address': '_ConvertIPAddressValue',
      'RoleGuid': '_ConvertGUIDToString',
      'TenantId': '_ConvertGUIDToString'}

  _DNS_TABLE_VALUE_MAPPINGS = {
      'Address': '_ConvertDNSAddressValue'}

  _VIRTUALMACHINES_TABLE_VALUE_MAPPINGS = {
      'BIOSGuid': '_ConvertGUIDToString',
      'VmGuid': '_ConvertGUIDToString'}

  _ROLE_ACCESS_TABLE_VALUE_MAPPINGS = {
      'RoleGuid': '_ConvertGUIDToString'}

  _ROLE_IDS_TABLE_VALUE_MAPPINGS = {
      'RoleGuid': '_ConvertGUIDToString'}

  def __init__(self):
    """Initializes an UAL ESE database file parser plugin."""
    super(UserAccessLoggingESEDBPlugin, self).__init__()
    self._role_mappings = {}

  def _ConvertDNSAddressValue(self, value):
    """Converts the address column value of a DNS table into a string.

    Args:
      value (bytes): DNS address.

    Returns:
      str: string representation of the DNS address.
    """
    return value.replace(b'\x00', b'').decode('utf-8')

  def _ConvertGUIDToString(self, value):
    """Converts a GUID into a string representation.

    Args:
      value (bytes): a little-endian GUID value.

    Returns:
      str: string representation of the GUID.
    """
    guid_value = uuid.UUID(bytes_le=value)
    return '{{{0!s}}}'.format(guid_value).lower()

  def _ConvertIPAddressValue(self, value):
    """Converts bytes representation of an IP to a string.

    Args:
     value (bytes): IP address.

    Returns:
      str: string representation of the IP address.
    """
    return str(ipaddress.ip_address(value))

  def ParseClientsTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a CLIENTS table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      database (Optional[ESEDatabase]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    if not self._role_mappings:
      system_identity_file_entry = self._GetSystemIdentityDatabase(
          parser_mediator)
      if system_identity_file_entry:
        self._ProcessSystemInformationDatabase(
            parser_mediator, system_identity_file_entry)

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break

      try:
        record_values = self._GetRecordValues(
            parser_mediator, table.name, record_index, esedb_record,
            value_mappings=self._CLIENTS_TABLE_VALUE_MAPPINGS)
      except (UnicodeDecodeError, ValueError):
        parser_mediator.ProduceExtractionWarning((
            'Unable to retrieve record values from record: {0:d} '
            'in table: {1:s}').format(record_index, table.name))
        continue

      event_data = UserAccessLoggingClientsEventsData()
      event_data.access_time = self._GetFiletimeRecordValue(
          record_values, 'LastAccess')
      event_data.authenticated_username = record_values.get(
          'AuthenticatedUserName', None)
      event_data.client_name = record_values.get('ClientName', None)
      event_data.role_identifier = record_values.get('RoleGuid', None)
      event_data.insert_time = self._GetFiletimeRecordValue(
          record_values, 'InsertDate')
      event_data.role_name = self._role_mappings.get(
          event_data.role_identifier, 'Unknown')
      event_data.source_ip_address = record_values.get('Address', None)
      event_data.tenant_identifier = record_values.get('TenantId', None)
      event_data.total_accesses = record_values.get('TotalAccesses', None)

      parser_mediator.ProduceEventData(event_data)

  def ParseRoleAccessTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a ROLE_ACCESS table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      database (Optional[ESEDatabase]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    if not self._role_mappings:
      system_identity_file_object = self._GetSystemIdentityDatabase(
          parser_mediator)
      if system_identity_file_object:
        self._ProcessSystemInformationDatabase(
            parser_mediator, system_identity_file_object)

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break

      try:
        record_values = self._GetRecordValues(
            parser_mediator, table.name, record_index, esedb_record,
            value_mappings=self._ROLE_ACCESS_TABLE_VALUE_MAPPINGS)
      except (UnicodeDecodeError, ValueError):
        parser_mediator.ProduceExtractionWarning((
            'Unable to retrieve record values from record: {0:d} '
            'in table: {1:s}').format(record_index, table.name))
        continue

      event_data = UserAccessLoggingRoleAccessEventsData()
      event_data.first_seen_time = self._GetFiletimeRecordValue(
          record_values, 'FirstSeen')
      event_data.last_seen_time = self._GetFiletimeRecordValue(
          record_values, 'LastSeen')
      event_data.role_identifier = record_values.get('RoleGuid', None)
      event_data.role_name = self._role_mappings.get(
          event_data.role_identifier, 'Unknown')

      parser_mediator.ProduceEventData(event_data)

  def ParseDNSTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a DNS table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      database (Optional[ESEDatabase]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break

      try:
        record_values = self._GetRecordValues(
            parser_mediator, table.name, record_index, esedb_record,
            value_mappings=self._DNS_TABLE_VALUE_MAPPINGS)
      except (UnicodeDecodeError, ValueError):
        parser_mediator.ProduceExtractionWarning((
            'Unable to retrieve record values from record: {0:d} '
            'in table: {1:s}').format(record_index, table.name))
        continue

      event_data = UserAccessLoggingDNSEventData()
      event_data.hostname = record_values.get('HostName', None)
      event_data.ip_address = record_values.get('Address', None)
      event_data.last_seen_time = self._GetFiletimeRecordValue(
          record_values, 'LastSeen')

      parser_mediator.ProduceEventData(event_data)

  def ParseVirtualMachinesTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a VIRTUALMACHINES table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      database (Optional[ESEDatabase]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break

      try:
        record_values = self._GetRecordValues(
            parser_mediator, table.name, record_index, esedb_record,
            value_mappings=self._VIRTUALMACHINES_TABLE_VALUE_MAPPINGS)
      except (UnicodeDecodeError, ValueError):
        parser_mediator.ProduceExtractionWarning((
            'Unable to retrieve record values from record: {0:d} '
            'in table: {1:s}').format(record_index, table.name))
        continue

      event_data = UserAccessLoggingVirtualMachinesEventData()
      event_data.bios_identifier = record_values.get('BIOSGuid', None)
      event_data.creation_time = self._GetFiletimeRecordValue(
          record_values, 'CreationTime')
      event_data.last_active_time = self._GetFiletimeRecordValue(
          record_values, 'LastSeenActive')
      event_data.serial_number = record_values.get('SerialNumber', None)
      event_data.vm_identifier = record_values.get('VMGuid', None)

      parser_mediator.ProduceEventData(event_data)

  def _GetSystemIdentityDatabase(self, parser_mediator):
    """Locate SystemIdentity.mdb.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.

    Returns:
      dfvfs.FileEntry: a file entry or None if the database cannot be located.
    """
    file_entry = parser_mediator.GetFileEntry()
    file_system = file_entry.GetFileSystem()
    path_segments = file_system.SplitPath(file_entry.path_spec.location)
    path_segments.pop()
    path_segments.append('SystemIdentity.mdb')

    kwargs = {}
    if file_entry.path_spec.parent:
      kwargs['parent'] = file_entry.path_spec.parent
    kwargs['location'] = file_system.JoinPath(path_segments)

    system_identity_file_path_spec = path_spec_factory.Factory.NewPathSpec(
        file_entry.path_spec.TYPE_INDICATOR, **kwargs)

    system_identity_file_entry = None
    try:
      system_identity_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
          system_identity_file_path_spec)
    except RuntimeError as exception:
      message = (
          'Unable to open SystemIdentity.mdb file: {0:s} with error: '
          '{1!s}'.format(kwargs['location'], exception))
      parser_mediator.ProduceExtractionWarning(message)

    return system_identity_file_entry

  def _ProcessSystemInformationDatabase(self, parser_mediator, file_entry):
    """Process SystemIdentity.mdb and extract Role GUID -> Role name mappings.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_entry (dfvfs.FileEntry): a file entry
    """
    file_object = file_entry.GetFileObject()
    database = esedb.ESEDatabase()

    try:
      database.Open(file_object)
    except (IOError, ValueError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to open SystemInformation.mdb with error: {0!s}'.format(
              exception))
      return

    role_ids_table = database.GetTableByName('ROLE_IDS')
    if not role_ids_table:
      parser_mediator.ProduceExtractionWarning(
          'unable to get ROLE_IDS table in SystemInformation.mdb')
    else:
      self._ParseRoleIDsTable(
          parser_mediator, database=database, table=role_ids_table)

    system_identity_table = database.GetTableByName('SYSTEM_IDENTITY')
    if not system_identity_table:
      parser_mediator.ProduceExtractionWarning(
         'unable to get SYSTEM_IDENTITY table in SystemInformation.mdb')
    else:
      self._ParseSystemIdentityTable(
          parser_mediator, database=database, table=system_identity_table)

    database.Close()

  def _ParseRoleIDsTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a SystemIdentity.mdb ROLE_IDS table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      database (Optional[ESEDatabase]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break
      try:
        record_values = self._GetRecordValues(
            parser_mediator, table.name, record_index, esedb_record,
            value_mappings=self._ROLE_IDS_TABLE_VALUE_MAPPINGS)
      except (UnicodeDecodeError, ValueError):
        parser_mediator.ProduceExtractionWarning((
            'Unable to retrieve record values from record: {0:d} '
            'in table: {1:s}').format(record_index, table.name))
        continue

      role_identifier = record_values.get('RoleGuid', None)
      role_name = record_values.get('RoleName', None)
      if role_identifier and role_name:
        self._role_mappings[role_identifier] = role_name

  def _ParseSystemIdentityTable(
      self, parser_mediator, database=None, table=None, **unused_kwargs):
    """Parses a SystemIdentity.mdb SYSTEM_IDENTITY table.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      database (Optional[ESEDatabase]): ESE database.
      table (Optional[pyesedb.table]): table.

    Raises:
      ValueError: if the database or table value is missing.
    """
    if database is None:
      raise ValueError('Missing database value.')

    if table is None:
      raise ValueError('Missing table value.')

    for record_index, esedb_record in enumerate(table.records):
      if parser_mediator.abort:
        break
      try:
        record_values = self._GetRecordValues(
            parser_mediator, table.name, record_index, esedb_record)
      except (UnicodeDecodeError, ValueError):
        parser_mediator.ProduceExtractionWarning((
            'Unable to retrieve record values from record: {0:d} '
            'in table: {1:s}').format(record_index, table.name))
        continue

      event_data = UserAccessLoggingSystemIdentityEventdata()
      event_data.creation_time = self._GetFiletimeRecordValue(
          record_values, 'CreationTime')
      event_data.operating_system_build = record_values.get(
          'OSBuildNumber', None)
      event_data.system_dns_hostname = record_values.get(
          'SystemDNSHostName', None)
      event_data.system_domain_name = record_values.get(
          'SystemDomainName', None)

      parser_mediator.ProduceEventData(event_data)


esedb.ESEDBParser.RegisterPlugin(UserAccessLoggingESEDBPlugin)
