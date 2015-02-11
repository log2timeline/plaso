# -*- coding: utf-8 -*-
"""Formatter for Windows IIS log files."""

from plaso.formatters import interface
from plaso.formatters import manager


__author__ = 'Ashley Holtz (ashley.a.holtz@gmail.com)'


class WinIISFormatter(interface.ConditionalEventFormatter):
  """A formatter for Windows IIS log entries."""

  DATA_TYPE = 'iis:log:line'

  FORMAT_STRING_PIECES = [
      u'{http_method}',
      u'{requested_uri_stem}',
      u'[',
      u'{source_ip}',
      u'>',
      u'{dest_ip}',
      u':',
      u'{dest_port}',
      u']',
      u'HTTP Status: {http_status}',
      u'Bytes Sent: {sent_bytes}',
      u'Bytes Received: {received_bytes}',
      u'User Agent: {user_agent}',
      u'Protocol Version: {protocol_version}',]

  FORMAT_STRING_SHORT_PIECES = [
      u'{http_method}',
      u'{requested_uri_stem}',
      u'[',
      u'{source_ip}',
      u'>',
      u'{dest_ip}',
      u':',
      u'{dest_port}',
      u']',]

  SOURCE_LONG = 'IIS Log'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(WinIISFormatter)
