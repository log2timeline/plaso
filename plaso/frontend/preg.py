#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""A front-end for Windows registry parsing using plaso plugins."""
import argparse
import logging
import os
import sys
import pytz

from IPython.frontend.terminal.embed import InteractiveShellEmbed

from plaso import preprocessors
from plaso import registry    # pylint: disable-msg=W0611

from plaso.lib import errors
from plaso.lib import pfile
from plaso.lib import preprocess
from plaso.lib import putils
from plaso.lib import timelib
from plaso.lib import utils
from plaso.lib import vss
from plaso.lib import win_registry_interface
from plaso.winreg import cache
from plaso.winreg import winregistry

import pytz


class RegCache(object):
  """Cache for current hive and registry key."""

  # Attributes that are cached.
  cur_key = ''
  hive = None
  hive_type = 'UNKNOWN'
  pre_obj = None
  fscache = None
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

  @classmethod
  def GetHiveName(cls):
    """Return the name of the registry hive file."""
    if not hasattr(cls, 'hive'):
      return 'N/A'

    return getattr(cls.hive, 'name', 'N/A')


# Lowercase name since this is used inside the python console shell.
def parse(verbose=False):
  """Parse the current key."""
  if not IsLoaded():
    return

  ParseKey(RegCache.cur_key, verbose=verbose)


# Lowercase name since this is used inside the python console shell.
def cd(key):
  """Change between registry keys, like a directory tree.

  The key path can either be an absolute path or a relative one.
  Absolute paths can use '.' and '..' to denote current and parent
  directory/key path.

  Args:
    key: The path to the key to traverse to.
  """
  registry_key = None
  key_path = key

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
        StripCurlyBrace(path))
  else:
    print 'Unable to change to [{}]'.format(key_path)


# Lowercase name since this is used inside the python console shell.
def pwd():
  """Print the current path."""
  if not IsLoaded():
    return

  print RegCache.cur_key.path


# Lowercase name since this is used inside the python console shell.
def ls(verbose=False):
  """List all subkeys and values of the current key."""
  if not IsLoaded():
    return

  sub = []
  for key in RegCache.cur_key.GetSubkeys():
    sub.append((u'{0:s>10}  {1:s}'.format('[KEY]', key.name), True))

  for value in RegCache.cur_key.GetValues():
    if not verbose:
      sub.append((u'[{0:s>10}]  {1:s}'.format(
          value.data_type_string, value.name), False))
    else:
      if value.DataIsString():
        value_string = u'{0:s}'.format(value.data)
      elif value.DataIsInteger():
        value_string = u'{0:d}'.format(value.data)
      elif value.DataIsMultiString():
        value_string = u'{0:s}'.format( u''.join(value.data))
      else:
        value_string = u''

      sub.append((u'[{0:s>10}]  {1:s<25}  {2:s}'.format(
          value.data_type_string, value.name, value_string), False))

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
    cd('\\')
    return True

  print 'No hive loaded, cannot complete action. Use OpenHive to load a hive.'
  return False


def OpenHive(filename, collector=None, codepage='cp1252'):
  """Open a registry hive based on a collector or a filename."""
  if not collector:
    file_object = putils.OpenOSFile(filename)
  else:
    file_object = collector.OpenFile(filename)

  use_codepage = getattr(RegCache.pre_obj, 'code_page', codepage)

  win_registry = winregistry.WinRegistry(
      winregistry.WinRegistry.BACKEND_PYREGF)

  RegCache.hive = win_registry.OpenFile(file_object, codepage=use_codepage)
  RegCache.SetHiveType()
  RegCache.BuildCache()
  RegCache.cur_key = RegCache.hive.GetKeyByPath('\\')


