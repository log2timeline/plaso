#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script to extract information about the supported data formats."""

import argparse
import collections
import importlib
import inspect
import os
import pkgutil
import sys

from urllib import parse as urllib_parse

from dtfabric import reader as dtfabric_reader
from dtfabric import registry as dtfabric_registry

import plaso

from plaso.parsers import interface as parsers_interface
from plaso.parsers import plugins as parsers_plugins


class DataFormatDescriptor(object):
  """Descriptor of a specific data format.

  Attributes:
    category (str): category of the data format, for example "File formats" or
        "OLE Compound File formats".
    name (str): name of the data format, for example "Chrome Extension
        activity database".
    url (str): URL to more information about the data format.
  """

  def __init__(self, category=None, name=None, url=None):
    """Initializes a data format descriptor.

    Args:
      category (Optional[str]): category of the data format, for example
        "File formats" or "OLE Compound File formats".
      name (Optional[str]): name of the data format, for example "Chrome
        Extension activity database".
      url (Optional[str]): URL to more information about the data format.
    """
    super(DataFormatDescriptor, self).__init__()
    # TODO: add data format name aliases.
    self.category = category
    self.name = name
    self.url = url


class DataFormatInformationExtractor(object):
  """Data format information extractor."""

  _CATEGORIES_OUTPUT_ORDER = [
      'Storage media image file formats',
      'Volume system formats',
      'File system formats',
      'File formats',
      'Bencode file formats',
      'Browser cookie formats',
      'Compound ZIP file formats',
      'ESE database file formats',
      'JSON-L log file formats',
      'OLE Compound File formats',
      'Property list (plist) formats',
      'SQLite database file formats',
      'Text-based log file formats',
      'Windows Registry formats']

  # TODO: consider extending Plaso parsers and parser plugins with metadata that
  # contain this information.
  _DATA_FORMAT_CATEGORY_PER_PACKAGE_PATH = {
      'plaso/parsers': 'File formats',
      'plaso/parsers/bencode_plugins': 'Bencode file formats',
      'plaso/parsers/cookie_plugins': 'Browser cookie formats',
      'plaso/parsers/czip_plugins': 'Compound ZIP file formats',
      'plaso/parsers/esedb_plugins': 'ESE database file formats',
      'plaso/parsers/jsonl_plugins': 'JSON-L log file formats',
      'plaso/parsers/olecf_plugins': 'OLE Compound File formats',
      'plaso/parsers/plist_plugins': 'Property list (plist) formats',
      'plaso/parsers/sqlite_plugins': 'SQLite database file formats',
      'plaso/parsers/text_plugins': 'Text-based log file formats',
      'plaso/parsers/winreg_plugins': 'Windows Registry formats'}

  _DTFORMATS_URL_PREFIX = (
      'https://github.com/libyal/dtformats/blob/main/documentation')

  # Names of parsers and parser plugins to ignore.
  _PARSER_NAME_IGNORE_LIST = frozenset([
      'base_parser',
      'base_plugin',
      'bencode_plugin',
      'cookie_plugin',
      'czip_plugin',
      'esedb_plugin',
      'filestat',
      'jsonl_plugin',
      'mrulistex_shell_item_list',
      'mrulistex_string',
      'mrulistex_string_and_shell_item',
      'mrulistex_string_and_shell_item_list',
      'mrulist_shell_item_list',
      'olecf_default',
      'olecf_plugin',
      'plist_default',
      'plist_plugin',
      'sqlite_plugin',
      'text_plugin',
      'winreg_default',
      'winreg_plugin'])

  _STANDARD_TEXT_PER_CATEGORY = {
      'File system formats': (
          'File System Format support is provided by [dfVFS]'
          '(https://dfvfs.readthedocs.io/en/latest/sources/'
          'Supported-formats.html#file-systems).'),
      'Storage media image file formats': (
          'Storage media image file format support is provided by [dfVFS]'
          '(https://dfvfs.readthedocs.io/en/latest/sources/'
          'Supported-formats.html#storage-media-types).'),
      'Volume system formats': (
          'Volume system format support is provided by [dfVFS]'
          '(https://dfvfs.readthedocs.io/en/latest/sources/'
          'Supported-formats.html#volume-systems).')}

  def FormatDataFormats(self, data_format_descriptors):
    """Formats data format information.

    Args:
      data_format_descriptors (list[DataFormatDescriptor]): data format
          descriptors.

    Returns:
      str: information about data formats.
    """
    lines = [
        '## Supported Formats',
        '',
        'The information below is based of version {0:s}'.format(
            plaso.__version__),
        '']

    descriptors_per_category = collections.defaultdict(list)
    for data_format_descriptor in data_format_descriptors:
      descriptors_per_category[data_format_descriptor.category].append(
          data_format_descriptor)

    for category in self._CATEGORIES_OUTPUT_ORDER:
      lines.append('### {0:s}'.format(category))
      lines.append('')

      standard_text = self._STANDARD_TEXT_PER_CATEGORY.get(category, None)
      if standard_text is not None:
        lines.append(standard_text)

      lines_per_category = []
      data_format_descriptors = descriptors_per_category.get(category, [])
      for data_format_descriptor in sorted(
          data_format_descriptors, key=lambda cls: cls.name):
        url = data_format_descriptor.url

        # TODO: add support for more generic generation of using information.
        if url.startswith('dtformats:'):
          url = url.split(':')[1]
          url = urllib_parse.quote(url)
          url = '{0:s}/{1:s}.asciidoc'.format(self._DTFORMATS_URL_PREFIX, url)
          line = '* [{0:s}]({1:s})'.format(data_format_descriptor.name, url)

        elif url.startswith('libyal:'):
          library_name, url = url.split(':')[1:3]
          library_url = 'https://github.com/libyal/{0:s}'.format(library_name)
          url = urllib_parse.quote(url)
          url = '{0:s}/blob/main/documentation/{1:s}.asciidoc'.format(
              library_url, url)
          line = '* [{0:s}]({1:s}) using [{2:s}]({3:s})'.format(
              data_format_descriptor.name, url, library_name, library_url)

        elif url.startswith('http:') or url.startswith('https:'):
          line = '* [{0:s}]({1:s})'.format(data_format_descriptor.name, url)

        else:
          line = '* {0:s}'.format(data_format_descriptor.name)

        lines_per_category.append(line)

      # Sort the lines per category case-insensitive and ignoring
      # non-alphanumeric characters.
      lines_per_category = sorted(
          lines_per_category,
          key=lambda name: ''.join(filter(str.isalnum, name.lower())))
      lines.extend(lines_per_category)

      if standard_text or data_format_descriptors:
        lines.append('')

    return '\n'.join(lines)

  def _GetDataFormatInformationFromPackage(self, package):
    """Retrieves event data attribute containers from a package.

    Args:
      package (list[str]): package name segments such as ["plaso", "parsers"].

    Returns:
      list[DataFormatDescriptor]: data format descriptors.
    """
    data_format_descriptors = []
    package_path = '/'.join(package)
    for _, name, is_package in pkgutil.iter_modules(path=[package_path]):
      sub_package = list(package)
      sub_package.append(name)
      if is_package:
        sub_data_format_descriptors = (
            self._GetDataFormatInformationFromPackage(sub_package))
        data_format_descriptors.extend(sub_data_format_descriptors)
      else:
        module_path = '.'.join(sub_package)
        try:
          module_object = importlib.import_module(module_path)
        except ImportError:
          module_object = None

        for _, cls in inspect.getmembers(module_object, inspect.isclass):
          if issubclass(cls, (
              parsers_interface.BaseParser, parsers_plugins.BasePlugin)):

            # TODO: detect corresponding dtFabric .yaml file
            parser_name = getattr(cls, 'NAME', None)
            if not parser_name or parser_name in self._PARSER_NAME_IGNORE_LIST:
              continue

            category = self._DATA_FORMAT_CATEGORY_PER_PACKAGE_PATH.get(
                package_path, 'File formats')

            data_format = getattr(cls, 'DATA_FORMAT', None)
            if not data_format:
              print(('WARNING: parser or plugin: {0:s} missing '
                     'DATA_FORMAT').format(parser_name))

            url = ''

            dtfabric_file = os.path.join(package_path, ''.join([name, '.yaml']))
            if os.path.exists(dtfabric_file):
              definitions_registry = (
                  dtfabric_registry.DataTypeDefinitionsRegistry())
              definitions_reader = (
                  dtfabric_reader.YAMLDataTypeDefinitionsFileReader())

              try:
                definitions_reader.ReadFile(definitions_registry, dtfabric_file)
                # TODO: determine the URL using definitions_registry.
              except Exception:  # pylint: disable=broad-except
                pass

            data_format_descriptor = DataFormatDescriptor(
                category=category, name=data_format, url=url)
            data_format_descriptors.append(data_format_descriptor)

    return data_format_descriptors

  def GetDataFormatInformation(self):
    """Retrieves data format information from Plaso.

    Returns:
      list[DataFormatDescriptor]: data format descriptors.
    """
    return self._GetDataFormatInformationFromPackage(['plaso'])


def Main():
  """The main program function.

  Returns:
    bool: True if successful or False if not.
  """
  argument_parser = argparse.ArgumentParser(description=(
      'Extract data format information from Plaso.'))

  # TODO: option to export for information on forensicswiki.
  # TODO: add information about supported compressed stream formats.
  # TODO: add information about supported archive file formats.

  argument_parser.parse_args()

  extractor = DataFormatInformationExtractor()

  data_format_descriptors = extractor.GetDataFormatInformation()
  if not data_format_descriptors:
    print('Unable to determine data format information')
    return False

  output_text = extractor.FormatDataFormats(data_format_descriptors)
  print(output_text)

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
