# -*- coding: utf-8 -*-
"""CSV (Comma Separated Values) parser plugin for M365 Defender tables."""

from plaso.containers import events

class DefenderAHCommonEventData(
  events.EventData):
  """M365 Defender common event data.
  
  Common event with common attributes

  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:common'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHCommonEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.initiatingprocessaccountdomain = None
    self.initiatingprocessaccountname = None
    self.initiatingprocesssha1 = None
    self.initiatingprocesssha256 = None
    self.initiatingprocessfilename = None
    self.initiatingprocessid = None
    self.initiatingprocesscommandline = None
    self.initiatingprocesscreationtime = None
    self.initiatingprocessfolderpath = None
    self.initiatingprocessparentid = None
    self.initiatingprocessparentfilename = None
    self.initiatingprocessparentcreationtime = None

class DefenderAHAntivirusDefinitionsUpdatedEventData(
  events.EventData):
  """M365 Defender AntivirusDefinitionsUpdated event data.

  Security intelligence updates for Windows Defender
  Antivirus were applied successfully.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
  """

  DATA_TYPE = 'm365:defenderah:antivirusdefinitionsupdated'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAntivirusDefinitionsUpdatedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None

class DefenderAHAntivirusDefinitionsUpdateFailedEventData(
  events.EventData):
  """M365 Defender AntivirusDefinitionsUpdateFailed event data.

  Security intelligence updates for Windows Defender Antivirus were not applied.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
  """

  DATA_TYPE = 'm365:defenderah:antivirusdefinitionsupdatefailed'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAntivirusDefinitionsUpdateFailedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None

class DefenderAHAntivirusDetectionEventData(
  DefenderAHCommonEventData):
  """M365 Defender AntivirusDetection event data.

  Windows Defender Antivirus detected a threat.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    fileoriginurl (str): URL where the file was downloaded from
    fileoriginip (str): IP address where the file was downloaded from
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:antivirusdetection'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAntivirusDetectionEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.fileoriginurl = None
    self.fileoriginip = None
    self.additionalfields = None

class DefenderAHAntivirusEmergencyUpdatesInstalledEventData(
  events.EventData):
  """M365 Defender AntivirusEmergencyUpdatesInstalled event data.

  Emergency security intelligence updates for Windows Defender
  Antivirus were applied.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
  """

  DATA_TYPE = 'm365:defenderah:antivirusemergencyupdatesinstalled'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAntivirusEmergencyUpdatesInstalledEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None

class DefenderAHAntivirusErrorEventData(
  events.EventData):
  """M365 Defender AntivirusError event data.

  Windows Defender Antivirus encountered an error while taking action 
  on malware or a potentially unwanted application.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
  """

  DATA_TYPE = 'm365:defenderah:antiviruserror'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAntivirusErrorEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None

class DefenderAHAntivirusMalwareActionFailedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AntivirusMalwareActionFailed event data.

  Windows Defender Antivirus attempted to take action on malware or
  a potentially unwanted application but the action failed.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    fileoriginurl (str): URL where the file was downloaded from
    fileoriginip (str): IP address where the file was downloaded from
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:antivirusmalwareactionfailed'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAntivirusMalwareActionFailedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.fileoriginurl = None
    self.fileoriginip = None
    self.additionalfields = None

class DefenderAHAntivirusMalwareBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AntivirusMalwareBlocked event data.

  Windows Defender Antivirus blocked files or activity involving 
  malware potentially unwanted applications or suspicious behavior.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    fileoriginurl (str): URL where the file was downloaded from
    fileoriginip (str): IP address where the file was downloaded from
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:antivirusmalwareblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAntivirusMalwareBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.fileoriginurl = None
    self.fileoriginip = None
    self.additionalfields = None

class DefenderAHAntivirusReportEventData(
  DefenderAHCommonEventData):
  """M365 Defender AntivirusReport event data.

  Microsoft Defender Antivirus reported a threat, which can either 
  be a memory, boot sector, or rootkit threat.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    fileoriginurl (str): URL where the file was downloaded from
    fileoriginip (str): IP address where the file was downloaded from
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:antivirusreport'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAntivirusReportEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.fileoriginurl = None
    self.fileoriginip = None
    self.additionalfields = None

class DefenderAHAntivirusScanCancelledEventData(
  DefenderAHCommonEventData):
  """M365 Defender AntivirusScanCancelled event data.

  A Windows Defender Antivirus scan was cancelled.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:antivirusscancancelled'

class DefenderAHAntivirusScanCompletedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AntivirusScanCompleted event data.

  A Windows Defender Antivirus scan completed successfully.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:antivirusscancompleted'

