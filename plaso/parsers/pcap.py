# -*- coding: utf-8 -*-
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
    self.timestamps = [packet[0]]
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

  def __init__(self, timestamp, usage, stream_object):
    """Initializes the event.

    Args:
      timestamp: The POSIX value of the timestamp.
      usage: A usage description value.
      stream_object: The stream object (instance of Stream).
    """
    super(PcapEvent, self).__init__(timestamp, usage)

    self.source_ip = stream_object.source_ip
    self.dest_ip = stream_object.dest_ip
    self.source_port = stream_object.source_port
    self.dest_port = stream_object.dest_port
    self.protocol = stream_object.protocol
    self.size = stream_object.size
    self.stream_type, self.protocol_data = stream_object.SpecialTypes()
    self.first_packet_id = min(stream_object.packet_id)
    self.last_packet_id = max(stream_object.packet_id)
    self.packet_count = len(stream_object.packet_id)
    self.stream_data = repr(stream_object.stream_data[:50])


class PcapParser(interface.SingleFileBaseParser):
  """Parses PCAP files."""

  NAME = 'pcap'
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

      stream_key = 'tcp: {0:s}:{1:d} > {2:s}:{3:d}'.format(
          source_ip_address, tcp.sport, destination_ip_address, tcp.dport)

      if stream_key in connections:
        connections[stream_key].AddPacket(packet_values, tcp)
      else:
        connections[stream_key] = Stream(
            packet_values, tcp, source_ip_address, destination_ip_address,
            'TCP')

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

      stream_key = 'udp: {0:s}:{1:d} > {2:s}:{3:d}'.format(
          source_ip_address, udp.sport, destination_ip_address, udp.dport)

      if stream_key in connections:
        connections[stream_key].AddPacket(packet_values, udp)
      else:
        connections[stream_key] = Stream(
            packet_values, udp, source_ip_address, destination_ip_address,
            'UDP')

    elif ip_packet.p == dpkt.ip.IP_PROTO_ICMP:
      # Later versions of dpkt seem to return a string instead of
      # an ICMP object.
      if isinstance(ip_packet.data, str):
        icmp = dpkt.icmp.ICMP(ip_packet.data)
      else:
        icmp = ip_packet.data

      stream_key = 'icmp: {0:d} {1:s} > {2:s}'.format(
          timestamp, source_ip_address, destination_ip_address)

      if stream_key in connections:
        connections[stream_key].AddPacket(packet_values, icmp)
      else:
        connections[stream_key] = Stream(
            packet_values, icmp, source_ip_address, destination_ip_address,
            'ICMP')

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
          binascii.hexlify(ether.dst), 'ARP')

      if arp.op == dpkt.arp.ARP_OP_REQUEST:
        arp_data.append('arp request: target IP = ')
        arp_data.append(socket.inet_ntoa(arp.tpa))
        stream_object.protocol_data = u' '.join(arp_data)

      elif arp.op == dpkt.arp.ARP_OP_REPLY:
        arp_data.append('arp reply: target IP = ')
        arp_data.append(socket.inet_ntoa(arp.tpa))
        arp_data.append(' target MAC = ')
        arp_data.append(binascii.hexlify(arp.tha))
        stream_object.protocol_data = u' '.join(arp_data)

      elif arp.op == dpkt.arp.ARP_OP_REVREQUEST:
        arp_data.append('arp protocol address request: target IP = ')
        arp_data.append(socket.inet_ntoa(arp.tpa))
        stream_object.protocol_data = u' '.join(arp_data)

      elif arp.op == dpkt.arp.ARP_OP_REVREPLY:
        arp_data.append('arp protocol address reply: target IP = ')
        arp_data.append(socket.inet_ntoa(arp.tpa))
        arp_data.append(' target MAC = ')
        arp_data.append(binascii.hexlify(arp.tha))
        stream_object.protocol_data = u' '.join(arp_data)

    elif ether.type == dpkt.ethernet.ETH_TYPE_IP6:
      ip6 = ether.data
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ip6.src),
          binascii.hexlify(ip6.dst), 'IPv6')
      stream_object.protocol_data = 'IPv6'

    elif ether.type == dpkt.ethernet.ETH_TYPE_CDP:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), 'CDP')
      stream_object.protocol_data = 'CDP'

    elif ether.type == dpkt.ethernet.ETH_TYPE_DTP:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), 'DTP')
      stream_object.protocol_data = 'DTP'

    elif ether.type == dpkt.ethernet.ETH_TYPE_REVARP:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), 'RARP')
      stream_object.protocol_data = 'Reverse ARP'

    elif ether.type == dpkt.ethernet.ETH_TYPE_8021Q:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), '8021Q packet')
      stream_object.protocol_data = '8021Q packet'

    elif ether.type == dpkt.ethernet.ETH_TYPE_IPX:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), 'IPX')
      stream_object.protocol_data = 'IPX'

    elif ether.type == dpkt.ethernet.ETH_TYPE_PPP:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), 'PPP')
      stream_object.protocol_data = 'PPP'

    elif ether.type == dpkt.ethernet.ETH_TYPE_MPLS:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), 'MPLS')
      stream_object.protocol_data = 'MPLS'

    elif ether.type == dpkt.ethernet.ETH_TYPE_MPLS_MCAST:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), 'MPLS')
      stream_object.protocol_data = 'MPLS MCAST'

    elif ether.type == dpkt.ethernet.ETH_TYPE_PPPoE_DISC:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), 'PPOE')
      stream_object.protocol_data = 'PPoE Disc packet'

    elif ether.type == dpkt.ethernet.ETH_TYPE_PPPoE:
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), 'PPPoE')
      stream_object.protocol_data = 'PPPoE'

    elif str(hex(ether.type)) == '0x2452':
      stream_object = Stream(
          packet_values, ether.data, binascii.hexlify(ether.src),
          binascii.hexlify(ether.dst), '802.11')
      stream_object.protocol_data = '802.11'

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
          destination_ip_address, 'BAD')
      stream_object.protocolData = 'Bad truncated IP packet'
      other_streams.append(stream_object)

    return other_streams

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses a PCAP file-like object.

    Args:
      parser_mediator: A parser context object (instance of ParserContext).
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
      timestamp = packet_header.tv_sec + (packet_header.tv_usec / 1000000.0)
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
        connections.values(), key=operator.attrgetter('start_time')):

      if not stream_object.protocol == 'ICMP':
        stream_object.Clean()

      event_objects = [
          PcapEvent(
              min(stream_object.timestamps),
              eventdata.EventTimestamp.START_TIME, stream_object),
          PcapEvent(
              max(stream_object.timestamps),
              eventdata.EventTimestamp.END_TIME, stream_object)]

      parser_mediator.ProduceEvents(event_objects)

    for stream_object in other_streams:
      event_objects = [
          PcapEvent(
              min(stream_object.timestamps),
              eventdata.EventTimestamp.START_TIME, stream_object),
          PcapEvent(
              max(stream_object.timestamps),
              eventdata.EventTimestamp.END_TIME, stream_object)]
      parser_mediator.ProduceEvents(event_objects)


manager.ParsersManager.RegisterParser(PcapParser)
