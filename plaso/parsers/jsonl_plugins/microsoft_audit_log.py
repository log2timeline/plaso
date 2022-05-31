# -*- coding: utf-8 -*-
"""JSON-L parser plugin for Microsoft (Office) 365 audit log files."""


from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class MicrosoftAuditLogEventData(events.EventData):
  """Microsoft (Office) 365 audit log event data.

  Attributes:
    audit_record_identifier (str): audit record identifier.
    application_access_context (str): application access context
    client_ip (str): client IP address.
    object_identifier (str): object identifier
    operation_name (str): operation name.
    organization_identifier (str): organization identifier.
    record_type (int): record type.
    result_status (str): result status
    scope (str): scope.
    user_identifier (str): user identifier
    user_key (str): user key.
    user_type (int): user type.
    workload (str): Microsoft 365 service
  """

  DATA_TYPE = "microsoft:auditlog:entry"

  def __init__(self):
    """Initializes event data."""
    super(MicrosoftAuditLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.audit_record_identifier = None
    self.application_access_context = None
    self.client_ip = None
    self.object_identifier = None
    self.operation_name = None
    self.organization_identifier = None
    self.record_type = None
    self.result_status = None
    self.scope = None
    self.user_identifier = None
    self.user_key = None
    self.user_type = None
    self.workload = None


class MicrosoftAuditLogJSONLPlugin(interface.JSONLPlugin):
  """JSON-L parser plugin for Microsoft (Office) 365 audit log files."""

  NAME = 'microsoft_audit_log'
  DATA_FORMAT = 'Microsoft Audit Log'

  def _ParseRecord(self, parser_mediator, json_dict):
    """Parses a Microsoft (Office) 365 audit log record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary of the log record.
    """
    creation_time = self._GetJSONValue(json_dict, 'CreationTime')
    if not creation_time:
      parser_mediator.ProduceExtractionWarning(
          'Creation time value missing from audit log entry')

    event_data = MicrosoftAuditLogEventData()

    event_data.audit_record_identifier = self._GetJSONValue(json_dict, 'Id')
    event_data.application_access_context = self._GetJSONValue(
        json_dict, 'AppAccessContext')
    event_data.client_ip = self._GetJSONValue(json_dict, 'ClientIP')
    event_data.object_identifier = self._GetJSONValue(json_dict, 'ObjectId')
    event_data.operation_name = self._GetJSONValue(json_dict, 'Operation')
    event_data.organization_identifier = self._GetJSONValue(
        json_dict, 'OrganizationId')
    event_data.record_type = self._GetJSONValue(json_dict, 'RecordType')
    event_data.result_status = self._GetJSONValue(json_dict, 'ResultStatus')
    event_data.scope = self._GetJSONValue(json_dict, 'Scope')
    event_data.user_identifier = self._GetJSONValue(json_dict, 'UserId')
    event_data.user_key = self._GetJSONValue(json_dict, 'UserKey')
    event_data.user_type = self._GetJSONValue(json_dict, 'UserType')
    event_data.workload = self._GetJSONValue(json_dict, 'Workload')

    try:
      date_time = dfdatetime_time_elements.TimeElements()
      date_time.CopyFromStringISO8601(creation_time)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to parse event time: {0:s} with error: {1!s}'.format(
              creation_time, exception))
      date_time = dfdatetime_semantic_time.InvalidTime()

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_RECORDED)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def CheckRequiredFormat(self, json_dict):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      json_dict (dict): JSON dictionary of the log record

    Returns:
      bool: True if this is the correct parsers, False otherwise.
    """
    audit_record_identifier = json_dict.get('Id', None)
    organization_identifier = json_dict.get('OrganizationId', None)
    creation_time = json_dict.get('CreationTime', None)

    if None in (audit_record_identifier, creation_time,
        organization_identifier):
      return False

    try:
      date_time = dfdatetime_time_elements.TimeElements()
      date_time.CopyFromStringISO8601(creation_time)
    except ValueError:
      return False

    return True


jsonl_parser.JSONLParser.RegisterPlugin(MicrosoftAuditLogJSONLPlugin)
