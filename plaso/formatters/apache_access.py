# -*- coding: utf-8 -*-
""" Apache access log file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class ApacheAccessFormatter(interface.ConditionalEventFormatter):
  """Formatter for a apache access log event."""

  DATA_TYPE = 'apache:access'

  FORMAT_STRING_PIECES = [
      'http_request: {http_request}',
      'from: {ip_address}',
      'code: {http_response_code}',
      'referer: {http_request_referer}',
      'user_agent: {http_request_user_agent}',
      'server_name: {server_name}',
      'port: {port_number}'
  ]

  FORMAT_STRING_SHORT_PIECES = [
      '{http_request}',
      'from: {ip_address}'
  ]

  SOURCE_LONG = 'Apache Access'
  SOURCE_SHORT = 'LOG'


manager.FormattersManager.RegisterFormatter(ApacheAccessFormatter)
