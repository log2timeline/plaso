# -*- coding: utf-8 -*-
"""The Windows firewall log file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class WinFirewallFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Windows firewall log entry event."""

  DATA_TYPE = 'windows:firewall:log_entry'

  # TODO: Add more "elegant" formatting, as in transform ICMP code/type into
  # a more human readable format as well as translating the additional info
  # column (meaning may depend on action field).
  FORMAT_STRING_PIECES = [
      '{action}',
      '[',
      '{protocol}',
      '{path}',
      ']',
      'From: {source_ip}',
      ':{source_port}',
      '>',
      '{dest_ip}',
      ':{dest_port}',
      'Size (bytes): {size}',
      'Flags [{flags}]',
      'TCP Seq Number: {tcp_seq}',
      'TCP ACK Number: {tcp_ack}',
      'TCP Window Size (bytes): {tcp_win}',
      'ICMP type: {icmp_type}',
      'ICMP code: {icmp_code}',
      'Additional info: {info}']

  FORMAT_STRING_SHORT_PIECES = [
      '{action}',
      '[{protocol}]',
      '{source_ip}',
      ': {source_port}',
      '>',
      '{dest_ip}',
      ': {dest_port}']

  SOURCE_LONG = 'Windows Firewall Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(WinFirewallFormatter)
