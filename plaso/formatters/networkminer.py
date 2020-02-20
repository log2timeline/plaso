# -*- coding: utf-8 -*-
"""The NetworkMiner file event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

class NetworkminerEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for NetworkMiner's fileinfo Log event."""

  DATA_TYPE = "networkminer:fileinfos:file"

  FORMAT_STRING_PIECES = [
      'Source IP: {source_ip}',
      'Source Port: {source_port}',
      'Destination IP: {destination_ip}',
      'Destination Port: {destination_port}',
      '{filename}',
      '{file_path}',
      '{file_size}',
      '{file_md5}',
      '{file_details}']

  FORMAT_STRING_SHORT_PIECES = [
      'Source IP: {source_ip}',
      'Destination IP: {destination_ip}',
      '{filename}',
      '{file_path}',
      '{file_md5}']
  SOURCE_LONG = 'NetworkMiner fileinfos'
  SOURCE_SHORT = 'NetworkMiner'

manager.FormattersManager.RegisterFormatter(NetworkminerEventFormatter)