class DefenderAHAsrAdobeReaderChildProcessBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrAdobeReaderChildProcessBlocked event data.

  An attack surface reduction rule blocked Adobe Reader 
  from creating a child process.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asradobereaderchildprocessblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrAdobeReaderChildProcessBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrExecutableEmailContentBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrExecutableEmailContentBlocked event data.

  An attack surface reduction rule blocked executable content from 
  an email client and or webmail.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrexecutableemailcontentblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrExecutableEmailContentBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrExecutableOfficeContentBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrExecutableOfficeContentBlocked event data.

  An attack surface reduction rule blocked an Office application 
  from creating executable content.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrexecutableofficecontentblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrExecutableOfficeContentBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrLsassCredentialTheftBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrLsassCredentialTheftBlocked event data.

  An attack surface reduction rule blocked possible credential theft 
  from lsass.exe.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrlsasscredentialtheftblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrLsassCredentialTheftBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrObfuscatedScriptBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrObfuscatedScriptBlocked event data.

  An attack surface reduction rule blocked the execution of scripts 
  that appear obfuscated.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrobfuscatedscriptblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrObfuscatedScriptBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrOfficeChildProcessBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrOfficeChildProcessBlocked event data.

  An attack surface reduction rule blocked an Office application from 
  creating child processes.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrofficechildprocessblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrOfficeChildProcessBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrOfficeCommAppChildProcessBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrOfficeCommAppChildProcessBlocked event data.

  An attack surface reduction rule blocked an Office communication app 
  from spawning a child process.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrofficecommappchildprocessblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrOfficeCommAppChildProcessBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrOfficeMacroWin32ApiCallsBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrOfficeMacroWin32ApiCallsBlocked event data.

  An attack surface reduction rule blocked Win32 API calls from Office macros.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrofficemacrowin32apicallsblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrOfficeMacroWin32ApiCallsBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrOfficeProcessInjectionBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrOfficeProcessInjectionBlocked event data.

  An attack surface reduction rule blocked an Office application from 
  injecting code into other processes.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrofficeprocessinjectionblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrOfficeProcessInjectionBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrPersistenceThroughWmiBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrPersistenceThroughWmiBlocked event data.

  An attack surface reduction rule blocked an attempt to establish persistence 
  through WMI event subscription.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrpersistencethroughwmiblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrPersistenceThroughWmiBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrPsexecWmiChildProcessBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrPsexecWmiChildProcessBlocked event data.

  An attack surface reduction rule blocked the use of PsExec or WMI commands 
  to spawn a child process.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrpsexecwmichildprocessblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrPsexecWmiChildProcessBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrRansomwareBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrRansomwareBlocked event data.

  An attack surface reduction rule blocked ransomware activity.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrransomwareblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrRansomwareBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrScriptExecutableDownloadBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrScriptExecutableDownloadBlocked event data.

  An attack surface reduction rule blocked JavaScript or VBScript code 
  from launching downloaded executable content.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrscriptexecutabledownloadblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrScriptExecutableDownloadBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrUntrustedExecutableBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrUntrustedExecutableBlocked event data.

  An attack surface reduction rule blocked the execution of an untrusted 
  file that doesn't meet criteria for age or prevalence.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asruntrustedexecutableblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrUntrustedExecutableBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrUntrustedUsbProcessBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrUntrustedUsbProcessBlocked event data.

  An attack surface reduction rule blocked the execution of an untrusted 
  and unsigned processes from a USB device.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asruntrustedusbprocessblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrUntrustedUsbProcessBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHAsrVulnerableSignedDriverBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender AsrVulnerableSignedDriverBlocked event data.

  An attack surface reduction rule blocked a signed driver that 
  has known vulnerabilities.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:asrvulnerablesigneddriverblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHAsrVulnerableSignedDriverBlockedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.additionalfields = None

class DefenderAHBrowserLaunchedToOpenUrlEventData(
  DefenderAHCommonEventData):
  """M365 Defender BrowserLaunchedToOpenUrl event data.

  A web browser opened a URL that originated as a link in another application.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteurl (str): URL or fully qualified domain name (FQDN) 
      that was being connected to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:browserlaunchedtoopenurl'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHBrowserLaunchedToOpenUrlEventData,
      self).__init__()
    self.remoteurl = None

class DefenderAHClickAllowedEventData(
  events.EventData):
  """M365 Defender ClickAllowed event data.

  The user was allowed to navigate to the URL.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    url (str): The full URL that was clicked on by the user
    workload (str): The application from which the user clicked on the link, 
      with the values being Email, Office, and Teams
    ipaddress (str): Public IP address of the device from which 
      the user clicked on the link
    urlchain (str): For scenarios involving redirections, it includes URLs 
      present in the redirection chain
  """

  DATA_TYPE = 'm365:defenderah:clickallowed'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHClickAllowedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.url = None
    self.workload = None
    self.ipaddress = None
    self.urlchain = None

class DefenderAHClickBlockedEventData(
  events.EventData):
  """M365 Defender ClickBlocked event data.

  The user was blocked from navigating to the URL.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    url (str): The full URL that was clicked on by the user
    workload (str): The application from which the user clicked on the link, 
      with the values being Email, Office, and Teams
    ipaddress (str): Public IP address of the device from which 
      the user clicked on the link
    urlchain (str): For scenarios involving redirections, it includes URLs 
      present in the redirection chain
    threattypes (str): Verdict at the time of click, which tells whether 
      the URL led to malware, phish or other threats
    detectionmethods (str): Detection technology that was used to identify 
      the threat at the time of click
  """

  DATA_TYPE = 'm365:defenderah:clickblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHClickBlockedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.url = None
    self.workload = None
    self.ipaddress = None
    self.urlchain = None
    self.threattypes = None
    self.detectionmethods = None

class DefenderAHClickBlockedByTenantPolicyEventData(
  events.EventData):
  """M365 Defender ClickBlockedByTenantPolicy event data.

  The user was blocked from navigating to the URL by a tenant policy.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    url (str): The full URL that was clicked on by the user
    workload (str): The application from which the user clicked on the link, 
      with the values being Email, Office, and Teams
    ipaddress (str): Public IP address of the device from which 
      the user clicked on the link
    urlchain (str): For scenarios involving redirections, it includes URLs 
      present in the redirection chain
  """

  DATA_TYPE = 'm365:defenderah:clickblockedbytenantpolicy'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHClickBlockedByTenantPolicyEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.url = None
    self.workload = None
    self.ipaddress = None
    self.urlchain = None

class DefenderAHConnectionFailedEventData(
  DefenderAHCommonEventData):
  """M365 Defender ConnectionFailed event data.

  An attempt to establish a network connection from the device failed.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    remoteurl (str): URL or fully qualified domain name (FQDN) 
      that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:connectionfailed'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHConnectionFailedEventData,
      self).__init__()
    self.remoteip = None
    self.remoteport = None
    self.remoteurl = None
    self.localip = None
    self.localport = None
    self.protocol = None

