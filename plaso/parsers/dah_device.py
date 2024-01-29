# -*- coding: utf-8 -*-
"""M365 Defender DeviceFileEvents table (CSV) parser."""

import csv
import json
import os

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import dsv_parser
from plaso.parsers import manager


class DefenderAHDeviceEventData(events.EventData):
  """M365 Defender event data.

  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
        the event was recorded.
    accountdomain (str): Domain of the account.
    accountname (str): User name of the account.
    additionalfields (str): Additional information about the entity or event
    detectionmethods (str): Detection technology that was used to identify
        the threat at the time of click.
    dnsquery (str): Inspected DNS query.
    failurereason (str): Information explaining why the recorded action failed.
    filename (str): Name of the file that the recorded action was applied to.
    fileoriginip (str): IP address where the file was downloaded from.
    fileoriginreferrerurl (str): URL of the web page that links
        to the downloaded file.
    fileoriginurl (str): URL where the file was downloaded from.
    folderpath (str): Folder containing the file that the recorded action
        was applied to.
    initiatingprocessaccountdomain (str): Domain of the account
        that ran the process responsible for the event.
    initiatingprocessaccountname (str): User name of the account
        that ran the process responsible for the event.
    initiatingprocesscommandline (str): Command line used to run the process
        that initiated the event.
    initiatingprocesscreationtime (str): Date and time when the process
        that initiated the event was started.
    initiatingprocessfilename (str): Name of the process
        that initiated the event.
    initiatingprocessfolderpath (str): Folder containing the process
        (image file) that initiated the event.
    initiatingprocessid (str): Process ID (PPID) of the process
        that initiated the event.
    initiatingprocessparentcreationtime (str): Date and time when the parent
        of the process responsible for the event was started.
    initiatingprocessparentfilename (str): Name of the parent process
        that spawned the process responsible for the event.
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
        that spawned the process responsible for the event.
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
        that initiated the event.
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
        that initiated the event.
    ipaddress (str): Public IP address of the device from which
        the user clicked on the link.
    localip (str): Source IP, or the IP address where
        the communication came from.
    localport (str): TCP port on the local machine used during communication.
    logontype (str): Type of logon session.
    previousfilename (str): Original name of the file that was renamed as
        a result of the action.
    previousfolderpath (str): Original folder containing the file before
        the recorded action was applied.
    previousregistrykey (str): Original registry key of the registry
        value before it was modified.
    previousregistryvaluedata (str): Original data of the registry
        value before it was modified.
    previousregistryvaluename (str): Original name of the registry
        value before it was modified.
    processid (str): Process ID (PID) of the newly created process.
    processcommandline (str): Command line used to create the new process.
    processcreationtime (str): Date and time the process was created.
    protocol (str): Protocol used during the communication.
    pscommand (str): Executed command.
    registrykey (str): Registry key that the recorded action was applied to.
    registryvaluedata (str): Data of the registry value that
        the recorded action was applied to.
    registryvaluename (str): Name of the registry value that
        the recorded action was applied to.
    remotedevicename (str): Name of the machine that performed a remote
        operation on the affected machine. Depending on the event being
        reported, this name could be a fully-qualified domain name (FQDN),
        a NetBIOS name or a host name without domain information.
    remoteip (str): IP address that was being connected to.
    remoteport (str): TCP port on the remote device that was being connected to.
    remoteurl (str): URL or fully qualified domain name (FQDN)
        that was being connected to.
    requestaccountdomain (str): Domain of the account used to remotely
        initiate the activity.
    requestaccountname (str): User name of account used to remotely
        initiate the activity.
    requestprotocol (str): Network protocol, if applicable, used to initiate
        the activity: Unknown, Local, SMB, or NFS.
    requestsourceip (str): IPv4 or IPv6 address of the remote device
        that initiated the activity.
    requestsourceport (str): Source port on the remote device
        that initiated the activity.
    server_name (str): Server hostname.
    sha1 (str): SHA-1 of the file that the recorded action was applied to.
    sha256 (str): SHA-256 of the file that the recorded action was applied to.
    sharename (str): Name of shared folder containing the file.
    taskname (str): Name of scheduled task.
    threattypes (str): Verdict at the time of click, which tells whether
        the URL led to malware, phish or other threats.
    url (str): The full URL that was clicked on by the user.
    urlchain (str): For scenarios involving redirections, it includes URLs
        present in the redirection chain.
    workload (str): The application from which the user clicked on the link,
        with the values being Email, Office, and Teams.
  """

  DATA_TYPE = 'm365:defenderah:event-action'

  def __init__(self, actiontype='event-action'):
    """Initializes event data."""
    self.DATA_TYPE = f'm365:defenderah:{actiontype}' # pylint: disable=invalid-name
    super(DefenderAHDeviceEventData, self).__init__(data_type=self.DATA_TYPE)
    self.timestamp = None

    self.accountdomain = None
    self.accountname = None
    self.additionalfields = None
    self.detectionmethods = None
    self.dnsquery = None
    self.failurereason = None
    self.filename = None
    self.fileoriginip = None
    self.fileoriginreferrerurl = None
    self.fileoriginurl = None
    self.folderpath = None
    self.initiatingprocessaccountdomain = None
    self.initiatingprocessaccountname = None
    self.initiatingprocesscommandline = None
    self.initiatingprocesscreationtime = None
    self.initiatingprocessfilename = None
    self.initiatingprocessfolderpath = None
    self.initiatingprocessid = None
    self.initiatingprocessparentcreationtime = None
    self.initiatingprocessparentfilename = None
    self.initiatingprocessparentid = None
    self.initiatingprocesssha1 = None
    self.initiatingprocesssha256 = None
    self.ipaddress = None
    self.localip = None
    self.localport = None
    self.logontype = None
    self.previousfilename = None
    self.previousfolderpath = None
    self.previousregistrykey = None
    self.previousregistryvaluedata = None
    self.previousregistryvaluename = None
    self.processid = None
    self.processcommandline = None
    self.processcreationtime = None
    self.protocol = None
    self.pscommand = None
    self.registrykey = None
    self.registryvaluedata = None
    self.registryvaluename = None
    self.remotedevicename = None
    self.remoteip = None
    self.remoteport = None
    self.remoteurl = None
    self.requestaccountdomain = None
    self.requestaccountname = None
    self.requestprotocol = None
    self.requestsourceip = None
    self.requestsourceport = None
    self.server_name = None
    self.sha1 = None
    self.sha256 = None
    self.sharename = None
    self.taskname = None
    self.threattypes = None
    self.url = None
    self.urlchain = None
    self.workload = None


