# -*- coding: utf-8 -*-
"""The System Resource Usage Monitor (SRUM) ESE database event formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class SRUMApplicationResourceUsageEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a SRUM application resource usage event."""

  DATA_TYPE = 'windows:srum:application_usage'

  FORMAT_STRING_PIECES = [
      'Identifier: {identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      '{identifier}']


class SRUMNetworkDataUsageEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SRUM network data usage event."""

  DATA_TYPE = 'windows:srum:network_usage'

  FORMAT_STRING_PIECES = [
      'Application identifier: {application_identifier}',
      'Bytes received: {bytes_received}',
      'Bytes sent: {bytes_sent}',
      'Interface LUID: {interface_luid}',
      'User identifer: {user_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      '{application_identifier}']


class SRUMNetworkConnectivityUsageEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a SRUM network connectivity usage event."""

  DATA_TYPE = 'windows:srum:network_connectivity'

  FORMAT_STRING_PIECES = [
      'Identifier: {identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      '{identifier}']


manager.FormattersManager.RegisterFormatters([
    SRUMApplicationResourceUsageEventFormatter,
    SRUMNetworkDataUsageEventFormatter,
    SRUMNetworkConnectivityUsageEventFormatter])
