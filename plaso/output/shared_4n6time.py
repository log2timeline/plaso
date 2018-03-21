# -*- coding: utf-8 -*-
"""Defines the shared code for 4n6time output modules."""

from __future__ import unicode_literals

from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface


# pylint: disable=abstract-method

class Shared4n6TimeOutputModule(interface.OutputModule):
  """Class defining the base 4n6time output module."""

  NAME = '4n6time_shared'

  _DEFAULT_FIELDS = [
      'datetime', 'host', 'source', 'sourcetype', 'user', 'type']

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.

    Raises:
      ValueError: when there are unused keyword arguments.
    """
    super(Shared4n6TimeOutputModule, self).__init__(output_mediator)
    self._append = False
    self._evidence = '-'
    self._fields = self._DEFAULT_FIELDS
    self._set_status = None

  def _GetSanitizedEventValues(self, event):
    """Sanitizes the event for use in 4n6time.

    Args:
      event (EventObject): event.

    Returns:
      dict[str, object]: dictionary containing the sanitized event values.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
          type in the event object.
    """
    data_type = getattr(event, 'data_type', 'UNKNOWN')

    event_formatter = self._output_mediator.GetEventFormatter(event)
    if not event_formatter:
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    message, _ = self._output_mediator.GetFormattedMessages(event)
    if message is None:
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    source_short, source = self._output_mediator.GetFormattedSources(event)
    if source is None or source_short is None:
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    datetime_object = None
    if event.timestamp is not None:
      datetime_object = timelib.Timestamp.CopyToDatetime(
          event.timestamp, self._output_mediator.timezone)
      if not datetime_object:
        self._ReportEventError(event, (
            'unable to copy timestamp: {0:d} to datetime object.'))
        return None

    format_variables = self._output_mediator.GetFormatStringAttributeNames(
        event)
    if format_variables is None:
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    extra_attributes = []
    for attribute_name, attribute_value in sorted(event.GetAttributes()):
      if (attribute_name in definitions.RESERVED_VARIABLE_NAMES or
          attribute_name in format_variables):
        continue
      extra_attributes.append(
          '{0:s}: {1!s} '.format(attribute_name, attribute_value))

    extra_attributes = ' '.join(extra_attributes)

    inode = event.inode
    if inode is None and hasattr(event, 'pathspec'):
      inode = getattr(event.pathspec, 'inode', '-')
    if inode is None:
      inode = '-'

    datetime_string = 'N/A'
    if datetime_object:
      datetime_string = (
          '{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(
              datetime_object.year, datetime_object.month, datetime_object.day,
              datetime_object.hour, datetime_object.minute,
              datetime_object.second))

    tags = None
    if getattr(event, 'tag', None):
      tags = getattr(event.tag, 'tags', None)

    taglist = ''
    if isinstance(tags, (list, tuple)):
      taglist = ','.join(tags)

    offset = event.offset
    if offset is None:
      offset = 0

    row = {
        'timezone': '{0!s}'.format(self._output_mediator.timezone),
        'MACB': self._output_mediator.GetMACBRepresentation(event),
        'source': source_short,
        'sourcetype': source,
        'type': getattr(event, 'timestamp_desc', '-'),
        'user': getattr(event, 'username', '-'),
        'host': getattr(event, 'hostname', '-'),
        'description': message,
        'filename': getattr(event, 'filename', '-'),
        'inode': inode,
        'notes': getattr(event, 'notes', '-'),
        'format': getattr(event, 'parser', '-'),
        'extra': extra_attributes,
        'datetime': datetime_string,
        'reportnotes': '',
        'inreport': '',
        'tag': taglist,
        'offset': offset,
        'vss_store_number': self._GetVSSNumber(event),
        'URL': getattr(event, 'url', '-'),
        'record_number': getattr(event, 'record_number', 0),
        'event_identifier': getattr(event, 'event_identifier', '-'),
        'event_type': getattr(event, 'event_type', '-'),
        'source_name': getattr(event, 'source_name', '-'),
        'user_sid': getattr(event, 'user_sid', '-'),
        'computer_name': getattr(event, 'computer_name', '-'),
        'evidence': self._evidence}

    return row

  def _GetVSSNumber(self, event):
    """Retrieves the VSS store number related to the event.

    Args:
      event (EventObject): event.

    Returns:
      int: VSS store number or -1 if not available.
    """
    if not hasattr(event, 'pathspec'):
      return -1

    return getattr(event.pathspec, 'vss_store_number', -1)

  def SetAppendMode(self, append):
    """Set the append status.

    Args:
      append (bool): True if the events should be added to the database.
    """
    self._append = append

  def SetEvidence(self, evidence):
    """Set the evidence field.

    Args:
      evidence (str): the evidence field.
    """
    self._evidence = evidence

  def SetFields(self, fields):
    """Set the fields that will be indexed in the database.

    Args:
      fields (list[str]): a list of fields that should be indexed.
    """
    self._fields = fields

  def SetStatusObject(self, status_object):
    """Set the status object.

    Args:
      status_object: status object provided by the 4n6time tool.
    """
    self._set_status = status_object