class DefenderAHConnectionFoundEventData(
  DefenderAHCommonEventData):
  """M365 Defender ConnectionFound event data.

  An active network connection was found on the device.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    remoteurl (str): URL or fully qualified domain name (FQDN) 
      that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:connectionfound'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHConnectionFoundEventData,
      self).__init__()
    self.remoteip = None
    self.remoteport = None
    self.remoteurl = None
    self.localip = None
    self.localport = None
    self.protocol = None

class DefenderAHConnectionRequestEventData(
  DefenderAHCommonEventData):
  """M365 Defender ConnectionRequest event data.

  The device initiated a network connection.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    remoteurl (str): URL or fully qualified domain name (FQDN) 
      that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:connectionrequest'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHConnectionRequestEventData,
      self).__init__()
    self.remoteip = None
    self.remoteport = None
    self.remoteurl = None
    self.localip = None
    self.localport = None
    self.protocol = None

class DefenderAHConnectionSuccessEventData(
  DefenderAHCommonEventData):
  """M365 Defender ConnectionSuccess event data.

  A network connection was successfully established from the device.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    remoteurl (str): URL or fully qualified domain name (FQDN) 
      that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:connectionsuccess'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHConnectionSuccessEventData,
      self).__init__()
    self.remoteip = None
    self.remoteport = None
    self.remoteurl = None
    self.localip = None
    self.localport = None
    self.protocol = None

class DefenderAHDnsConnectionInspectedEventData(
  events.EventData):
  """M365 Defender DnsConnectionInspected event data.

  The deep packet inspection engine in Microsoft Defender for Endpoint 
  inspected a DNS connection.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    dnsquery (str): Inspected DNS query
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:dnsconnectioninspected'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHDnsConnectionInspectedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None
    self.protocol = None
    self.dnsquery = None
    self.additionalfields = None

class DefenderAHDnsQueryResponseEventData(
  DefenderAHCommonEventData):
  """M365 Defender DnsQueryResponse event data.

  A response to a DNS query was sent.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    dnsquery (str): DNS query
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:dnsqueryresponse'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHDnsQueryResponseEventData,
      self).__init__()
    self.dnsquery = None
    self.additionalfields = None

class DefenderAHFileCreatedEventData(
  DefenderAHCommonEventData):
  """M365 Defender FileCreated event data.

  A file was created on the device.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    fileoriginurl (str): URL where the file was downloaded from
    fileoriginreferrerurl (str): URL of the web page that links 
      to the downloaded file
    fileoriginip (str): IP address where the file was downloaded from
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    requestprotocol (str): Network protocol, if applicable, used to initiate 
      the activity: Unknown, Local, SMB, or NFS
    requestsourceip (str): IPv4 or IPv6 address of the remote device 
      that initiated the activity
    requestsourceport (str): Source port on the remote device 
      that initiated the activity
    requestaccountname (str): User name of account used to remotely 
      initiate the activity
    requestaccountdomain (str): Domain of the account used to remotely 
      initiate the activity    
    sharename (str): Name of shared folder containing the file
    additionalfields (str): Additional information about the entity or event
  """

  DATA_TYPE = 'm365:defenderah:filecreated'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHFileCreatedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.fileoriginurl = None
    self.fileoriginreferrerurl = None
    self.fileoriginip = None
    self.requestprotocol = None
    self.requestsourceip = None
    self.requestsourceport = None
    self.requestaccountname = None
    self.requestaccountdomain = None
    self.sharename = None
    self.additionalfields = None

class DefenderAHFileDeletedEventData(
  DefenderAHCommonEventData):
  """M365 Defender FileDeleted event data.

  A file was deleted.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    fileoriginurl (str): URL where the file was downloaded from
    fileoriginreferrerurl (str): URL of the web page that links 
      to the downloaded file
    fileoriginip (str): IP address where the file was downloaded from
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    requestprotocol (str): Network protocol, if applicable, used to initiate 
      the activity: Unknown, Local, SMB, or NFS
    requestsourceip (str): IPv4 or IPv6 address of the remote device 
      that initiated the activity
    requestsourceport (str): Source port on the remote device 
      that initiated the activity
    requestaccountname (str): User name of account used to remotely 
      initiate the activity
    requestaccountdomain (str): Domain of the account used to remotely 
      initiate the activity    
    sharename (str): Name of shared folder containing the file
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:filedeleted'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHFileDeletedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.fileoriginurl = None
    self.fileoriginreferrerurl = None
    self.fileoriginip = None
    self.requestprotocol = None
    self.requestsourceip = None
    self.requestsourceport = None
    self.requestaccountname = None
    self.requestaccountdomain = None
    self.sharename = None
    self.additionalfields = None

