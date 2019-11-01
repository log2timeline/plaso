# -*- coding: utf-8 -*-
"""Shared functionality for 4n6time output modules."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.output import interface
from plaso.output import logger


class Shared4n6TimeOutputModule(interface.OutputModule):
  """Shared functionality for an 4n6time output module."""

  # pylint: disable=abstract-method

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

  def _FormatDateTime(self, event, event_data):
    """Formats the date and time.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.

    Returns:
      str: date and time string or "N/A" if no event timestamp is available.
    """
    if not event.timestamp:
      return 'N/A'

    # TODO: preserve dfdatetime as an object.
    # TODO: add support for self._output_mediator.timezone
    date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=event.timestamp)

    year, month, day_of_month = date_time.GetDate()
    hours, minutes, seconds = date_time.GetTimeOfDay()

    try:
      return '{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'.format(
          year, month, day_of_month, hours, minutes, seconds)
    except (TypeError, ValueError):
      self._ReportEventError(event, event_data, (
          'unable to copy timestamp: {0!s} to a human readable date and '
          'time. Defaulting to: "0000-00-00 00:00:00"').format(event.timestamp))

      return '0000-00-00 00:00:00'

  def _FormatInode(self, event_data):
    """Formats the inode.

    Args:
      event_data (EventData): event data.

    Returns:
      str: inode field.
    """
    inode = getattr(event_data, 'inode', None)
    if inode is None:
      pathspec = getattr(event_data, 'pathspec', None)
      if pathspec and hasattr(pathspec, 'inode'):
        inode = pathspec.inode
    if inode is None:
      inode = '-'

    return inode

  def _FormatTag(self, event_tag):
    """Formats the event tag.

    Args:
      event_tag (EventTag): event tag or None if not set.

    Returns:
      str: event tag labels or an empty string if event tag is not set.
    """
    if not event_tag:
      return ''

    return ' '.join(event_tag.labels)

  def _FormatVSSNumber(self, event_data):
    """Formats the VSS store number related to the event.

    Args:
      event_data (EventData): event data.

    Returns:
      int: VSS store number or -1 if not available.
    """
    if not hasattr(event_data, 'pathspec'):
      return -1

    return getattr(event_data.pathspec, 'vss_store_number', -1)

  def _GetSanitizedEventValues(self, event, event_data, event_tag):
    """Sanitizes the event for use in 4n6time.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.

    Returns:
      dict[str, object]: dictionary containing the sanitized event values.

    Raises:
      NoFormatterFound: If no event formatter can be found to match the data
          type in the event data.
    """
    data_type = getattr(event_data, 'data_type', 'UNKNOWN')

    event_formatter = self._output_mediator.GetEventFormatter(event_data)
    if not event_formatter:
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    message, _ = self._output_mediator.GetFormattedMessages(event_data)
    if message is None:
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    source_short, source = self._output_mediator.GetFormattedSources(
        event, event_data)
    if source is None or source_short is None:
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    datetime_string = self._FormatDateTime(event, event_data)

    unformatted_attributes = (
        formatters_manager.FormattersManager.GetUnformattedAttributes(
            event_data))
    if unformatted_attributes is None:
      raise errors.NoFormatterFound(
          'Unable to find event formatter for: {0:s}.'.format(data_type))

    extra_attributes = []
    for attribute_name, attribute_value in sorted(event_data.GetAttributes()):
      if attribute_name in unformatted_attributes:
        # Some parsers have written bytes values to storage.
        if isinstance(attribute_value, py2to3.BYTES_TYPE):
          attribute_value = attribute_value.decode('utf-8', 'replace')
          logger.warning(
              'Found bytes value for attribute "{0:s}" for data type: '
              '{1!s}. Value was converted to UTF-8: "{2:s}"'.format(
                  attribute_name, event_data.data_type, attribute_value))
        extra_attributes.append('{0:s}: {1!s} '.format(
            attribute_name, attribute_value))

    extra_attributes = ' '.join(extra_attributes)

    inode = self._FormatInode(event_data)
    vss_store_number = self._FormatVSSNumber(event_data)

    tag = self._FormatTag(event_tag)

    offset = event_data.offset
    if offset is None:
      offset = 0

    row = {
        'timezone': '{0!s}'.format(self._output_mediator.timezone),
        'MACB': self._output_mediator.GetMACBRepresentation(event, event_data),
        'source': source_short,
        'sourcetype': source,
        'type': event.timestamp_desc or '-',
        'user': getattr(event_data, 'username', '-'),
        'host': getattr(event_data, 'hostname', '-'),
        'description': message,
        'filename': getattr(event_data, 'filename', '-'),
        'inode': inode,
        'notes': getattr(event_data, 'notes', '-'),
        'format': getattr(event_data, 'parser', '-'),
        'extra': extra_attributes,
        'datetime': datetime_string,
        'reportnotes': '',
        'inreport': '',
        'tag': tag,
        'offset': offset,
        'vss_store_number': vss_store_number,
        'URL': getattr(event_data, 'url', '-'),
        'record_number': getattr(event_data, 'record_number', 0),
        'event_identifier': getattr(event_data, 'event_identifier', '-'),
        'event_type': getattr(event_data, 'event_type', '-'),
        'source_name': getattr(event_data, 'source_name', '-'),
        'user_sid': getattr(event_data, 'user_sid', '-'),
        'computer_name': getattr(event_data, 'computer_name', '-'),
        'evidence': self._evidence}

    return row

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
      status_object (object): status object provided by the 4n6time tool.
    """
    self._set_status = status_object
