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
"""Parser for PCAP files."""

import binascii
import operator
import socket

import dpkt

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Dominique Kilman (lexistar97@gmail.com)'


def ParseDNS(dns_packet_data):
  """Parse DNS packets and return a string with relevant details.

  Args:
    dns_packet_data: DNS packet data.

  Returns:
    Formatted DNS details.
  """
  dns_data = []

  try:
    dns = dpkt.dns.DNS(dns_packet_data)
    if dns.rcode is dpkt.dns.DNS_RCODE_NOERR:
      if dns.get_qr() == 1:
        if not dns.an:
          dns_data.append('DNS Response: No answer for ')
          dns_data.append(dns.qd[0].name)
        else:
          # Type of DNS answer.
          for answer in dns.an:
            if answer.type == 5:
              dns_data.append('DNS-CNAME request ')
              dns_data.append(answer.name)
              dns_data.append(' response: ')
              dns_data.append(answer.cname)
            elif answer.type == 1:
              dns_data.append('DNS-A request ')
              dns_data.append(answer.name)
              dns_data.append(' response: ')
              dns_data.append(socket.inet_ntoa(answer.rdata))
            elif answer.type == 12:
              dns_data.append('DNS-PTR request ')
              dns_data.append(answer.name)
              dns_data.append(' response: ')
              dns_data.append(answer.ptrname)
      elif not dns.get_qr():
        dns_data.append('DNS Query for ')
        dns_data.append(dns.qd[0].name)
    else:
      dns_data.append('DNS error code ')
      dns_data.append(str(dns.rcode))

  except dpkt.UnpackError as exception:
    dns_data.append('DNS Unpack Error: {0:s}. First 20 of data {1:s}'.format(
        exception, repr(dns_packet_data[:20])))
  except IndexError as exception:
    dns_data.append('DNS Index Error: {0:s}'.format(exception))

  return u' '.join(dns_data)


def ParseNetBios(netbios_packet):
  """Parse the netBIOS stream details.

  Args:
    netbios_packet: NetBIOS packet.

  Returns:
     Formatted netBIOS details.
  """
  netbios_data = []
  for query in netbios_packet.qd:
    netbios_data.append('NETBIOS qd:')
    netbios_data.append(repr(dpkt.netbios.decode_name(query.name)))
  for answer in netbios_packet.an:
    netbios_data.append('NETBIOS an:')
    netbios_data.append(repr(dpkt.netbios.decode_name(answer.name)))
  for name in netbios_packet.ns:
    netbios_data.append('NETBIOS ns:')
    netbios_data.append(repr(dpkt.netbios.decode_name(name.name)))

  return u' '.join(netbios_data)


def TCPFlags(flag):
  """Check the tcp flags for a packet for future use.

  Args:
    flag: Flag value from TCP packet.

  Returns:
    String with printable flags for specific packet.
  """
  res = []
  if flag & dpkt.tcp.TH_FIN:
    res.append('FIN')
  if flag & dpkt.tcp.TH_SYN:
    res.append('SYN')
  if flag & dpkt.tcp.TH_RST:
    res.append('RST')
  if flag & dpkt.tcp.TH_PUSH:
    res.append('PUSH')
  if flag & dpkt.tcp.TH_ACK:
    res.append('ACK')
  if flag & dpkt.tcp.TH_URG:
    res.append('URG')
  if flag & dpkt.tcp.TH_ECE:
    res.append('ECN')
  if flag & dpkt.tcp.TH_CWR:
    res.append('CWR')

  return '|'.join(res)