class DefenderAHFileModifiedEventData(
  DefenderAHCommonEventData):
  """M365 Defender FileModified event data.

  A file on the device was modified.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    fileoriginurl (str): URL where the file was downloaded from
    fileoriginreferrerurl (str): URL of the web page that links 
      to the downloaded file
    fileoriginip (str): IP address where the file was downloaded from
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    requestprotocol (str): Network protocol, if applicable, used to initiate 
      the activity: Unknown, Local, SMB, or NFS
    requestsourceip (str): IPv4 or IPv6 address of the remote device 
      that initiated the activity
    requestsourceport (str): Source port on the remote device 
      that initiated the activity
    requestaccountname (str): User name of account used to remotely 
      initiate the activity
    requestaccountdomain (str): Domain of the account used to remotely 
      initiate the activity    
    sharename (str): Name of shared folder containing the file
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:filemodified'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHFileModifiedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.fileoriginurl = None
    self.fileoriginreferrerurl = None
    self.fileoriginip = None
    self.requestprotocol = None
    self.requestsourceip = None
    self.requestsourceport = None
    self.requestaccountname = None
    self.requestaccountdomain = None
    self.sharename = None
    self.additionalfields = None

class DefenderAHFileRenamedEventData(
  DefenderAHCommonEventData):
  """M365 Defender FileRenamed event data.

  A file on the device was renamed.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    fileoriginurl (str): URL where the file was downloaded from
    fileoriginreferrerurl (str): URL of the web page that links 
      to the downloaded file
    fileoriginip (str): IP address where the file was downloaded from
    previousfolderpath (str): Original folder containing the file before
      the recorded action was applied
    previousfilename (str): Original name of the file that was renamed as 
      a result of the action    
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    requestprotocol (str): Network protocol, if applicable, used to initiate 
      the activity: Unknown, Local, SMB, or NFS
    requestsourceip (str): IPv4 or IPv6 address of the remote device 
      that initiated the activity
    requestsourceport (str): Source port on the remote device 
      that initiated the activity
    requestaccountname (str): User name of account used to remotely 
      initiate the activity
    requestaccountdomain (str): Domain of the account used to remotely 
      initiate the activity    
    sharename (str): Name of shared folder containing the file
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:filerenamed'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHFileRenamedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.fileoriginurl = None
    self.fileoriginreferrerurl = None
    self.fileoriginip = None
    self.previousfolderpath = None
    self.previousfilename = None
    self.requestprotocol = None
    self.requestsourceip = None
    self.requestsourceport = None
    self.requestaccountname = None
    self.requestaccountdomain = None
    self.sharename = None
    self.additionalfields = None

class DefenderAHFirewallInboundConnectionBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender FirewallInboundConnectionBlocked event data.

  A firewall or another application blocked an inbound connection using 
  the Windows Filtering Platform.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:firewallinboundconnectionblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHFirewallInboundConnectionBlockedEventData,
      self).__init__()
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None

class DefenderAHFirewallInboundConnectionToAppBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender FirewallInboundConnectionToAppBlocked event data.

  The firewall blocked an inbound connection to an app.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:firewallinboundconnectiontoappblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHFirewallInboundConnectionToAppBlockedEventData,
      self).__init__()
    self.additionalfields = None

class DefenderAHFirewallOutboundConnectionBlockedEventData(
  DefenderAHCommonEventData):
  """M365 Defender FirewallInboundConnectionBlocked event data.

  A firewall or another application blocked an outbound connection using 
  the Windows Filtering Platform.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:firewalloutboundconnectionblocked'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHFirewallOutboundConnectionBlockedEventData,
      self).__init__()
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None

class DefenderAHFirewallServiceStoppedEventData(
  DefenderAHCommonEventData):
  """M365 Defender FirewallServiceStopped event data.

  The firewall service was stopped.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:firewallservicestopped'

class DefenderAHFtpConnectionInspectedEventData(
  events.EventData):
  """M365 Defender FtpConnectionInspected event data.

  The deep packet inspection engine in Microsoft Defender for Endpoint 
  inspected an FTP connection.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    direction (str): Direction of communication
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:ftpconnectioninspected'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHFtpConnectionInspectedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None
    self.protocol = None
    self.direction = None
    self.additionalfields = None

class DefenderAHGetClipboardDataEventData(
  DefenderAHCommonEventData):
  """M365 Defender GetClipboardData event data.

  The GetClipboardData function was called. This function can be used obtain 
  the contents of the system clipboard.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:getclipboarddata'

class DefenderAHHttpConnectionInspectedEventData(
  events.EventData):
  """M365 Defender HttpConnectionInspected event data.

  The deep packet inspection engine in Microsoft Defender for Endpoint 
  inspected an HTTP connection.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    host (str): Server hostname
    direction (str): Direction of communication
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:httpconnectioninspected'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHHttpConnectionInspectedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None
    self.protocol = None
    self.host = None
    self.direction = None
    self.additionalfields = None

class DefenderAHIcmpConnectionInspectedEventData(
  events.EventData):
  """M365 Defender IcmpConnectionInspected event data.

  The deep packet inspection engine in Microsoft Defender for Endpoint 
  inspected an ICMP connection.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    protocol (str): Protocol used during the communication
    direction (str): Direction of communication
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:icmpconnectioninspected'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHIcmpConnectionInspectedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.remoteip = None
    self.localip = None
    self.protocol = None
    self.direction = None
    self.additionalfields = None

