#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Formatter for PCAP files."""

from plaso.lib import eventdata


__author__ = 'Dominique Kilman (lexistar97@gmail.com)'


class PCAPFormatter(eventdata.ConditionalEventFormatter):
  """Define the formatting PCAP record."""

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