def ICMPTypes(packet):
  """Parse the type information for the icmp packets.

  Args:
    packet: ICMP packet data.

  Returns:
    Formatted ICMP details.
  """
  icmp_type = packet.type
  icmp_code = packet.code
  icmp_data = []
  icmp_data.append('ICMP')

  # TODO: Make the below code more readable.
  # Possible to use lookup dict? Or method
  # calls?
  if icmp_type is dpkt.icmp.ICMP_CODE_NONE:
    icmp_data.append('ICMP without codes')
  elif icmp_type is dpkt.icmp.ICMP_ECHOREPLY:
    icmp_data.append('echo reply')
  elif icmp_type is dpkt.icmp.ICMP_UNREACH:
    icmp_data.append('ICMP dest unreachable')
    if icmp_code is dpkt.icmp.ICMP_UNREACH_NET:
      icmp_data.append(': bad net')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_HOST:
      icmp_data.append(': host unreachable')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_PROTO:
      icmp_data.append(': bad protocol')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_PORT:
      icmp_data.append(': port unreachable')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_NEEDFRAG:
      icmp_data.append(': IP_DF caused drop')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_SRCFAIL:
      icmp_data.append(': src route failed')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_NET_UNKNOWN:
      icmp_data.append(': unknown net')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_HOST_UNKNOWN:
      icmp_data.append(': unknown host')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_ISOLATED:
      icmp_data.append(': src host isolated')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_NET_PROHIB:
      icmp_data.append(': for crypto devs')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_HOST_PROHIB:
      icmp_data.append(': for cypto devs')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_TOSNET:
      icmp_data.append(': bad tos for net')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_TOSHOST:
      icmp_data.append(': bad tos for host')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_FILTER_PROHIB:
      icmp_data.append(': prohibited access')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_HOST_PRECEDENCE:
      icmp_data.append(': precedence error')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_PRECEDENCE_CUTOFF:
      icmp_data.append(': precedence cutoff')
  elif icmp_type is dpkt.icmp.ICMP_SRCQUENCH:
    icmp_data.append('ICMP source quench')
  elif icmp_type is dpkt.icmp.ICMP_REDIRECT:
    icmp_data.append('ICMP Redirect')
    if icmp_code is dpkt.icmp.ICMP_REDIRECT_NET:
      icmp_data.append(' for network')
    elif icmp_code is dpkt.icmp.ICMP_REDIRECT_HOST:
      icmp_data.append(' for host')
    elif icmp_code is dpkt.icmp.ICMP_REDIRECT_TOSNET:
      icmp_data.append(' for tos and net')
    elif icmp_code is dpkt.icmp.ICMP_REDIRECT_TOSHOST:
      icmp_data.append(' for tos and host')
  elif icmp_type is dpkt.icmp.ICMP_ALTHOSTADDR:
    icmp_data.append('ICMP alternate host address')
  elif icmp_type is dpkt.icmp.ICMP_ECHO:
    icmp_data.append('ICMP echo')
  elif icmp_type is dpkt.icmp.ICMP_RTRADVERT:
    icmp_data.append('ICMP Route advertisement')
    if icmp_code is dpkt.icmp.ICMP_RTRADVERT_NORMAL:
      icmp_data.append(': normal')
    elif icmp_code is dpkt.icmp.ICMP_RTRADVERT_NOROUTE_COMMON:
      icmp_data.append(': selective routing')
  elif icmp_type is dpkt.icmp.ICMP_RTRSOLICIT:
    icmp_data.append('ICMP Router solicitation')
  elif icmp_type is dpkt.icmp.ICMP_TIMEXCEED:
    icmp_data.append('ICMP time exceeded, code:')
    if icmp_code is dpkt.icmp.ICMP_TIMEXCEED_INTRANS:
      icmp_data.append(' ttl==0 in transit')
    elif icmp_code is dpkt.icmp.ICMP_TIMEXCEED_REASS:
      icmp_data.append('ttl==0 in reass')
  elif icmp_type is dpkt.icmp.ICMP_PARAMPROB:
    icmp_data.append('ICMP ip header bad')
    if icmp_code is dpkt.icmp.ICMP_PARAMPROB_ERRATPTR:
      icmp_data.append(':req. opt. absent')
    elif icmp_code is dpkt.icmp.ICMP_PARAMPROB_OPTABSENT:
      icmp_data.append(': req. opt. absent')
    elif icmp_code is dpkt.icmp.ICMP_PARAMPROB_LENGTH:
      icmp_data.append(': length')
  elif icmp_type is dpkt.icmp.ICMP_TSTAMP:
    icmp_data.append('ICMP timestamp request')
  elif icmp_type is dpkt.icmp.ICMP_TSTAMPREPLY:
    icmp_data.append('ICMP timestamp reply')
  elif icmp_type is dpkt.icmp.ICMP_INFO:
    icmp_data.append('ICMP information request')
  elif icmp_type is dpkt.icmp.ICMP_INFOREPLY:
    icmp_data.append('ICMP information reply')
  elif icmp_type is dpkt.icmp.ICMP_MASK:
    icmp_data.append('ICMP address mask request')
  elif icmp_type is dpkt.icmp.ICMP_MASKREPLY:
    icmp_data.append('ICMP address mask reply')
  elif icmp_type is dpkt.icmp.ICMP_TRACEROUTE:
    icmp_data.append('ICMP traceroute')
  elif icmp_type is dpkt.icmp.ICMP_DATACONVERR:
    icmp_data.append('ICMP data conversion error')
  elif icmp_type is dpkt.icmp.ICMP_MOBILE_REDIRECT:
    icmp_data.append('ICMP mobile host redirect')
  elif icmp_type is dpkt.icmp.ICMP_IP6_WHEREAREYOU:
    icmp_data.append('ICMP IPv6 where-are-you')
  elif icmp_type is dpkt.icmp.ICMP_IP6_IAMHERE:
    icmp_data.append('ICMP IPv6 i-am-here')
  elif icmp_type is dpkt.icmp.ICMP_MOBILE_REG:
    icmp_data.append('ICMP mobile registration req')
  elif icmp_type is dpkt.icmp.ICMP_MOBILE_REGREPLY:
    icmp_data.append('ICMP mobile registration reply')
  elif icmp_type is dpkt.icmp.ICMP_DNS:
    icmp_data.append('ICMP domain name request')
  elif icmp_type is dpkt.icmp.ICMP_DNSREPLY:
    icmp_data.append('ICMP domain name reply')
  elif icmp_type is dpkt.icmp.ICMP_PHOTURIS:
    icmp_data.append('ICMP Photuris')
    if icmp_code is dpkt.icmp.ICMP_PHOTURIS_UNKNOWN_INDEX:
      icmp_data.append(': unknown sec index')
    elif icmp_code is dpkt.icmp.ICMP_PHOTURIS_AUTH_FAILED:
      icmp_data.append(': auth failed')
    elif icmp_code is dpkt.icmp.ICMP_PHOTURIS_DECOMPRESS_FAILED:
      icmp_data.append(': decompress failed')
    elif icmp_code is dpkt.icmp.ICMP_PHOTURIS_DECRYPT_FAILED:
      icmp_data.append(': decrypt failed')
    elif icmp_code is dpkt.icmp.ICMP_PHOTURIS_NEED_AUTHN:
      icmp_data.append(': no authentication')
    elif icmp_code is dpkt.icmp.ICMP_PHOTURIS_NEED_AUTHZ:
      icmp_data.append(': no authorization')
  elif icmp_type is dpkt.icmp.ICMP_TYPE_MAX:
    icmp_data.append('ICMP Type Max')

  return u' '.join(icmp_data)