class DefenderAHImageLoadedEventData(
  DefenderAHCommonEventData):
  """M365 Defender ImageLoaded event data.

  A dynamic link library (DLL) was loaded.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:imageloaded'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHImageLoadedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None

class DefenderAHInboundConnectionAcceptedEventData(
  events.EventData):
  """M365 Defender InboundConnectionAccepted event data.

  The device accepted a network connection initiated by another device.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
  """

  DATA_TYPE = 'm365:defenderah:inboundconnectionaccepted'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHInboundConnectionAcceptedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None
    self.protocol = None

class DefenderAHInboundInternetScanInspectedEventData(
  events.EventData):
  """M365 Defender InboundInternetScanInspected event data.

  An incoming packet from a Microsoft Defender External Attack Surface 
  Management scan was inspected on the device.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:inboundinternetscaninspected'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHInboundInternetScanInspectedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None
    self.protocol = None
    self.additionalfields = None

class DefenderAHListeningConnectionCreatedEventData(
  DefenderAHCommonEventData):
  """M365 Defender ListeningConnectionCreated event data.

  A process has started listening for connections on a certain port.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:listeningconnectioncreated'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHListeningConnectionCreatedEventData,
      self).__init__()
    self.localip = None
    self.localport = None
    self.protocol = None

class DefenderAHLogonAttemptedEventData(
  DefenderAHCommonEventData):
  """M365 Defender LogonAttempted event data.

  A user attempted to log on to the device.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    logontype (str): Type of logon session
    accountdomain (str): Domain of the account
    accountname (str): User name of the account
    protocol (str): Protocol used during the communication
    remotedevicename (str): Name of the machine that performed a remote 
      operation on the affected machine. Depending on the event being reported,
      this name could be a fully-qualified domain name (FQDN), a NetBIOS name 
      or a host name without domain information
    remoteip (str): IP address of the device from which the 
      logon attempt was performed
    remoteport (str): TCP port on the remote device that was being connected to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:logonattempted'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHLogonAttemptedEventData,
      self).__init__()
    self.logontype = None
    self.accountdomain = None
    self.accountname = None
    self.protocol = None
    self.remotedevicename = None
    self.remoteip = None
    self.remoteport = None
    self.additionalfields = None

class DefenderAHLogonFailedEventData(
  DefenderAHCommonEventData):
  """M365 Defender LogonFailed event data.

  A user attempted to logon to the device but failed.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    logontype (str): Type of logon session
    accountdomain (str): Domain of the account
    accountname (str): User name of the account
    protocol (str): Protocol used during the communication
    failurereason (str): Information explaining why the recorded action failed
    remotedevicename (str): Name of the machine that performed a remote 
      operation on the affected machine. Depending on the event being reported,
      this name could be a fully-qualified domain name (FQDN), a NetBIOS name 
      or a host name without domain information
    remoteip (str): IP address of the device from which the 
      logon attempt was performed
    remoteport (str): TCP port on the remote device that was being connected to    
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:logonfailed'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHLogonFailedEventData,
      self).__init__()
    self.logontype = None
    self.accountdomain = None
    self.accountname = None
    self.protocol = None
    self.failurereason = None
    self.remotedevicename = None
    self.remoteip = None
    self.remoteport = None
    self.additionalfields = None

class DefenderAHLogonSuccessEventData(
  DefenderAHCommonEventData):
  """M365 Defender LogonSuccess event data.

  A user successfully logged on to the device.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    logontype (str): Type of logon session
    accountdomain (str): Domain of the account
    accountname (str): User name of the account
    protocol (str): Protocol used during the communication
    remotedevicename (str): Name of the machine that performed a remote 
      operation on the affected machine. Depending on the event being reported,
      this name could be a fully-qualified domain name (FQDN), a NetBIOS name 
      or a host name without domain information
    remoteip (str): IP address of the device from which the 
      logon attempt was performed
    remoteport (str): TCP port on the remote device that was being connected to    
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:logonsuccess'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHLogonSuccessEventData,
      self).__init__()
    self.logontype = None
    self.accountdomain = None
    self.accountname = None
    self.protocol = None
    self.remotedevicename = None
    self.remoteip = None
    self.remoteport = None
    self.additionalfields = None

class DefenderAHNetworkProtectionUserBypassEventEventData(
  DefenderAHCommonEventData):
  """M365 Defender NetworkProtectionUserBypassEvent event data.

  A user has bypassed network protection and accessed 
  a blocked IP address, domain, or URL.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:networkprotectionuserbypassevent'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHNetworkProtectionUserBypassEventEventData,
      self).__init__()
    self.additionalfields = None

class DefenderAHNetworkShareObjectAddedEventData(
  DefenderAHCommonEventData):
  """M365 Defender NetworkShareObjectAdded event data.

  A file or folder was shared on the network.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:networkshareobjectadded'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHNetworkShareObjectAddedEventData,
      self).__init__()
    self.additionalfields = None