def PrintEvent(event_object, show_hex=False):
  """Print information from an extracted EventObject."""
  fmt_length = 15
  for attribute in event_object.regvalue:
    if len(attribute) > fmt_length:
      fmt_length = len(attribute)

  fmt = u'{:>%ds} : {}' % fmt_length
  print utils.FormatHeader('Standard Attributes', '-')
  print fmt.format(
      'timestamp',
      timelib.Timestamp.CopyToIsoFormat(event_object.timestamp, pytz.utc))

  for attribute, value in event_object.GetValues().items():
    if attribute in ('timestamp', 'regvalue'):
      continue
    print fmt.format(attribute, value)

  print utils.FormatHeader('Attributes', '-')
  for attribute, value in event_object.regvalue.items():
    print fmt.format(attribute, value)

  if show_hex:
    # pylint: disable-msg=W0212
    event_object.pathspec = RegCache.hive.file_object.pathspec
    print utils.FormatHeader('Hex Output From Event.', '-')
    print putils.GetEventData(event_object, RegCache.fscache)


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
  for name, collector in collectors:
    print '*'*80
    print u'{:>15} : {}{}'.format('Hive File', hive_path, name)
    OpenHive(hive_path, collector)
    for key_str in keys:
      key_str_use = key_str
      key_dict = {}
      if RegCache.reg_cache:
        key_dict.update(RegCache.reg_cache.attributes.items())

      if RegCache.pre_obj:
        key_dict.update(RegCache.pre_obj.__dict__.items())

      try:
        key_str_use = key_str.format(**key_dict)
      except KeyError as e:
        logging.warning(
            u'Unable to format key string %s, error message: %s', key_str, e)

      key = RegCache.hive.GetKeyByPath(key_str_use)
      print u'{:>15} : {}'.format('Key Name', key_str_use)
      if not key:
        print 'Unable to open key: {}'.format(key_str_use)
        continue
      print u'{:>15} : {}'.format('Subkeys', key.number_of_subkeys)
      print u'{:>15} : {}'.format('Values', key.number_of_values)
      print ''

      if verbose:
        print '{:-^80}'.format(' SubKeys ')
        for subkey in key.GetSubkeys():
          print u'{:>15} : {}'.format('Key Name', subkey.path)

      print ''
      print '{:-^80}'.format(' Plugins ')
      ParseKey(key, verbose=verbose, use_plugins=use_plugins)


def ParseKey(key, verbose=False, use_plugins=None):
  """Parse a single registry key and print out parser information.

  Parses the registry key either using the supplied plugin or trying against
  all avilable plugins.

  Args:
    key: The registry key to parse, WinRegKey object or a string.
    verbose: Print additional information, such as a hex dump.
    use_plugins: A list of plugin names to use, or none if all should be used.
  """
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
  regplugins = win_registry_interface.GetRegistryPlugins()

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
        print u'{:^80}'.format(' ** Plugin : %s **' % plugin.plugin_name)
        for event_object in call_back:
          PrintEvent(event_object, verbose)
        print ''

  print '*'*80
  print ''


def FindRegistryPaths(pattern, collector):
  """Return a list of Windows registry file paths."""
  hive_paths = []
  try:
    file_path, _, file_name = pattern.rpartition('/')
    paths = list(collector.FindPaths(file_path))

    if not paths:
      logging.debug(u'No paths found for pattern [%s]' % file_path)
      return hive_paths

    for path in paths:
      fh_paths = list(collector.GetFilePaths(path, file_name))
      if not fh_paths:
        logging.debug(u'File [%s] not found in path [%s]....' % (
            file_name, path))
        continue
      for fh_path in fh_paths:
        hive_paths.append(fh_path)
  except errors.PreProcessFail as e:
    logging.debug('Path: %s not found, error: %s' % (pattern, e))
  except errors.PathNotFound as e:
    logging.debug('Path: %s not found, error: %s' % (pattern, e))

  return hive_paths


def ErrorAndDie(arg_parser, error):
  """Print error message and a help message."""
  arg_parser.print_help()
  print ''
  logging.error(error)
  sys.exit(1)


