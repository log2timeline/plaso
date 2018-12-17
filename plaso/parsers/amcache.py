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


class AmcacheEventData(events.EventData):
  """Amcache event data.

  Attributes:
    full_path (str): full path of file
    sha1 (str): sha1 of file
    productname (str): product name file belongs to
    companyname (str): company name that created product file belongs to
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

  def ParseFileObject(self, parser_mediator, file_object):
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
        self._ProcessAMCacheFileKey(am_entry, parser_mediator)

    root_program_key = root_key.get_sub_key_by_path(
        self._AMCACHE_ROOT_PROGRAM_KEY)
    if root_program_key is None:
      regf_file.close()
      return

    for am_entry in root_program_key.sub_keys:
      self._ProcessAMCacheProgramKey(am_entry, parser_mediator)

    regf_file.close()

  def _ProcessAMCacheProgramKey(self, am_entry, parser_mediator):
    """Parses an Amcache Root/Programs key for events.

    Args:
      am_entry (pyregf.key): amcache Programs key.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """
    amcache_datetime = am_entry.get_value_by_name(
        self._AMCACHE_P_INSTALLDATE).get_data_as_integer()
    event_data = AmcacheProgramEventData()

    name = am_entry.get_value_by_name(self._AMCACHE_P_NAME)
    if name:
      event_data.name = name.get_data_as_string()

    version = am_entry.get_value_by_name(self._AMCACHE_P_VERSION)
    if version:
      event_data.version = version.get_data_as_string()

    publisher = am_entry.get_value_by_name(self._AMCACHE_P_PUBLISHER)
    if publisher:
      event_data.publisher = publisher.get_data_as_string()

    languagecode = am_entry.get_value_by_name(self._AMCACHE_P_LANGUAGECODE)
    if languagecode:
      event_data.languagecode = languagecode.get_data_as_string()

    entrytype = am_entry.get_value_by_name(self._AMCACHE_P_ENTRYTYPE)
    if entrytype:
      event_data.entrytype = entrytype.get_data_as_string()

    uninstallkey = am_entry.get_value_by_name(self._AMCACHE_P_UNINSTALLKEY)
    if uninstallkey:
      uninstallkey = uninstallkey.get_data()
      uninstallkey = uninstallkey.decode('utf-16-LE')
      event_data.uninstallkey = uninstallkey

    filepaths = am_entry.get_value_by_name(self._AMCACHE_P_FILEPATHS)
    if filepaths:
      filepaths = filepaths.get_data()
      filepaths = filepaths.decode('utf-16-LE')
      event_data.filepaths = filepaths

    productcode = am_entry.get_value_by_name(self._AMCACHE_P_PRODUCTCODE)
    if productcode:
      event_data.productcode = productcode.get_data_as_string()

    packagecode = am_entry.get_value_by_name(self._AMCACHE_P_PACKAGECODE)
    if packagecode:
      event_data.packagecode = packagecode.get_data_as_string()

    msiproductcode = am_entry.get_value_by_name(self._AMCACHE_P_MSIPRODUCTCODE)
    if msiproductcode:
      msiproductcode = msiproductcode.get_data()
      msiproductcode = msiproductcode.decode('utf-16-LE')
      event_data.msiproductcode = msiproductcode

    msipackagecode = am_entry.get_value_by_name(self._AMCACHE_P_MSIPACKAGECODE)
    if msipackagecode:
      msipackagecode = msipackagecode.get_data()
      msipackagecode = msipackagecode.decode('utf-16-LE')
      event_data.msipackagecode = msipackagecode

    files = am_entry.get_value_by_name(self._AMCACHE_P_FILES)
    if files:
      files = files.get_data()
      files = files.decode('utf-16-LE')
      event_data.files = files

    event = time_events.DateTimeValuesEvent(
        posix_time.PosixTime(amcache_datetime),
        definitions.TIME_DESCRIPTION_INSTALLATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ProcessAMCacheFileKey(self, am_entry, parser_mediator):
    """"Parses an Amcache Root/File key for events.

    Args:
      am_entry (pyregf.key): amcache File key.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """
    amcache_datetime = am_entry.get_value_by_name(
        self._AMCACHE_DATETIME).get_data_as_integer()
    event_data = AmcacheEventData()

    event_data.full_path = am_entry.get_value_by_name(
        self._AMCACHE_FULL_PATH).get_data_as_string()
    # Strip off the 4 leading zero's from the sha1 hash.
    event_data.sha1 = am_entry.get_value_by_name(
        self._AMCACHE_SHA1).get_data_as_string()[4:]

    productname = am_entry.get_value_by_name(self._AMCACHE_PRODUCTNAME)
    if productname:
      event_data.productname = productname.get_data_as_string()

    companyname = am_entry.get_value_by_name(self._AMCACHE_COMPANYNAME)
    if companyname:
      event_data.companyname = companyname.get_data_as_string()

    fileversion = am_entry.get_value_by_name(self._AMCACHE_FILEVERSION)
    if fileversion:
      event_data.fileversion = fileversion.get_data_as_string()

    languagecode = am_entry.get_value_by_name(self._AMCACHE_LANGUAGECODE)
    if languagecode:
      event_data.languagecode = languagecode.get_data_as_integer()

    filesize = am_entry.get_value_by_name(self._AMCACHE_FILESIZE)
    if filesize:
      event_data.filesize = filesize.get_data_as_integer()

    filedescription = am_entry.get_value_by_name(self._AMCACHE_FILEDESCRIPTION)
    if filedescription:
      event_data.filedescription = filedescription.get_data_as_string()

    linkerts = am_entry.get_value_by_name(self._AMCACHE_LINKERTS)
    if linkerts:
      event_data.linkerts = linkerts.get_data_as_integer()

    lastmodifiedts = am_entry.get_value_by_name(self._AMCACHE_LASTMODIFIEDTS)
    if lastmodifiedts:
      event_data.lastmodifiedts = lastmodifiedts.get_data_as_integer()

    createdts = am_entry.get_value_by_name(self._AMCACHE_CREATEDTS)
    if createdts:
      event_data.createdts = createdts.get_data_as_integer()

    programid = am_entry.get_value_by_name(self._AMCACHE_PROGRAMID)
    if programid:
      event_data.programid = programid.get_data_as_string()

    event = time_events.DateTimeValuesEvent(
        filetime.Filetime(amcache_datetime),
        definitions.TIME_DESCRIPTION_MODIFICATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    if event_data.createdts:
      event = time_events.DateTimeValuesEvent(
          filetime.Filetime(event_data.createdts),
          definitions.TIME_DESCRIPTION_CREATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if event_data.lastmodifiedts:
      event = time_events.DateTimeValuesEvent(
          filetime.Filetime(event_data.lastmodifiedts),
          definitions.TIME_DESCRIPTION_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    if event_data.linkerts:
      event = time_events.DateTimeValuesEvent(
          posix_time.PosixTime(event_data.linkerts),
          definitions.TIME_DESCRIPTION_CHANGE)
      parser_mediator.ProduceEventWithEventData(event, event_data)

manager.ParsersManager.RegisterParser(AmcacheParser)
