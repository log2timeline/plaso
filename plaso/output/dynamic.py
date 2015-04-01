# -*- coding: utf-8 -*-
"""Contains a formatter for a dynamic output module for plaso."""

import logging
import re

from plaso.formatters import manager as formatters_manager
from plaso.lib import errors
from plaso.lib import timelib
from plaso.output import helper
from plaso.output import interface
from plaso.output import manager


class DynamicOutput(interface.FileOutputModule):
  """Dynamic selection of fields for a separated value output format."""

  NAME = u'dynamic'
  DESCRIPTION = (
      u'Dynamic selection of fields for a separated value output format.')

  FORMAT_ATTRIBUTE_RE = re.compile('{([^}]+)}')

  # A dict containing mappings between "special" attributes and
  # how they should be calculated and presented.
  # They should be documented here:
  #   http://plaso.kiddaland.net/usage/psort/output
  SPECIAL_HANDLING = {
      'date': 'ParseDate',
      'datetime': 'ParseDateTime',
      'description': 'ParseMessage',
      'description_short': 'ParseMessageShort',
      'host': 'ParseHostname',
      'hostname': 'ParseHostname',
      'inode': 'ParseInode',
      'macb': 'ParseMacb',
      'message': 'ParseMessage',
      'message_short': 'ParseMessageShort',
      'source': 'ParseSourceShort',
      'sourcetype': 'ParseSource',
      'source_long': 'ParseSource',
      'tag': 'ParseTag',
      'time': 'ParseTime',
      'timezone': 'ParseZone',
      'type': 'ParseTimestampDescription',
      'user': 'ParseUsername',
      'username': 'ParseUsername',
      'zone': 'ParseZone',
  }

  def ParseTimestampDescription(self, event_object):
    """Return the timestamp description."""
    return getattr(event_object, 'timestamp_desc', '-')

  def ParseTag(self, event_object):
    """Return tagging information."""
    tag = getattr(event_object, 'tag', None)

    if not tag:
      return u'-'

    return u' '.join(tag.tags)

  def ParseSource(self, event_object):
    """Return the source string."""
    # TODO: move this to an output module interface.
    event_formatter = formatters_manager.FormattersManager.GetFormatterObject(
        event_object.data_type)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find no event formatter for: {0:s}.'.format(
              event_object.data_type))

    _, source = event_formatter.GetSources(event_object)
    return source

  def ParseSourceShort(self, event_object):
    """Return the source string."""
    # TODO: move this to an output module interface.
    event_formatter = formatters_manager.FormattersManager.GetFormatterObject(
        event_object.data_type)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find no event formatter for: {0:s}.'.format(
              event_object.data_type))

    source, _ = event_formatter.GetSources(event_object)
    return source

  def ParseZone(self, _):
    """Return a timezone."""
    return self._timezone

  def ParseDate(self, event_object):
    """Return a date string from a timestamp value."""
    try:
      date_use = timelib.Timestamp.CopyToDatetime(
          event_object.timestamp, self._timezone, raise_error=True)
    except OverflowError as exception:
      logging.error((
          u'Unable to copy {0:d} into a human readable timestamp with error: '
          u'{1:s}. Event {2:d}:{3:d} triggered the exception.').format(
              event_object.timestamp, exception,
              getattr(event_object, 'store_number', u''),
              getattr(event_object, 'store_index', u'')))
      return u'0000-00-00'
    return u'{0:04d}-{1:02d}-{2:02d}'.format(
        date_use.year, date_use.month, date_use.day)

  def ParseDateTime(self, event_object):
    """Return a datetime object from a timestamp, in an ISO format."""
    try:
      return timelib.Timestamp.CopyToIsoFormat(
          event_object.timestamp, timezone=self._timezone, raise_error=True)

    except OverflowError as exception:
      logging.error((
          u'Unable to copy {0:d} into a human readable timestamp with error: '
          u'{1:s}. Event {2:d}:{3:d} triggered the exception.').format(
              event_object.timestamp, exception,
              getattr(event_object, 'store_number', u''),
              getattr(event_object, 'store_index', u'')))
      return u'0000-00-00T00:00:00'

  def ParseTime(self, event_object):
    """Return a timestamp string from an integer timestamp value."""
    try:
      date_use = timelib.Timestamp.CopyToDatetime(
          event_object.timestamp, self._timezone, raise_error=True)
    except OverflowError as exception:
      logging.error((
          u'Unable to copy {0:d} into a human readable timestamp with error: '
          u'{1:s}. Event {2:d}:{3:d} triggered the exception.').format(
              event_object.timestamp, exception,
              getattr(event_object, 'store_number', u''),
              getattr(event_object, 'store_index', u'')))
      return u'00:00:00'
    return u'{0:02d}:{1:02d}:{2:02d}'.format(
        date_use.hour, date_use.minute, date_use.second)

  def ParseHostname(self, event_object):
    """Return a hostname."""
    hostname = getattr(event_object, 'hostname', '')
    if self.store:
      if not hostname:
        hostname = self._hostnames.get(event_object.store_number, '-')

    return hostname

  # TODO: move this into a base output class.
  def ParseUsername(self, event_object):
    """Determines an username based on an event and extracted information.

    Uses the extracted information from the pre processing information and the
    event object itself to determine an username.

    Args:
      event_object: The event object (instance of EventObject).

    Returns:
      An Unicode string containing the username, or - if none found.
    """
    username = getattr(event_object, u'username', u'-')
    if self.store:
      pre_obj = self._preprocesses.get(event_object.store_number)
      if pre_obj:
        check_user = pre_obj.GetUsernameById(username)

        if check_user != u'-':
          username = check_user

    if username == '-' and hasattr(event_object, u'user_sid'):
      if not pre_obj:
        return getattr(event_object, u'user_sid', u'-')

      return pre_obj.GetUsernameById(
          getattr(event_object, u'user_sid', u'-'))

    return username

  def ParseMessage(self, event_object):
    """Return the message string from the EventObject.

    Args:
      event_object: The event object (EventObject).

    Raises:
      errors.NoFormatterFound: If no formatter for that event is found.
    """
    # TODO: move this to an output module interface.
    event_formatter = formatters_manager.FormattersManager.GetFormatterObject(
        event_object.data_type)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find no event formatter for: {0:s}.'.format(
              event_object.data_type))

    msg, _ = event_formatter.GetMessages(self._formatter_mediator, event_object)
    return msg

  def ParseMessageShort(self, event_object):
    """Return the message string from the EventObject.

    Args:
      event_object: The event object (EventObject).

    Raises:
      errors.NoFormatterFound: If no formatter for that event is found.
    """
    # TODO: move this to an output module interface.
    event_formatter = formatters_manager.FormattersManager.GetFormatterObject(
        event_object.data_type)
    if not event_formatter:
      raise errors.NoFormatterFound(
          u'Unable to find no event formatter for: {0:s}.'.format(
              event_object.data_type))

    _, msg_short = event_formatter.GetMessages(
        self._formatter_mediator, event_object)
    return msg_short

  def ParseInode(self, event_object):
    """Return an inode number."""
    inode = getattr(event_object, 'inode', '-')
    if inode == '-':
      if hasattr(event_object, 'pathspec') and hasattr(
          event_object.pathspec, 'image_inode'):
        inode = event_object.pathspec.image_inode

    return inode

  def ParseMacb(self, event_object):
    """Return a legacy MACB representation."""
    return helper.GetLegacy(event_object)

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    row = []
    for field in self.fields:
      has_call_back = self.SPECIAL_HANDLING.get(field, None)
      call_back = None
      if has_call_back:
        call_back = getattr(self, has_call_back, None)

      if call_back:
        row.append(call_back(event_object))
      else:
        row.append(getattr(event_object, field, u'-'))

    out_write = u'{0:s}\n'.format(
        self.separator.join(unicode(x).replace(
            self.separator, u' ') for x in row))
    self._WriteLine(out_write)

  def WriteHeader(self):
    """Writes the header to the output."""
    # Start by finding out which fields are to be used.
    self.fields = []

    if self._filter:
      self.fields = self._filter.fields
      self.separator = self._filter.separator
    else:
      self.separator = u','

    if not self.fields:
      # TODO: Evaluate which fields should be included by default.
      self.fields = [
          'datetime', 'timestamp_desc', 'source', 'source_long',
          'message', 'parser', 'display_name', 'tag', 'store_number',
          'store_index']

    if self.store:
      self._hostnames = helper.BuildHostDict(self.store)
      self._preprocesses = {}
      for info in self.store.GetStorageInformation():
        if hasattr(info, 'store_range'):
          for store_number in range(info.store_range[0], info.store_range[1]):
            self._preprocesses[store_number] = info

    self._WriteLine('{0:s}\n'.format(self.separator.join(self.fields)))


manager.OutputManager.RegisterOutput(DynamicOutput)