class DefenderAHDeviceEventsParser(dsv_parser.DSVParser):
  """Parse Device events from DSV files."""  

  NAME = 'dah_device'
  DATA_FORMAT = 'M365 Defender device events'

  COLUMNS = (
      'Timestamp',
      'ActionType',
      'InitiatingProcessAccountDomain',
      'InitiatingProcessAccountName',
      'InitiatingProcessSHA1',
      'InitiatingProcessSHA256',
      'InitiatingProcessFolderPath',
      'InitiatingProcessFileName',
      'InitiatingProcessId',
      'InitiatingProcessCommandLine',
      'InitiatingProcessCreationTime',
      'InitiatingProcessParentId',
      'InitiatingProcessParentFileName',
      'InitiatingProcessParentCreationTime')

  # List of accepted activities ...
  _ACTIVITIES = {
      'antivirusdefinitionsupdated': [],
      'antivirusdefinitionsupdatefailed': [],
      'antivirusdetection': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'fileoriginurl',
          'fileoriginip',
          'additionalfields'],
      'antivirusemergencyupdatesinstalled': [],
      'antiviruserror': [],
      'antivirusmalwareactionfailed': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'fileoriginurl',
          'fileoriginip',
          'additionalfields'],
    'antivirusmalwareblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'fileoriginurl',
          'fileoriginip',
          'additionalfields'],
    'antivirusreport': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'fileoriginurl',
          'fileoriginip',
          'additionalfields'],
    'antivirusscancancelled': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'antivirusscancompleted': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'asradobereaderchildprocessblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrexecutableemailcontentblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrexecutableofficecontentblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrlsasscredentialtheftblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrobfuscatedscriptblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrofficechildprocessblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrofficecommappchildprocessblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrofficemacrowin32apicallsblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrofficeprocessinjectionblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrpersistencethroughwmiblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrpsexecwmichildprocessblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrransomwareblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrscriptexecutabledownloadblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asruntrustedexecutableblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asruntrustedusbprocessblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'asrvulnerablesigneddriverblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'additionalfields'],
    'browserlaunchedtoopenurl': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'remoteurl'],
    'clickallowed': [
          'url',
          'workload',
          'ipaddress',
          'urlchain'],
    'clickblocked': [
          'url',
          'workload',
          'ipaddress',
          'urlchain',
          'threattypes',
          'detectionmethods'],
    'clickblockedbytenantpolicy': [
          'url',
          'workload',
          'ipaddress',
          'urlchain'],
    'connectionfailed': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'remoteip',
          'remoteport',
          'remoteurl',
          'localip',
          'localport',
          'protocol'],
    'connectionfound': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'remoteip',
          'remoteport',
          'remoteurl',
          'localip',
          'localport',
          'protocol'],
    'connectionrequest': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'remoteip',
          'remoteport',
          'remoteurl',
          'localip',
          'localport',
          'protocol'],
    'connectionsuccess': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'remoteip',
          'remoteport',
          'remoteurl',
          'localip',
          'localport',
          'protocol'],
    'dnsconnectioninspected': [
          'remoteip',
          'remoteport',
          'localip',
          'localport',
          'protocol',
          'additionalfields'],
    'dnsqueryresponse': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'filecreated': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'fileoriginurl',
          'fileoriginreferrerurl',
          'fileoriginip',
          'requestprotocol',
          'requestsourceip',
          'requestsourceport',
          'requestaccountname',
          'requestaccountdomain',
          'sharename',
          'additionalfields'],
    'filedeleted': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'fileoriginurl',
          'fileoriginreferrerurl',
          'fileoriginip',
          'requestprotocol',
          'requestsourceip',
          'requestsourceport',
          'requestaccountname',
          'requestaccountdomain',
          'sharename',
          'additionalfields'],
    'filemodified': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'fileoriginurl',
          'fileoriginreferrerurl',
          'fileoriginip',
          'requestprotocol',
          'requestsourceip',
          'requestsourceport',
          'requestaccountname',
          'requestaccountdomain',
          'sharename',
          'additionalfields'],
    'filerenamed': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'fileoriginurl',
          'fileoriginreferrerurl',
          'fileoriginip',
          'previousfolderpath',
          'previousfilename',
          'requestprotocol',
          'requestsourceip',
          'requestsourceport',
          'requestaccountname',
          'requestaccountdomain',
          'sharename',
          'additionalfields'],
    'firewallinboundconnectionblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'remoteip',
          'remoteport',
          'localip',
          'localport'],
    'firewallinboundconnectiontoappblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'firewalloutboundconnectionblocked': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'remoteip',
          'remoteport',
          'localip',
          'localport'],
    'firewallservicestopped': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime'],
    'ftpconnectioninspected': [
          'remoteip',
          'remoteport',
          'localip',
          'localport',
          'protocol',
          'additionalfields'],
    'getclipboarddata': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime'],
    'httpconnectioninspected': [
          'remoteip',
          'remoteport',
          'localip',
          'localport',
          'protocol',
          'additionalfields'],
    'icmpconnectioninspected': [
          'remoteip',
          'localip',
          'protocol',
          'additionalfields'],
    'imageloaded': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256'],
    'inboundconnectionaccepted': [
          'remoteip',
          'remoteport',
          'localip',
          'localport',
          'protocol'],
    'inboundinternetscaninspected': [
          'remoteip',
          'remoteport',
          'localip',
          'localport',
          'protocol',
          'additionalfields'],
    'listeningconnectioncreated': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'localip',
          'localport',
          'protocol'],
    'logonattempted': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'logontype',
          'accountdomain',
          'accountname',
          'protocol',
          'remotedevicename',
          'remoteip',
          'remoteport',
          'additionalfields'],
    'logonfailed': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'logontype',
          'accountdomain',
          'accountname',
          'protocol',
          'failurereason',
          'remotedevicename',
          'remoteip',
          'remoteport',
          'additionalfields'],
    'logonsuccess': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'logontype',
          'accountdomain',
          'accountname',
          'protocol',
          'remotedevicename',
          'remoteip',
          'remoteport',
          'additionalfields'],
    'networkprotectionuserbypassevent': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'networkshareobjectadded': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'networksignatureinspected': [
          'remoteip',
          'remoteport',
          'localip',
          'localport',
          'additionalfields'],
    'ntlmauthenticationinspected': [
          'remoteip',
          'remoteport',
          'localip',
          'localport',
          'protocol',
          'additionalfields'],
    'openprocess': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256'],
    'powershellcommand': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime'],
    'processcreated': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'filename',
          'folderpath',
          'sha1',
          'sha256',
          'processid',
          'processcommandline',
          'processcreationtime',
          'accountdomain',
          'accountname'],
    'processcreatedusingwmiquery': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'additionalfields'],
    'registrykeycreated': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'registrykey'],
    'registrykeydeleted': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'previousregistrykey'],
    'registrykeyrenamed': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'previousregistrykey',
          'registrykey'],
    'registryvaluedeleted': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'previousregistrykey',
          'previousregistryvaluename',
          'previousregistryvaluedata'],
    'registryvalueset': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'registrykey',
          'registryvaluename',
          'registryvaluedata',
          'previousregistryvaluename',
          'previousregistryvaluedata'],
    'remotedesktopconnection': [
          'localip',
          'localport',
          'additionalfields'],
    'remotewmioperation': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'remotedevicename',
          'additionalfields'],
    'scheduledtaskcreated': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'screenshottaken': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime'],
    'scriptcontent': [
          'sha256',
          'initiatingprocessid'],
    'securitygroupcreated': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocessid',
          'initiatingprocessparentid'],
    'securitylogcleared': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname'],
    'serviceinstalled': [
          'filename',
          'folderpath',
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'smartscreenappwarning': [
          'filename',
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'smartscreenexploitwarning': [
          'remoteurl',
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'smartscreenurlwarning': [
          'remoteurl',
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'smtpconnectioninspected': [
          'remoteip',
          'remoteport',
          'localip',
          'localport',
          'protocol',
          'additionalfields'],
    'sshconnectioninspected': [
          'remoteip',
          'remoteport',
          'localip',
          'localport',
          'protocol',
          'additionalfields'],
    'sslconnectioninspected': [
          'remoteip',
          'remoteport',
          'localip',
          'localport',
          'protocol',
          'additionalfields'],
    'tamperingattempt': [
          'filename',
          'folderpath',
          'registrykey',
          'registryvaluename',
          'registryvaluedata',
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'initiatingprocesssha1',
          'initiatingprocesssha256',
          'initiatingprocessfilename',
          'initiatingprocessid',
          'initiatingprocesscommandline',
          'initiatingprocesscreationtime',
          'initiatingprocessfolderpath',
          'initiatingprocessparentid',
          'initiatingprocessparentfilename',
          'initiatingprocessparentcreationtime',
          'additionalfields'],
    'untrustedwificonnection': [
          'additionalfields'],
    'urlerrorpage': [
          'url',
          'workload',
          'ipaddress',
          'urlchain'],
    'urlscaninprogress': [
          'url',
          'workload',
          'ipaddress',
          'urlchain'],
    'useraccountaddedtolocalgroup': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'additionalfields'],
    'useraccountcreated': [
          'initiatingprocessaccountdomain',
          'initiatingprocessaccountname',
          'accountdomain',
          'accountname']}

  _ADDITIONALFIELDS = {
      'dnsconnectioninspected': {
          'query': 'dnsquery'},
      'dnsqueryresponse': {
          'DnsQueryString': 'dnsquery'},
      'ftpconnectioninspected': {
          'direction': 'direction'},
      'httpconnectioninspected': {
          'direction': 'direction',
          'host': 'host'},
      'icmpconnectioninspected': {
          'direction': 'direction'},
      'ntlmauthenticationinspected': {
          'direction': 'direction'},
      'powershellcommand': {
          'Command': 'pscommand'},
      'scheduledtaskcreated': {
          'TaskName': 'taskname'},
      'scriptcontent': {
          'ScriptContent': 'scriptcontent'},
      'securitygroupcreated': {
          'GroupName': 'groupname'},
      'serviceinstalled': {
          'ServiceName': 'servicename'},
      'smtpconnectioninspected': {
          'direction': 'direction'},
      'sshconnectioninspected': {
          'direction': 'direction'},
      'sslconnectioninspected': {
          'direction': 'direction',
          'server_name': 'server_name'},
      'useraccountaddedtolocalgroup': {
          'GroupDomainName': 'groupdomainname',
          'GroupName': 'groupname'}}

  _MINIMUM_NUMBER_OF_COLUMNS = 30

  _ENCODING = 'utf-8'

  def _ParseDataFromAdditionalFields(self, additionalfields, dataname):
    """Parses data from additionalfields.

    Args:
      additionalfields (str): Additional information about
          the event in JSON array format.

    Returns:
      str: data.
    """
    result = ''

    try:
      if len(additionalfields) > 0 and dataname in additionalfields:
        addjson = json.loads(additionalfields)
        result = addjson[dataname]

    finally:
      pass

    return result

  def _CreateDictReader(self, line_reader):
    """Returns a reader that processes each row and yields dictionaries.

    csv.DictReader does this job well for single-character delimiters; parsers
    that need multi-character delimiters need to override this method.

    Args:
      line_reader (iter): yields lines from a file-like object.

    Returns:
      iter: a reader of dictionaries, as returned by csv.DictReader().
    """
    # Note that doublequote overrules ESCAPE_CHARACTER and needs to be set
    # to False if an escape character is used.
    if self.ESCAPE_CHARACTER:
      csv_dict_reader = csv.DictReader(
          line_reader, delimiter=self.DELIMITER, doublequote=False,
          escapechar=self.ESCAPE_CHARACTER, fieldnames=None,
          restkey=self._MAGIC_TEST_STRING, restval=self._MAGIC_TEST_STRING)
    else:
      csv_dict_reader = csv.DictReader(
          line_reader, delimiter=self.DELIMITER, fieldnames=None,
          quotechar=self.QUOTE_CHAR, restkey=self._MAGIC_TEST_STRING,
          restval=self._MAGIC_TEST_STRING)

    return csv_dict_reader

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a DSV text file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    encoding, text_offset = self._CheckForByteOrderMark(file_object)

    if encoding and self._encoding and encoding != self._encoding:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser((
          '[{0:s}] Unable to parse DSV file: {1:s} encoding does not match the '
          'one required by the parser.').format(self._encoding, display_name))

    encoding = self._encoding
    if not encoding:
      encoding = parser_mediator.GetCodePage()

    file_object.seek(text_offset, os.SEEK_SET)

    try:
      if not self._HasExpectedLineLength(file_object, encoding=encoding):
        display_name = parser_mediator.GetDisplayName()
        raise errors.WrongParser((
            '[{0:s}] Unable to parse DSV file: {1:s} with error: '
            'unexpected line length.').format(self.NAME, display_name))

    except UnicodeDecodeError as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          '[{0:s}] Unable to parse DSV file: {1:s} with error: {2!s}.'.format(
              self.NAME, display_name, exception))

    try:
      line_reader = self._CreateLineReader(file_object, encoding=encoding)
      reader = self._CreateDictReader(line_reader)
      row_offset = line_reader.tell()
      row = next(reader)
    except (StopIteration, UnicodeDecodeError, csv.Error) as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          '[{0:s}] Unable to parse DSV file: {1:s} with error: {2!s}.'.format(
              self.NAME, display_name, exception))

    if not self.CheckRequiredColumns(reader.fieldnames):
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser((
          '[{0:s}] Unable to parse DSV file: {1:s}. Required columns '
          'not found.').format(self.NAME, display_name))

    number_of_columns = len(self.COLUMNS)
    number_of_records = len(row)

    if number_of_records < number_of_columns:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser((
          '[{0:s}] Unable to parse DSV file: {1:s}. Wrong number of '
          'records (expected: {2:d} or more, got: {3:d})').format(
              self.NAME, display_name, number_of_columns,
              number_of_records))

    for key, value in row.items():
      if self._MAGIC_TEST_STRING in (key, value):
        display_name = parser_mediator.GetDisplayName()
        raise errors.WrongParser((
            '[{0:s}] Unable to parse DSV file: {1:s}. Signature '
            'mismatch.').format(self.NAME, display_name))

    if not self.VerifyRow(parser_mediator, row):
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser((
          '[{0:s}] Unable to parse DSV file: {1:s}. Verification '
          'failed.').format(self.NAME, display_name))

    self.ParseRow(parser_mediator, row_offset, row)
    row_offset = line_reader.tell()
    line_number = 2

    while row:
      if parser_mediator.abort:
        break

      # next() is used here to be able to handle lines that the Python csv
      # module fails to parse.
      try:
        row = next(reader)

        self.ParseRow(parser_mediator, row_offset, row)
        row_offset = line_reader.tell()

      except StopIteration:
        break

      except csv.Error as exception:
        parser_mediator.ProduceExtractionWarning(
            'unable to parse line: {0:d} with error: {1!s}'.format(
                line_number, exception))
        break

  def CheckRequiredColumns(self, headers):
    """Check if CSV file has the minimal columns required by the plugin.

    Args:
      headers (list[str]): headers of CSV file.

    Returns:
      bool: True if CSV file has the required columns defined by
          the plugin, or False if it does not or if the plugin does not define
          required columns. The CSV file can have more columns than
          specified by the plugin and still return True.
    """
    if not self.COLUMNS or self.COLUMNS is None:
      return False

    if not headers or headers is None:
      return False

    search = [item.lower().strip() for item in self.COLUMNS]
    data = [item.lower().strip() for item in headers]

    # All of them
    return 0 not in [c in data for c in search]

  def ParseRow(self, parser_mediator, row_offset, row):
    """Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      row_offset (int): line number of the row.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
    try:
      tmp_row = dict((k.lower().strip(), v) for k,v in row.items())
      tmp_action = tmp_row['actiontype'].lower().strip()

      if not tmp_action in self._ACTIVITIES:
        return

      # pylint: disable=line-too-long
      timestamp = tmp_row['timestamp']
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(timestamp)

      event_data = DefenderAHDeviceEventData(tmp_action)
      event_data.timestamp = date_time

      for attribute_name in self._ACTIVITIES[tmp_action]:
        if attribute_name in tmp_row:
          setattr(event_data, attribute_name, tmp_row[attribute_name])

      if 'additionalfields' in tmp_row:
        if tmp_action in self._ADDITIONALFIELDS:
          for key, value in self._ADDITIONALFIELDS[tmp_action].items():
            setattr(
                event_data,
                value,
                self._ParseDataFromAdditionalFields(
                    tmp_row['additionalfields'],
                    key))

      parser_mediator.ProduceEventData(event_data)

    except (TypeError, ValueError, errors.ParseError) as exception:
      parser_mediator.ProduceExtractionWarning(
          'Unable to parse page record with error: {0!s}'.format(
          exception))

  def VerifyRow(self, parser_mediator, row):
    """Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    if len(row) < self._MINIMUM_NUMBER_OF_COLUMNS:
      return False

    # Check the date format
    # If it doesn't parse, then this isn't a M365 Defender export.
    timestamp_value = row.get('Timestamp', None)
    if timestamp_value != 'Timestamp':
      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromStringISO8601(timestamp_value)
      except (TypeError, ValueError):
        return False

    return True


manager.ParsersManager.RegisterParser(DefenderAHDeviceEventsParser)
