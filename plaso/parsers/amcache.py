# -*- coding: utf-8 -*-
"""File containing a Windows Registry plugin to parse the Amcache Hive."""

from __future__ import unicode_literals
import pyregf

from dfdatetime import filetime
from dfdatetime import posix_time
from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import interface
from plaso.parsers import manager

__author__ = 'Ramses de Beer, rbdebeer@google.com'

class AmcacheEventData(events.EventData):
  """Amcache event data.

  Attributes:
    full_path (str): full path of file
    sha1 (str): sha1 of file
    productname (str): product name file belongs to
    companyname (str): company name that created product file belogs to
    fileversion (str): version of file
    languagecode (int): language code of file
    filesize (int): size of file in bytes
    filedescription (str): description of file
    linkerts (int): unix timestamp when file was linked
    lastmodifiedts (int): filetime timestamp of last modified datetime of file
    createdtd (int): filetime timestamp of created datetime of file
    programid (str): GUID of entry under Root/Program key file belongs to
  """

  DATA_TYPE = 'windows:registry:amcache'

  def __init__(self):
    """Initializes event data."""
    super(AmcacheEventData, self).__init__(data_type=self.DATA_TYPE)
    self.full_path = None
    self.sha1 = None
    self.productname = None
    self.companyname = None
    self.fileversion = None
    self.languagecode = None
    self.filesize = None
    self.filedescription = None
    self.linkerts = None
    self.lastmodifiedts = None
    self.createdts = None
    self.programid = None

class AmcacheProgramEventData(events.EventData):
  """Amcache programs event data.

  Attributes:
    name (str): name of installed program
    version (str): version of program
    publisher (str): publisher of program
    languagecode (int): languagecode of program
    entrytype (str): type of entry (usually AddRemoveProgram)
    uninstallkey (str): unicode string of uninstall registry key for program
    filepath (str): file path of installed program
    productcode (str): product code of program
    packagecode (str): package code of program
    msiproductcode (str): MSI product code of program
    msipackagecode (str): MSI package code of program
    files (str): list of files belonging to program
  """

  DATA_TYPE = 'windows:registry:amcache:programs'

  def __init__(self):
    """Initializes event data."""
    super(AmcacheProgramEventData, self).__init__(data_type=self.DATA_TYPE)
    self.name = None
    self.version = None
    self.publisher = None
    self.languagecode = None
    self.entrytype = None
    self.uninstallkey = None
    self.filepaths = None
    self.productcode = None
    self.packagecode = None
    self.msiproductcode = None
    self.msipackagecode = None
    self.files = None