class Stream(object):
  """Used to store packet details on network streams parsed from a pcap file."""

  def __init__(self, packet, prot_data, source_ip, dest_ip, prot):
    """Initialize new stream.

    Args:
      packet: Packet data.
      prot_data: Protocol level data for ARP, UDP, RCP, ICMP.
          other types of ether packets, this is just the ether.data.
      source_ip: Source IP.
      dest_ip: Dest IP.
      prot: Protocol (TCP, UDP, ICMP, ARP).
    """
    self.packet_id = [packet[1]]
    self.time_stamps = [packet[0]]
    self.size = packet[3]
    self.start_time = packet[0]
    self.all_data = [prot_data]
    self.protocol_data = ''
    self.stream_data = []

    if prot == 'TCP' or prot == 'UDP':
      self.source_port = prot_data.sport
      self.dest_port = prot_data.dport
    else:
      self.source_port = ''
      self.dest_port = ''

    self.source_ip = source_ip
    self.dest_ip = dest_ip
    self.protocol = prot

  def AddPacket(self, packet, prot_data):
    """Add another packet to an existing stream.

    Args:
      packet: Packet data.
      prot_data: Protocol level data for ARP, UDP, RCP, ICMP.
          other types of ether packets, this is just the ether.data
    """
    self.packet_id.append(packet[1])
    self.time_stamps.append(packet[0])
    self.all_data.append(prot_data)
    self.size += packet[3]

  def SpecialTypes(self):
    """Checks for some special types of packets.

    This method checks for some special packets and assembles usable data
    currently works for: DNS (udp 53), http, netbios (udp 137), ICMP.

    Returns:
      A tuple consisting of a basic desctiption of the stream
      (i.e. HTTP Request) and the prettyfied string for the protocols.
    """
    packet_details = []
    if self.stream_data[:4] == 'HTTP':
      try:
        http = dpkt.http.Response(self.stream_data)
        packet_details.append('HTTP Response: status: ')
        packet_details.append(http.status)
        packet_details.append(' reason: ')
        packet_details.append(http.reason)
        packet_details.append(' version: ')
        packet_details.append(http.version)
        return 'HTTP Response', u' '.join(packet_details)

      except dpkt.UnpackError as exception:
        packet_details = (
            u'HTTP Response Unpack Error: {0:s}. '
            u'First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return 'HTTP Response', packet_details

      except IndexError as exception:
        packet_details = (
            u'HTTP Response Index Error: {0:s}. First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return 'HTTP Response', packet_details

      except ValueError as exception:
        packet_details = (
            u'HTTP Response parsing error: {0:s}. '
            u'First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return 'HTTP Response', packet_details

    elif self.stream_data[:3] == 'GET' or self.stream_data[:4] == 'POST':
      try:
        http = dpkt.http.Request(self.stream_data)
        packet_details.append('HTTP Request: method: ')
        packet_details.append(http.method)
        packet_details.append(' uri: ')
        packet_details.append(http.uri)
        packet_details.append(' version: ')
        packet_details.append(http.version)
        packet_details.append(' headers: ')
        packet_details.append(repr(http.headers))
        return 'HTTP Request', u' '.join(packet_details)

      except dpkt.UnpackError as exception:
        packet_details = (
            u'HTTP Request unpack error: {0:s}. First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return 'HTTP Request', packet_details

      except ValueError as exception:
        packet_details = (
            u'HTTP Request parsing error: {0:s}. '
            u'First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return 'HTTP Request', packet_details

    elif self.protocol == 'UDP' and (
        self.source_port == 53 or self.dest_port == 53):
      # DNS request/replies.
      # Check to see if the lengths are valid.
      for packet in self.all_data:
        if not packet.ulen == len(packet):
          packet_details.append('Truncated DNS packets - unable to parse: ')
          packet_details.append(repr(self.stream_data[15:40]))
          return 'DNS', u' '.join(packet_details)

      return 'DNS', ParseDNS(self.stream_data)

    elif self.protocol == 'UDP' and (
        self.source_port == 137 or self.dest_port == 137):
      return 'NetBIOS', ParseNetBios(dpkt.netbios.NS(self.stream_data))

    elif self.protocol == 'ICMP':
      # ICMP packets all end up as 1 stream, so they need to be
      #  processed 1 by 1.
      return 'ICMP', ICMPTypes(self.all_data[0])

    elif '\x03\x01' in self.stream_data[1:3]:
      # Some form of ssl3 data.
      try:
        ssl = dpkt.ssl.SSL2(self.stream_data)
        packet_details.append('SSL data. Length: ')
        packet_details.append(str(ssl.len))
        return 'SSL', u' '.join(packet_details)
      except dpkt.UnpackError as exception:
        packet_details = (
            u'SSL unpack error: {0:s}. First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return 'SSL', packet_details

    elif '\x03\x00' in self.stream_data[1:3]:
       # Some form of ssl3 data.
      try:
        ssl = dpkt.ssl.SSL2(self.stream_data)
        packet_details.append('SSL data. Length: ')
        packet_details.append(str(ssl.len))
        return 'SSL', u' '.join(packet_details)

      except dpkt.UnpackError as exception:
        packet_details = (
            u'SSL unpack error: {0:s}. First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return 'SSL', packet_details

    return 'other', self.protocol_data

  def Clean(self):
    """Clean up stream data."""
    clean_data = []
    for packet in self.all_data:
      try:
        clean_data.append(packet.data)
      except AttributeError:
        pass

      self.stream_data = ''.join(clean_data)


class PcapEvent(time_events.PosixTimeEvent):
  """Convenience class for a PCAP record event."""

  DATA_TYPE = 'metadata:pcap'

  def __init__(self, timestamp, usage, this_stream):
    """Initializes the event.

    Args:
      timestamp: The POSIX value of the timestamp.
      usage: A usage description value.
      this_stream: The pcap stream.
    """
    super(PcapEvent, self).__init__(timestamp, usage)

    self.source_ip = this_stream.source_ip
    self.dest_ip = this_stream.dest_ip
    self.source_port = this_stream.source_port
    self.dest_port = this_stream.dest_port
    self.protocol = this_stream.protocol
    self.size = this_stream.size
    self.stream_type, self.protocol_data = this_stream.SpecialTypes()
    self.first_packet_id = min(this_stream.packet_id)
    self.last_packet_id = max(this_stream.packet_id)
    self.packet_count = len(this_stream.packet_id)
    self.stream_data = repr(this_stream.stream_data[:50])


class PcapParser(interface.BaseParser):
  """Parses PCAP files."""

  NAME = 'pcap'
  DESCRIPTION = u'Parser for PCAP files.'

  def Parse(self, parser_context, file_entry):
    """Extract data from a pcap file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
    """
    file_object = file_entry.GetFileObject()

    # TODO: this is a hack for a limitation in dpkt that expects the file
    # object to have a name. This needs to be fixed properly by creating
    # a plaso specific dpkt Reader object that takes a file entry as input.
    #file_object.name = file_entry.name

    try:
      pcap_reader = dpkt.pcap.Reader(file_object)
    except ValueError as exception:
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, file_entry.name, exception))
    except dpkt.NeedData as exception:
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, file_entry.name, exception))

    packet_id = 0
    ip_list = []
    other_list = []
    trunc_list = []

    for ts, data in pcap_reader:
      packet_id += 1
      ether = dpkt.ethernet.Ethernet(data)

      if ether.type == dpkt.ethernet.ETH_TYPE_IP:
        ip_list.append([ts, packet_id, ether.data, len(ether)])
      else:
        other_list.append([ts, packet_id, ether, len(ether)])

    connections = {}
    for ip_packet in ip_list:
      ip_data = ip_packet[2]

      if ip_data.p == dpkt.ip.IP_PROTO_TCP:
        tcp = ip_data.data
        try:
          new_stream = (
              'tcp', socket.inet_ntoa(ip_data.src), tcp.sport,
              socket.inet_ntoa(ip_data.dst), tcp.dport)
        except AttributeError:
          trunc_list.append(ip_packet)
          continue
        if new_stream in connections:
          connections[new_stream].AddPacket(ip_packet, tcp)
        else:
          connections[new_stream] = Stream(
              ip_packet, tcp, socket.inet_ntoa(ip_data.src),
              socket.inet_ntoa(ip_data.dst), 'TCP')
      elif ip_data.p == dpkt.ip.IP_PROTO_UDP:
        udp = ip_data.data
        try:
          new_stream = ('udp', socket.inet_ntoa(ip_data.src), udp.sport,
                        socket.inet_ntoa(ip_data.dst), udp.dport)
        except AttributeError:
          trunc_list.append(ip_packet)
          continue

        if new_stream in connections:
          connections[new_stream].AddPacket(ip_packet, udp)
        else:
          connections[new_stream] = Stream(
              ip_packet, udp, socket.inet_ntoa(ip_data.src),
              socket.inet_ntoa(ip_data.dst), 'UDP')

      elif ip_data.p == dpkt.ip.IP_PROTO_ICMP:
        icmp = ip_data.data
        new_stream = (
            'icmp', socket.inet_ntoa(ip_data.src), ip_packet[1],
            socket.inet_ntoa(ip_data.dst), ip_packet[1])

        if new_stream in connections:
          connections[new_stream].AddPacket(ip_packet, icmp)
        else:
          connections[new_stream] = Stream(
              ip_packet, icmp, socket.inet_ntoa(ip_data.src),
              socket.inet_ntoa(ip_data.dst), 'ICMP')

    other_streams = self.OtherStream(other_list, trunc_list)

    sorted_list = sorted(
        connections.values(), key=operator.attrgetter('start_time'))

    for entry in sorted_list:
      if not entry.protocol == 'ICMP':
        entry.Clean()
      parser_context.ProduceEvents(
          [PcapEvent(
              min(entry.time_stamps), eventdata.EventTimestamp.START_TIME,
              entry),
           PcapEvent(
               max(entry.time_stamps), eventdata.EventTimestamp.END_TIME,
               entry)],
          parser_name=self.NAME, file_entry=file_entry)

    for other_stream in other_streams:
      parser_context.ProduceEvents(
          [PcapEvent(
              min(other_stream.time_stamps),
              eventdata.EventTimestamp.START_TIME, other_stream),
           PcapEvent(
               max(other_stream.time_stamps), eventdata.EventTimestamp.END_TIME,
               other_stream)],
          parser_name=self.NAME, file_entry=file_entry)

    file_object.close()

  def OtherStream(self, other_list, trunc_list):
    """Process packets that are no IP packets.

    For all packets that were not IP packets, create stream containers
    depending on the type of packet.

    Args:
      other_list: List of non-ip packets.
      trunc_list: List of packets that truncated strangely and
                  couldn't be streamified.
    Returns:
      A stream container with detail information about the stream.
    """
    other_streams = []

    for packet in other_list:
      ether = packet[2]
      if ether.type == dpkt.ethernet.ETH_TYPE_ARP:
        arp = ether.data
        arp_data = []
        this_stream = Stream(packet, arp, binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst), 'ARP')
        if arp.op == dpkt.arp.ARP_OP_REQUEST:
          arp_data.append('arp request: target IP = ')
          arp_data.append(socket.inet_ntoa(arp.tpa))
          this_stream.protocol_data = u' '.join(arp_data)
        elif arp.op == dpkt.arp.ARP_OP_REPLY:
          arp_data.append('arp reply: target IP = ')
          arp_data.append(socket.inet_ntoa(arp.tpa))
          arp_data.append(' target MAC = ')
          arp_data.append(binascii.hexlify(arp.tha))
          this_stream.protocol_data = u' '.join(arp_data)
        elif arp.op == dpkt.arp.ARP_OP_REVREQUEST:
          arp_data.append('arp protocol address request: target IP = ')
          arp_data.append(socket.inet_ntoa(arp.tpa))
          this_stream.protocol_data = u' '.join(arp_data)
        elif arp.op == dpkt.arp.ARP_OP_REVREPLY:
          arp_data.append('arp protocol address reply: target IP = ')
          arp_data.append(socket.inet_ntoa(arp.tpa))
          arp_data.append(' target MAC = ')
          arp_data.append(binascii.hexlify(arp.tha))
          this_stream.protocol_data = u' '.join(arp_data)

        other_streams.append(this_stream)

      elif ether.type == dpkt.ethernet.ETH_TYPE_IP6:
        ip6 = ether.data
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ip6.src),
                             binascii.hexlify(ip6.dst), 'IPv6')
        this_stream.protocol_data = 'IPv6'
        other_streams.append(this_stream)
      elif ether.type == dpkt.ethernet.ETH_TYPE_CDP:
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst), 'CDP')
        this_stream.protocol_data = 'CDP'
        other_streams.append(this_stream)
      elif ether.type == dpkt.ethernet.ETH_TYPE_DTP:
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst), 'DTP')
        this_stream.protocol_data = 'DTP'
        other_streams.append(this_stream)
      elif ether.type == dpkt.ethernet.ETH_TYPE_REVARP:
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst), 'RARP')
        this_stream.protocol_data = 'Reverse ARP'
        other_streams.append(this_stream)
      elif ether.type == dpkt.ethernet.ETH_TYPE_8021Q:
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst),
                             '8021Q packet')
        this_stream.protocol_data = '8021Q packet'
        other_streams.append(this_stream)
      elif ether.type == dpkt.ethernet.ETH_TYPE_IPX:
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst), 'IPX')
        this_stream.protocol_data = 'IPX'
        other_streams.append(this_stream)
      elif ether.type == dpkt.ethernet.ETH_TYPE_PPP:
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst), 'PPP')
        this_stream.protocol_data = 'PPP'
        other_streams.append(this_stream)
      elif ether.type == dpkt.ethernet.ETH_TYPE_MPLS:
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst), 'MPLS')
        this_stream.protocol_data = 'MPLS'
        other_streams.append(this_stream)
      elif ether.type == dpkt.ethernet.ETH_TYPE_MPLS_MCAST:
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst), 'MPLS')
        this_stream.protocol_data = 'MPLS MCAST'
        other_streams.append(this_stream)
      elif ether.type == dpkt.ethernet.ETH_TYPE_PPPoE_DISC:
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst), 'PPOE')
        this_stream.protocol_data = 'PPoE Disc packet'
        other_streams.append(this_stream)
      elif ether.type == dpkt.ethernet.ETH_TYPE_PPPoE:
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst), 'PPPoE')
        this_stream.protocol_data = 'PPPoE'
        other_streams.append(this_stream)
      elif str(hex(ether.type)) == '0x2452':
        this_stream = Stream(packet, ether.data,
                             binascii.hexlify(ether.src),
                             binascii.hexlify(ether.dst), '802.11')
        this_stream.protocol_data = '802.11'
        other_streams.append(this_stream)

    for packet in trunc_list:
      ip = packet[2]
      this_stream = Stream(packet, ip.data, socket.inet_ntoa(ip.src),
                           socket.inet_ntoa(ip.dst), 'BAD')
      this_stream.protocolData = 'Bad truncated IP packet'
      other_streams.append(this_stream)

    return other_streams


manager.ParsersManager.RegisterParser(PcapParser)
