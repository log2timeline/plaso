# -*- coding: utf-8 -*-
"""Defines the shared code for 4n6time output modules."""

from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import interface


# pylint: disable=abstract-method

class Base4n6TimeOutputModule(interface.OutputModule):
  """Class defining the base 4n6time output module."""

  NAME = '4n6time_shared'

  _DEFAULT_FIELDS = [
      u'datetime', u'host', u'source', u'sourcetype', u'user', u'type']

  def __init__(self, output_mediator):
    """Initializes the output module object.

    Args:
      output_mediator: The output mediator object (instance of OutputMediator).

    Raises:
      ValueError: when there are unused keyword arguments.
    """
    super(Base4n6TimeOutputModule, self).__init__(output_mediator)
    self._append = False
    self._evidence = u'-'
    self._fields = self._DEFAULT_FIELDS
    self._set_status = None

  def _GetSanitizedEventValues(self, event_object):
    """Sanitizes the event object for use in 4n6time.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A dictionary object containing the sanitized values.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
                        type in the event object.
    """
    data_type = getattr(event_object, u'data_type', u'UNKNOWN')

    event_formatter = self._output_mediator.GetEventFormatter(event_object)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    message, _ = self._output_mediator.GetFormattedMessages(event_object)
    if message is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    source_short, source = self._output_mediator.GetFormattedSources(
        event_object)
    if source is None or source_short is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    date_use = timelib.Timestamp.CopyToDatetime(
        event_object.timestamp, self._output_mediator.timezone)
    if not date_use:
      self._ReportEventError(event_object, (
          u'unable to copy timestamp: {0:d} to datetime object.'))
      return

    format_variables = self._output_mediator.GetFormatStringAttributeNames(
        event_object)
    if format_variables is None:
      raise errors.NoFormatterFound(
          u'Unable to find event formatter for: {0:s}.'.format(data_type))

    extra = []
    for attribute_name in event_object.GetAttributes():
      if (attribute_name in definitions.RESERVED_VARIABLE_NAMES or
          attribute_name in format_variables):
        continue
      attribute_value = getattr(event_object, attribute_name, None)
      extra.append(u'{0:s}: {1!s} '.format(attribute_name, attribute_value))

    extra = u' '.join(extra)

    inode = getattr(event_object, u'inode', u'-')
    if inode == u'-' and hasattr(event_object, u'pathspec'):
      inode = getattr(event_object.pathspec, u'inode', u'-')

    date_use_string = u'{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(
        date_use.year, date_use.month, date_use.day, date_use.hour,
        date_use.minute, date_use.second)

    if getattr(event_object, u'tag', None):
      tags = getattr(event_object.tag, u'tags', None)
    else:
      tags = None

    if isinstance(tags, (list, tuple)):
      taglist = u','.join(tags)
    else:
      taglist = u''

    row = {
        u'timezone': u'{0!s}'.format(self._output_mediator.timezone),
        u'MACB': self._output_mediator.GetMACBRepresentation(event_object),
        u'source': source_short,
        u'sourcetype': source,
        u'type': getattr(event_object, u'timestamp_desc', u'-'),
        u'user': getattr(event_object, u'username', u'-'),
        u'host': getattr(event_object, u'hostname', u'-'),
        u'description': message,
        u'filename': getattr(event_object, u'filename', u'-'),
        u'inode': inode,
        u'notes': getattr(event_object, u'notes', u'-'),
        u'format': getattr(event_object, u'parser', u'-'),
        u'extra': extra,
        u'datetime': date_use_string,
        u'reportnotes': u'',
        u'inreport': u'',
        u'tag': taglist,
        u'offset': getattr(event_object, u'offset', 0),
        u'vss_store_number': self._GetVSSNumber(event_object),
        u'URL': getattr(event_object, u'url', u'-'),
        u'record_number': getattr(event_object, u'record_number', 0),
        u'event_identifier': getattr(event_object, u'event_identifier', u'-'),
        u'event_type': getattr(event_object, u'event_type', u'-'),
        u'source_name': getattr(event_object, u'source_name', u'-'),
        u'user_sid': getattr(event_object, u'user_sid', u'-'),
        u'computer_name': getattr(event_object, u'computer_name', u'-'),
        u'evidence': self._evidence}

    return row

  def _GetVSSNumber(self, event_object):
    """Retrieves the VSS store number related to the event.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      The VSS store number or -1 if not available.
    """
    if not hasattr(event_object, u'pathspec'):
      return -1

    return getattr(event_object.pathspec, u'vss_store_number', -1)

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