class AmcacheParser(interface.FileObjectParser):
  """Amcache Registry plugin for recently run programs."""

  NAME = 'amcache'
  DESCRIPTION = 'Parser for Amcache Registry entries.'

  URLS = [
      ('http://www.swiftforensics.com/2013/12/'
       'amcachehve-in-windows-8-goldmine-for.html')]

  _AMCACHE_SHA1 = "101"
  _AMCACHE_DATETIME = "17"
  _AMCACHE_FULL_PATH = "15"
  _AMCACHE_ROOT_FILE_KEY = "Root\\File"
  _AMCACHE_ROOT_PROGRAM_KEY = "Root\\Programs"
  _AMCACHE_PRODUCTNAME = "0"
  _AMCACHE_COMPANYNAME = "1"
  _AMCACHE_FILEVERSION = "5"
  _AMCACHE_LANGUAGECODE = "3"
  _AMCACHE_FILESIZE = "6"
  _AMCACHE_FILEDESCRIPTION = "c"
  _AMCACHE_LINKERTS = "f"
  _AMCACHE_LASTMODIFIEDTS = "11"
  _AMCACHE_CREATEDTS = "12"
  _AMCACHE_PROGRAMID = "100"

  _AMCACHE_P_INSTALLDATE = "a"
  _AMCACHE_P_NAME = "0"
  _AMCACHE_P_VERSION = "1"
  _AMCACHE_P_PUBLISHER = "2"
  _AMCACHE_P_LANGUAGECODE = "3"
  _AMCACHE_P_ENTRYTYPE = "6"
  _AMCACHE_P_UNINSTALLKEY = "7"
  _AMCACHE_P_FILEPATHS = "d"
  _AMCACHE_P_PRODUCTCODE = "f"
  _AMCACHE_P_PACKAGECODE = "10"
  _AMCACHE_P_MSIPRODUCTCODE = "11"
  _AMCACHE_P_MSIPACKAGECODE = "12"
  _AMCACHE_P_FILES = "Files"

  #TODO Add GetFormatSpecification when issues are fixed with adding
  #     multiple parsers for the same file format (in this case regf files)
  #     AddNewSignature ->
  #     b'\x41\x00\x6d\x00\x63\x00\x61\x00\x63\x00\x68\x00\x65', offset=88

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an Amcache.hve file for events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.
    """
    regf_file = pyregf.file() # pylint: disable=no-member
    try:
      regf_file.open_file_object(file_object)
    except IOError:
      # The error is currently ignored -> see TODO above related to the
      # fixing of handling multiple parsers for the same file format.
      return

    root_key = regf_file.get_root_key()
    if root_key is None:
      regf_file.close()
      return

    root_file_key = root_key.get_sub_key_by_path(self._AMCACHE_ROOT_FILE_KEY)
    if root_file_key is None:
      regf_file.close()
      return

    for volume_key in root_file_key.sub_keys:
      for am_entry in volume_key.sub_keys:
        amcache_datetime = am_entry.get_value_by_name(
            self._AMCACHE_DATETIME).get_data_as_integer()
        event_data = AmcacheEventData()
        event_data.full_path = am_entry.get_value_by_name(
            self._AMCACHE_FULL_PATH).get_data_as_string()
        # Strip off the 4 leading zero's from the sha1 hash.
        event_data.sha1 = am_entry.get_value_by_name(
            self._AMCACHE_SHA1).get_data_as_string()[4:]
        if am_entry.get_value_by_name(self._AMCACHE_PRODUCTNAME) is not None:
          event_data.productname = am_entry.get_value_by_name(
              self._AMCACHE_PRODUCTNAME).get_data_as_string()
        if am_entry.get_value_by_name(self._AMCACHE_COMPANYNAME) is not None:
          event_data.companyname = am_entry.get_value_by_name(
              self._AMCACHE_COMPANYNAME).get_data_as_string()
        if am_entry.get_value_by_name(self._AMCACHE_FILEVERSION) is not None:
          event_data.fileversion = am_entry.get_value_by_name(
              self._AMCACHE_FILEVERSION).get_data_as_string()
        if am_entry.get_value_by_name(self._AMCACHE_LANGUAGECODE) is not None:
          event_data.languagecode = am_entry.get_value_by_name(
              self._AMCACHE_LANGUAGECODE).get_data_as_integer()
        if am_entry.get_value_by_name(self._AMCACHE_FILESIZE) is not None:
          event_data.filesize = am_entry.get_value_by_name(
              self._AMCACHE_FILESIZE).get_data_as_integer()
        if am_entry.get_value_by_name(self._AMCACHE_FILEDESCRIPTION) is not None: # pylint: disable=line-too-long
          event_data.filedescription = am_entry.get_value_by_name(
              self._AMCACHE_FILEDESCRIPTION).get_data_as_string()
        if am_entry.get_value_by_name(self._AMCACHE_LINKERTS) is not None:
          event_data.linkerts = am_entry.get_value_by_name(
              self._AMCACHE_LINKERTS).get_data_as_integer()
        if am_entry.get_value_by_name(self._AMCACHE_LASTMODIFIEDTS) is not None:
          event_data.lastmodifiedts = am_entry.get_value_by_name(
              self._AMCACHE_LASTMODIFIEDTS).get_data_as_integer()
        if am_entry.get_value_by_name(self._AMCACHE_CREATEDTS) is not None:
          event_data.createdts = am_entry.get_value_by_name(
              self._AMCACHE_CREATEDTS).get_data_as_integer()
        if am_entry.get_value_by_name(self._AMCACHE_PROGRAMID) is not None:
          event_data.programid = am_entry.get_value_by_name(
              self._AMCACHE_PROGRAMID).get_data_as_string()
        event = time_events.DateTimeValuesEvent(
            filetime.Filetime(amcache_datetime),
            definitions.TIME_DESCRIPTION_LAST_RUN)
        parser_mediator.ProduceEventWithEventData(event, event_data)
        if event_data.createdts is not None:
          event = time_events.DateTimeValuesEvent(
              filetime.Filetime(event_data.createdts),
              definitions.TIME_DESCRIPTION_CREATION)
          parser_mediator.ProduceEventWithEventData(event, event_data)
        if event_data.lastmodifiedts is not None:
          event = time_events.DateTimeValuesEvent(
              filetime.Filetime(event_data.lastmodifiedts),
              definitions.TIME_DESCRIPTION_MODIFICATION)
          parser_mediator.ProduceEventWithEventData(event, event_data)
        if event_data.linkerts is not None:
          event = time_events.DateTimeValuesEvent(
              posix_time.PosixTime(event_data.linkerts),
              definitions.TIME_DESCRIPTION_CHANGE)
          parser_mediator.ProduceEventWithEventData(event, event_data)
    root_program_key = root_key.get_sub_key_by_path(
        self._AMCACHE_ROOT_PROGRAM_KEY)
    if root_program_key is None:
      regf_file.close()
      return

    for am_entry in root_program_key.sub_keys:
      amcache_datetime = am_entry.get_value_by_name(
	         self._AMCACHE_P_INSTALLDATE).get_data_as_integer()
      pevent_data = AmcacheProgramEventData()
      if am_entry.get_value_by_name(self._AMCACHE_P_NAME) is not None:
        pevent_data.name = am_entry.get_value_by_name(
	           self._AMCACHE_P_NAME).get_data_as_string()
      if am_entry.get_value_by_name(self._AMCACHE_P_VERSION) is not None:
        pevent_data.version = am_entry.get_value_by_name(
	           self._AMCACHE_P_VERSION).get_data_as_string()
      if am_entry.get_value_by_name(self._AMCACHE_P_PUBLISHER) is not None:
        pevent_data.publisher = am_entry.get_value_by_name(
	           self._AMCACHE_P_PUBLISHER).get_data_as_string()
      if am_entry.get_value_by_name(self._AMCACHE_P_LANGUAGECODE) is not None:
        pevent_data.languagecode = am_entry.get_value_by_name(
	           self._AMCACHE_P_LANGUAGECODE).get_data_as_string()
      if am_entry.get_value_by_name(self._AMCACHE_P_ENTRYTYPE) is not None:
        pevent_data.entrytype = am_entry.get_value_by_name(
	           self._AMCACHE_P_ENTRYTYPE).get_data_as_string()
      if am_entry.get_value_by_name(self._AMCACHE_P_UNINSTALLKEY) is not None:
        pevent_data.uninstallkey = am_entry.get_value_by_name(
	           self._AMCACHE_P_UNINSTALLKEY).get_data().decode('utf-16-LE')
      if am_entry.get_value_by_name(self._AMCACHE_P_FILEPATHS) is not None:
        pevent_data.filepaths = am_entry.get_value_by_name(
	           self._AMCACHE_P_FILEPATHS).get_data().decode('utf-16-LE')
      if am_entry.get_value_by_name(self._AMCACHE_P_PRODUCTCODE) is not None:
        pevent_data.productcode = am_entry.get_value_by_name(
	           self._AMCACHE_P_PRODUCTCODE).get_data_as_string()
      if am_entry.get_value_by_name(self._AMCACHE_P_PACKAGECODE) is not None:
        pevent_data.packagecode = am_entry.get_value_by_name(
	           self._AMCACHE_P_PACKAGECODE).get_data_as_string()
      if am_entry.get_value_by_name(self._AMCACHE_P_MSIPRODUCTCODE) is not None:
        pevent_data.msiproductcode = am_entry.get_value_by_name(
	           self._AMCACHE_P_MSIPRODUCTCODE).get_data().decode('utf-16-LE')
      if am_entry.get_value_by_name(self._AMCACHE_P_MSIPACKAGECODE) is not None:
        pevent_data.msipackagecode = am_entry.get_value_by_name(
	           self._AMCACHE_P_MSIPACKAGECODE).get_data().decode('utf-16-LE')
      if am_entry.get_value_by_name(self._AMCACHE_P_FILES) is not None:
        pevent_data.files = am_entry.get_value_by_name(
	           self._AMCACHE_P_FILES).get_data()
      event = time_events.DateTimeValuesEvent(
	         posix_time.PosixTime(amcache_datetime),
	         definitions.TIME_DESCRIPTION_INSTALLATION)
      parser_mediator.ProduceEventWithEventData(event, pevent_data)

    regf_file.close()

manager.ParsersManager.RegisterParser(AmcacheParser)
