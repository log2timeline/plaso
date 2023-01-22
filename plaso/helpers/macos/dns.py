# -*- coding: utf-8 -*-
"""MacOS DNS data helper."""

import ipaddress
import os

from plaso.lib import dtfabric_helper


class DNS(dtfabric_helper.DtFabricHelper):
  """DNS Parser.

  Also see:
    https://github.com/apple-oss-distributions/mDNSResponder
  """

  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'dns.yaml')

  # Query Response
  QR_MASK = 0x8000

  # Op Code
  OPCODE_MASK = 0x7800

  _DNS_FLAGS = {
      'AA': 0x0400,  # Authoritative Answer
      'TC': 0x0200,  # Truncated Response
      'RD': 0x0100,  # Recursion Desired
      'RA': 0x0080,  # Recursion Available
      'AD': 0x0020,  # Authentic Data
      'CD': 0x0010}  # Checking Disabled

  # Response Code
  R = 0x000F

  _QUERY_RESPONSE_FLAG = {
      0: 'Q',
      1: 'R'}

  _DNS_OPCODES = {
      0: 'Query',
      1: 'IQuery',
      2: 'Status',
      3: 'Unassigned',
      4: 'Notify',
      5: 'Update',
      6: 'DSO'}

  _DNS_RESPONSE_CODES = {
      0: 'NoError',
      1: 'FormErr',
      2: 'ServFail',
      3: 'NXDomain',
      4: 'NotImp',
      5: 'Refused',
      6: 'YXDomain',
      7: 'YXRRSet',
      8: 'NXRRSet',
      9: 'NotAuth',
      10: 'NotZone',
      11: 'DSOTypeNI'}

  _DNS_RECORD_TYPES = {
      1: 'A',
      2: 'NS',
      5: 'CNAME',
      6: 'SOA',
      12: 'PTR',
      13: 'HINFO',
      15: 'MX',
      16: 'TXT',
      17: 'RP',
      18: 'AFSDB',
      24: 'SIG',
      25: 'KEY',
      28: 'AAAA',
      29: 'LOC',
      33: 'SRV',
      35: 'NAPTR',
      36: 'KX',
      37: 'CERT',
      39: 'DNAME',
      42: 'APL',
      43: 'DS',
      44: 'SSHFP',
      45: 'IPSECKEY',
      46: 'RRSIG',
      47: 'NSEC',
      48: 'DNSKEY',
      49: 'DHCID',
      50: 'NSEC3',
      51: 'NSEC3PARAM',
      52: 'TLSA',
      53: 'SMIMEA',
      55: 'HIP',
      59: 'CDS',
      60: 'CDNSKEY',
      61: 'OPENPGPKEY',
      62: 'CSYNC',
      63: 'ZONEMD',
      64: 'SVCB',
      65: 'HTTPS',
      108: 'EUI48',
      109: 'EUI64',
      249: 'TKEY',
      250: 'TSIG',
      256: 'URI',
      257: 'CAA',
      32768: 'TA',
      32769: 'DLV'}

  _DNS_PROTOCOLS = {
      1: 'UDP',
      2: 'TCP',
      4: 'HTTPS'}

  _DNS_REASONS = {
      1: 'no-data',
      2: 'nxdomain',
      3: 'no-dns-service',
      4: 'query-suppressed',
      5: 'server error'}

  @classmethod
  def ParseFlags(cls, flags):
    """Parses the DNS reponse flags

    Args:
      flags (int): DNS flags

    Returns:
      str: formatted string.
    """
    enabled_flags = []
    for flag, value in cls._DNS_FLAGS.items():
      if flags & value != 0:
        enabled_flags.append(flag)

    enabled_flags = ', '.join(enabled_flags)

    qr_value = 'R' if flags & cls.QR_MASK else 'Q'
    opcode_value = cls._DNS_OPCODES.get(
        (flags & cls.OPCODE_MASK) >> 11, '?')
    reponse_code = cls._DNS_RESPONSE_CODES.get(flags & cls.R, '?')

    return '{0:s}/{1:s}, {2:s}, {3:s}'.format(
        qr_value, opcode_value, enabled_flags, reponse_code)

  @classmethod
  def GetRecordType(cls, record_type):
    """Retrieves the DNS record type

    Args:
      record_type (int): DNS record type code

    Returns:
      str: DNS record type
    """
    return cls._DNS_RECORD_TYPES.get(record_type, str(record_type))

  @classmethod
  def GetProtocolType(cls, protocol_type):
    """Retrieves the DNS protocol type

    Args:
      protocol_type (int): DNS protocol type code

    Returns:
      str: DNS protocol type
    """
    return cls._DNS_PROTOCOLS.get(protocol_type, str(protocol_type))

  @classmethod
  def GetReasons(cls, reason_type):
    """Retrieves the DNS reason type

    Args:
      reason_type (int): DNS reason type code

    Returns:
      str: DNS reason type
    """
    return cls._DNS_REASONS.get(
        reason_type, 'UNKNOWN: {0:d}'.format(reason_type))

  def ParseDNSHeader(self, data):
    """Parses given data as a DNS Header chunk

    Args:
      data (bytes): Raw data

    Returns:
      str: The formatted DNS ID, Flags and Counts

    Raises:
      ParseError: if the data cannot be parsed.
    """
    dnsheader = self._ReadStructureFromByteStream(
        data, 0, self._GetDataTypeMap('dns_header'))
    flag_string = self.ParseFlags(dnsheader.flags)
    return ('id: {0:s} ({1:d}), flags: 0x{2:04x} ({3:s}), counts: '
            '{4:d}/{5:d}/{6:d}/{7:d}').format(
        hex(dnsheader.id), dnsheader.id, dnsheader.flags, flag_string,
        dnsheader.questions, dnsheader.answers,
        dnsheader.authority_records, dnsheader.additional_records)

  def ParseDNSSVCB(self, data):
    """Parses given data as a DNS SVCB chunk

    Args:
      data (bytes): Raw data

    Returns:
      str: The formatted SCVB string

    Raises:
      ParseError: if the data cannot be parsed.
    """
    dns_svcb = self._ReadStructureFromByteStream(
        data, 0, self._GetDataTypeMap('dns_svcb'))
    if dns_svcb.url:
      return dns_svcb.url

    rets = []
    offset = 0

    if dns_svcb.apln_data:
      alpns = []
      while offset < dns_svcb.alpn_total_size:
        alpn_data = self._ReadStructureFromByteStream(
            dns_svcb.apln_data[offset:],
            offset,
            self._GetDataTypeMap('dns_svcb_alpn'),
        )
        offset += 1 + alpn_data.entry_size
        alpns.append(alpn_data.data)

    if alpns:
      rets.append('alpn="{0:s}"'.format(",".join(alpns)))

    offset += 7
    ipv4s = []
    ipv6s = []
    while offset < len(data):
      ip_hint = self._ReadStructureFromByteStream(
          data[offset:], offset, self._GetDataTypeMap('dns_svcb_ip_hints'))
      offset += 4

      if ip_hint.ipv4s:
        for ip_addr in ip_hint.ipv4s:
          ipv4s.append(self._FormatPackedIPv4Address(ip_addr.segments))
          offset += 4
      if ip_hint.ipv6s:
        for ip_addr in ip_hint.ipv6s:
          ipv6s.append(ipaddress.ip_address(ip_addr.ip).compressed)
          offset += 16

    if ipv4s:
      rets.append('ipv4hint="{0:s}"'.format(','.join(ipv4s)))
    if ipv6s:
      rets.append('ipv6hint="{0:s}"'.format(','.join(ipv6s)))
    return " ".join(rets)
