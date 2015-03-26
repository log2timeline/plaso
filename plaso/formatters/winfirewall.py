# -*- coding: utf-8 -*-
"""Formatter for Windows firewall log files."""

from plaso.formatters import interface
from plaso.formatters import manager


class WinFirewallFormatter(interface.ConditionalEventFormatter):
  """A formatter for Windows firewall log entries."""

  DATA_TYPE = 'windows:firewall:log_entry'

  # TODO: Add more "elegant" formatting, as in transform ICMP code/type into
  # a more human readable format as well as translating the additional info
  # column (meaning may depend on action field).
  FORMAT_STRING_PIECES = [
      u'{action}',
      u'[',
      u'{protocol}',
      u'{path}',
      u']',
      u'From: {source_ip}',
      u':{source_port}',
      u'>',
      u'{dest_ip}',
      u':{dest_port}',
      u'Size (bytes): {size}',
      u'Flags [{flags}]',
      u'TCP Seq Number: {tcp_seq}',
      u'TCP ACK Number: {tcp_ack}',
      u'TCP Window Size (bytes): {tcp_win}',
      u'ICMP type: {icmp_type}',
      u'ICMP code: {icmp_code}',
      u'Additional info: {info}',
      ]

  FORMAT_STRING_SHORT_PIECES = [
      u'{action}',
      u'[{protocol}]',
      u'{source_ip}',
      u': {source_port}',
      u'>',
      u'{dest_ip}',
      u': {dest_port}',
      ]

  SOURCE_LONG = 'Windows Firewall Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(WinFirewallFormatter)
