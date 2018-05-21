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
      'Application: {application}']

  FORMAT_STRING_SHORT_PIECES = [
      '{application}']


class SRUMNetworkDataUsageEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a SRUM network data usage event."""

  DATA_TYPE = 'windows:srum:network_usage'

  FORMAT_STRING_PIECES = [
      'Application: {application}',
      'Bytes received: {bytes_received}',
      'Bytes sent: {bytes_sent}',
      'Interface LUID: {interface_luid}',
      'User identifier: {user_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      '{application}']


class SRUMNetworkConnectivityUsageEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a SRUM network connectivity usage event."""

  DATA_TYPE = 'windows:srum:network_connectivity'

  FORMAT_STRING_PIECES = [
      'Application: {application}']

  FORMAT_STRING_SHORT_PIECES = [
      '{application}']


manager.FormattersManager.RegisterFormatters([
    SRUMApplicationResourceUsageEventFormatter,
    SRUMNetworkDataUsageEventFormatter,
    SRUMNetworkConnectivityUsageEventFormatter])
