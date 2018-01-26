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
      '{path}', 'Flag Values:', '{flag_values}', 'Flags:', '{hex_flags}',
      'Event Identifier:', '{event_identifier}'
  ]

  FORMAT_STRING_SHORT_PIECES = ['{path}', '{flag_values}']

  SOURCE_SHORT = 'FSEVENT'

  # pylint: disable=line-too-long
  # Flag values are similar, but not identical to those described in the Apple
  # documentation [1]. For example, the value of the IsDir flag is 0x00020000
  # but the value 0x00000001 corresponds to a change to a directory item in
  # an fseventsd file, by observation.
  # [1] https://developer.apple.com/documentation/coreservices/core_services_enumerations/1455361-fseventstreameventflags

  _FLAG_VALUES = {
      0x00000000: 'None',
      0x00000001: 'IsDirectory',
      0x00000002: 'Mount',
      0x00000004: 'Unmount',
      0x00000020: 'EndOfTransaction',
      0x00000800: 'LastHardLinkRemoved',
      0x00001000: 'IsHardLink',
      0x00004000: 'IsSymbolicLink',
      0x00008000: 'IsFile',
      0x00010000: 'PermissionChanged',
      0x00020000: 'ExtendedAttributeModified',
      0x00040000: 'ExtendedAttributeRemoved',
      0x00100000: 'DocumentRevision',
      0x00400000: 'ItemCloned',
      0x01000000: 'Created',
      0x02000000: 'Removed',
      0x04000000: 'InodeMetadataModified',
      0x08000000: 'Renamed',
      0x10000000: 'Modified',
      0x20000000: 'Exchange',
      0x40000000: 'FinderInfoModified',
      0x80000000: 'DirectoryCreated'}

  def _GetFlagValues(self, flags):
    """Determines which events are indicated by a set of fsevents flags.

    Args:
      flags (int): fsevents record flags.

    Returns:
      str: a comma separated string containing descriptions of the flag values
          stored in an fsevents record.
    """
    event_types = []
    for event_flag, description in self._FLAG_VALUES.items():
      if event_flag & flags:
        event_types.append(description)
    return ', '.join(event_types)

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
    event_values['hex_flags'] = '0x{0:X}'.format(flags)
    event_values['flag_values'] = self._GetFlagValues(flags)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatter(FSEventsdEventFormatter)