def Main():
  """Run the tool."""
  arg_parser = argparse.ArgumentParser(
      description=((
          'preg is a simple Windows registry parser using the plaso registry '
          'plugins and image parsing capabilities.')))

  arg_parser.add_argument(
      '-i', '--image', dest='image', action='store', type=str, default='',
      help=('If the registry file lies within an image, this is the path to '
            'that image file.'))

  arg_parser.add_argument(
      '-o', '--offset', dest='offset', action='store', type=int, default=0,
      help='Sector offset into the image, if one is provided.')

  arg_parser.add_argument(
      '-r', '--restore_points', dest='restore_points', action='store_true',
      default=False, help='Incldue restore points for hive locations.')

  arg_parser.add_argument(
      '-v', '--verbose', dest='verbose', action='store_true', default=False,
      help='Print sub key information.')

  arg_parser.add_argument(
      '--vss', dest='vss', action='store_true', default=False,
      help='Indicate that we are pulling the registry hive from VSS as well.')

  arg_parser.add_argument(
      '--vss-stores', dest='vss_stores', action='store', type=str, default=None,
      help=('List of stores to parse, format is X..Y where X and Y are intege'
            'rs, or a list of entries separated with a comma, eg: X,Y,Z or a '
            'list of ranges and entries, eg: X,Y-Z,G,H-J.'))

  arg_parser.add_argument(
      '-c', '--console', dest='console', action='store_true', default=False,
      help='Drop into a console session Instead of printing output to STDOUT.')

  arg_parser.add_argument(
      '--info', dest='info', action='store_true', default=False,
      help='Print out information about supported plugins.')

  arg_parser.add_argument(
      'regkey_or_plugin', action='store', metavar='REGKEY_OR_PLUGIN', nargs='?',
      help='The registry key to parse.')

  arg_parser.add_argument(
      'regfile', action='store', metavar='REGHIVE', nargs='?',
      help=('The registry hive to read key from (not needed if running using a '
            'plugin)'))

  options = arg_parser.parse_args()

  plugins = win_registry_interface.GetRegistryPlugins()

  # TODO: Move some of this logic to a separate function calls to make
  # GUI writing on top of this front-end simpler.

  if options.info:
    print utils.FormatHeader('Supported Plugins')
    key_plugin = plugins.GetAllKeyPlugins()[0]

    for plugin, obj in sorted(key_plugin.classes.items()):
      doc_string, _, _ = obj.__doc__.partition('\n')
      print utils.FormatOutputString(plugin, doc_string)
    sys.exit(0)

  if not options.regkey_or_plugin and not options.regfile:
    ErrorAndDie(arg_parser, (
        'Wrong usage, need to define either an image path or a '
        'registry file.'))

  if not options.image and not options.regkey_or_plugin:
    ErrorAndDie(
        arg_parser, 'Wrong usage, must provide hive, key or plugins.')

  if options.image:
    if not os.path.isfile(options.image):
      ErrorAndDie(arg_parser, 'Image file must exist.')
  else:
    if options.regfile:
      if not os.path.isfile(options.regfile):
        ErrorAndDie(
            arg_parser, 'Registry file must exist [{}] does not exist.'.format(
                options.regfile))
    else:
      if not options.regkey_or_plugin:
        ErrorAndDie(arg_parser, 'Not enough parameters to proceed.')
      if not os.path.isfile(options.regkey_or_plugin):
        ErrorAndDie(
            arg_parser, 'Not a registry file: {}'.format(
                options.regkey_or_plugin))

  RegCache.pre_obj = preprocess.PlasoPreprocess()
  RegCache.pre_obj.zone = pytz.UTC

  hives = []
  collector = None
  vss_collectors = {}

  if options.vss_stores:
    options.vss = True
    stores = []
    try:
      for store in options.vss_stores.split(','):
        if '..' in store:
          begin, end = store.split('..')
          for nr in range(int(begin), int(end)):
            if nr not in stores:
              stores.append(nr)
        else:
          if int(store) not in stores:
            stores.append(int(store))
    except ValueError:
      arg_parser.print_help()
      print ''
      logging.error('VSS store range is wrongly formed.')
      sys.exit(1)

    options.vss_stores = sorted(stores)

  key_plugin_names = []
  for plugin in plugins.GetAllKeyPlugins():
    temp_obj = plugin(None, None, None)
    key_plugin_names.append(temp_obj.plugin_name)

  # TODO: Add the option of selecting registry types instead of a key name.
  # This will be something like 'ntuser', which will pick all keys implementing
  # the NTUSER registry type.

  # Determine if we are running against a plugin or a key (behavior differs).
  plugins_to_run = []
  for key_plugin in key_plugin_names:
    if options.regkey_or_plugin.lower() in key_plugin.lower():
      plugins_to_run.append(key_plugin)

  paths = []
  keys = []
  if plugins_to_run:
    if options.restore_points:
      restore_path = '/System Volume Information/_restor.+/RP[0-9]+/snapshot/'
    # Gather the registry files to fetch.
    types = []
    for plugin in plugins_to_run:
      for reg_plugin in plugins.GetAllKeyPlugins():
        temp_obj = reg_plugin(None, None, None)
        if plugin is temp_obj.plugin_name:
          if temp_obj.REG_KEY not in keys:
            keys.append(temp_obj.REG_KEY)
          if temp_obj.REG_TYPE not in types:
            types.append(temp_obj.REG_TYPE)

    for reg_type in types:
      if reg_type == 'NTUSER':
        paths.append('/Documents And Settings/.+/NTUSER.DAT')
        paths.append('/Users/.+/NTUSER.DAT')
        if options.restore_points:
          paths.append('{}/_REGISTRY_USER_NTUSER.+'.format(restore_path))
      elif reg_type == 'SOFTWARE':
        paths.append('{sysregistry}/SOFTWARE')
        if options.restore_points:
          paths.append('{}/_REGISTRY_MACHINE_SOFTWARE'.format(restore_path))
      elif reg_type == 'SYSTEM':
        paths.append('{sysregistry}/SYSTEM')
        if options.restore_points:
          paths.append('{}/_REGISTRY_MACHINE_SYSTEM'.format(restore_path))
      elif reg_type == 'SECURITY':
        paths.append('{sysregistry}/SECURITY')
        if options.restore_points:
          paths.append('{}/_REGISTRY_MACHINE_SECURITY'.format(restore_path))
      elif reg_type == 'SAM':
        paths.append('{sysregistry}/SAM')
        if options.restore_points:
          paths.append('{}/_REGISTRY_MACHINE_SAM'.format(restore_path))

  if options.image:
    if not os.path.isfile(options.image):
      print 'Image must be a file ({})'.format(options.image)
      sys.exit(1)

    RegCache.fscache = pfile.FilesystemCache()
    collector = preprocess.TSKFileCollector(
        RegCache.pre_obj, options.image, options.offset * 512)

    # Run pre processing on image.
    pre_plugin_list = preprocessors.PreProcessList(RegCache.pre_obj, collector)
    guessed_os = preprocess.GuessOS(collector)
    for weight in pre_plugin_list.GetWeightList(guessed_os):
      for plugin in pre_plugin_list.GetWeight(guessed_os, weight):
        try:
          plugin.Run()
        except (IOError, errors.PreProcessFail) as e:
          logging.warning(u'Unable to run plugin: {}, reason {}'.format(
              plugin.plugin_name, e))

    if options.regfile:
      hives = FindRegistryPaths(options.regfile, collector)
    elif paths:
      hives = []
      for path in paths:
        hives.extend(FindRegistryPaths(path, collector))
    else:
      # Check if hive path is given in other option.
      if '/' in options.regkey_or_plugin:
        hives = FindRegistryPaths(options.regkey_or_plugin, collector)

    # Check for VSS.
    if options.vss:
      if not options.vss_stores:
        options.vss_stores = range(0, vss.GetVssStoreCount(
            options.image, options.offset * 512))

      for store in options.vss_stores:
        vss_collectors[store + 1] = preprocess.VSSFileCollector(
            RegCache.pre_obj, options.image, store, options.offset * 512)

    if len(hives) == 1:
      OpenHive(hives[0], collector)
      if not options.vss:
        hives = []
  else:
    if options.regfile:
      OpenHive(options.regfile)
    elif options.regkey_or_plugin and os.path.isfile(options.regkey_or_plugin):
      OpenHive(options.regkey_or_plugin)

  if options.console:
    namespace = {}
    namespace.update(globals())
    namespace.update(
        {'collector': collector, 'hives': hives,
         'vss_collectors': vss_collectors})

    function_name_length = 15
    banners = []
    banners.append(utils.FormatHeader(
        'Welcome to PREG - home of the Plaso Windows Registry Parsing.'))
    banners.append('')
    banners.append('Some of the commands that are available for use are:')
    banners.append('')
    banners.append(utils.FormatOutputString(
        'cd(key)', 'Navigate the registry like a directory structure.',
        function_name_length))
    banners.append(utils.FormatOutputString(
        'ls(verbose)', ('List all subkeys and values of a registry key. If '
                        'verbose is True then values of keys will be included'
                        ' in the output.'),
        function_name_length))
    banners.append(utils.FormatOutputString(
        'parse(verbose)', 'Parse the current key using all plugins.',
        function_name_length))

    banners.append('')

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
      banners.append(utils.FormatOutputString(text, (
          'Collector is an available attribute and NR is a number ranging'
          ' from 0 to %d (see above which files these numbers belong to).'
          ' To get the name of the loaded hive use RegCache.GetHiveName()'
          ' and RegCache.hive_type to get the '
          'type.') % (len(hives) + 1), len(text)))

    if vss_collectors:
      banners.append('')
      banners.append((
          'VSS collectors are available. To use any of them use vss_collectors'
          '[NR]\n instead of the attribute "collector" in the OpenHive '
          'function.\nThe available VSS stores are:'))
      for store in vss_collectors:
        banners.append(' - NR: {}'.format(store))

    banners.append('')
    banners.append('Happy command line console fu-ing.')

    ipshell = InteractiveShellEmbed(
        user_ns=namespace, banner1=u'\n'.join(banners), exit_msg='')
    ipshell.confirm_exit = False
    ipshell()
    sys.exit(0)

  collectors = [('', collector)]
  if options.vss:
    for store, vss_collector in vss_collectors.items():
      collectors.append(('VSS Store {}'.format(store), vss_collector))

  if not keys:
    if '\\' not in options.regkey_or_plugin:
      ErrorAndDie(arg_parser, u'Key not correctly formed: {}'.format(
          options.regkey_or_plugin))

    keys = [options.regkey_or_plugin]

  # "Fix" for Windows redirect.
  for key in keys:
    if key.startswith('\\Software') and 'Wow6432Node' not in key:
      _, first, second = key.partition('\\Software')
      keys.append(u'{}\\Wow6432Node{}'.format(first, second))

  if not hives:
    if RegCache.GetHiveName() == 'N/A':
      ErrorAndDie(arg_parser, 'No hive open, cannot continue.')
    hives = [RegCache.GetHiveName()]

  for hive in hives:
    ParseHive(hive, collectors, keys, plugins_to_run, options.verbose)


if __name__ == '__main__':
  Main()
