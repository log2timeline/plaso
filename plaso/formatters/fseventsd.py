# -*- coding: utf-8 -*-
"""The fseventsd event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class FSEventsdEventFormatter(interface.ConditionalEventFormatter):
  """The fseventsd event formatter."""

  DATA_TYPE = 'macos:fseventsd:record'

  FORMAT_STRING_PIECES = [
      '{object_type}:', '{path}', 'Changes:', '{event_types}', 'Event ID:',
      '{event_identifier}'
  ]

  FORMAT_STRING_SHORT_PIECES = ['{path}', '{event_types}']

  SOURCE_SHORT = 'FSEVENT'

  _OBJECT_TYPE_MASKS = {
      0x00000001: 'Folder',
      0x00001000: 'HardLink',
      0x00004000: 'SymbolicLink',
      0x00008000: 'File'}

  _EVENT_MASKS = {
      0x00000000: 'None',
      0x00000002: 'Mount',
      0x00000004: 'Unmount',
      0x00000020: 'EndOfTransaction',
      0x00000800: 'LastHardLinkRemoved',
      0x00010000: 'PermissionChanged',
      0x00020000: 'ExtendedAttrModified',
      0x00040000: 'ExtendedAttrRemoved',
      0x00100000: 'DocumentRevision',
      0x00400000: 'ItemCloned',
      0x01000000: 'Created',
      0x02000000: 'Removed',
      0x04000000: 'InodeMetaModified',
      0x08000000: 'Renamed',
      0x10000000: 'Modified',
      0x20000000: 'Exchange',
      0x40000000: 'FinderInfoModified',
      0x80000000: 'FolderCreated'}

  def _GetObjectType(self, flags):
    """Determines the object type for a given set of FSEvents flags.

    Args:
      flags (int): fsevents record type flags.

    Returns:
      str: name of the object type represented by the mask.
    """
    for value in self._OBJECT_TYPE_MASKS:
      if value & flags:
        return self._OBJECT_TYPE_MASKS[value]
    return 'UNKNOWN'

  def _GetEventTypes(self, mask):
    """Determines which events are stored in a set of fsevents flags.

    Args:
      mask (int): fsevents record type mask.

    Returns:
      str: a comma separated string containing all the events listed in an
          fsevents record.
    """
    event_types = []
    for value in self._EVENT_MASKS:
      if value & mask:
        event_types.append(self._EVENT_MASKS[value])
    return ','.join(event_types)

  def GetMessages(self, unused_formatter_mediator, event):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions between
          formatters and other components, such as storage and Windows EventLog
          resources.
      event (EventObject): event.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event.data_type:
      raise errors.WrongFormatter(
          'Unsupported data type: {0:s}.'.format(event.data_type))

    event_values = event.CopyToDict()
    flags = event_values['flags']
    event_values['object_type'] = self._GetObjectType(flags)
    event_values['event_types'] = self._GetEventTypes(flags)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(FSEventsdEventFormatter)
