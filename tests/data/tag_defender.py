#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tag_defender.txt tagging file."""

import unittest

from plaso.parsers.csv_plugins import dah_events

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
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHProcessCreatedEventData,
        attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'm365:defenderah:imageloaded'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHImageLoadedEventData,
        attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'm365:defenderah:openprocess'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHOpenProcessEventData,
        attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'm365:defenderah:processcreatedusingwmiquery'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHProcessCreatedUsingWmiQueryEventData,
        attribute_values_per_name,
        ['application_execution'])

  def testFileCreated(self):
    """Tests the file_created tagging rule."""
    # Test: data_type is 'm365:defenderah:filecreated'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHFileCreatedEventData,
        attribute_values_per_name,
        ['file_created'])

  def testFileDeleted(self):
    """Tests the file_deleted tagging rule."""
    # Test: data_type is 'm365:defenderah:filedeleted'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHFileDeletedEventData,
        attribute_values_per_name,
        ['file_deleted'])

  def testFileModified(self):
    """Tests the file_modified tagging rule."""
    # Test: data_type is 'm365:defenderah:filemodified'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHFileModifiedEventData,
        attribute_values_per_name,
        ['file_modified'])

  def testFileRenamed(self):
    """Tests the file_renamed tagging rule."""
    # Test: data_type is 'm365:defenderah:filerenamed'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHFileRenamedEventData,
        attribute_values_per_name,
        ['file_renamed'])

  def testLoginFailed(self):
    """Tests the login_failed tagging rule."""
    # Test: data_type is 'm365:defenderah:logonfailed'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHLogonFailedEventData,
        attribute_values_per_name,
        ['login_failed'])

  def testLoginAttempt(self):
    """Tests the login_attempt tagging rule."""
    # Test: data_type is 'm365:defenderah:logonattempted'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHLogonAttemptedEventData,
        attribute_values_per_name,
        ['login_attempt'])

  def testLoginSuccess(self):
    """Tests the login_success tagging rule."""
    # Test: data_type is 'm365:defenderah:logonsuccess'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHLogonSuccessEventData,
        attribute_values_per_name,
        ['login_success'])

  def testRegistryModified(self):
    """Tests the registry_modified tagging rule."""
    # Test: data_type is 'm365:defenderah:registrykeycreated'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHRegistryKeyCreatedEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'm365:defenderah:registrykeydeleted'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHRegistryKeyDeletedEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'm365:defenderah:registrykeyrenamed'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHRegistryKeyRenamedEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'm365:defenderah:registryvaluedeleted'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHRegistryValueDeletedEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'm365:defenderah:registryvalueset'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHRegistryValueSetEventData,
        attribute_values_per_name,
        ['registry_modified'])

  def testConnectionFailed(self):
    """Tests the connection_failed tagging rule."""
    # Test: data_type is 'm365:defenderah:connectionfailed'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHConnectionFailedEventData,
        attribute_values_per_name,
        ['connection_failed'])

  def testConnectionSuccess(self):
    """Tests the connection_success tagging rule."""
    # Test: data_type is 'm365:defenderah:connectionsuccess'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHConnectionSuccessEventData,
        attribute_values_per_name,
        ['connection_success'])

  def testDnsConnection(self):
    """Tests the dns_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:dnsconnectioninspected'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHDnsConnectionInspectedEventData,
        attribute_values_per_name,
        ['dns_connection'])

  def testFtpConnection(self):
    """Tests the ftp_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:ftpconnectioninspected'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHFtpConnectionInspectedEventData,
        attribute_values_per_name,
        ['ftp_connection'])

  def testHttpConnection(self):
    """Tests the http_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:httpconnectioninspected'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHHttpConnectionInspectedEventData,
        attribute_values_per_name,
        ['http_connection'])

  def testIcmpConnection(self):
    """Tests the icmp_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:icmpconnectioninspected'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHIcmpConnectionInspectedEventData,
        attribute_values_per_name,
        ['icmp_connection'])

  def testInboundConnection(self):
    """Tests the inbound_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:inboundconnectionaccepted'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHInboundConnectionAcceptedEventData,
        attribute_values_per_name,
        ['inbound_connection'])

  def testOpenPort(self):
    """Tests the open_port tagging rule."""
    # Test: data_type is 'm365:defenderah:listeningconnectioncreated'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHListeningConnectionCreatedEventData,
        attribute_values_per_name,
        ['open_port'])

  def testSmtpConnection(self):
    """Tests the smtp_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:smtpconnectioninspected'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHSmtpConnectionInspectedEventData,
        attribute_values_per_name,
        ['smtp_connection'])

  def testSshConnection(self):
    """Tests the ssh_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:sshconnectioninspected'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHSshConnectionInspectedEventData,
        attribute_values_per_name,
        ['ssh_connection'])

  def testSslConnection(self):
    """Tests the ssl_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:sslconnectioninspected'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHSslConnectionInspectedEventData,
        attribute_values_per_name,
        ['ssl_connection'])

  def testThreatDetection(self):
    """Tests the threat_detection tagging rule."""
    # Test: data_type is 'm365:defenderah:antivirusdetection'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAntivirusDetectionEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'm365:defenderah:antiviruserror'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAntivirusErrorEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'm365:defenderah:antivirusmalwareactionfailed'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAntivirusMalwareActionFailedEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'm365:defenderah:antivirusmalwareblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAntivirusMalwareBlockedEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'm365:defenderah:antivirusreport'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAntivirusReportEventData,
        attribute_values_per_name,
        ['threat_detection'])

  def testAsrBlock(self):
    """Tests the asr_block tagging rule."""
    # Test: data_type is 'm365:defenderah:asradobereaderchildprocessblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrAdobeReaderChildProcessBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrexecutableemailcontentblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrExecutableEmailContentBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrexecutableofficecontentblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrExecutableOfficeContentBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrlsasscredentialtheftblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrLsassCredentialTheftBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrobfuscatedscriptblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrObfuscatedScriptBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrofficechildprocessblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrOfficeChildProcessBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrofficecommappchildprocessblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrOfficeCommAppChildProcessBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrofficemacrowin32apicallsblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrOfficeMacroWin32ApiCallsBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrofficeprocessinjectionblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrOfficeProcessInjectionBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrpersistencethroughwmiblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrPersistenceThroughWmiBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrpsexecwmichildprocessblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrPsexecWmiChildProcessBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrransomwareblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrRansomwareBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrscriptexecutabledownloadblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrScriptExecutableDownloadBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asruntrustedexecutableblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrUntrustedExecutableBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asruntrustedusbprocessblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrUntrustedUsbProcessBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'm365:defenderah:asrvulnerablesigneddriverblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHAsrVulnerableSignedDriverBlockedEventData,
        attribute_values_per_name,
        ['asr_block'])

  def testFirewallBlock(self):
    """Tests the firewall_block tagging rule."""
    # Test: data_type is 'm365:defenderah:firewallinboundconnectionblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHFirewallInboundConnectionBlockedEventData,
        attribute_values_per_name,
        ['firewall_block'])

    # Test: data_type is 'm365:defenderah:firewallinboundconnectiontoappblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHFirewallInboundConnectionToAppBlockedEventData,
        attribute_values_per_name,
        ['firewall_block'])

    # Test: data_type is 'm365:defenderah:firewalloutboundconnectionblocked'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHFirewallOutboundConnectionBlockedEventData,
        attribute_values_per_name,
        ['firewall_block'])

  def testFirewallChange(self):
    """Tests the firewall_change tagging rule."""
    # Test: data_type is 'm365:defenderah:firewallservicestopped'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHFirewallServiceStoppedEventData,
        attribute_values_per_name,
        ['firewall_change'])

  def testRdpConnection(self):
    """Tests the rdp_connection tagging rule."""
    # Test: data_type is 'm365:defenderah:remotedesktopconnection'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHRemoteDesktopConnectionEventData,
        attribute_values_per_name,
        ['rdp_connection'])

  def testTaskSchedule(self):
    """Tests the task_schedule tagging rule."""
    # Test: data_type is 'm365:defenderah:scheduledtaskcreated'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHScheduledTaskCreatedEventData,
        attribute_values_per_name,
        ['task_schedule'])

  def testGroupCreated(self):
    """Tests the group_created tagging rule."""
    # Test: data_type is 'm365:defenderah:securitygroupcreated'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHSecurityGroupCreatedEventData,
        attribute_values_per_name,
        ['group_created'])

  def testEventlogCleared(self):
    """Tests the eventlog_cleared tagging rule."""
    # Test: data_type is 'm365:defenderah:securitylogcleared'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHSecurityLogClearedEventData,
        attribute_values_per_name,
        ['eventlog_cleared'])

  def testServiceNew(self):
    """Tests the service_new tagging rule."""
    # Test: data_type is 'm365:defenderah:serviceinstalled'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHServiceInstalledEventData,
        attribute_values_per_name,
        ['service_new'])

  def testGroupAddedAccount(self):
    """Tests the group_added_account tagging rule."""
    # Test: data_type is 'm365:defenderah:useraccountaddedtolocalgroup'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHUserAccountAddedToLocalGroupEventData,
        attribute_values_per_name,
        ['group_added_account'])

  def testAccountCreated(self):
    """Tests the account_created tagging rule."""
    # Test: data_type is 'm365:defenderah:useraccountcreated'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        dah_events.DefenderAHUserAccountCreatedEventData,
        attribute_values_per_name,
        ['account_created'])

if __name__ == '__main__':
  unittest.main()
  