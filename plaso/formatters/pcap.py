# -*- coding: utf-8 -*-
"""The PCAP event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


__author__ = 'Dominique Kilman (lexistar97@gmail.com)'


class PCAPFormatter(interface.ConditionalEventFormatter):
  """Formatter for a PCAP event."""

  DATA_TYPE = 'metadata:pcap'

  FORMAT_STRING_PIECES = [
      u'Source IP: {source_ip}',
      u'Destination IP: {dest_ip}',
      u'Source Port: {source_port}',
      u'Destination Port: {dest_port}',
      u'Protocol: {protocol}',
      u'Type: {stream_type}',
      u'Size: {size}',
      u'Protocol Data: {protocol_data}',
      u'Stream Data: {stream_data}',
      u'First Packet ID: {first_packet_id}',
      u'Last Packet ID: {last_packet_id}',
      u'Packet Count: {packet_count}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Type: {stream_type}',
      u'First Packet ID: {first_packet_id}']

  SOURCE_LONG = 'Packet Capture File (pcap)'
  SOURCE_SHORT = 'PCAP'


manager.FormattersManager.RegisterFormatter(PCAPFormatter)
