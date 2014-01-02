#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Parse your Windows registry files using preg.

preg is a simple Windows registry parser using the plaso registry plugins and
image parsing capabilities. It uses the back-end libraries of plaso to read
raw image files and extract registry files from VSS and restore points and then
runs the registry plugins of plaso against the registry hive and presents it
in a textual format.
"""

import argparse
import binascii
import logging
import os
import sys
import textwrap

try:
  # Support version 1.X of IPython.
  # pylint: disable-msg=no-name-in-module
  from IPython.terminal.embed import InteractiveShellEmbed
except ImportError:
  from IPython.frontend.terminal.embed import InteractiveShellEmbed

from IPython.core import magic

from plaso import preprocessors

from plaso.collector import factory as collector_factory
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import preprocess
from plaso.lib import timelib
from plaso.lib import utils
from plaso.lib import putils
from plaso.parsers import winreg_plugins    # pylint: disable-msg=unused-import
from plaso.parsers.winreg_plugins import interface
from plaso.pvfs import pvfs
from plaso.pvfs import utils as pvfs_utils
from plaso.pvfs import vss
from plaso.winreg import cache
from plaso.winreg import path_expander as winreg_path_expander
from plaso.winreg import winregistry

import pytz


class RegistryPluginHeader(eventdata.EventFormatter):
  """A formatting class that prints some registry plugin header information."""
  DATA_TYPE = 'windows:registry:key_value'
  FMT_LENGTH = 15

  # A list of attributes that do not need printing out.
  SKIP_ATTRIBUTES = frozenset(
      ['data_type', 'offset', 'timestamp', 'regvalue', 'source_append'])

  # A small dictionary to map back attribute names to more
  # friendly print names.
  ATTRIBUTE_TO_NAME = {
      'timestamp': 'Date',
      'timestamp_desc': 'Type',
      'keyname': 'Key Path',
  }

  def GetMessages(self, event_object):
    """Return a list of short and long message string (short being empty)."""
    ret_strings = []
    fmt_length = self.FMT_LENGTH
    for attribute in event_object.regvalue:
      if len(attribute) > fmt_length:
        fmt_length = len(attribute)

    fmt = u'{:>%ds} : {}' % fmt_length
    ret_strings.append(utils.FormatHeader('Attributes', '-'))
    ret_strings.append(fmt.format(
      'Date',
      timelib.Timestamp.CopyToIsoFormat(event_object.timestamp, pytz.utc)))

    for attribute, value in event_object.GetValues().items():
      if attribute in self.SKIP_ATTRIBUTES:
        continue
      ret_strings.append(fmt.format(
          self.ATTRIBUTE_TO_NAME.get(attribute, attribute), value))

    ret_strings.append(utils.FormatHeader('Data', '-'))
    return u'\n'.join(ret_strings), u''


class RegistryFormatter(eventdata.EventFormatter):
  """A formatting class for registry based events."""
  DATA_TYPE = 'windows:registry:key_value'
  FMT_LENGTH = 15

  def GetMessages(self, event_object):
    """Return a list of short and long message string (short being empty)."""
    ret_strings = []
    fmt_length = self.FMT_LENGTH
    for attribute in event_object.regvalue:
      if len(attribute) > fmt_length:
        fmt_length = len(attribute)

    fmt = u'{:>%ds} : {}' % fmt_length
    for attribute, value in event_object.regvalue.items():
      ret_strings.append(fmt.format(attribute, value))

    return u'\n'.join(ret_strings), u''


class RegistryHexFormatter(RegistryFormatter):
  """A formatting class that adds hex data to printouts."""

  def GetMessages(self, event_object):
    """Return a list of short and long message strings (short being empty)."""
    msg, _ = super(RegistryHexFormatter, self).GetMessages(event_object)

    ret_strings = [msg]

    # pylint: disable-msg=W0212
    event_object.pathspec = RegCache.hive.file_object.pathspec
    ret_strings.append(utils.FormatHeader('Hex Output From Event.', '-'))
    ret_strings.append(putils.GetEventData(event_object, RegCache.fscache))

    return u'\n'.join(ret_strings), u''


class RegCache(object):
  """Cache for current hive and registry key."""

  # Attributes that are cached.
  cur_key = ''
  hive = None
  hive_type = 'UNKNOWN'
  pre_obj = None
  fscache = None
  path_expander = None
  reg_cache = None

  REG_TYPES = {
      'NTUSER': ('\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer',),
      'SOFTWARE': ('\\Microsoft\\Windows\\CurrentVersion\\App Paths',),
      'SECURITY': ('\\Policy\\PolAdtEv',),
      'SYSTEM': ('\\Select',),
      'SAM': ('\\SAM\\Domains\\Account\\Users',),
      'UNKNOWN': (),
  }

  @classmethod
  def SetHiveType(cls):
    """Guess the type of the current hive in the cache."""
    # Detect registry type.
    registry_type = 'UNKNOWN'
    for reg_type in cls.REG_TYPES:
      if reg_type == 'UNKNOWN':
        continue
      found = True
      for reg_key in cls.REG_TYPES[reg_type]:
        if not RegCache.hive.GetKeyByPath(reg_key):
          found = False
          break
      if found:
        registry_type = reg_type
        break

    cls.hive_type = registry_type

  @classmethod
  def BuildCache(cls):
    """Build the registry cache."""
    # Calculate the registry cache.
    cls.reg_cache = cache.WinRegistryCache(cls.hive, cls.hive_type)
    cls.reg_cache.BuildCache()
    cls.path_expander = winreg_path_expander.WinRegistryKeyPathExpander(
        cls.pre_obj, cls.reg_cache)

  @classmethod
  def GetHiveName(cls):
    """Return the name of the registry hive file."""
    if not hasattr(cls, 'hive'):
      return 'N/A'

    return getattr(cls.hive, 'name', 'N/A')


def CdCompleter(dummy_self, dummy_event):
  """Completer function for the cd command, returning back sub keys."""
  return_list = []
  for key in RegCache.cur_key.GetSubkeys():
    return_list.append(key.name)

  return return_list


def PluginCompleter(dummy_self, event):
  """Completer function that returns a list of available plugins."""
  ret_list = []

  if not IsLoaded():
    return ret_list

  if not '-h' in event.line:
    ret_list.append('-h')

  plugin_obj = interface.GetRegistryPlugins()

  for plugin_cls in plugin_obj.GetKeyPlugins(RegCache.hive_type):
    plugin_obj = plugin_cls(RegCache.hive, RegCache.pre_obj, RegCache.reg_cache)
    if plugin_obj.plugin_name == 'DefaultPlugin':
      continue
    ret_list.append(plugin_obj.plugin_name)

  return ret_list


def VerboseCompleter(dummy_self, event):
  """Completer function that suggests simple verbose settings."""
  if '-v' in event.line:
    return []
  else:
    return ['-v']


@magic.magics_class
class MyMagics(magic.Magics):
  """A simple class holding all magic functions for console."""

  # Lowercase name since this is used inside the python console shell.
  @magic.line_magic
  def plugin(self, line):
    """Parse a registry key using a specific plugin."""
    if not IsLoaded():
      print 'No hive loaded, unable to parse.'
      return

    if not line:
      print 'No plugin name added.'
      return

    plugin_name = line
    if '-h' in line:
      items = line.split()
      if len(items) != 2:
        print 'Wrong usage: plugin [-h] PluginName'
        return
      if items[0] == '-h':
        plugin_name = items[1]
      else:
        plugin_name = items[0]

    plugin_obj = interface.GetRegistryPlugins()
    plugin_found = False
    for plugin_cls in plugin_obj.GetKeyPlugins(RegCache.hive_type):
      plugin = plugin_cls(RegCache.hive, RegCache.pre_obj, RegCache.reg_cache)
      if plugin.plugin_name == plugin_name:
        # If we found the correct plugin.
        plugin_found = True
        break

    if not plugin_found:
      print u'No plugin named [{}] available for registry type {}'.format(
          plugin_name, RegCache.hive_type)
      return

    if not hasattr(plugin, 'REG_KEY'):
      print 'Plugin {} has no key information.'.format(line)
      return

    try:
      key_fixed = RegCache.path_expander.ExpandPath(plugin.REG_KEY)
    except KeyError:
      print u'Unable to use plugin {}'.format(line)
      return

    if '-h' in line:
      print utils.FormatHeader(plugin_name)
      print utils.FormatOutputString('Registry Key', plugin.REG_KEY)
      if plugin.REG_KEY != key_fixed:
        print utils.FormatOutputString('Expanded Key', key_fixed)
      print ''
      print utils.FormatOutputString('Description', plugin.__doc__)
      return

    key = RegCache.hive.GetKeyByPath(key_fixed)
    if not key:
      print u'Key {} not found'.format(key_fixed)
      return

    # Move the current location to the key to be parsed.
    self.cd(key_fixed)
    # Parse the key.
    print_strings = ParseKey(
        RegCache.cur_key, verbose=True, use_plugins=[plugin_name])
    print u'\n'.join(print_strings)

  # Lowercase name since this is used inside the python console shell.
  @magic.line_magic
  def parse(self, line):
    """Parse the current key."""
    if 'true' in line.lower():
      verbose = True
    elif '-v' in line.lower():
      verbose = True
    else:
      verbose = False

    if not IsLoaded():
      return

    print_strings = ParseKey(RegCache.cur_key, verbose=verbose)
    print u'\n'.join(print_strings)

    # Print out a hex dump of all binary values.
    if verbose:
      header_shown = False
      for value in RegCache.cur_key.GetValues():
        if value.DataIsBinaryData():
          if not header_shown:
            header_shown = True
            print utils.FormatHeader('Hex Dump')
          # Print '-' 80 times.
          print '-'*80
          print utils.FormatOutputString('Attribute', value.name)
          print '-'*80
          print putils.GetHexDump(value.data)
          print ''
          print '+-'*40
          print ''

  # Lowercase name since this is used inside the python console shell.
  @magic.line_magic
  def cd(self, key):
    """Change between registry keys, like a directory tree.

    The key path can either be an absolute path or a relative one.
    Absolute paths can use '.' and '..' to denote current and parent
    directory/key path.

    Args:
      key: The path to the key to traverse to.
    """
    registry_key = None
    key_path = key

    if not key:
      self.cd('\\')

    if key.startswith('\\'):
      registry_key = RegCache.hive.GetKeyByPath(key)
    elif key == '.':
      return
    elif key.startswith('.\\'):
      current_path = RegCache.hive.cur_key.path
      _, _, key_path = key.partition('\\')
      registry_key = RegCache.hive.GetKeyByPath(u'{}\\{}'.format(
          current_path, key_path))
    elif key.startswith('..'):
      parent_path, _, _ = RegCache.cur_key.path.rpartition('\\')
      _, _, key_path = key.partition('\\')
      if parent_path:
        if key_path:
          path = u'{}\\{}'.format(parent_path, key_path)
        else:
          path = parent_path
        registry_key = RegCache.hive.GetKeyByPath(path)
      else:
        registry_key = RegCache.hive.GetKeyByPath(u'\\{}'.format(key_path))

    else:
      # Check if key is not set at all, then assume traversal from root.
      if not RegCache.cur_key:
        RegCache.cur_key = RegCache.hive.GetKeyByPath('\\')

      if RegCache.cur_key.name == RegCache.hive.GetKeyByPath('\\').name:
        key_path = u'\\{}'.format(key)
      else:
        key_path = u'{}\\{}'.format(RegCache.cur_key.path, key)
      registry_key = RegCache.hive.GetKeyByPath(key_path)

    if registry_key:
      if key_path == '\\':
        path = '\\'
      else:
        path = registry_key.path

      # Set the registry key and the prompt.
      RegCache.cur_key = registry_key
      ip = get_ipython()    # pylint: disable-msg=E0602
      ip.prompt_manager.in_template = u'{}->{} [\\#] '.format(
          StripCurlyBrace(RegCache.GetHiveName()),
          StripCurlyBrace(path).replace('\\', '\\\\'))
    else:
      print 'Unable to change to [{}]'.format(key_path)

  # Lowercase name since this is used inside the python console shell.
  @magic.line_magic
  def pwd(self, dummy_line):
    """Print the current path."""
    if not IsLoaded():
      return

    print RegCache.cur_key.path

  # Lowercase name since this is used inside the python console shell.
  @magic.line_magic
  def ls(self, line):
    """List all subkeys and values of the current key."""
    if not IsLoaded():
      return

    if 'true' in line.lower():
      verbose = True
    elif '-v' in line.lower():
      verbose = True
    else:
      verbose = False


    sub = []
    for key in RegCache.cur_key.GetSubkeys():
      timestamp, _, _ = putils.PrintTimestamp(
          key.last_written_timestamp).partition('.')

      sub.append((u'{0:>19s} {1:>15s}  {2:s}'.format(
          timestamp.replace('T', ' '), '[KEY]',
          key.name), True))

    for value in RegCache.cur_key.GetValues():
      if not verbose:
        sub.append((u'{:>19s} {:>14s}]  {:s}'.format(
            '', '[' + value.data_type_string, value.name), False))
      else:
        if value.DataIsString():
          value_string = u'{0:s}'.format(value.data)
        elif value.DataIsInteger():
          value_string = u'{0:d}'.format(value.data)
        elif value.DataIsMultiString():
          value_string = u'{0:s}'.format( u''.join(value.data))
        elif value.DataIsBinaryData():
          hex_string = binascii.hexlify(value.data)
          # We'll just print the first few bytes, but we need to pad them
          # to make it fit in a single line if shorter.
          if len(hex_string) % 32:
            breakpoint = len(hex_string) / 32
            leftovers = hex_string[breakpoint:]
            pad = ' ' * (32 - len(leftovers))
            hex_string += pad

          value_string = putils.GetHexDumpLine(hex_string, 0)
        else:
          value_string = u''

        sub.append((u'{:>19s} {:>14s}]  {:<25s}  {:s}'.format(
            '', '[' + value.data_type_string, value.name, value_string), False))

    for entry, subkey in sorted(sub):
      if subkey:
        print u'dr-xr-xr-x {}'.format(entry)
      else:
        print u'-r-xr-xr-x {}'.format(entry)


def StripCurlyBrace(string):
  """Return a format "safe" string."""
  return string.replace('}', '}}').replace('{', '{{')


def IsLoaded():
  """Checks if a Windows Registry Hive is loaded."""
  if hasattr(RegCache.cur_key, 'path'):
    return True

  if RegCache.GetHiveName() != 'N/A':
    return True

  print 'No hive loaded, cannot complete action. Use OpenHive to load a hive.'
  return False


def OpenHive(filename, collector=None, codepage='cp1252'):
  """Open a registry hive based on a collector or a filename."""
  if not collector:
    file_object = pvfs_utils.OpenOSFileIO(filename)
  else:
    file_entry = collector.OpenFileEntry(filename)
    file_object = file_entry.Open()

  use_codepage = getattr(RegCache.pre_obj, 'code_page', codepage)

  win_registry = winregistry.WinRegistry(
      winregistry.WinRegistry.BACKEND_PYREGF)

  try:
    RegCache.hive = win_registry.OpenFile(file_object, codepage=use_codepage)
  except IOError:
    ErrorAndDie(u'Unable to open registry hive: {}'.format(filename))
  RegCache.SetHiveType()
  RegCache.BuildCache()
  RegCache.cur_key = RegCache.hive.GetKeyByPath('\\')


def PrintEventHeader(event_object):
  """Print event header."""
  event_formatter = RegistryPluginHeader()

  msg, _ = event_formatter.GetMessages(event_object)

  return msg


def PrintEvent(event_object, show_hex=False):
  """Print information from an extracted EventObject."""
  if show_hex:
    event_formatter = RegistryHexFormatter()
  else:
    event_formatter = RegistryFormatter()

  msg, _ = event_formatter.GetMessages(event_object)

  return msg


def ParseHive(hive_path, collectors, keys, use_plugins, verbose):
  """Opens a hive file, and prints out information about parsed keys.

  This function takes a path to a hive and a list of collectors (or
  none if the registry file is passed to the tool).

  The function then opens up the hive inside each collector and runs
  the plugins defined (or all if no plugins are defined) against all
  the keys supplied to it.

  Args:
    hive_path: Full path to the hive file in question.
    collectors: A list of collectors to use.
    keys: A list of registry keys (strings) that are to be parsed.
    use_plugins: A list of plugins used to parse the key, None if all
    plugins should be used.
    verbose: Print more verbose content, like hex dump of extracted events.
  """
  print_strings = []
  for name, collector in collectors:
    # Printing '*' 80 times.
    print_strings.append(u'*'*80)
    print_strings.append(
        u'{:>15} : {}{}'.format(u'Hive File', hive_path, name))
    OpenHive(hive_path, collector)
    for key_str in keys:
      key_texts = []
      key_str_use = key_str
      key_dict = {}
      if RegCache.reg_cache:
        key_dict.update(RegCache.reg_cache.attributes.items())

      if RegCache.pre_obj:
        key_dict.update(RegCache.pre_obj.__dict__.items())

      try:
        key_str_use = key_str.format(**key_dict)
      except KeyError as e:
        logging.warning((
            u'Unable to format key string {0:s} with error: '
            u'{1:s}').format(key_str, e))

      key = RegCache.hive.GetKeyByPath(key_str_use)
      key_texts.append(u'{:>15} : {}'.format(u'Key Name', key_str_use))
      if not key:
        key_texts.append(u'Unable to open key: {}'.format(key_str_use))
        if verbose:
          print_strings.extend(key_texts)
        continue
      key_texts.append(
          u'{:>15} : {}'.format(u'Subkeys', key.number_of_subkeys))
      key_texts.append(u'{:>15} : {}'.format(
          u'Values', key.number_of_values))
      key_texts.append(u'')

      if verbose:
        key_texts.append(u'{:-^80}'.format(u' SubKeys '))
        for subkey in key.GetSubkeys():
          key_texts.append(
              u'{:>15} : {}'.format(u'Key Name', subkey.path))

      key_texts.append(u'')
      key_texts.append(u'{:-^80}'.format(u' Plugins '))
      key_texts.extend(
          ParseKey(key, verbose=verbose, use_plugins=use_plugins))
      print_strings.extend(key_texts)

  print u'\n'.join(print_strings)


def ParseKey(key, verbose=False, use_plugins=None):
  """Parse a single registry key and print out parser information.

  Parses the registry key either using the supplied plugin or trying against
  all avilable plugins.

  Args:
    key: The registry key to parse, WinRegKey object or a string.
    verbose: Print additional information, such as a hex dump.
    use_plugins: A list of plugin names to use, or none if all should be used.

  Returns:
    A list of strings.
  """
  print_strings = []
  # Check if hive is set.
  if not RegCache.hive:
    return

  if type(key) in (unicode, str):
    key = RegCache.hive.GetKeyByPath(key)

  if not key:
    return

  # Detect registry type.
  registry_type = RegCache.hive_type

  plugins = {}
  regplugins = interface.GetRegistryPlugins()
  # Compile a list of plugins we are about to use.
  for weight in regplugins.GetWeights():
    plugin_list = regplugins.GetWeightPlugins(weight, registry_type)
    plugins[weight] = []
    for plugin in plugin_list:
      if use_plugins:
        plugin_obj = plugin(RegCache.hive, RegCache.pre_obj, RegCache.reg_cache)
        if plugin_obj.plugin_name in use_plugins:
          plugins[weight].append(plugin_obj)
      else:
        plugins[weight].append(plugin(
            RegCache.hive, RegCache.pre_obj, RegCache.reg_cache))

  # Run all the plugins in the correct order of weight.
  for weight in plugins:
    for plugin in plugins[weight]:
      call_back = plugin.Process(key)
      if call_back:
        print_strings.append(
            u'{:^80}'.format(u' ** Plugin : {0:s} **'.format(
                plugin.plugin_name)))
        first = True
        for event_object in call_back:
          if first:
            print_strings.append(PrintEventHeader(event_object))
            first = False
          print_strings.append(PrintEvent(event_object, verbose))
        print_strings.append(u'')

  # Printing '*' 80 times.
  print_strings.append(u'*'*80)
  print_strings.append(u'')

  return print_strings


def FindRegistryPaths(pattern, collector):
  """Return a list of Windows registry file paths."""
  hive_paths = []
  try:
    file_path, _, file_name = pattern.rpartition('/')
    paths = list(collector.FindPaths(file_path))

    if not paths:
      logging.debug(u'No paths found for pattern [{0:s}]'.format(file_path))
      return hive_paths

    for path in paths:
      fh_paths = list(collector.GetFilePaths(path, file_name))
      if not fh_paths:
        logging.debug(u'File [{0:s}] not found in path [{1:s}]....'.format(
            file_name, path))
        continue
      for fh_path in fh_paths:
        hive_paths.append(fh_path)
  except errors.PreProcessFail as e:
    logging.debug('Path: {0:s} not found, error: {1:s}'.format(pattern, e))
  except errors.PathNotFound as e:
    logging.debug('Path: {0:s} not found, error: {1:s}'.format(pattern, e))

  return hive_paths


def ErrorAndDie(error):
  """Print error message and a help message."""
  if argument_parser:
    argument_parser.print_help()
  else:
    print 'Unable to print help message.'
  print ''
  logging.error(error)
  sys.exit(1)


def ParseOptions():
  """Parse command line parameters and return a configuration object."""
  epilog = textwrap.dedent(
      """

