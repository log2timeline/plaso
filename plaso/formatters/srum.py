# -*- coding: utf-8 -*-
"""The System Resource Usage Monitor (SRUM) ESE database event formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SRUMNetworkDataUsageMonitorEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a SRUM network data usage monitor event."""

  DATA_TYPE = 'windows:srum:network_usage'

  FORMAT_STRING_PIECES = [
      'Application identifier: {application_identifier}',
      'Bytes received: {bytes_received}',
      'Bytes sent: {bytes_sent}',
      'Interface LUID: {interface_luid}',
      'User identifer: {user_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      '{application_identifier}']


manager.FormattersManager.RegisterFormatters([
    SRUMNetworkDataUsageMonitorEventFormatter])
