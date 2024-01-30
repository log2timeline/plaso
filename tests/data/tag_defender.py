#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tag_defender.txt tagging file."""

import unittest

from plaso.parsers import defender_device

from tests.data import test_lib


class DefenderTaggingFileTest(test_lib.TaggingFileTestCase):
  """Tests the tag_defender.txt tagging file.

  In the tests below the EventData classes are used to catch failing tagging
  rules in case event data types are renamed.
  """

  _TAG_FILE = 'tag_defender.txt'

  def testApplicationExecution(self):
    """Tests the application_execution tagging rule."""
    # Test: data_type is 'm365:defenderah:processcreated'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:processcreated']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'm365:defenderah:imageloaded'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:imageloaded']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'm365:defenderah:openprocess'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:openprocess']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'm365:defenderah:processcreatedusingwmiquery'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:processcreatedusingwmiquery']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['application_execution'])

  def testFileCreated(self):
    """Tests the file_created tagging rule."""
    # Test: data_type is 'm365:defenderah:filecreated'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:filecreated']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['file_created'])

  def testFileDeleted(self):
    """Tests the file_deleted tagging rule."""
    # Test: data_type is 'm365:defenderah:filedeleted'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:filedeleted']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['file_deleted'])

  def testFileModified(self):
    """Tests the file_modified tagging rule."""
    # Test: data_type is 'm365:defenderah:filemodified'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:filemodified']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['file_modified'])

  def testFileRenamed(self):
    """Tests the file_renamed tagging rule."""
    # Test: data_type is 'm365:defenderah:filerenamed'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:filerenamed']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['file_renamed'])

  def testLoginFailed(self):
    """Tests the login_failed tagging rule."""
    # Test: data_type is 'm365:defenderah:logonfailed'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:logonfailed']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['login_failed'])

  def testLoginAttempt(self):
    """Tests the login_attempt tagging rule."""
    # Test: data_type is 'm365:defenderah:logonattempted'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:logonattempted']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['login_attempt'])

  def testLoginSuccess(self):
    """Tests the login_success tagging rule."""
    # Test: data_type is 'm365:defenderah:logonsuccess'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:logonsuccess']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['login_success'])

  def testRegistryModified(self):
    """Tests the registry_modified tagging rule."""
    # Test: data_type is 'm365:defenderah:registrykeycreated'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:registrykeycreated']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'm365:defenderah:registrykeydeleted'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:registrykeydeleted']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'm365:defenderah:registrykeyrenamed'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:registrykeyrenamed']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'm365:defenderah:registryvaluedeleted'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:registryvaluedeleted']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'm365:defenderah:registryvalueset'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:registryvalueset']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['registry_modified'])

  def testConnectionFailed(self):
    """Tests the connection_failed tagging rule."""
    # Test: data_type is 'm365:defenderah:connectionfailed'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:connectionfailed']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['connection_failed'])

  def testConnectionSuccess(self):
    """Tests the connection_success tagging rule."""
    # Test: data_type is 'm365:defenderah:connectionsuccess'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:connectionsuccess']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['connection_success'])

  def testDnsConnection(self):
    """Tests the dns_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:dnsconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:dnsconnectioninspected']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['dns_connection'])

  def testFtpConnection(self):
    """Tests the ftp_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:ftpconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:ftpconnectioninspected']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['ftp_connection'])

  def testHttpConnection(self):
    """Tests the http_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:httpconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:httpconnectioninspected']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['http_connection'])

  def testIcmpConnection(self):
    """Tests the icmp_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:icmpconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:icmpconnectioninspected']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['icmp_connection'])

  def testInboundConnection(self):
    """Tests the inbound_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:inboundconnectionaccepted'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:inboundconnectionaccepted']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['inbound_connection'])

  def testOpenPort(self):
    """Tests the open_port tagging rule."""
    # Test: data_type is 'm365:defenderah:listeningconnectioncreated'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:listeningconnectioncreated']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['open_port'])

  def testSmtpConnection(self):
    """Tests the smtp_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:smtpconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:smtpconnectioninspected']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['smtp_connection'])

  def testSshConnection(self):
    """Tests the ssh_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:sshconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:sshconnectioninspected']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['ssh_connection'])

  def testSslConnection(self):
    """Tests the ssl_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:sslconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:sslconnectioninspected']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['ssl_connection'])

  def testThreatDetection(self):
    """Tests the threat_detection tagging rule."""
    # Test: data_type is 'm365:defenderah:antivirusdetection'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:antivirusdetection']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'm365:defenderah:antiviruserror'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:antiviruserror']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'm365:defenderah:antivirusmalwareactionfailed'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:antivirusmalwareactionfailed']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'm365:defenderah:antivirusmalwareblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:antivirusmalwareblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'm365:defenderah:antivirusreport'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:antivirusreport']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['threat_detection'])

  def testAsrBlock(self):
    """Tests the asr_block tagging rule."""
    # Test: data_type is 'm365:defenderah:asradobereaderchildprocessblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asradobereaderchildprocessblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrexecutableemailcontentblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrexecutableemailcontentblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrexecutableofficecontentblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrexecutableofficecontentblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrlsasscredentialtheftblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrlsasscredentialtheftblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrobfuscatedscriptblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrobfuscatedscriptblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrofficechildprocessblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrofficechildprocessblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrofficecommappchildprocessblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrofficecommappchildprocessblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrofficemacrowin32apicallsblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrofficemacrowin32apicallsblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrofficeprocessinjectionblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrofficeprocessinjectionblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrpersistencethroughwmiblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrpersistencethroughwmiblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrpsexecwmichildprocessblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrpsexecwmichildprocessblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrransomwareblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrransomwareblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrscriptexecutabledownloadblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrscriptexecutabledownloadblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asruntrustedexecutableblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asruntrustedexecutableblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asruntrustedusbprocessblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asruntrustedusbprocessblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrvulnerablesigneddriverblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:asrvulnerablesigneddriverblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['asr_block'])

  def testFirewallBlock(self):
    """Tests the firewall_block tagging rule."""
    # Test: data_type is 'm365:defenderah:firewallinboundconnectionblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:firewallinboundconnectionblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['firewall_block'])

    # Test: data_type is 'm365:defenderah:firewallinboundconnectiontoappblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:firewallinboundconnectiontoappblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['firewall_block'])

    # Test: data_type is 'm365:defenderah:firewalloutboundconnectionblocked'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:firewalloutboundconnectionblocked']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['firewall_block'])

  def testFirewallChange(self):
    """Tests the firewall_change tagging rule."""
    # Test: data_type is 'm365:defenderah:firewallservicestopped'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:firewallservicestopped']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['firewall_change'])

  def testRdpConnection(self):
    """Tests the rdp_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:remotedesktopconnection'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:remotedesktopconnection']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['rdp_connection'])

  def testTaskSchedule(self):
    """Tests the task_schedule tagging rule."""
    # Test: data_type is 'm365:defenderah:scheduledtaskcreated'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:scheduledtaskcreated']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['task_schedule'])

  def testGroupCreated(self):
    """Tests the group_created tagging rule."""
    # Test: data_type is 'm365:defenderah:securitygroupcreated'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:securitygroupcreated']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['group_created'])

  def testEventlogCleared(self):
    """Tests the eventlog_cleared tagging rule."""
    # Test: data_type is 'm365:defenderah:securitylogcleared'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:securitylogcleared']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['eventlog_cleared'])

  def testServiceNew(self):
    """Tests the service_new tagging rule."""
    # Test: data_type is 'm365:defenderah:serviceinstalled'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:serviceinstalled']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['service_new'])

  def testGroupAddedAccount(self):
    """Tests the group_added_account tagging rule."""
    # Test: data_type is 'm365:defenderah:useraccountaddedtolocalgroup'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:useraccountaddedtolocalgroup']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['group_added_account'])

  def testAccountCreated(self):
    """Tests the account_created tagging rule."""
    # Test: data_type is 'm365:defenderah:useraccountcreated'
    attribute_values_per_name = {
        'data_type': ['m365:defenderah:useraccountcreated']}
    self._CheckTaggingRule(
        defender_device.DefenderDeviceEventData,
        attribute_values_per_name,
        ['account_created'])


if __name__ == '__main__':
  unittest.main()