Example usage:

Parse the SOFTWARE hive from an image:
  {0} [--vss] [--vss-stores VSS_STORES] -i IMAGE_PATH [-o OFFSET] -c SOFTWARE

Parse an userassist key within an extracted hive:
  {0} -p userassist MYNTUSER.DAT

Parse the run key from all registry keys (in vss too):
  {0} --vss -i IMAGE_PATH [-o OFFSET] -p run

Open up a console session for the SYSTEM hive inside an image:
  {0} -i IMAGE_PATH [-o OFFSET] -c SYSTEM
      """).format(os.path.basename(sys.argv[0]))

  description = textwrap.dedent(
      """
preg is a simple Windows registry parser using the plaso registry
plugins and image parsing capabilities.

It uses the back-end libraries of plaso to read raw image files and
extract registry files from VSS and restore points and then runs the
registry plugins of plaso against the registry hive and presents it
in a textual format.

      """)

  arg_parser = argparse.ArgumentParser(
      epilog=epilog, description=description, add_help=False,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  # Create the different argument groups.
  mode_options = arg_parser.add_argument_group('Run Mode Options')
  image_options = arg_parser.add_argument_group('Image Options')
  info_options = arg_parser.add_argument_group('Informational Options')
  additional_data = arg_parser.add_argument_group('Additional Options')

  mode_options.add_argument(
      '-c', '--console', dest='console', action='store_true', default=False,
      help='Drop into a console session Instead of printing output to STDOUT.')

  additional_data.add_argument(
      '-r', '--restore_points', dest='restore_points', action='store_true',
      default=False, help='Include restore points for hive locations.')

  image_options.add_argument(
      '-i', '--image', dest='image', action='store', type=str, default='',
      metavar='IMAGE_PATH',
      help=('If the registry file lies within an image, this is the path to '
            'that image file.'))

  image_options.add_argument(
      '-o', '--offset', dest='offset', action='store', type=int, default=0,
      help='Sector offset into the image, if one is provided.')

  info_options.add_argument(
      '-v', '--verbose', dest='verbose', action='store_true', default=False,
      help='Print sub key information.')

  info_options.add_argument(
      '-h', '--help', action='help', help='Show this help message and exit.')

  additional_data.add_argument(
      '--vss', dest='vss', action='store_true', default=False,
      help='Indicate that we are pulling the registry hive from VSS as well.')

  additional_data.add_argument(
      '--vss-stores', dest='vss_stores', action='store', type=str, default=None,
      help=('List of stores to parse, format is X..Y where X and Y are '
            'integers, or a list of entries separated with a comma, eg: X,Y,Z '
            'or a list of ranges and entries, eg: X,Y-Z,G,H-J.'))

  info_options.add_argument(
      '--info', dest='info', action='store_true', default=False,
      help='Print out information about supported plugins.')

  mode_options.add_argument(
      '-p', '--plugins', dest='plugin_name', action='store', default='',
      type=str, metavar='PLUGIN_NAME',
      help='Substring match of the registry plugin to be used.')

  mode_options.add_argument(
      '-k', '--key', dest='key', action='store', default='', type=str,
      metavar='REGISTRY_KEYPATH',
      help=('A registry key path that the tool should parse using all '
            'available plugins.'))

  arg_parser.add_argument(
      'regfile', action='store', metavar='REGHIVE', nargs='?',
      help=('The registry hive to read key from (not needed if running using a '
            'plugin)'))

  return arg_parser


def Main(arguments):
  """Run the tool."""
  # Parse the command line arguments.
  options = arguments.parse_args()

  options.plugins = interface.GetRegistryPlugins()

  # TODO: Move some of this logic to a separate function calls to make
  # GUI writing on top of this front-end simpler.

  # Run some common operations (common to all run modes)
  # Detect run mode and run appropriate method calls.
  if options.info:
    print utils.FormatHeader('Supported Plugins')
    key_plugin = options.plugins.GetAllKeyPlugins()[0]

    for plugin, obj in sorted(key_plugin.classes.items()):
      doc_string, _, _ = obj.__doc__.partition('\n')
      print utils.FormatOutputString(plugin, doc_string)
    sys.exit(0)

  if not options.image:
    if not options.regfile:
      ErrorAndDie('Not enough parameters to proceed.')

    if not os.path.isfile(options.regfile):
      ErrorAndDie(
          'Registry file must exist [{}] does not exist.'.format(
              options.regfile))

  # Run the tool, using the run mode according to the options passed to the
  # tool.
  if options.console:
    RunModeConsole(options)
  elif options.key and options.regfile:
    RunModeRegistryKey(options)
  elif options.plugin_name:
    RunModeRegistryPlugin(options)
  elif options.regfile:
    RunModeRegistryFile(options)
  else:
    ErrorAndDie((
        'Wrong usage, need to define either an image path or a '
        'registry file.'))


def RunModeRegistryFile(config):
  """Run against a registry file.

  Finds and opens all registry hives as configured in the configuration
  object and determines the type of registry file opened. Then it will
  load up all the registry plugins suitable for that particular registry
  file, find all registry keys they are able to parse and run through
  them, one by one.

  Args:
    config: The configuration object (most likely an argparse object.
  """
  # Get all the hives and collectors.
  hives, collectors = GetHivesAndCollectors(config)

  for hive in hives:
    for _, collector in collectors:
      OpenHive(hive, collector)
      config.plugin_name = RegCache.hive_type
      keys = GetRegistryKeysFromType(config, config.plugin_name)
      ExpandKeysRedirect(keys)
      plugins_to_run = GetRegistryPlugins(config)
      ParseHive(hive, collectors, keys, plugins_to_run, config.verbose)


def RunModeRegistryKey(config):
  """Run against a specific registry key.

  Finds and opens all registry hives as configured in the configuration
  object and tries to open the registry key that is stored in the configuration
  object for every detected hive file and parses it using all available plugins.

  Args:
    config: The configuration object (most likely an argparse object.
  """
  hives, collectors = GetHivesAndCollectors(config)

  # Get the registry key.
  keys = [config.key]

  # Expand the keys if there is a need (due to Windows redirect).
  ExpandKeysRedirect(keys)

  for hive in hives:
    ParseHive(hive, collectors, keys, None, config.verbose)


def GetHivesAndCollectors(config):
  """Returns a list of discovered registry hives and collectors."""
  if config.image:
    collectors = GetCollectorsFromAnImage(config)
    _, collector = collectors[0]
    # Find all the registry paths we need to check.
    if config.regfile:
      paths = GetRegistryFilePaths(config, config.regfile.upper())
    else:
      paths = GetRegistryFilePaths(config)

    hives = []
    for path in paths:
      hives.extend(FindRegistryPaths(path, collector))
  else:
    hives = [config.regfile]
    collectors = [('', None)]

  return hives, collectors


def RunModeRegistryPlugin(config):
  """Run against a set of registry plugins."""
  hives, collectors = GetHivesAndCollectors(config)

  plugin_list = GetRegistryPlugins(config)

  # Need to get all the appropriate keys from these plugins.
  keys = []
  for plugin in plugin_list:
    for reg_plugin in config.plugins.GetAllKeyPlugins():
      temp_obj = reg_plugin(None, None, None)
      if temp_obj.plugin_name == plugin:
        keys.append(temp_obj.REG_KEY)

  for hive in hives:
    ParseHive(hive, collectors, keys, plugin_list, config.verbose)


def StartPreProcess():
  """Run preprocessing on the image."""
  RegCache.pre_obj = preprocess.PlasoPreprocess()
  RegCache.pre_obj.zone = pytz.UTC


def GetCollectorsFromAnImage(config):
  """Open up an image and return back a list of collectors."""
  collectors = []
  StartPreProcess()
  if config.vss_stores:
    config.vss = True
    stores = []
    try:
      for store in config.vss_stores.split(','):
        if '..' in store:
          begin, end = store.split('..')
          for nr in range(int(begin), int(end)):
            if nr not in stores:
              stores.append(nr)
        else:
          if int(store) not in stores:
            stores.append(int(store))
    except ValueError:
      ErrorAndDie('VSS store range is wrongly formed.')

    config.vss_stores = sorted(stores)

  RegCache.fscache = pvfs.FilesystemCache()
  try:
    main_collector = collector_factory.GetImagePreprocessCollector(
        RegCache.pre_obj, config.image, byte_offset=(config.offset * 512))
  except errors.UnableToOpenFilesystem:
    ErrorAndDie(
        u'Unable to open the file system image: {}'.format(config.image))
  collectors.append(('', main_collector))

  # Run pre processing on image.
  pre_plugin_list = preprocessors.PreProcessList(
      RegCache.pre_obj, main_collector)
  guessed_os = preprocess.GuessOS(main_collector)
  for weight in pre_plugin_list.GetWeightList(guessed_os):
    for plugin in pre_plugin_list.GetWeight(guessed_os, weight):
      try:
        plugin.Run()
      except (IOError, errors.PreProcessFail) as e:
        logging.warning(u'Unable to run plugin: {}, reason {}'.format(
            plugin.plugin_name, e))

  # Check for VSS.
  if config.vss:
    if not config.vss_stores:
      config.vss_stores = range(0, vss.GetVssStoreCount(
          config.image, config.offset * 512))

    for store in config.vss_stores:
      vss_collector = collector_factory.GetImagePreprocessCollector(
          RegCache.pre_obj, config.image, byte_offset=(config.offset * 512),
          vss_store_number=store)
      collectors.append((':VSS Store {}'.format(store + 1), vss_collector))

  return collectors


def GetRegistryPlugins(config):
  """Return a list of registry plugins by examining configuration object."""
  key_plugin_names = []
  for plugin in config.plugins.GetAllKeyPlugins():
    temp_obj = plugin(None, None, None)
    key_plugin_names.append(temp_obj.plugin_name)

  # Determine if we are running against a plugin or a key (behavior differs).
  plugins_to_run = []
  if config.plugin_name:
    for key_plugin in key_plugin_names:
      if config.plugin_name.lower() in key_plugin.lower():
        plugins_to_run.append(key_plugin)
  else:
    plugins_to_run = key_plugin_names

  return plugins_to_run


def GetRegistryTypes(config):
  """Return back a list of all available registry types."""
  types = []
  for plugin in GetRegistryPlugins(config):
    for reg_plugin in config.plugins.GetAllKeyPlugins():
      temp_obj = reg_plugin(None, None, None)
      if plugin is temp_obj.plugin_name:
        if temp_obj.REG_TYPE not in types:
          types.append(temp_obj.REG_TYPE)
        break

  return types


def GetRegistryKeysFromType(config, registry_type):
  """Return a list of all key plugins for a given registry type."""
  keys = []
  for reg_plugin in config.plugins.GetAllKeyPlugins():
    temp_obj = reg_plugin(None, None, None)
    if temp_obj.REG_TYPE == registry_type:
      keys.append(temp_obj.REG_KEY)

  return keys


def GetRegistryFilePaths(config, registry_type=None):
  """Returns a list of registry paths from a configuration object."""
  if config.restore_points:
    restore_path = '/System Volume Information/_restor.+/RP[0-9]+/snapshot/'
  else:
    restore_path = ''

  if registry_type:
    types = [registry_type]
  else:
    types = GetRegistryTypes(config)

  # Gather the registry files to fetch.
  paths = []

  for reg_type in types:
    if reg_type == 'NTUSER':
      paths.append('/Documents And Settings/.+/NTUSER.DAT')
      paths.append('/Users/.+/NTUSER.DAT')
      if restore_path:
        paths.append('{}/_REGISTRY_USER_NTUSER.+'.format(restore_path))
    elif reg_type == 'SOFTWARE':
      paths.append('{sysregistry}/SOFTWARE')
      if restore_path:
        paths.append('{}/_REGISTRY_MACHINE_SOFTWARE'.format(restore_path))
    elif reg_type == 'SYSTEM':
      paths.append('{sysregistry}/SYSTEM')
      if restore_path:
        paths.append('{}/_REGISTRY_MACHINE_SYSTEM'.format(restore_path))
    elif reg_type == 'SECURITY':
      paths.append('{sysregistry}/SECURITY')
      if restore_path:
        paths.append('{}/_REGISTRY_MACHINE_SECURITY'.format(restore_path))
    elif reg_type == 'SAM':
      paths.append('{sysregistry}/SAM')
      if restore_path:
        paths.append('{}/_REGISTRY_MACHINE_SAM'.format(restore_path))

  return paths


def ExpandKeysRedirect(keys):
  """Expand a key list with registry redirect keys."""
  for key in keys:
    if key.startswith('\\Software') and 'Wow6432Node' not in key:
      _, first, second = key.partition('\\Software')
      keys.append(u'{}\\Wow6432Node{}'.format(first, second))


def RunModeConsole(config):
  """Open up an iPython console."""
  namespace = {}
  hives, collectors = GetHivesAndCollectors(config)

  function_name_length = 23
  banners = []
  banners.append(utils.FormatHeader(
      'Welcome to PREG - home of the Plaso Windows Registry Parsing.'))
  banners.append('')
  banners.append('Some of the commands that are available for use are:')
  banners.append('')
  banners.append(utils.FormatOutputString(
      'cd key', 'Navigate the registry like a directory structure.',
      function_name_length))
  banners.append(utils.FormatOutputString(
      'ls [-v]', (
          'List all subkeys and values of a registry key. If called as '
          'ls True then values of keys will be included in the output.'),
      function_name_length))
  banners.append(utils.FormatOutputString(
      'parse -[v]', 'Parse the current key using all plugins.',
      function_name_length))
  banners.append(utils.FormatOutputString(
      'pwd', 'Print the working "directory" or the path of the current key.',
      function_name_length))
  banners.append(utils.FormatOutputString(
      'plugin [-h] plugin_name', (
          'Run a particular key-based plugin on the loaded hive. The correct '
          'registry key will be loaded, opened and then parsed.'),
      function_name_length))

  banners.append('')

  if len(hives) == 1:
    hive = hives[0]
    hives = []
  else:
    hive = None

  if len(collectors) == 1:
    collector = collectors[0][1]
    collectors = []
  else:
    collector = None

  if hive and not collectors:
    OpenHive(hive, collector)

  if RegCache.hive and RegCache.GetHiveName() != 'N/A':
    banners.append(
        u'Registry hive [{}] is available and loaded.'.format(
            RegCache.GetHiveName()))
  elif hives:
    banners.append('More than one registry file ready for use.')
    banners.append('')
    banners.append('Registry files discovered:')
    for number, hive in enumerate(hives):
      banners.append(' - {}  {}'.format(number, hive))
    banners.append('')
    banners.append('To load a hive use:')
    text = 'OpenHive(hives[NR], collector)'

    if collectors:
      banners.append('')
      banners.append((
          'There is more than one collector available. To use any of them '
          'instead of the attribute "collector" in the OpenHive '
          'function use the collectors attribute.\nThe available collectors '
          'are:'))
      counter = 0
      for name, _ in collectors:
        if not name:
          name = 'Current Value'
        banners.append(' {} = {}'.format(counter, name))
        counter += 1

      banners.append(
          'To use the collector use:\ncollector = collectors[NR][1]\nwhere '
          'NR is the number as listed above.')
    else:
      banners.append(utils.FormatOutputString(text, (
          'Collector is an available attribute and NR is a number ranging'
          ' from 0 to {0:d} (see above which files these numbers belong to).'
          ' To get the name of the loaded hive use RegCache.GetHiveName()'
          ' and RegCache.hive_type to get the '
          'type.').format(len(hives) + 1), len(text)))
  else:
    # We have a single hive but many collectors.
    banners.append(
        'There is more than one collector available for the hive that was '
        'discovered. To open up a hive use:\nOpenHive(hive, collectors[NR][1])'
        '\nWhere NR is one of the following values:')

    counter = 0
    for name, _ in collectors:
      if not name:
        name = 'Current Value'
      banners.append(' {} = {}'.format(counter, name))
      counter += 1

  banners.append('')
  banners.append('Happy command line console fu-ing.')

  # Adding variables in scope.
  namespace.update(globals())
  namespace.update({
      'hives': hives,
      'hive': hive,
      'collector': collector,
      'collectors': collectors})

  # Starting the shell.
  ipshell = InteractiveShellEmbed(
      user_ns=namespace, banner1=u'\n'.join(banners), exit_msg='')
  ipshell.confirm_exit = False
  # Adding "magic" functions.
  ipshell.register_magics(MyMagics)
  # Registering command completion for the magic commands.
  ipshell.set_hook('complete_command', CdCompleter, str_key='%cd')
  ipshell.set_hook('complete_command', VerboseCompleter, str_key='%ls')
  ipshell.set_hook('complete_command', VerboseCompleter, str_key='%parse')
  ipshell.set_hook('complete_command', PluginCompleter, str_key='%plugin')
  ipshell()


if __name__ == '__main__':
  argument_parser = ParseOptions()
  Main(argument_parser)
