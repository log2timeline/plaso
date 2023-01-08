#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the tag_linux.txt tagging file."""

import unittest

from plaso.containers import events
from plaso.lib import definitions
from plaso.parsers import fish_history
from plaso.parsers import utmp
from plaso.parsers.jsonl_plugins import docker_layer_config
from plaso.parsers.text_plugins import bash_history
from plaso.parsers.text_plugins import dpkg
from plaso.parsers.text_plugins import selinux
from plaso.parsers.text_plugins import syslog
from plaso.parsers.text_plugins import zsh_extended_history

from tests.data import test_lib


class LinuxTaggingFileTest(test_lib.TaggingFileTestCase):
  """Tests the tag_linux.txt tagging file.

  In the tests below the EventData classes are used to catch failing tagging
  rules in case event data types are renamed.
  """

  _TAG_FILE = 'tag_linux.txt'

  def testRuleApplicationExecution(self):
    """Tests the application_execution tagging rule."""
    # Test: data_type is 'bash:history:command'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        bash_history.BashHistoryEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'docker:layer:configuration'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        docker_layer_config.DockerLayerConfigurationEventData,
        attribute_values_per_name, ['application_execution'])

    # Test: data_type is 'fish:history:command'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        fish_history.FishHistoryEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'selinux:line' AND (audit_type is 'EXECVE' OR
    #       audit_type is 'USER_CMD')
    attribute_values_per_name = {
        'audit_type': ['EXECVE', 'USER_CMD']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'shell:zsh:history'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        zsh_extended_history.ZshHistoryEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: data_type is 'syslog:cron:task_run'
    attribute_values_per_name = {}
    self._CheckTaggingRule(
        syslog.SyslogCronTaskRunEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: reporter is 'sudo' AND body contains 'COMMAND='
    attribute_values_per_name = {
        'body': ['test if my COMMAND=bogus'],
        'reporter': ['sudo']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['application_execution'])

    # Test: reporter is 'CROND' AND body contains 'CMD'
    attribute_values_per_name = {
        'body': ['test if my CMD bogus'],
        'reporter': ['CROND']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['application_execution'])

  def testRuleLogin(self):
    """Tests the login tagging rule."""
    # Test: data_type is 'linux:utmp:event' AND type == 7
    attribute_values_per_name = {
        'type': [7]}
    self._CheckTaggingRule(
        utmp.UtmpEventData, attribute_values_per_name,
        ['login'])

    # Test: data_type is 'selinux:line' AND audit_type is 'LOGIN'
    attribute_values_per_name = {
        'audit_type': ['LOGIN']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['login'])

    # Test: reporter is 'login' AND (body contains 'logged in' OR
    #       body contains 'ROOT LOGIN' OR body contains 'session opened')
    attribute_values_per_name = {
        'body': ['logged in', 'ROOT LOGIN', 'session opened'],
        'reporter': ['login']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['login'])

    # Test: reporter is 'sshd' AND (body contains 'session opened' OR
    #       body contains 'Starting session')
    attribute_values_per_name = {
        'body': ['session opened', 'Starting session'],
        'reporter': ['sshd']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['login'])

    # Test: reporter is 'dovecot' AND body contains 'imap-login: Login:'
    attribute_values_per_name = {
        'body': ['imap-login: Login:'],
        'reporter': ['dovecot']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['login'])

    # Test: reporter is 'postfix/submission/smtpd' AND body contains 'sasl_'
    attribute_values_per_name = {
        'body': ['sasl_method=PLAIN, sasl_username='],
        'reporter': ['postfix/submission/smtpd']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['login'])

  def testRuleLoginFailed(self):
    """Tests the login_failed tagging rule."""
    # Test: data_type is 'selinux:line' AND audit_type is 'ANOM_LOGIN_FAILURES'
    attribute_values_per_name = {
        'audit_type': ['ANOM_LOGIN_FAILURES']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['login_failed'])

    # Test: data_type is 'selinux:line' AND audit_type is 'USER_LOGIN' AND
    #       body contains 'res=failed'
    attribute_values_per_name = {
        'audit_type': ['USER_LOGIN'],
        'body': ['res=failed']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['login_failed'])

    # Test: data_type is 'syslog:line' AND body contains 'pam_tally2'
    attribute_values_per_name = {
        'body': ['pam_tally2']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['login_failed'])

    # Test: (reporter is 'sshd' OR
    #        reporter is 'login' OR
    #        reporter is 'postfix/submission/smtpd' OR
    #        reporter is 'sudo') AND
    #        body contains 'uthentication fail'
    attribute_values_per_name = {
        'body': ['authentication failed', 'authentication failure',
                 'Authentication failure'],
        'reporter': ['login', 'postfix/submission/smtpd', 'sshd', 'sudo']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['login_failed'])

    # Test: (reporter is 'xscreensaver' or
    #        reporter is 'login') AND
    #       body contains 'FAILED LOGIN'
    attribute_values_per_name = {
        'body': ['FAILED LOGIN'],
        'reporter': ['login', 'xscreensaver']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['login_failed'])

    # Test: reporter is 'su' AND body contains 'DENIED'
    attribute_values_per_name = {
        'body': ['DENIED su from'],
        'reporter': ['su']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['login_failed'])

    # Test: reporter is 'nologin'
    attribute_values_per_name = {
        'reporter': ['nologin']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['login_failed'])

  def testRuleUserAdd(self):
    """Tests the useradd tagging rule."""
    # Test: reporter is 'useradd' AND body contains 'new user'
    attribute_values_per_name = {
        'reporter': ['useradd'],
        'body': ['new user']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['useradd'])

    # Test: data_type is 'selinux:line' AND audit_type is 'ADD_USER'
    attribute_values_per_name = {
        'audit_type': ['ADD_USER']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['useradd'])

  def testRuleGroupAdd(self):
    """Tests the groupadd tagging rule."""
    # Test: reporter is 'useradd' AND body contains 'new group'
    attribute_values_per_name = {
        'reporter': ['useradd'],
        'body': ['new group']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['groupadd'])

    # Test: data_type is 'selinux:line' AND audit_type is 'ADD_GROUP'
    attribute_values_per_name = {
        'audit_type': ['ADD_GROUP']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['groupadd'])

    # Test: reporter is 'groupadd'
    attribute_values_per_name = {
        'reporter': ['groupadd']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['groupadd'])

  def testRuleUserDel(self):
    """Tests the userdel tagging rule."""
    # Test: reporter is 'userdel' AND body contains 'delete user'
    attribute_values_per_name = {
        'reporter': ['userdel'],
        'body': ['delete user']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['userdel'])

    # Test: data_type is 'selinux:line' AND audit_type is 'DEL_USER'
    attribute_values_per_name = {
        'audit_type': ['DEL_USER']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['userdel'])

  def testRuleGroupDel(self):
    """Tests the groupdel tagging rule."""
    # Test: reporter is 'userdel' AND body contains 'removed group'
    attribute_values_per_name = {
        'reporter': ['userdel'],
        'body': ['removed group']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['groupdel'])

    # Test: data_type is 'selinux:line' AND audit_type is 'DEL_GROUP'
    attribute_values_per_name = {
        'audit_type': ['DEL_GROUP']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['groupdel'])

    # Test: reporter is 'groupdel'
    attribute_values_per_name = {
        'reporter': ['groupdel']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['groupdel'])

  def testRuleFirewallChange(self):
    """Tests the firewall_change tagging rule."""
    # Test: data_type is 'selinux:line' AND audit_type is 'NETFILTER_CFG'
    attribute_values_per_name = {
        'audit_type': ['NETFILTER_CFG']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['firewall_change'])

  def testRuleLogout(self):
    """Tests the logout tagging rule."""
    # Test: data_type is 'linux:utmp:event' AND type == 8 AND terminal != '' AND
    #       pid != 0

    # Cannot use _CheckTaggingRule here because of terminal != ''
    event = events.EventObject()
    event.timestamp = self._TEST_TIMESTAMP
    event.timestamp_desc = definitions.TIME_DESCRIPTION_UNKNOWN

    event_data = utmp.UtmpEventData()
    event_data.type = 0
    event_data.terminal = 'tty1'
    event_data.pid = 1

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event_data.type = 8
    event_data.terminal = ''

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event_data.terminal = 'tty1'
    event_data.pid = 0

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, [])

    event_data.pid = 1

    storage_writer = self._TagEvent(event, event_data, None)

    self._CheckLabels(storage_writer, ['logout'])

    # Test: reporter is 'login' AND body contains 'session closed'
    attribute_values_per_name = {
        'body': ['session closed'],
        'reporter': ['login']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name, ['logout'])

    # Test: reporter is 'sshd' AND (body contains 'session closed' OR
    #       body contains 'Close session')
    attribute_values_per_name = {
        'body': ['Close session', 'session closed'],
        'reporter': ['sshd']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name, ['logout'])

    # Test: reporter is 'systemd-logind' AND body contains 'logged out'
    attribute_values_per_name = {
        'body': ['logged out'],
        'reporter': ['systemd-logind']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name, ['logout'])

    # Test: reporter is 'dovecot' AND body contains 'Logged out'
    attribute_values_per_name = {
        'body': ['Logged out'],
        'reporter': ['dovecot']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name, ['logout'])

    # Test: data_type is 'selinux:line' AND audit_type is 'USER_LOGOUT'
    attribute_values_per_name = {
        'audit_type': ['USER_LOGOUT']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['logout'])

  def testRuleSessionStart(self):
    """Tests the session_start tagging rule."""
    # Test: reporter is 'systemd-logind' and body contains 'New session'
    attribute_values_per_name = {
        'body': ['New session'],
        'reporter': ['systemd-logind']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['session_start'])

  def testRuleSessionStop(self):
    """Tests the session_stop tagging rule."""
    # Test: reporter is 'systemd-logind' and body contains 'Removed session'
    attribute_values_per_name = {
        'body': ['Removed session'],
        'reporter': ['systemd-logind']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['session_stop'])

  def testRuleBoot(self):
    """Tests the boot tagging rule."""
    # Test: data_type is 'linux:utmp:event' AND type == 2 AND
    #       terminal is 'system boot' AND username is 'reboot'
    attribute_values_per_name = {
        'terminal': ['system boot'],
        'type': [2],
        'username': ['reboot']}
    self._CheckTaggingRule(
        utmp.UtmpEventData, attribute_values_per_name, ['boot'])

    # Test: data_type is 'selinux:line' AND audit_type is 'SYSTEM_BOOT'
    attribute_values_per_name = {
        'audit_type': ['SYSTEM_BOOT']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['boot'])

  def testRuleShutdown(self):
    """Tests the shutdonw tagging rule."""
    # Test: data_type is 'linux:utmp:event' AND type == 1 AND
    #       (terminal is '~~' OR terminal is 'system boot') AND
    #       username is 'shutdown'
    attribute_values_per_name = {
        'terminal': ['~~', 'system boot'],
        'type': [1],
        'username': ['shutdown']}
    self._CheckTaggingRule(
        utmp.UtmpEventData, attribute_values_per_name, ['shutdown'])

    # Test: data_type is 'selinux:line' AND audit_type is 'SYSTEM_SHUTDOWN'
    attribute_values_per_name = {
        'audit_type': ['SYSTEM_SHUTDOWN']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['shutdown'])

  def testRuleRunlevel(self):
    """Tests the runlevel tagging rule."""
    # Test: data_type is 'linux:utmp:event' AND type == 1 AND
    #       username is 'runlevel'
    attribute_values_per_name = {
        'type': [1],
        'username': ['runlevel']}
    self._CheckTaggingRule(
        utmp.UtmpEventData, attribute_values_per_name, ['runlevel'])

    # Test: data_type is 'selinux:line' AND audit_type is 'SYSTEM_RUNLEVEL'
    attribute_values_per_name = {
        'audit_type': ['SYSTEM_RUNLEVEL']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['runlevel'])

  def testRuleDeviceConnection(self):
    """Tests the device_connection tagging rule."""
    # Test: reporter is 'kernel' AND body contains 'New USB device found'
    attribute_values_per_name = {
        'body': ['New USB device found'],
        'reporter': ['kernel']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['device_connection'])

  def testRuleDeviceDisconnection(self):
    """Tests the device_disconnection tagging rule."""
    # Test: reporter is 'kernel' AND body contains 'USB disconnect'
    attribute_values_per_name = {
        'body': ['USB disconnect'],
        'reporter': ['kernel']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['device_disconnection'])

  def testRuleApplicationInstall(self):
    """Tests the application_install tagging rule."""
    # Test: data_type is 'linux:dpkg_log:entry' AND
    #       body contains 'status installed'
    attribute_values_per_name = {
        'body': ['status installed']}
    self._CheckTaggingRule(
        dpkg.DpkgEventData, attribute_values_per_name,
        ['application_install'])

  def testRuleServiceStart(self):
    """Tests the service_start tagging rule."""
    # Test: data_type is 'selinux:line' AND audit_type is 'SERVICE_START'
    attribute_values_per_name = {
        'audit_type': ['SERVICE_START']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['service_start'])

  def testRuleServiceStop(self):
    """Tests the service_stop tagging rule."""
    # Test: data_type is 'selinux:line' AND audit_type is 'SERVICE_STOP'
    attribute_values_per_name = {
        'audit_type': ['SERVICE_STOP']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['service_stop'])

  def testRulePromiscuous(self):
    """Tests the promiscuous tagging rule."""
    # Test: data_type is 'selinux:line' AND audit_type is 'ANOM_PROMISCUOUS'
    attribute_values_per_name = {
        'audit_type': ['ANOM_PROMISCUOUS']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name,
        ['promiscuous'])

    # Test: reporter is 'kernel' AND body contains 'promiscuous mode'
    attribute_values_per_name = {
        'body': ['promiscuous mode'],
        'reporter': ['kernel']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name,
        ['promiscuous'])

  def testRuleCrach(self):
    """Tests the crash tagging rule."""
    # Test: data_type is 'selinux:line' AND audit_type is 'ANOM_ABEND'
    attribute_values_per_name = {
        'audit_type': ['ANOM_ABEND']}
    self._CheckTaggingRule(
        selinux.SELinuxLogEventData, attribute_values_per_name, ['crash'])

    # Test: reporter is 'kernel' AND body contains 'segfault'
    attribute_values_per_name = {
        'body': ['segfault'],
        'reporter': ['kernel']}
    self._CheckTaggingRule(
        syslog.SyslogLineEventData, attribute_values_per_name, ['crash'])


if __name__ == '__main__':
  unittest.main()