class DefenderAHNetworkSignatureInspectedEventData(
  events.EventData):
  """M365 Defender NetworkSignatureInspected event data.

  A packet content was inspected.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:networksignatureinspected'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHNetworkSignatureInspectedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None
    self.additionalfields = None

class DefenderAHNtlmAuthenticationInspectedEventData(
  events.EventData):
  """M365 Defender NtlmAuthenticationInspected event data.

  The deep packet inspection engine in Microsoft Defender for Endpoint 
  inspected a connection with NTLM authentication.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    direction (str): Direction of communication
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:ntlmauthenticationinspected'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHNtlmAuthenticationInspectedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None
    self.protocol = None
    self.direction = None
    self.additionalfields = None

class DefenderAHOpenProcessEventData(
  DefenderAHCommonEventData):
  """M365 Defender OpenProcess event data.
  
  The OpenProcess function was called indicating an attempt to open a handle to
  a local process and potentially manipulate that process.

  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:openprocess'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHOpenProcessEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None

class DefenderAHPowerShellCommandEventData(
  DefenderAHCommonEventData):
  """M365 Defender PowerShellCommand event data.

  A PowerShell alias function filter cmdlet external script application script 
  workflow or configuration was executed from a PowerShell host process.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    pscommand (str): Executed command
  """

  DATA_TYPE = 'm365:defenderah:powershellcommand'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHPowerShellCommandEventData,
      self).__init__()
    self.pscommand = None

class DefenderAHProcessCreatedEventData(
  DefenderAHCommonEventData):
  """M365 Defender ProcessCreated event data.

  A process was launched on the device.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    sha1 (str): SHA-1 of the file that the recorded action was applied to
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    processid (str): Process ID (PID) of the newly created process
    processcommandline (str): Command line used to create the new process
    accountdomain (str): Domain of the account
    accountname (str): User name of the account
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:processcreated'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHProcessCreatedEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.sha1 = None
    self.sha256 = None
    self.processid = None
    self.processcommandline = None
    self.processcreationtime = None
    self.accountdomain = None
    self.accountname = None

class DefenderAHProcessCreatedUsingWmiQueryEventData(
  events.EventData):
  """M365 Defender ProcessCreatedUsingWmiQuery event data.

  A process was created using Windows Management Instrumentation (WMI).
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:processcreatedusingwmiquery'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHProcessCreatedUsingWmiQueryEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.initiatingprocessaccountdomain = None
    self.initiatingprocessaccountname = None
    self.additionalfields = None

class DefenderAHRegistryKeyCreatedEventData(
  DefenderAHCommonEventData):
  """M365 Defender RegistryKeyCreated event data.

  A registry key was created.
  
  Attributes: 
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    registrykey (str): Registry key that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:registrykeycreated'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHRegistryKeyCreatedEventData,
      self).__init__()
    self.registrykey = None

class DefenderAHRegistryKeyDeletedEventData(
  DefenderAHCommonEventData):
  """M365 Defender RegistryKeyDeleted event data.

  A registry key was deleted.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    previousregistrykey (str): Original registry key of the registry
      value before it was modified
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:registrykeydeleted'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHRegistryKeyDeletedEventData,
      self).__init__()
    self.previousregistrykey = None

class DefenderAHRegistryKeyRenamedEventData(
  DefenderAHCommonEventData):
  """M365 Defender RegistryKeyRenamed event data.

  A registry key was renamed.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    registrykey (str): Registry key that the recorded action was applied to
    previousregistrykey (str): Original registry key of the registry
      value before it was modified
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:registrykeyrenamed'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHRegistryKeyRenamedEventData,
      self).__init__()
    self.registrykey = None
    self.previousregistrykey = None

class DefenderAHRegistryValueDeletedEventData(
  DefenderAHCommonEventData):
  """M365 Defender RegistryValueDeleted event data.

  A registry value was deleted.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    previousregistrykey (str): Original registry key of the registry
      value before it was modified
    previousregistryvaluename (str): Original name of the registry 
      value before it was modified
    previousregistryvaluedata (str): Original data of the registry 
      value before it was modified
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:registryvaluedeleted'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHRegistryValueDeletedEventData,
      self).__init__()
    self.previousregistrykey = None
    self.previousregistryvaluename = None
    self.previousregistryvaluedata = None

class DefenderAHRegistryValueSetEventData(
  DefenderAHCommonEventData):
  """M365 Defender RegistryValueSet event data.

  The data for a registry value was modified.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    registrykey (str): Registry key that the recorded action was applied to
    registryvaluename (str): Name of the registry value that 
      the recorded action was applied to
    registryvaluedata (str): Data of the registry value that 
      the recorded action was applied to
    previousregistryvaluename (str): Original name of the registry 
      value before it was modified
    previousregistryvaluedata (str): Original data of the registry 
      value before it was modified
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:registryvalueset'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHRegistryValueSetEventData,
      self).__init__()
    self.registrykey = None
    self.registryvaluename = None
    self.registryvaluedata = None
    self.previousregistryvaluename = None
    self.previousregistryvaluedata = None

