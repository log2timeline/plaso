# -*- coding: utf-8 -*-

from plaso.formatters import interface
from plaso.formatters import manager


class WinEvtxFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows XML EventLog (EVTX) record."""
  DATA_TYPE = 'windows:evtx:record'

  FORMAT_STRING_PIECES = [
      u'[{event_identifier} /',
      u'0x{event_identifier:04x}]',
      u'Record Number: {record_number}',
      u'Event Level: {event_level}',
      u'Source Name: {source_name}',
      u'Computer Name: {computer_name}',
      u'Strings: {strings}',
      u'XML string: {xml_strings}']

  FORMAT_STRING_SHORT_PIECES = [
      u'[{event_identifier} /',
      u'0x{event_identifier:04x}]',
      u'Strings: {strings}']

  SOURCE_LONG = 'WinEVTX'
  SOURCE_SHORT = 'EVT'


manager.FormattersManager.RegisterFormatter(WinEvtxFormatter)
