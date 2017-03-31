# -*- coding: utf-8 -*-
"""Parser for PCAP files."""

import binascii
import operator
import socket

import dpkt

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
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
      if dns.qr == 1:
        if not dns.an:
          dns_data.append(u'DNS Response: No answer for ')
          dns_data.append(dns.qd[0].name)
        else:
          # Type of DNS answer.
          for answer in dns.an:
            if answer.type == 5:
              dns_data.append(u'DNS-CNAME request ')
              dns_data.append(answer.name)
              dns_data.append(u' response: ')
              dns_data.append(answer.cname)
            elif answer.type == 1:
              dns_data.append(u'DNS-A request ')
              dns_data.append(answer.name)
              dns_data.append(u' response: ')
              dns_data.append(socket.inet_ntoa(answer.rdata))
            elif answer.type == 12:
              dns_data.append(u'DNS-PTR request ')
              dns_data.append(answer.name)
              dns_data.append(u' response: ')
              dns_data.append(answer.ptrname)
      elif not dns.qr:
        dns_data.append(u'DNS Query for ')
        dns_data.append(dns.qd[0].name)
    else:
      dns_data.append(u'DNS error code ')
      dns_data.append(str(dns.rcode))

  except dpkt.UnpackError as exception:
    dns_data.append(u'DNS Unpack Error: {0:s}. First 20 of data {1:s}'.format(
        exception, repr(dns_packet_data[:20])))
  except IndexError as exception:
    dns_data.append(u'DNS Index Error: {0:s}'.format(exception))

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
    netbios_data.append(u'NETBIOS qd:')
    netbios_data.append(repr(dpkt.netbios.decode_name(query.name)))
  for answer in netbios_packet.an:
    netbios_data.append(u'NETBIOS an:')
    netbios_data.append(repr(dpkt.netbios.decode_name(answer.name)))
  for name in netbios_packet.ns:
    netbios_data.append(u'NETBIOS ns:')
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
    res.append(u'FIN')
  if flag & dpkt.tcp.TH_SYN:
    res.append(u'SYN')
  if flag & dpkt.tcp.TH_RST:
    res.append(u'RST')
  if flag & dpkt.tcp.TH_PUSH:
    res.append(u'PUSH')
  if flag & dpkt.tcp.TH_ACK:
    res.append(u'ACK')
  if flag & dpkt.tcp.TH_URG:
    res.append(u'URG')
  if flag & dpkt.tcp.TH_ECE:
    res.append(u'ECN')
  if flag & dpkt.tcp.TH_CWR:
    res.append(u'CWR')

  return u'|'.join(res)


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
  icmp_data.append(u'ICMP')

  # TODO: Make the below code more readable.
  # Possible to use lookup dict? Or method
  # calls?
  if icmp_type is dpkt.icmp.ICMP_CODE_NONE:
    icmp_data.append(u'ICMP without codes')
  elif icmp_type is dpkt.icmp.ICMP_ECHOREPLY:
    icmp_data.append(u'echo reply')
  elif icmp_type is dpkt.icmp.ICMP_UNREACH:
    icmp_data.append(u'ICMP dest unreachable')
    if icmp_code is dpkt.icmp.ICMP_UNREACH_NET:
      icmp_data.append(u': bad net')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_HOST:
      icmp_data.append(u': host unreachable')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_PROTO:
      icmp_data.append(u': bad protocol')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_PORT:
      icmp_data.append(u': port unreachable')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_NEEDFRAG:
      icmp_data.append(u': IP_DF caused drop')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_SRCFAIL:
      icmp_data.append(u': src route failed')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_NET_UNKNOWN:
      icmp_data.append(u': unknown net')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_HOST_UNKNOWN:
      icmp_data.append(u': unknown host')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_ISOLATED:
      icmp_data.append(u': src host isolated')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_NET_PROHIB:
      icmp_data.append(u': for crypto devs')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_HOST_PROHIB:
      icmp_data.append(u': for cypto devs')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_TOSNET:
      icmp_data.append(u': bad tos for net')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_TOSHOST:
      icmp_data.append(u': bad tos for host')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_FILTER_PROHIB:
      icmp_data.append(u': prohibited access')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_HOST_PRECEDENCE:
      icmp_data.append(u': precedence error')
    elif icmp_code is dpkt.icmp.ICMP_UNREACH_PRECEDENCE_CUTOFF:
      icmp_data.append(u': precedence cutoff')
  elif icmp_type is dpkt.icmp.ICMP_SRCQUENCH:
    icmp_data.append(u'ICMP source quench')
  elif icmp_type is dpkt.icmp.ICMP_REDIRECT:
    icmp_data.append(u'ICMP Redirect')
    if icmp_code is dpkt.icmp.ICMP_REDIRECT_NET:
      icmp_data.append(u' for network')
    elif icmp_code is dpkt.icmp.ICMP_REDIRECT_HOST:
      icmp_data.append(u' for host')
    elif icmp_code is dpkt.icmp.ICMP_REDIRECT_TOSNET:
      icmp_data.append(u' for tos and net')
    elif icmp_code is dpkt.icmp.ICMP_REDIRECT_TOSHOST:
      icmp_data.append(u' for tos and host')
  elif icmp_type is dpkt.icmp.ICMP_ALTHOSTADDR:
    icmp_data.append(u'ICMP alternate host address')
  elif icmp_type is dpkt.icmp.ICMP_ECHO:
    icmp_data.append(u'ICMP echo')
  elif icmp_type is dpkt.icmp.ICMP_RTRADVERT:
    icmp_data.append(u'ICMP Route advertisement')
    if icmp_code is dpkt.icmp.ICMP_RTRADVERT_NORMAL:
      icmp_data.append(u': normal')
    elif icmp_code is dpkt.icmp.ICMP_RTRADVERT_NOROUTE_COMMON:
      icmp_data.append(u': selective routing')
  elif icmp_type is dpkt.icmp.ICMP_RTRSOLICIT:
    icmp_data.append(u'ICMP Router solicitation')
  elif icmp_type is dpkt.icmp.ICMP_TIMEXCEED:
    icmp_data.append(u'ICMP time exceeded, code:')
    if icmp_code is dpkt.icmp.ICMP_TIMEXCEED_INTRANS:
      icmp_data.append(u' ttl==0 in transit')
    elif icmp_code is dpkt.icmp.ICMP_TIMEXCEED_REASS:
      icmp_data.append(u'ttl==0 in reass')
  elif icmp_type is dpkt.icmp.ICMP_PARAMPROB:
    icmp_data.append(u'ICMP ip header bad')
    if icmp_code is dpkt.icmp.ICMP_PARAMPROB_ERRATPTR:
      icmp_data.append(u':req. opt. absent')
    elif icmp_code is dpkt.icmp.ICMP_PARAMPROB_OPTABSENT:
      icmp_data.append(u': req. opt. absent')
    elif icmp_code is dpkt.icmp.ICMP_PARAMPROB_LENGTH:
      icmp_data.append(u': length')
  elif icmp_type is dpkt.icmp.ICMP_TSTAMP:
    icmp_data.append(u'ICMP timestamp request')
  elif icmp_type is dpkt.icmp.ICMP_TSTAMPREPLY:
    icmp_data.append(u'ICMP timestamp reply')
  elif icmp_type is dpkt.icmp.ICMP_INFO:
    icmp_data.append(u'ICMP information request')
  elif icmp_type is dpkt.icmp.ICMP_INFOREPLY:
    icmp_data.append(u'ICMP information reply')
  elif icmp_type is dpkt.icmp.ICMP_MASK:
    icmp_data.append(u'ICMP address mask request')
  elif icmp_type is dpkt.icmp.ICMP_MASKREPLY:
    icmp_data.append(u'ICMP address mask reply')
  elif icmp_type is dpkt.icmp.ICMP_TRACEROUTE:
    icmp_data.append(u'ICMP traceroute')
  elif icmp_type is dpkt.icmp.ICMP_DATACONVERR:
    icmp_data.append(u'ICMP data conversion error')
  elif icmp_type is dpkt.icmp.ICMP_MOBILE_REDIRECT:
    icmp_data.append(u'ICMP mobile host redirect')
  elif icmp_type is dpkt.icmp.ICMP_IP6_WHEREAREYOU:
    icmp_data.append(u'ICMP IPv6 where-are-you')
  elif icmp_type is dpkt.icmp.ICMP_IP6_IAMHERE:
    icmp_data.append(u'ICMP IPv6 i-am-here')
  elif icmp_type is dpkt.icmp.ICMP_MOBILE_REG:
    icmp_data.append(u'ICMP mobile registration req')
  elif icmp_type is dpkt.icmp.ICMP_MOBILE_REGREPLY:
    icmp_data.append(u'ICMP mobile registration reply')
  elif icmp_type is dpkt.icmp.ICMP_DNS:
    icmp_data.append(u'ICMP domain name request')
  elif icmp_type is dpkt.icmp.ICMP_DNSREPLY:
    icmp_data.append(u'ICMP domain name reply')
  elif icmp_type is dpkt.icmp.ICMP_PHOTURIS:
    icmp_data.append(u'ICMP Photuris')
    if icmp_code is dpkt.icmp.ICMP_PHOTURIS_UNKNOWN_INDEX:
      icmp_data.append(u': unknown sec index')
    elif icmp_code is dpkt.icmp.ICMP_PHOTURIS_AUTH_FAILED:
      icmp_data.append(u': auth failed')
    elif icmp_code is dpkt.icmp.ICMP_PHOTURIS_DECOMPRESS_FAILED:
      icmp_data.append(u': decompress failed')
    elif icmp_code is dpkt.icmp.ICMP_PHOTURIS_DECRYPT_FAILED:
      icmp_data.append(u': decrypt failed')
    elif icmp_code is dpkt.icmp.ICMP_PHOTURIS_NEED_AUTHN:
      icmp_data.append(u': no authentication')
    elif icmp_code is dpkt.icmp.ICMP_PHOTURIS_NEED_AUTHZ:
      icmp_data.append(u': no authorization')
  elif icmp_type is dpkt.icmp.ICMP_TYPE_MAX:
    icmp_data.append(u'ICMP Type Max')

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
    super(Stream, self).__init__()
    self.all_data = [prot_data]
    self.dest_ip = dest_ip
    self.packet_id = [packet[1]]
    self.protocol = prot
    self.protocol_data = u''
    self.size = packet[3]
    self.source_ip = source_ip
    self.start_time = packet[0]
    self.stream_data = b''
    self.timestamps = [packet[0]]

    if prot in (u'TCP', u'UDP'):
      self.dest_port = prot_data.dport
      self.source_port = prot_data.sport
    else:
      self.dest_port = u''
      self.source_port = u''

  def AddPacket(self, packet, prot_data):
    """Add another packet to an existing stream.

    Args:
      packet: Packet data.
      prot_data: Protocol level data for ARP, UDP, RCP, ICMP.
          other types of ether packets, this is just the ether.data
    """
    self.packet_id.append(packet[1])
    self.timestamps.append(packet[0])
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
    if self.stream_data[:4] == b'HTTP':
      try:
        http = dpkt.http.Response(self.stream_data)
        packet_details.append(u'HTTP Response: status: ')
        packet_details.append(http.status)
        packet_details.append(u' reason: ')
        packet_details.append(http.reason)
        packet_details.append(u' version: ')
        packet_details.append(http.version)
        return u'HTTP Response', u' '.join(packet_details)

      except dpkt.UnpackError as exception:
        packet_details = (
            u'HTTP Response Unpack Error: {0:s}. '
            u'First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return u'HTTP Response', packet_details

      except IndexError as exception:
        packet_details = (
            u'HTTP Response Index Error: {0:s}. First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return u'HTTP Response', packet_details

      except ValueError as exception:
        packet_details = (
            u'HTTP Response parsing error: {0:s}. '
            u'First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return u'HTTP Response', packet_details

    elif self.stream_data[:3] == b'GET' or self.stream_data[:4] == b'POST':
      try:
        http = dpkt.http.Request(self.stream_data)
        packet_details.append(u'HTTP Request: method: ')
        packet_details.append(http.method)
        packet_details.append(' uri: ')
        packet_details.append(http.uri)
        packet_details.append(' version: ')
        packet_details.append(http.version)
        packet_details.append(' headers: ')
        packet_details.append(repr(http.headers))
        return u'HTTP Request', u' '.join(packet_details)

      except dpkt.UnpackError as exception:
        packet_details = (
            u'HTTP Request unpack error: {0:s}. First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return u'HTTP Request', packet_details

      except ValueError as exception:
        packet_details = (
            u'HTTP Request parsing error: {0:s}. '
            u'First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return u'HTTP Request', packet_details

    elif self.protocol == u'UDP' and (
        self.source_port == 53 or self.dest_port == 53):
      # DNS request/replies.
      # Check to see if the lengths are valid.
      for packet in self.all_data:
        if not packet.ulen == len(packet):
          packet_details.append(u'Truncated DNS packets - unable to parse: ')
          packet_details.append(repr(self.stream_data[15:40]))
          return u'DNS', u' '.join(packet_details)

      return u'DNS', ParseDNS(self.stream_data)

    elif self.protocol == u'UDP' and (
        self.source_port == 137 or self.dest_port == 137):
      return u'NetBIOS', ParseNetBios(dpkt.netbios.NS(self.stream_data))

    elif self.protocol == u'ICMP':
      # ICMP packets all end up as 1 stream, so they need to be
      #  processed 1 by 1.
      return u'ICMP', ICMPTypes(self.all_data[0])

    elif b'\x03\x01' in self.stream_data[1:3]:
      # Some form of ssl3 data.
      try:
        ssl = dpkt.ssl.SSL2(self.stream_data)
        packet_details.append(u'SSL data. Length: ')
        packet_details.append(str(ssl.len))
        return u'SSL', u' '.join(packet_details)
      except dpkt.UnpackError as exception:
        packet_details = (
            u'SSL unpack error: {0:s}. First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return u'SSL', packet_details

    elif b'\x03\x00' in self.stream_data[1:3]:
       # Some form of ssl3 data.
      try:
        ssl = dpkt.ssl.SSL2(self.stream_data)
        packet_details.append(u'SSL data. Length: ')
        packet_details.append(str(ssl.len))
        return u'SSL', u' '.join(packet_details)

      except dpkt.UnpackError as exception:
        packet_details = (
            u'SSL unpack error: {0:s}. First 20 of data {1:s}').format(
                exception, repr(self.stream_data[:20]))
        return u'SSL', packet_details

    return u'other', self.protocol_data

  def Clean(self):
    """Clean up stream data."""
    clean_data = []
    for packet in self.all_data:
      try:
        clean_data.append(packet.data)
      except AttributeError:
        pass

      self.stream_data = b''.join(clean_data)


class PcapEventData(events.EventData):
  """PCAP event data.

  Attributes:
    dest_ip (str): destination IP address.
    dest_port (str): destination TCP or UDP port number.
    first_packet_id (int): identifier of the first PCAP packet in a stream.
    last_packet_id (int): identifier of the last PCAP packet in a stream.
    packet_count (int): number of PCAP packets in a stream.
    protocol (str): most specific protocol.
    protocol_data (bytes): protocol data ???
    size (int): size of a stream in bytes.
    source_ip (str): source IP address.
    source_port (str): source TCP or UDP port number.
    stream_data (str): human readable representation of the first 50 bytes
        of the stream data.
    stream_type (str): stream type.
  """

  DATA_TYPE = u'metadata:pcap'

  def __init__(self):
    """Initializes event data."""
    super(PcapEventData, self).__init__(data_type=self.DATA_TYPE)
    self.dest_ip = None
    self.dest_port = None
    self.first_packet_id = None
    self.last_packet_id = None
    self.packet_count = None
    self.protocol = None
    self.protocol_data = None
    self.size = None
    self.source_ip = None
    self.source_port = None
    self.stream_data = None
    self.stream_type = None


class PcapParser(interface.FileObjectParser):
  """Parses PCAP files."""

  NAME = u'pcap'
  DESCRIPTION = u'Parser for PCAP files.'

  def _ParseIPPacket(
      self, connections, trunc_list, packet_number, timestamp,
      packet_data_size, ip_packet):
    """Parses an IP packet.

    Args:
      connections: A dictionary object to track the IP connections.
      trunc_list: A list of packets that truncated strangely and could
                  not be turned into a stream.
      packet_number: The PCAP packet number, where 1 is the first packet.
      timestamp: The PCAP packet timestamp.
      packet_data_size: The packet data size.
      ip_packet: The IP packet (instance of dpkt.ip.IP).
    """
    packet_values = [timestamp, packet_number, ip_packet, packet_data_size]

    source_ip_address = socket.inet_ntoa(ip_packet.src)
    destination_ip_address = socket.inet_ntoa(ip_packet.dst)

    if ip_packet.p == dpkt.ip.IP_PROTO_TCP:
      # Later versions of dpkt seem to return a string instead of a TCP object.
      if isinstance(ip_packet.data, str):
        try:
          tcp = dpkt.tcp.TCP(ip_packet.data)
        except (dpkt.NeedData, dpkt.UnpackError):
          trunc_list.append(packet_values)
          return

      else:
        tcp = ip_packet.data

      stream_key = u'tcp: {0:s}:{1:d} > {2:s}:{3:d}'.format(
          source_ip_address, tcp.sport, destination_ip_address, tcp.dport)

      if stream_key in connections:
        connections[stream_key].AddPacket(packet_values, tcp)
      else:
        connections[stream_key] = Stream(
            packet_values, tcp, source_ip_address, destination_ip_address,
            u'TCP')

    elif ip_packet.p == dpkt.ip.IP_PROTO_UDP:
      # Later versions of dpkt seem to return a string instead of an UDP object.
      if isinstance(ip_packet.data, str):
        try:
          udp = dpkt.udp.UDP(ip_packet.data)
        except (dpkt.NeedData, dpkt.UnpackError):
          trunc_list.append(packet_values)
          return

      else:
        udp = ip_packet.data

      stream_key = u'udp: {0:s}:{1:d} > {2:s}:{3:d}'.format(
          source_ip_address, udp.sport, destination_ip_address, udp.dport)

      if stream_key in connections:
        connections[stream_key].AddPacket(packet_values, udp)
      else:
        connections[stream_key] = Stream(
            packet_values, udp, source_ip_address, destination_ip_address,
            u'UDP')

    elif ip_packet.p == dpkt.ip.IP_PROTO_ICMP:
      # Later versions of dpkt seem to return a string instead of
      # an ICMP object.
      if isinstance(ip_packet.data, str):
        icmp = dpkt.icmp.ICMP(ip_packet.data)
      else:
        icmp = ip_packet.data

      stream_key = u'icmp: {0:d} {1:s} > {2:s}'.format(
          timestamp, source_ip_address, destination_ip_address)

      if stream_key in connections:
        connections[stream_key].AddPacket(packet_values, icmp)
      else:
        connections[stream_key] = Stream(
            packet_values, icmp, source_ip_address, destination_ip_address,
            u'ICMP')

  def _ParseOtherPacket(self, packet_values):
    """Parses a non-IP packet.

    Args:
      packet_values: list of packet values

    Returns:
      A stream object (instance of Stream) or None if the packet data
      is not supported.
    """
    ether = packet_values[2]
    stream_object = None

    if ether.type == dpkt.ethernet.ETH_TYPE_ARP:
      arp = ether.data
      arp_data = []
      stream_object = Stream(
          packet_values, arp, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'ARP')

      if arp.op == dpkt.arp.ARP_OP_REQUEST:
        arp_data.append(u'arp request: target IP = ')
        arp_data.append(socket.inet_ntoa(arp.tpa))
        stream_object.protocol_data = u' '.join(arp_data)

      elif arp.op == dpkt.arp.ARP_OP_REPLY:
        arp_data.append(u'arp reply: target IP = ')
        arp_data.append(socket.inet_ntoa(arp.tpa))
        arp_data.append(u' target MAC = ')
        arp_data.append(binascii.hexlify(arp.tha))
        stream_object.protocol_data = u' '.join(arp_data)

      elif arp.op == dpkt.arp.ARP_OP_REVREQUEST:
        arp_data.append(u'arp protocol address request: target IP = ')
        arp_data.append(socket.inet_ntoa(arp.tpa))
        stream_object.protocol_data = u' '.join(arp_data)

      elif arp.op == dpkt.arp.ARP_OP_REVREPLY:
        arp_data.append(u'arp protocol address reply: target IP = ')
        arp_data.append(socket.inet_ntoa(arp.tpa))
        arp_data.append(u' target MAC = ')
        arp_data.append(binascii.hexlify(arp.tha))
        stream_object.protocol_data = u' '.join(arp_data)

    elif ether.type == dpkt.ethernet.ETH_TYPE_IP6:
      ip6 = ether.data
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ip6.src),
          binascii.hexlify(ip6.dst), u'IPv6')
      stream_object.protocol_data = u'IPv6'

    elif ether.type == dpkt.ethernet.ETH_TYPE_CDP:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'CDP')
      stream_object.protocol_data = u'CDP'

    elif ether.type == dpkt.ethernet.ETH_TYPE_DTP:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'DTP')
      stream_object.protocol_data = u'DTP'

    elif ether.type == dpkt.ethernet.ETH_TYPE_REVARP:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'RARP')
      stream_object.protocol_data = u'Reverse ARP'

    elif ether.type == dpkt.ethernet.ETH_TYPE_8021Q:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'8021Q packet')
      stream_object.protocol_data = u'8021Q packet'

    elif ether.type == dpkt.ethernet.ETH_TYPE_IPX:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'IPX')
      stream_object.protocol_data = u'IPX'

    elif ether.type == dpkt.ethernet.ETH_TYPE_PPP:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'PPP')
      stream_object.protocol_data = u'PPP'

    elif ether.type == dpkt.ethernet.ETH_TYPE_MPLS:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'MPLS')
      stream_object.protocol_data = u'MPLS'

    elif ether.type == dpkt.ethernet.ETH_TYPE_MPLS_MCAST:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'MPLS')
      stream_object.protocol_data = u'MPLS MCAST'

    elif ether.type == dpkt.ethernet.ETH_TYPE_PPPoE_DISC:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'PPOE')
      stream_object.protocol_data = u'PPoE Disc packet'

    elif ether.type == dpkt.ethernet.ETH_TYPE_PPPoE:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'PPPoE')
      stream_object.protocol_data = u'PPPoE'

    elif ether.type == 0x2452:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), u'802.11')
      stream_object.protocol_data = u'802.11'

    return stream_object

  def _ParseOtherStreams(self, other_list, trunc_list):
    """Process PCAP packets that are not IP packets.

    For all packets that were not IP packets, create stream containers
    depending on the type of packet.

    Args:
      other_list: List of non-ip packets.
      trunc_list: A list of packets that truncated strangely and could
                  not be turned into a stream.

    Returns:
      A list of stream objects (instances of Stream).
    """
    other_streams = []

    for packet_values in other_list:
      stream_object = self._ParseOtherPacket(packet_values)
      if stream_object:
        other_streams.append(stream_object)

    for packet_values in trunc_list:
      ip_packet = packet_values[2]

      source_ip_address = socket.inet_ntoa(ip_packet.src)
      destination_ip_address = socket.inet_ntoa(ip_packet.dst)
      stream_object = Stream(
          packet_values, ip_packet.data, source_ip_address,
          destination_ip_address, u'BAD')
      stream_object.protocol_data = u'Bad truncated IP packet'
      other_streams.append(stream_object)

    return other_streams

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a PCAP file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    data = file_object.read(dpkt.pcap.FileHdr.__hdr_len__)

    try:
      file_header = dpkt.pcap.FileHdr(data)
      packet_header_class = dpkt.pcap.PktHdr

    except (dpkt.NeedData, dpkt.UnpackError) as exception:
      raise errors.UnableToParseFile(
          u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, parser_mediator.GetDisplayName(), exception))

    if file_header.magic == dpkt.pcap.PMUDPCT_MAGIC:
      try:
        file_header = dpkt.pcap.LEFileHdr(data)
        packet_header_class = dpkt.pcap.LEPktHdr

      except (dpkt.NeedData, dpkt.UnpackError) as exception:
        raise errors.UnableToParseFile(
            u'[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
                self.NAME, parser_mediator.GetDisplayName(), exception))

    elif file_header.magic != dpkt.pcap.TCPDUMP_MAGIC:
      raise errors.UnableToParseFile(u'Unsupported file signature')

    packet_number = 1
    connections = {}
    other_list = []
    trunc_list = []

    data = file_object.read(dpkt.pcap.PktHdr.__hdr_len__)
    while data:
      packet_header = packet_header_class(data)
      timestamp = (packet_header.tv_sec * 1000000) + packet_header.tv_usec
      packet_data = file_object.read(packet_header.caplen)

      ethernet_frame = dpkt.ethernet.Ethernet(packet_data)

      if ethernet_frame.type == dpkt.ethernet.ETH_TYPE_IP:
        self._ParseIPPacket(
            connections, trunc_list, packet_number, timestamp,
            len(ethernet_frame), ethernet_frame.data)

      else:
        packet_values = [
            timestamp, packet_number, ethernet_frame, len(ethernet_frame)]
        other_list.append(packet_values)

      packet_number += 1
      data = file_object.read(dpkt.pcap.PktHdr.__hdr_len__)

    other_streams = self._ParseOtherStreams(other_list, trunc_list)

    for stream_object in sorted(
        connections.values(), key=operator.attrgetter(u'start_time')):

      if not stream_object.protocol == u'ICMP':
        stream_object.Clean()

      event_data = PcapEventData()
      event_data.dest_ip = stream_object.dest_ip
      event_data.dest_port = stream_object.dest_port
      event_data.first_packet_id = min(stream_object.packet_id)
      event_data.last_packet_id = max(stream_object.packet_id)
      event_data.packet_count = len(stream_object.packet_id)
      event_data.protocol = stream_object.protocol
      event_data.size = stream_object.size
      event_data.source_ip = stream_object.source_ip
      event_data.source_port = stream_object.source_port
      event_data.stream_data = repr(stream_object.stream_data[:50])
      event_data.stream_type, event_data.protocol_data = (
          stream_object.SpecialTypes())

      date_time = dfdatetime_posix_time.PosixTime(
          timestamp=min(stream_object.timestamps))
      event = time_events.DateTimeValuesEvent(
          date_time, eventdata.EventTimestamp.START_TIME)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      date_time = dfdatetime_posix_time.PosixTime(
          timestamp=max(stream_object.timestamps))
      event = time_events.DateTimeValuesEvent(
          date_time, eventdata.EventTimestamp.END_TIME)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for stream_object in other_streams:
      event_data = PcapEventData()
      event_data.dest_ip = stream_object.dest_ip
      event_data.dest_port = stream_object.dest_port
      event_data.first_packet_id = min(stream_object.packet_id)
      event_data.last_packet_id = max(stream_object.packet_id)
      event_data.packet_count = len(stream_object.packet_id)
      event_data.protocol = stream_object.protocol
      event_data.size = stream_object.size
      event_data.source_ip = stream_object.source_ip
      event_data.source_port = stream_object.source_port
      event_data.stream_data = repr(stream_object.stream_data[:50])
      event_data.stream_type, event_data.protocol_data = (
          stream_object.SpecialTypes())

      date_time = dfdatetime_posix_time.PosixTime(
          timestamp=min(stream_object.timestamps))
      event = time_events.DateTimeValuesEvent(
          date_time, eventdata.EventTimestamp.START_TIME)
      parser_mediator.ProduceEventWithEventData(event, event_data)

      date_time = dfdatetime_posix_time.PosixTime(
          timestamp=max(stream_object.timestamps))
      event = time_events.DateTimeValuesEvent(
          date_time, eventdata.EventTimestamp.END_TIME)
      parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(PcapParser)
