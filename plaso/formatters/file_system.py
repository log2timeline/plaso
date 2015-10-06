# -*- coding: utf-8 -*-
"""The file system stat event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class FileStatEventFormatter(interface.ConditionalEventFormatter):
  """The file system stat event formatter."""

  DATA_TYPE = u'fs:stat'

  FORMAT_STRING_PIECES = [
      u'{display_name}',
      u'({unallocated})']

  FORMAT_STRING_SHORT_PIECES = [
      u'{filename}']

  SOURCE_SHORT = u'FILE'

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.GetValues()

    # The usage of allocated is deprecated in favor of is_allocated but
    # is kept here to be backwards compatible.
    if (not event_values.get(u'allocated', False) and
        not event_values.get(u'is_allocated', False)):
      event_values[u'unallocated'] = u'unallocated'

    return self._ConditionalFormatMessages(event_values)

  def GetSources(self, event_object):
    """Determines the the short and long source for an event object.

    Args:
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple of the short and long source string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    file_system_type = getattr(event_object, u'file_system_type', u'UNKNOWN')
    timestamp_desc = getattr(event_object, u'timestamp_desc', u'Time')
    source_long = u'{0:s} {1:s}'.format(file_system_type, timestamp_desc)

    return self.SOURCE_SHORT, source_long


class NTFSFileStatEventFormatter(FileStatEventFormatter):
  """The NTFS file system stat event formatter."""

  DATA_TYPE = u'fs:stat:ntfs'

  FORMAT_STRING_PIECES = [
      u'{display_name}',
      u'File reference: {file_reference}',
      u'Attribute name: {attribute_name}',
      u'Name: {name}',
      u'Parent file reference: {parent_file_reference}',
      u'({unallocated})']

  FORMAT_STRING_SHORT_PIECES = [
      u'{filename}',
      u'{file_reference}',
      u'{attribute_name}']

  SOURCE_SHORT = u'FILE'

  _ATTRIBUTE_NAMES = {
      0x00000010: u'$STANDARD_INFORMATION',
      0x00000030: u'$FILE_NAME'
  }

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.GetValues()

    attribute_type = event_values.get(u'attribute_type', 0)
    event_values[u'attribute_name'] = self._ATTRIBUTE_NAMES.get(
        attribute_type, u'UNKNOWN')

    file_reference = event_values.get(u'file_reference', 0)
    event_values[u'file_reference'] = u'{0:d}-{1:d}'.format(
        file_reference & 0xffffffffffff, file_reference >> 48)

    parent_file_reference = event_values.get(u'parent_file_reference', 0)
    if parent_file_reference:
      event_values[u'parent_file_reference'] = u'{0:d}-{1:d}'.format(
          parent_file_reference & 0xffffffffffff, parent_file_reference >> 48)

    if not event_values.get(u'is_allocated', False):
      event_values[u'unallocated'] = u'unallocated'

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatters([
    FileStatEventFormatter, NTFSFileStatEventFormatter])
