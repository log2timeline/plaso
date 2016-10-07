# -*- coding: utf-8 -*-
"""Defines the shared code for 4n6time output modules."""

from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface


# pylint: disable=abstract-method

class Shared4n6TimeOutputModule(interface.OutputModule):
  """Class defining the base 4n6time output module."""

  NAME = '4n6time_shared'

  _DEFAULT_FIELDS = [
      u'datetime', u'host', u'source', u'sourcetype', u'user', u'type']

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
    self._evidence = u'-'
    self._fields = self._DEFAULT_FIELDS
    self._set_status = None

  def _GetSanitizedEventValues(self, event):
    """Sanitizes the event object for use in 4n6time.

    Args:
      event (EventObject): event.

    Returns:
      A dictionary object containing the sanitized values.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    data_type = getattr(event, u'data_type', u'UNKNOWN')

    event_formatter = self._output_mediator.GetEventFormatter(event)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    message, _ = self._output_mediator.GetFormattedMessages(event)
    if message is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    source_short, source = self._output_mediator.GetFormattedSources(event)
    if source is None or source_short is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    datetime_object = None
    if event.timestamp is not None:
      datetime_object = timelib.Timestamp.CopyToDatetime(
          event.timestamp, self._output_mediator.timezone)
      if not datetime_object:
        self._ReportEventError(event, (
            u'unable to copy timestamp: {0:d} to datetime object.'))
        return

    format_variables = self._output_mediator.GetFormatStringAttributeNames(
        event)
    if format_variables is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    extra_attributes = []
    for attribute_name, attribute_value in sorted(event.GetAttributes()):
      if (attribute_name in definitions.RESERVED_VARIABLE_NAMES or
          attribute_name in format_variables):
        continue
      extra_attributes.append(
          u'{0:s}: {1!s} '.format(attribute_name, attribute_value))

    extra_attributes = u' '.join(extra_attributes)

    inode = event.inode
    if inode is None and hasattr(event, u'pathspec'):
      inode = getattr(event.pathspec, u'inode', u'-')
    if inode is None:
      inode = u'-'

    datetime_string = u'N/A'
    if datetime_object:
      datetime_string = (
          u'{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(
              datetime_object.year, datetime_object.month, datetime_object.day,
              datetime_object.hour, datetime_object.minute,
              datetime_object.second))

    tags = None
    if getattr(event, u'tag', None):
      tags = getattr(event.tag, u'tags', None)

    taglist = u''
    if isinstance(tags, (list, tuple)):
      taglist = u','.join(tags)

    offset = event.offset
    if offset is None:
      offset = 0

    row = {
        u'timezone': u'{0!s}'.format(self._output_mediator.timezone),
        u'MACB': self._output_mediator.GetMACBRepresentation(event),
        u'source': source_short,
        u'sourcetype': source,
        u'type': getattr(event, u'timestamp_desc', u'-'),
        u'user': getattr(event, u'username', u'-'),
        u'host': getattr(event, u'hostname', u'-'),
        u'description': message,
        u'filename': getattr(event, u'filename', u'-'),
        u'inode': inode,
        u'notes': getattr(event, u'notes', u'-'),
        u'format': getattr(event, u'parser', u'-'),
        u'extra': extra_attributes,
        u'datetime': datetime_string,
        u'reportnotes': u'',
        u'inreport': u'',
        u'tag': taglist,
        u'offset': offset,
        u'vss_store_number': self._GetVSSNumber(event),
        u'URL': getattr(event, u'url', u'-'),
        u'record_number': getattr(event, u'record_number', 0),
        u'event_identifier': getattr(event, u'event_identifier', u'-'),
        u'event_type': getattr(event, u'event_type', u'-'),
        u'source_name': getattr(event, u'source_name', u'-'),
        u'user_sid': getattr(event, u'user_sid', u'-'),
        u'computer_name': getattr(event, u'computer_name', u'-'),
        u'evidence': self._evidence}

    return row

  def _GetVSSNumber(self, event):
    """Retrieves the VSS store number related to the event.

    Args:
      event (EventObject): event.

    Returns:
      The VSS store number or -1 if not available.
    """
    if not hasattr(event, u'pathspec'):
      return -1

    return getattr(event.pathspec, u'vss_store_number', -1)

  def SetAppendMode(self, append):
    """Set the append status.

    Args:
      append: boolean that determines whether or not to append to the database.
    """
    if append:
      self._append = True
    else:
      self._append = False

  def SetEvidence(self, evidence):
    """Set the evidence field.

    Args:
      evidence: the evidence field.
    """
    self._evidence = evidence

  def SetFields(self, fields):
    """Set the fields that will be indexed in the database.

    Args:
      fields: a list of fields that should be indexed.
    """
    self._fields = fields

  def SetStatusObject(self, status_object):
    """Set the status object.

    Args:
      status_object: status object provided by the 4n6time tool.
    """
    self._set_status = status_object
