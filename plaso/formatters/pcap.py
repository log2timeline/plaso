# -*- coding: utf-8 -*-
"""The PCAP event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class PCAPFormatter(interface.ConditionalEventFormatter):
  """Formatter for a PCAP event."""

  DATA_TYPE = 'metadata:pcap'

  FORMAT_STRING_PIECES = [
      'Source IP: {source_ip}',
      'Destination IP: {dest_ip}',
      'Source Port: {source_port}',
      'Destination Port: {dest_port}',
      'Protocol: {protocol}',
      'Type: {stream_type}',
      'Size: {size}',
      'Protocol Data: {protocol_data}',
      'Stream Data: {stream_data}',
      'First Packet ID: {first_packet_id}',
      'Last Packet ID: {last_packet_id}',
      'Packet Count: {packet_count}']

  FORMAT_STRING_SHORT_PIECES = [
      'Type: {stream_type}',
      'First Packet ID: {first_packet_id}']

  SOURCE_LONG = 'Packet Capture File (pcap)'
  SOURCE_SHORT = 'PCAP'


manager.FormattersManager.RegisterFormatter(PCAPFormatter)