class DefenderAHRemoteDesktopConnectionEventData(
  events.EventData):
  """M365 Defender RemoteDesktopConnection event data.

  A Remote Desktop connection was established.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:remotedesktopconnection'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHRemoteDesktopConnectionEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.localip = None
    self.localport = None
    self.additionalfields = None

class DefenderAHRemoteWmiOperationEventData(
  DefenderAHCommonEventData):
  """M365 Defender RemoteWmiOperation event data.

  A Windows Management Instrumentation (WMI) operation was 
  initiated from a remote device.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remotedevicename (str): Name of the machine that performed a remote 
      operation on the affected machine. Depending on the event being reported,
      this name could be a fully-qualified domain name (FQDN), a NetBIOS name 
      or a host name without domain information
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:remotewmioperation'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHRemoteWmiOperationEventData,
      self).__init__()
    self.remotedevicename = None
    self.additionalfields = None

class DefenderAHScheduledTaskCreatedEventData(
  DefenderAHCommonEventData):
  """M365 Defender ScheduledTaskCreated event data.

  A scheduled task was created.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    taskname (str): Name of scheduled task
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:scheduledtaskcreated'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHScheduledTaskCreatedEventData,
      self).__init__()
    self.taskname = None
    self.additionalfields = None

class DefenderAHScreenshotTakenEventData(
  DefenderAHCommonEventData):
  """M365 Defender ScreenshotTaken event data.

  A screenshot was taken.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
  """

  DATA_TYPE = 'm365:defenderah:screenshottaken'

class DefenderAHScriptContentEventData(
  events.EventData):
  """M365 Defender ScriptContent event data.

  The content of script.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    sha256 (str): SHA-256 of the file that the recorded action was applied to
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    scriptcontent (str): Content of the script
  """

  DATA_TYPE = 'm365:defenderah:scriptcontent'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHScriptContentEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.sha256 = None
    self.initiatingprocessid = None
    self.scriptcontent = None

class DefenderAHSecurityGroupCreatedEventData(
  events.EventData):
  """M365 Defender SecurityGroupCreated event data.

  A security group was created.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    groupname (str): Name of created security group
  """

  DATA_TYPE = 'm365:defenderah:securitygroupcreated'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHSecurityGroupCreatedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.initiatingprocessaccountdomain = None
    self.initiatingprocessaccountname = None
    self.initiatingprocessid = None
    self.initiatingprocessparentid = None
    self.groupname = None

class DefenderAHSecurityLogClearedEventData(
  events.EventData):
  """M365 Defender SecurityLogCleared event data.

  The security log was cleared.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
  """

  DATA_TYPE = 'm365:defenderah:securitylogcleared'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHSecurityLogClearedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.initiatingprocessaccountdomain = None
    self.initiatingprocessaccountname = None

class DefenderAHServiceInstalledEventData(
  DefenderAHCommonEventData):
  """M365 Defender ServiceInstalled event data.

  A service was installed. This is based on Windows event ID 4697, 
  which requires the advanced security audit setting 
  Audit Security System Extension.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    servicename (str): Name of installed service
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:serviceinstalled'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHServiceInstalledEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.servicename = None
    self.additionalfields = None

class DefenderAHSmartScreenAppWarningEventData(
  DefenderAHCommonEventData):
  """M365 Defender SmartScreenAppWarning event data.

  SmartScreen warned about running a downloaded application 
  that is untrusted or malicious.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:smartscreenappwarning'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHSmartScreenAppWarningEventData,
      self).__init__()
    self.filename = None
    self.additionalfields = None

class DefenderAHSmartScreenExploitWarningEventData(
  DefenderAHCommonEventData):
  """M365 Defender SmartScreenExploitWarning event data.

  SmartScreen warned about opening a web page that contains an exploit.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteurl (str): URL or fully qualified domain name (FQDN) 
      that was being connected to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:smartscreenexploitwarning'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHSmartScreenExploitWarningEventData,
      self).__init__()
    self.remoteurl = None
    self.additionalfields = None

class DefenderAHSmartScreenUrlWarningEventData(
  DefenderAHCommonEventData):
  """M365 Defender SmartScreenUrlWarning event data.

  SmartScreen warned about opening a low-reputation URL that might be hosting 
  malware or is a phishing site.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteurl (str): URL or fully qualified domain name (FQDN) 
      that was being connected to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:smartscreenurlwarning'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHSmartScreenUrlWarningEventData,
      self).__init__()
    self.remoteurl = None
    self.additionalfields = None

class DefenderAHSmtpConnectionInspectedEventData(
  events.EventData):
  """M365 Defender SmtpConnectionInspected event data.

  The deep packet inspection engine in Microsoft Defender for Endpoint 
  inspected an SMTP connection.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    direction (str): Direction of communication
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:smtpconnectioninspected'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHSmtpConnectionInspectedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None
    self.protocol = None
    self.direction = None
    self.additionalfields = None

class DefenderAHSshConnectionInspectedEventData(
  events.EventData):
  """M365 Defender SshConnectionInspected event data.

  The deep packet inspection engine in Microsoft Defender for Endpoint 
  inspected an SSH connection. 
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    direction (str): Direction of communication
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:sshconnectioninspected'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHSshConnectionInspectedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None
    self.protocol = None
    self.direction = None
    self.additionalfields = None

class DefenderAHSslConnectionInspectedEventData(
  events.EventData):
  """M365 Defender SslConnectionInspected event data.

  The deep packet inspection engine in Microsoft Defender for Endpoint 
  inspected an SSL connection. 
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    remoteip (str): IP address that was being connected to
    remoteport (str): TCP port on the remote device that was being connected to
    localip (str): Source IP, or the IP address where 
      the communication came from
    localport (str): TCP port on the local machine used during communication
    protocol (str): Protocol used during the communication
    server_name (str): Server hostname
    direction (str): Direction of communication
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:sslconnectioninspected'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHSslConnectionInspectedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.remoteip = None
    self.remoteport = None
    self.localip = None
    self.localport = None
    self.protocol = None
    self.server_name = None
    self.direction = None
    self.additionalfields = None

