#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tag_defender.txt tagging file."""

import unittest

from plaso.parsers import defender_hunting

from tests.data import test_lib


class DefenderTaggingFileTest(test_lib.TaggingFileTestCase):
  """Tests the tag_defender.txt tagging file.

  In the tests below the EventData classes are used to catch failing tagging
  rules in case event data types are renamed.
  """

  _TAG_FILE = 'tag_defender.txt'

  def testApplicationExecution(self):
    """Tests the application_execution tagging rule."""
    # Test: data_type is 'defender:hunting:processcreated'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:processcreated']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'defender:hunting:imageloaded'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:imageloaded']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'defender:hunting:openprocess'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:openprocess']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'defender:hunting:processcreatedusingwmiquery'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:processcreatedusingwmiquery']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['application_execution'])

  def testFileCreated(self):
    """Tests the file_created tagging rule."""
    # Test: data_type is 'defender:hunting:filecreated'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:filecreated']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['file_created'])

  def testFileDeleted(self):
    """Tests the file_deleted tagging rule."""
    # Test: data_type is 'defender:hunting:filedeleted'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:filedeleted']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['file_deleted'])

  def testFileModified(self):
    """Tests the file_modified tagging rule."""
    # Test: data_type is 'defender:hunting:filemodified'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:filemodified']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['file_modified'])

  def testFileRenamed(self):
    """Tests the file_renamed tagging rule."""
    # Test: data_type is 'defender:hunting:filerenamed'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:filerenamed']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['file_renamed'])

  def testLoginFailed(self):
    """Tests the login_failed tagging rule."""
    # Test: data_type is 'defender:hunting:logonfailed'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:logonfailed']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['login_failed'])

  def testLoginAttempt(self):
    """Tests the login_attempt tagging rule."""
    # Test: data_type is 'defender:hunting:logonattempted'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:logonattempted']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['login_attempt'])

  def testLoginSuccess(self):
    """Tests the login_success tagging rule."""
    # Test: data_type is 'defender:hunting:logonsuccess'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:logonsuccess']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['login_success'])

  def testRegistryModified(self):
    """Tests the registry_modified tagging rule."""
    # Test: data_type is 'defender:hunting:registrykeycreated'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:registrykeycreated']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'defender:hunting:registrykeydeleted'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:registrykeydeleted']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'defender:hunting:registrykeyrenamed'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:registrykeyrenamed']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'defender:hunting:registryvaluedeleted'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:registryvaluedeleted']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['registry_modified'])

    # Test: data_type is 'defender:hunting:registryvalueset'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:registryvalueset']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['registry_modified'])

  def testConnectionFailed(self):
    """Tests the connection_failed tagging rule."""
    # Test: data_type is 'defender:hunting:connectionfailed'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:connectionfailed']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['connection_failed'])

  def testConnectionSuccess(self):
    """Tests the connection_success tagging rule."""
    # Test: data_type is 'defender:hunting:connectionsuccess'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:connectionsuccess']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['connection_success'])

  def testDnsConnection(self):
    """Tests the dns_connection tagging rule."""
    # Test: data_type is 'defender:hunting:dnsconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:dnsconnectioninspected']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['dns_connection'])

  def testFtpConnection(self):
    """Tests the ftp_connection tagging rule."""
    # Test: data_type is 'defender:hunting:ftpconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:ftpconnectioninspected']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['ftp_connection'])

  def testHttpConnection(self):
    """Tests the http_connection tagging rule."""
    # Test: data_type is 'defender:hunting:httpconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:httpconnectioninspected']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['http_connection'])

  def testIcmpConnection(self):
    """Tests the icmp_connection tagging rule."""
    # Test: data_type is 'defender:hunting:icmpconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:icmpconnectioninspected']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['icmp_connection'])

  def testInboundConnection(self):
    """Tests the inbound_connection tagging rule."""
    # Test: data_type is 'defender:hunting:inboundconnectionaccepted'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:inboundconnectionaccepted']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['inbound_connection'])

  def testOpenPort(self):
    """Tests the open_port tagging rule."""
    # Test: data_type is 'defender:hunting:listeningconnectioncreated'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:listeningconnectioncreated']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['open_port'])

  def testSmtpConnection(self):
    """Tests the smtp_connection tagging rule."""
    # Test: data_type is 'defender:hunting:smtpconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:smtpconnectioninspected']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['smtp_connection'])

  def testSshConnection(self):
    """Tests the ssh_connection tagging rule."""
    # Test: data_type is 'defender:hunting:sshconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:sshconnectioninspected']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['ssh_connection'])

  def testSslConnection(self):
    """Tests the ssl_connection tagging rule."""
    # Test: data_type is 'defender:hunting:sslconnectioninspected'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:sslconnectioninspected']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['ssl_connection'])

  def testThreatDetection(self):
    """Tests the threat_detection tagging rule."""
    # Test: data_type is 'defender:hunting:antivirusdetection'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:antivirusdetection']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'defender:hunting:antiviruserror'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:antiviruserror']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'defender:hunting:antivirusmalwareactionfailed'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:antivirusmalwareactionfailed']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'defender:hunting:antivirusmalwareblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:antivirusmalwareblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['threat_detection'])

    # Test: data_type is 'defender:hunting:antivirusreport'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:antivirusreport']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['threat_detection'])

  def testAsrBlock(self):
    """Tests the asr_block tagging rule."""
    # Test: data_type is 'defender:hunting:asradobereaderchildprocessblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asradobereaderchildprocessblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrexecutableemailcontentblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrexecutableemailcontentblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrexecutableofficecontentblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrexecutableofficecontentblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrlsasscredentialtheftblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrlsasscredentialtheftblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrobfuscatedscriptblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrobfuscatedscriptblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrofficechildprocessblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrofficechildprocessblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrofficecommappchildprocessblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrofficecommappchildprocessblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrofficemacrowin32apicallsblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrofficemacrowin32apicallsblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrofficeprocessinjectionblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrofficeprocessinjectionblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrpersistencethroughwmiblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrpersistencethroughwmiblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrpsexecwmichildprocessblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrpsexecwmichildprocessblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrransomwareblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrransomwareblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrscriptexecutabledownloadblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrscriptexecutabledownloadblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asruntrustedexecutableblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asruntrustedexecutableblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asruntrustedusbprocessblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asruntrustedusbprocessblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

    # Test: data_type is 'defender:hunting:asrvulnerablesigneddriverblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:asrvulnerablesigneddriverblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['asr_block'])

  def testFirewallBlock(self):
    """Tests the firewall_block tagging rule."""
    # Test: data_type is 'defender:hunting:firewallinboundconnectionblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:firewallinboundconnectionblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['firewall_block'])

    # Test: data_type is
    # 'defender:hunting:firewallinboundconnectiontoappblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:firewallinboundconnectiontoappblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['firewall_block'])

    # Test: data_type is 'defender:hunting:firewalloutboundconnectionblocked'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:firewalloutboundconnectionblocked']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['firewall_block'])

  def testFirewallChange(self):
    """Tests the firewall_change tagging rule."""
    # Test: data_type is 'defender:hunting:firewallservicestopped'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:firewallservicestopped']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['firewall_change'])

  def testRdpConnection(self):
    """Tests the rdp_connection tagging rule."""
    # Test: data_type is 'defender:hunting:remotedesktopconnection'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:remotedesktopconnection']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['rdp_connection'])

  def testTaskSchedule(self):
    """Tests the task_schedule tagging rule."""
    # Test: data_type is 'defender:hunting:scheduledtaskcreated'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:scheduledtaskcreated']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['task_schedule'])

  def testGroupCreated(self):
    """Tests the group_created tagging rule."""
    # Test: data_type is 'defender:hunting:securitygroupcreated'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:securitygroupcreated']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['group_created'])

  def testEventlogCleared(self):
    """Tests the eventlog_cleared tagging rule."""
    # Test: data_type is 'defender:hunting:securitylogcleared'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:securitylogcleared']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['eventlog_cleared'])

  def testServiceNew(self):
    """Tests the service_new tagging rule."""
    # Test: data_type is 'defender:hunting:serviceinstalled'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:serviceinstalled']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['service_new'])

  def testGroupAddedAccount(self):
    """Tests the group_added_account tagging rule."""
    # Test: data_type is 'defender:hunting:useraccountaddedtolocalgroup'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:useraccountaddedtolocalgroup']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['group_added_account'])

  def testAccountCreated(self):
    """Tests the account_created tagging rule."""
    # Test: data_type is 'defender:hunting:useraccountcreated'
    attribute_values_per_name = {
        'data_type': ['defender:hunting:useraccountcreated']}
    self._CheckTaggingRule(
        defender_hunting.DefenderAdvancedHuntingEventData,
        attribute_values_per_name,
        ['account_created'])


if __name__ == '__main__':
  unittest.main()
