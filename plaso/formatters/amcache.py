# -*- coding: utf-8 -*-
"""The Windows Registry Amcache entries event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class AmcacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Amcache Windows Registry event."""

  DATA_TYPE = u'windows:registry:amcache'

  FORMAT_STRING_PIECES = [
      u'path: {full_path}',
      u'sha1: {sha1}',
      u'productname: {productname}',
      u'companyname: {companyname}',
      u'fileversion: {fileversion}',
      u'languagecode: {languagecode}',
      u'filesize: {filesize}',
      u'filedescription: {filedescription}',
      u'linkerts: {linkerts}',
      u'lastmodifiedts: {lastmodifiedts}',
      u'createdts: {createdts}',
      u'programid: {programid}',]

  FORMAT_STRING_SHORT_PIECES = [u'path: {full_path}']

  SOURCE_LONG = u'Amcache Registry Entry'
  SOURCE_SHORT = u'AMCACHE'

class AmcacheProgramsFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Amcache Programs Windows Registry event."""

  DATA_TYPE = u'windows:registry:amcache:programs'

  FORMAT_STRING_PIECES = [
      u'name: {name}',
      u'version: {version}',
      u'publisher: {publisher}',
      u'languagecode: {languagecode}',
      u'entrytype: {entrytype}',
      u'uninstallkey: {uninstallkey}',
      u'filepaths: {filepaths}',
      u'productcode: {productcode}',
      u'packagecode: {packagecode}',
      u'msiproductcode: {msiproductcode}',
      u'msipackagecode: {msipackagecode}',
      u'files: {files}',]

  FORMAT_STRING_SHORT_PIECES = [u'name: {name}']

  SOURCE_LONG = u'Amcache Programs Registry Entry'
  SOURCE_SHORT = u'AMCACHEPROGRAM'

manager.FormattersManager.RegisterFormatter(AmcacheFormatter)
manager.FormattersManager.RegisterFormatter(AmcacheProgramsFormatter)