class DefenderAHTamperingAttemptEventData(
  DefenderAHCommonEventData):
  """M365 Defender TamperingAttempt event data.

  An attempt to change Microsoft Defender 365 settings was made.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    filename (str): Name of the file that the recorded action was applied to
    folderpath (str): Folder containing the file that the recorded action
      was applied to
    registrykey (str): Registry key that the recorded action was applied to
    registryvaluename (str): Name of the registry value that 
      the recorded action was applied to
    registryvaluedata (str): Data of the registry value that 
      the recorded action was applied to
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    initiatingprocesssha1 (str): SHA-1 of the process (image file)
      that initiated the event
    initiatingprocesssha256 (str): SHA-256 of the process (image file)
      that initiated the event
    initiatingprocessfilename (str): Name of the process
      that initiated the event
    initiatingprocessid (str): Process ID (PPID) of the process
      that initiated the event
    initiatingprocesscommandline (str): Command line used to run the process
      that initiated the event
    initiatingprocesscreationtime (str): Date and time when the process
      that initiated the event was started
    initiatingprocessfolderpath (str): Folder containing the process
      (image file) that initiated the event
    initiatingprocessparentid (str): Process ID (PPPID) of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentfilename (str): Name of the parent process
      that spawned the process responsible for the event
    initiatingprocessparentcreationtime (str): Date and time when the parent
      of the process responsible for the event was started
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:tamperingattempt'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHTamperingAttemptEventData,
      self).__init__()
    self.filename = None
    self.folderpath = None
    self.registrykey = None
    self.registryvaluename = None
    self.registryvaluedata = None
    self.additionalfields = None

class DefenderAHUntrustedWifiConnectionEventData(
  events.EventData):
  """M365 Defender UntrustedWifiConnection event data.

  A connection was established to an open Wi-Fi access point 
  that is set to connect automatically.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:untrustedwificonnection'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHUntrustedWifiConnectionEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.additionalfields = None

class DefenderAHUrlErrorPageEventData(
  events.EventData):
  """M365 Defender UrlErrorPage event data.

  The URL the user clicked showed an error page.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    url (str): The full URL that was clicked on by the user
    workload (str): The application from which the user clicked on the link, 
      with the values being Email, Office, and Teams
    ipaddress (str): Public IP address of the device from which the user 
      clicked on the link
    urlchain (str): For scenarios involving redirections, it includes URLs 
      present in the redirection chain
  """

  DATA_TYPE = 'm365:defenderah:urlerrorpage'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHUrlErrorPageEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.url = None
    self.workload = None
    self.ipaddress = None
    self.urlchain = None

class DefenderAHUrlScanInProgressEventData(
  events.EventData):
  """M365 Defender UrlScanInProgress event data.

  The URL the user clicked is being scanned by Safe Links.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    url (str): The full URL that was clicked on by the user
    workload (str): The application from which the user clicked on the link, 
      with the values being Email, Office, and Teams
    ipaddress (str): Public IP address of the device from which the user 
      clicked on the link
    urlchain (str): For scenarios involving redirections, it includes URLs 
      present in the redirection chain
  """

  DATA_TYPE = 'm365:defenderah:urlscaninprogress'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHUrlScanInProgressEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.url = None
    self.workload = None
    self.ipaddress = None
    self.urlchain = None

class DefenderAHUserAccountAddedToLocalGroupEventData(
  events.EventData):
  """M365 Defender UserAccountAddedToLocalGroup event data.

  A user was added to a security-enabled local group.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    groupdomainname (str): Domain of the group
    groupname (str): Name of the group
    additionalfields (str): Additional information about 
      the event in JSON array format
  """

  DATA_TYPE = 'm365:defenderah:useraccountaddedtolocalgroup'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHUserAccountAddedToLocalGroupEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.initiatingprocessaccountdomain = None
    self.initiatingprocessaccountname = None
    self.groupdomainname = None
    self.groupname = None
    self.additionalfields = None

class DefenderAHUserAccountCreatedEventData(
  events.EventData):
  """M365 Defender UserAccountCreated event data.

  A local SAM account or a domain account was created.
  
  Attributes:
    timestamp (dfdatetime.DateTimeValues): Date and time when
      the event was recorded
    initiatingprocessaccountdomain (str): Domain of the account
      that ran the process responsible for the event
    initiatingprocessaccountname (str): User name of the account
      that ran the process responsible for the event
    accountdomain (str): Domain of the account
    accountname (str): User name of the account
  """

  DATA_TYPE = 'm365:defenderah:useraccountcreated'

  def __init__(self):
    """Initializes event data."""
    super(
      DefenderAHUserAccountCreatedEventData,
      self).__init__(
        data_type=self.DATA_TYPE)
    self.timestamp = None
    self.initiatingprocessaccountdomain = None
    self.initiatingprocessaccountname = None
    self.accountdomain = None
    self.accountname = None
