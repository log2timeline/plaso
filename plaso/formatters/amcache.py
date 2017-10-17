# -*- coding: utf-8 -*-
"""The Windows Registry Amcache entries event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class AmcacheFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Amcache Windows Registry event."""

  DATA_TYPE = 'windows:registry:amcache'

  FORMAT_STRING_PIECES = [
      'path: {full_path}',
      'sha1: {sha1}',
      'productname: {productname}',
      'companyname: {companyname}',
      'fileversion: {fileversion}',
      'languagecode: {languagecode}',
      'filesize: {filesize}',
      'filedescription: {filedescription}',
      'linkerts: {linkerts}',
      'lastmodifiedts: {lastmodifiedts}',
      'createdts: {createdts}',
      'programid: {programid}',]

  FORMAT_STRING_SHORT_PIECES = ['path: {full_path}']

  SOURCE_LONG = 'Amcache Registry Entry'
  SOURCE_SHORT = 'AMCACHE'

class AmcacheProgramsFormatter(interface.ConditionalEventFormatter):
  """Formatter for an Amcache Programs Windows Registry event."""

  DATA_TYPE = 'windows:registry:amcache:programs'

  FORMAT_STRING_PIECES = [
      'name: {name}',
      'version: {version}',
      'publisher: {publisher}',
      'languagecode: {languagecode}',
      'entrytype: {entrytype}',
      'uninstallkey: {uninstallkey}',
      'filepaths: {filepaths}',
      'productcode: {productcode}',
      'packagecode: {packagecode}',
      'msiproductcode: {msiproductcode}',
      'msipackagecode: {msipackagecode}',
      'files: {files}',]

  FORMAT_STRING_SHORT_PIECES = ['name: {name}']

  SOURCE_LONG = 'Amcache Programs Registry Entry'
  SOURCE_SHORT = 'AMCACHEPROGRAM'

manager.FormattersManager.RegisterFormatter(AmcacheFormatter)
manager.FormattersManager.RegisterFormatter(AmcacheProgramsFormatter)
