#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Parse your Windows Registry files using preg.

preg is a simple Windows Registry parser using the plaso Registry plugins and
image parsing capabilities. It uses the back-end libraries of plaso to read
raw image files and extract Registry files from VSS and restore points and then
runs the Registry plugins of plaso against the Registry hive and presents it
in a textual format.
"""

import argparse
import binascii
import logging
import os
import re
import sys
import textwrap

try:
  # Support version 1.X of IPython.
  # pylint: disable=no-name-in-module
  from IPython.terminal.embed import InteractiveShellEmbed
except ImportError:
  # pylint: disable=no-name-in-module
  from IPython.frontend.terminal.embed import InteractiveShellEmbed

import IPython
from IPython.config.loader import Config
from IPython.core import magic

# Import the winreg formatter to register it, adding the option
# to print event objects using the default formatter.
# pylint: disable=unused-import
from plaso.formatters import winreg as winreg_formatter

from plaso.cli import storage_media_tool
from plaso.cli import tools as cli_tools
from plaso.frontend import frontend
from plaso.frontend import preg
from plaso.frontend import utils as frontend_utils
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import manager as parsers_manager
from plaso.parsers import winreg as winreg_parser
from plaso.parsers import winreg_plugins  # pylint: disable=unused-import
from plaso.preprocessors import interface as preprocess_interface
from plaso.preprocessors import manager as preprocess_manager
from plaso.winreg import cache
from plaso.winreg import path_expander as winreg_path_expander
from plaso.winreg import winregistry


# Older versions of IPython don't have a version_info attribute.
if getattr(IPython, 'version_info', (0, 0, 0)) < (1, 2, 1):
  raise ImportWarning(
      'Preg requires at least IPython version 1.2.1.')


class ConsoleConfig(object):
  """Class that contains functions to configure console actions."""

  @classmethod
  def GetConfig(cls):
    """Retrieves the iPython config.

    Returns:
      The IPython config object (instance of
      IPython.terminal.embed.InteractiveShellEmbed)
    """
    try:
      # The "get_ipython" function does not exist except within an IPython
      # session.
      return get_ipython()  # pylint: disable=undefined-variable
    except NameError:
      return Config()

  @classmethod
  def SetPrompt(
      cls, hive_path=None, config=None, prepend_string=None):
    """Sets the prompt string on the console.

    Args:
      hive_path: The hive name or path as a string, this is optional name or
                 location of the loaded hive. If not defined the name is derived
                 from a default string.
      config: The IPython configuration object (instance of
              IPython.terminal.embed.InteractiveShellEmbed), this is optional
              and is automatically derived if not used.
      prepend_string: An optional string that can be injected into the prompt
                      just prior to the command count.
    """
    if hive_path is None:
      path_string = u'Unknown hive loaded'
    else:
      path_string = hive_path

    prompt_strings = [
        r'[{color.LightBlue}\T{color.Normal}]',
        r'{color.LightPurple} ',
        path_string,
        r'\n{color.Normal}']
    if prepend_string is not None:
      prompt_strings.append(u'{0:s} '.format(prepend_string))
    prompt_strings.append(r'[{color.Red}\#{color.Normal}] \$ ')

    if config is None:
      ipython_config = cls.GetConfig()
    else:
      ipython_config = config

    try:
      ipython_config.PromptManager.in_template = r''.join(prompt_strings)
    except AttributeError:
      ipython_config.prompt_manager.in_template = r''.join(prompt_strings)


def CdCompleter(unused_self, unused_event):
  """Completer function for the cd command, returning back sub keys."""
  return_list = []
  current_hive = preg.PregCache.hive_storage.loaded_hive
  current_key = current_hive.GetCurrentRegistryKey()
  for key in current_key.GetSubkeys():
    return_list.append(key.name)

  return return_list


def PluginCompleter(unused_self, event_object):
  """Completer function that returns a list of available plugins."""
  ret_list = []

  if not IsLoaded():
    return ret_list

  if not '-h' in event_object.line:
    ret_list.append('-h')

  plugins_list = parsers_manager.ParsersManager.GetWindowsRegistryPlugins()

  current_hive = preg.PregCache.hive_storage.loaded_hive
  hive_type = current_hive.type

  for plugin_cls in plugins_list.GetKeyPlugins(hive_type):
    plugins_list = plugin_cls(reg_cache=current_hive.reg_cache)

    plugin_name = plugins_list.plugin_name

    if plugin_name == 'winreg_default':
      continue
    ret_list.append(plugin_name)

  return ret_list


def VerboseCompleter(unused_self, event_object):
  """Completer function that suggests simple verbose settings."""
  if '-v' in event_object.line:
    return []
  else:
    return ['-v']


@magic.magics_class
class MyMagics(magic.Magics):
  """A simple class holding all magic functions for console."""

  EXPANSION_KEY_OPEN = r'{'
  EXPANSION_KEY_CLOSE = r'}'

  # Match against one instance, not two of the expansion key.
  EXPANSION_RE = re.compile(r'{0:s}{{1}}[^{1:s}]+?{1:s}'.format(
      EXPANSION_KEY_OPEN, EXPANSION_KEY_CLOSE))

  output_writer = sys.stdout

  @magic.line_magic('cd')
  def ChangeDirectory(self, key):
    """Change between Registry keys, like a directory tree.

    The key path can either be an absolute path or a relative one.
    Absolute paths can use '.' and '..' to denote current and parent
    directory/key path.

    Args:
      key: The path to the key to traverse to.
    """
    registry_key = None
    key_path = key

    if not key:
      self.ChangeDirectory('\\')

    loaded_hive = preg.PregCache.hive_storage.loaded_hive

    if not loaded_hive:
      return

    # Check if we need to expand environment attributes.
    match = self.EXPANSION_RE.search(key)
    if match and u'{0:s}{0:s}'.format(
        self.EXPANSION_KEY_OPEN) not in match.group(0):
      try:
        key = loaded_hive.path_expander.ExpandPath(
            key, pre_obj=preg.PregCache.knowledge_base_object.pre_obj)
      except (KeyError, IndexError):
        pass

    if key.startswith(u'\\'):
      registry_key = loaded_hive.GetKeyByPath(key)
    elif key == '.':
      return
    elif key.startswith(u'.\\'):
      current_path = loaded_hive.GetCurrentRegistryPath()
      _, _, key_path = key.partition(u'\\')
      registry_key = loaded_hive.GetKeyByPath(u'{0:s}\\{1:s}'.format(
          current_path, key_path))
    elif key.startswith(u'..'):
      parent_path, _, _ = loaded_hive.GetCurrentRegistryPath().rpartition(u'\\')
      # We know the path starts with a "..".
      if len(key) == 2:
        key_path = u''
      else:
        key_path = key[3:]
      if parent_path:
        if key_path:
          path = u'{0:s}\\{1:s}'.format(parent_path, key_path)
        else:
          path = parent_path
        registry_key = loaded_hive.GetKeyByPath(path)
      else:
        registry_key = loaded_hive.GetKeyByPath(u'\\{0:s}'.format(key_path))

    else:
      # Check if key is not set at all, then assume traversal from root.
      if not loaded_hive.GetCurrentRegistryPath():
        _ = loaded_hive.GetKeyByPath(u'\\')

      current_key = loaded_hive.GetCurrentRegistryKey()
      if current_key.name == loaded_hive.root_key.name:
        key_path = u'\\{0:s}'.format(key)
      else:
        key_path = u'{0:s}\\{1:s}'.format(current_key.path, key)
      registry_key = loaded_hive.GetKeyByPath(key_path)

    if registry_key:
      if key_path == '\\':
        path = '\\'
      else:
        path = registry_key.path

      ConsoleConfig.SetPrompt(
          hive_path=loaded_hive.path,
          prepend_string=StripCurlyBrace(path).replace('\\', '\\\\'))
    else:
      print u'Unable to change to: {0:s}'.format(key_path)

  @magic.line_magic('hive')
  def HiveActions(self, line):
    """Define the hive command on the console prompt."""
    if line.startswith('list'):
      print preg.PregCache.hive_storage.ListHives()

      print u''
      print u'To open a hive, use: hive_open INDEX'
    elif line.startswith('open ') or line.startswith('load '):
      preg.PregCache.hive_storage.SetOpenHive(line[5:])
      hive_helper = preg.PregCache.hive_storage.loaded_hive
      print u'Opening hive: {0:s} [{1:s}]'.format(
          hive_helper.path, hive_helper.collector_name)
      ConsoleConfig.SetPrompt(hive_path=hive_helper.path)
    elif line.startswith('scan'):
      items = line.split()
      if len(items) < 2:
        print (
            u'Unable to scan for an empty keyword. Please specify a keyword, '
            u'eg: NTUSER, SOFTWARE, etc')
        return

      preg.PregCache.hive_storage.Scan(items[1:])

  @magic.line_magic('ls')
  def ListDirectoryContent(self, line):
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
    current_hive = preg.PregCache.hive_storage.loaded_hive
    if not current_hive:
      return

    current_key = current_hive.GetCurrentRegistryKey()
    for key in current_key.GetSubkeys():
      # TODO: move this construction into a separate function in OutputWriter.
      timestamp, _, _ = frontend_utils.OutputWriter.GetDateTimeString(
          key.last_written_timestamp).partition('.')

      sub.append((u'{0:>19s} {1:>15s}  {2:s}'.format(
          timestamp.replace('T', ' '), '[KEY]',
          key.name), True))

    for value in current_key.GetValues():
      if not verbose:
        sub.append((u'{0:>19s} {1:>14s}]  {2:s}'.format(
            u'', '[' + value.data_type_string, value.name), False))
      else:
        if value.DataIsString():
          value_string = u'{0:s}'.format(value.data)
        elif value.DataIsInteger():
          value_string = u'{0:d}'.format(value.data)
        elif value.DataIsMultiString():
          value_string = u'{0:s}'.format(u''.join(value.data))
        elif value.DataIsBinaryData():
          hex_string = binascii.hexlify(value.data)
          # We'll just print the first few bytes, but we need to pad them
          # to make it fit in a single line if shorter.
          if len(hex_string) % 32:
            breakpoint = len(hex_string) / 32
            leftovers = hex_string[breakpoint:]
            pad = ' ' * (32 - len(leftovers))
            hex_string += pad

          value_string = frontend_utils.OutputWriter.GetHexDumpLine(
              hex_string, 0)
        else:
          value_string = u''

        sub.append((
            u'{0:>19s} {1:>14s}]  {2:<25s}  {3:s}'.format(
                u'', '[' + value.data_type_string, value.name, value_string),
            False))

    for entry, subkey in sorted(sub):
      if subkey:
        self.output_writer.write(u'dr-xr-xr-x {0:s}\n'.format(entry))
      else:
        self.output_writer.write(u'-r-xr-xr-x {0:s}\n'.format(entry))

  @magic.line_magic('parse')
  def ParseCurrentKey(self, line):
    """Parse the current key."""
    if 'true' in line.lower():
      verbose = True
    elif '-v' in line.lower():
      verbose = True
    else:
      verbose = False

    if not IsLoaded():
      return

    current_hive = preg.PregCache.hive_storage.loaded_hive
    if not current_hive:
      return

    # Clear the last results from parse key.
    preg.PregCache.events_from_last_parse = []

    print_strings = preg.ParseKey(
        key=current_hive.GetCurrentRegistryKey(), hive_helper=current_hive,
        shell_helper=preg.PregCache.shell_helper, verbose=verbose)
    self.output_writer.write(u'\n'.join(print_strings))

    # Print out a hex dump of all binary values.
    if verbose:
      header_shown = False
      for value in current_hive.GetCurrentRegistryKey().GetValues():
        if value.DataIsBinaryData():
          if not header_shown:
            header_shown = True
            print frontend_utils.FormatHeader('Hex Dump')
          # Print '-' 80 times.
          self.output_writer.write(u'-'*80)
          self.output_writer.write(u'\n')
          self.output_writer.write(
              frontend_utils.FormatOutputString('Attribute', value.name))
          self.output_writer.write(u'-'*80)
          self.output_writer.write(u'\n')
          self.output_writer.write(
              frontend_utils.OutputWriter.GetHexDump(value.data))
          self.output_writer.write(u'\n')
          self.output_writer.write(u'+-'*40)
          self.output_writer.write(u'\n')

    self.output_writer.flush()

  @magic.line_magic('plugin')
  def ParseWithPlugin(self, line):
    """Parse a Registry key using a specific plugin."""
    if not IsLoaded():
      print u'No hive loaded, unable to parse.'
      return

    current_hive = preg.PregCache.hive_storage.loaded_hive
    if not current_hive:
      return

    if not line:
      print u'No plugin name added.'
      return

    plugin_name = line
    if '-h' in line:
      items = line.split()
      if len(items) != 2:
        print u'Wrong usage: plugin [-h] PluginName'
        return
      if items[0] == '-h':
        plugin_name = items[1]
      else:
        plugin_name = items[0]

    hive_type = current_hive.type
    plugins_list = parsers_manager.ParsersManager.GetWindowsRegistryPlugins()
    plugin_found = False
    for plugin_cls in plugins_list.GetKeyPlugins(hive_type):
      plugin = plugin_cls(reg_cache=current_hive.reg_cache)
      if plugin.plugin_name == plugin_name:
        # If we found the correct plugin.
        plugin_found = True
        break

    if not plugin_found:
      print u'No plugin named: {0:s} available for Registry type {1:s}'.format(
          plugin_name, hive_type)
      return

    if not hasattr(plugin, 'REG_KEYS'):
      print u'Plugin: {0:s} has no key information.'.format(line)
      return

    if '-h' in line:
      print frontend_utils.FormatHeader(plugin_name)
      print frontend_utils.FormatOutputString('Description', plugin.__doc__)
      print u''
      for registry_key in plugin.expanded_keys:
        print frontend_utils.FormatOutputString('Registry Key', registry_key)
      return

    if not plugin.expanded_keys:
      plugin.ExpandKeys(preg.PregCache.parser_mediator)

    # Clear the last results from parse key.
    preg.PregCache.events_from_last_parse = []

    # Defining outside of for loop for optimization.
    get_key_by_path = current_hive.GetKeyByPath
    for registry_key in plugin.expanded_keys:
      key = get_key_by_path(registry_key)
      if not key:
        print u'Key: {0:s} not found'.format(registry_key)
        continue

      # Move the current location to the key to be parsed.
      self.ChangeDirectory(registry_key)
      # Parse the key.
      print_strings = preg.ParseKey(
          key=current_hive.GetCurrentRegistryKey(), hive_helper=current_hive,
          shell_helper=preg.PregCache.shell_helper, verbose=False,
          use_plugins=[plugin_name])
      self.output_writer.write(u'\n'.join(print_strings))
    self.output_writer.flush()

  @magic.line_magic('pwd')
  def PrintCurrentWorkingDirectory(self, unused_line):
    """Print the current path."""
    if not IsLoaded():
      return

    current_hive = preg.PregCache.hive_storage.loaded_hive
    if not current_hive:
      return

    self.output_writer.write(u'{0:s}\n'.format(
        current_hive.GetCurrentRegistryPath()))

  @magic.line_magic('redirect_output')
  def RedirectOutput(self, output_object):
    """Change the output writer to redirect plugin output to a file."""

    if isinstance(output_object, basestring):
      output_object = open(output_object, 'wb')

    if hasattr(output_object, 'write'):
      self.output_writer = output_object


def StripCurlyBrace(string):
  """Return a format "safe" string."""
  return string.replace('}', '}}').replace('{', '{{')


def IsLoaded():
  """Checks if a Windows Registry Hive is loaded."""
  current_hive = preg.PregCache.hive_storage.loaded_hive
  if not current_hive:
    return False

  current_key = current_hive.GetCurrentRegistryKey()
  if hasattr(current_key, 'path'):
    return True

  if current_hive.name != 'N/A':
    return True

  print (
      u'No hive loaded, cannot complete action. Use "hive list" '
      u'and "hive open" to load a hive.')
  return False


def GetValue(value_name):
  """Return a value object from the currently loaded Registry key.

  Args:
    value_name: A string containing the name of the value to be retrieved.

  Returns:
    The Registry value (instance of WinPyregfValue) if it exists, None if
    either there is no currently loaded Registry key or if the value does
    not exist.
  """
  current_hive = preg.PregCache.hive_storage.loaded_hive
  current_key = current_hive.GetCurrentRegistryKey()

  if not current_key:
    return

  return current_key.GetValue(value_name)


def GetValueData(value_name):
  """Return the value data from a value in the currently loaded Registry key.

  Args:
    value_name: A string containing the name of the value to be retrieved.

  Returns:
    The data from a Registry value if it exists, None if either there is no
    currently loaded Registry key or if the value does not exist.
  """
  value = GetValue(value_name)

  if not value:
    return

  return value.data


def GetCurrentKey():
  """Return the currently loaded Registry key (instance of WinPyregfKey).

  Returns:
    The currently loaded Registry key (instance of WinPyregfKey) or None
    if there is no loaded key.
  """
  current_hive = preg.PregCache.hive_storage.loaded_hive
  return current_hive.GetCurrentRegistryKey()


def GetRangeForAllLoadedHives():
  """Return a range or a list of all loaded hives."""
  return range(0, GetTotalNumberOfLoadedHives())


def GetTotalNumberOfLoadedHives():
  """Return the total number of Registy hives that are loaded."""
  return len(preg.PregCache.hive_storage)


def RunModeConsole(front_end, options):
  """Open up an iPython console.

  Args:
    options: the command line arguments (instance of argparse.Namespace).
  """
  namespace = {}

  function_name_length = 23
  banners = []
  banners.append(frontend_utils.FormatHeader(
      u'Welcome to PREG - home of the Plaso Windows Registry Parsing.'))
  banners.append(u'')
  banners.append(u'Some of the commands that are available for use are:')
  banners.append(u'')
  banners.append(frontend_utils.FormatOutputString(
      u'cd key', u'Navigate the Registry like a directory structure.',
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      u'ls [-v]', (
          u'List all subkeys and values of a Registry key. If called as '
          u'ls True then values of keys will be included in the output.'),
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      u'parse -[v]', u'Parse the current key using all plugins.',
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      u'pwd', u'Print the working "directory" or the path of the current key.',
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      u'plugin [-h] plugin_name', (
          u'Run a particular key-based plugin on the loaded hive. The correct '
          u'Registry key will be loaded, opened and then parsed.'),
      function_name_length))
  banners.append(frontend_utils.FormatOutputString(
      u'get_value value_name', (
          u'Get a value from the currently loaded Registry key.')))
  banners.append(frontend_utils.FormatOutputString(
      u'get_value_data value_name', (
          u'Get a value data from a value stored in the currently loaded '
          u'Registry key.')))
  banners.append(frontend_utils.FormatOutputString(
      u'get_key', u'Return the currently loaded Registry key.'))

  banners.append(u'')

  # Build the global cache and prepare the tool.
  hive_storage = preg.PregStorage()
  shell_helper = preg.PregHelper(options, front_end, hive_storage)
  parser_mediator = shell_helper.BuildParserMediator()

  preg.PregCache.parser_mediator = parser_mediator
  preg.PregCache.shell_helper = shell_helper
  preg.PregCache.hive_storage = hive_storage

  registry_types = getattr(options, 'regfile', None)
  if isinstance(registry_types, basestring):
    registry_types = registry_types.split(u',')

  if not registry_types:
    registry_types = [
        'NTUSER', 'USRCLASS', 'SOFTWARE', 'SYSTEM', 'SAM', 'SECURITY']
  preg.PregCache.shell_helper.Scan(registry_types)

  if len(preg.PregCache.hive_storage) == 1:
    preg.PregCache.hive_storage.SetOpenHive(0)
    hive_helper = preg.PregCache.hive_storage.loaded_hive
    banners.append(
        u'Opening hive: {0:s} [{1:s}]'.format(
            hive_helper.path, hive_helper.collector_name))
    ConsoleConfig.SetPrompt(hive_path=hive_helper.path)

  loaded_hive = preg.PregCache.hive_storage.loaded_hive

  if loaded_hive and loaded_hive.name != u'N/A':
    banners.append(
        u'Registry hive: {0:s} is available and loaded.'.format(
            loaded_hive.name))
  else:
    banners.append(u'More than one Registry file ready for use.')
    banners.append(u'')
    banners.append(preg.PregCache.hive_storage.ListHives())
    banners.append(u'')
    banners.append((
        u'Use "hive open INDEX" to load a hive and "hive list" to see a '
        u'list of available hives.'))

  banners.append(u'')
  banners.append(u'Happy command line console fu-ing.')

  # Adding variables in scope.
  namespace.update(globals())
  namespace.update({
      'get_current_key': GetCurrentKey,
      'get_key': GetCurrentKey,
      'get_value': GetValue,
      'get_value_data': GetValueData,
      'number_of_hives': GetTotalNumberOfLoadedHives,
      'range_of_hives': GetRangeForAllLoadedHives,
      'options': options})

  ipshell_config = ConsoleConfig.GetConfig()

  if loaded_hive:
    ConsoleConfig.SetPrompt(
        hive_path=loaded_hive.name, config=ipshell_config)
  else:
    ConsoleConfig.SetPrompt(hive_path=u'NO HIVE LOADED', config=ipshell_config)

  # Starting the shell.
  ipshell = InteractiveShellEmbed(
      user_ns=namespace, config=ipshell_config, banner1=u'\n'.join(banners),
      exit_msg='')
  ipshell.confirm_exit = False
  # Adding "magic" functions.
  ipshell.register_magics(MyMagics)
  # Set autocall to two, making parenthesis not necessary when calling
  # function names (although they can be used and are necessary sometimes,
  # like in variable assignments, etc).
  ipshell.autocall = 2
  # Registering command completion for the magic commands.
  ipshell.set_hook('complete_command', CdCompleter, str_key='%cd')
  ipshell.set_hook('complete_command', VerboseCompleter, str_key='%ls')
  ipshell.set_hook('complete_command', VerboseCompleter, str_key='%parse')
  ipshell.set_hook('complete_command', PluginCompleter, str_key='%plugin')

  ipshell()


def Main():
  """Run the tool."""
  input_reader = cli_tools.StdinInputReader()
  output_writer = cli_tools.StdoutOutputWriter()

  front_end = preg.PregFrontend(output_writer)
  storage_media_frontend = storage_media_tool.StorageMediaTool(
      input_reader, output_writer)

  epilog = textwrap.dedent("""

Example usage:

Parse the SOFTWARE hive from an image:
  {0:s} [--vss] [--vss-stores VSS_STORES] -i IMAGE_PATH [-o OFFSET] -c SOFTWARE

Parse an userassist key within an extracted hive:
  {0:s} -p userassist MYNTUSER.DAT

Parse the run key from all Registry keys (in vss too):
  {0:s} --vss -i IMAGE_PATH [-o OFFSET] -p run

Open up a console session for the SYSTEM hive inside an image:
  {0:s} -i IMAGE_PATH [-o OFFSET] -c SYSTEM
      """).format(os.path.basename(sys.argv[0]))

  description = textwrap.dedent("""
preg is a simple Windows Registry parser using the plaso Registry
plugins and image parsing capabilities.

It uses the back-end libraries of plaso to read raw image files and
extract Registry files from VSS and restore points and then runs the
Registry plugins of plaso against the Registry hive and presents it
in a textual format.

      """)

  arg_parser = argparse.ArgumentParser(
      epilog=epilog, description=description, add_help=False,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  # Create the different argument groups.
  mode_options = arg_parser.add_argument_group(u'Run Mode Options')
  image_options = arg_parser.add_argument_group(u'Image Options')
  info_options = arg_parser.add_argument_group(u'Informational Options')
  additional_data = arg_parser.add_argument_group(u'Additional Options')

  mode_options.add_argument(
      '-c', '--console', dest='console', action='store_true', default=False,
      help=u'Drop into a console session Instead of printing output to STDOUT.')

  additional_data.add_argument(
      '-r', '--restore_points', dest='restore_points', action='store_true',
      default=False, help=u'Include restore points for hive locations.')

  image_options.add_argument(
      '-i', '--image', dest='image', action='store', type=unicode, default='',
      metavar='IMAGE_PATH',
      help=(u'If the Registry file is contained within a storage media image, '
            u'set this option to specify the path of image file.'))

  storage_media_frontend.AddStorageMediaImageOptions(image_options)

  info_options.add_argument(
      '-v', '--verbose', dest='verbose', action='store_true', default=False,
      help=u'Print sub key information.')

  info_options.add_argument(
      '-h', '--help', action='help', help=u'Show this help message and exit.')

  storage_media_frontend.AddVssProcessingOptions(additional_data)

  info_options.add_argument(
      '--info', dest='info', action='store_true', default=False,
      help=u'Print out information about supported plugins.')

  mode_options.add_argument(
      '-p', '--plugins', dest='plugin_names', action='append', default=[],
      type=unicode, metavar='PLUGIN_NAME',
      help=(
          u'Substring match of the Registry plugin to be used, this '
          u'parameter can be repeated to create a list of plugins to be '
          u'run against, eg: "-p userassist -p rdp" or "-p userassist".'))

  mode_options.add_argument(
      '-k', '--key', dest='key', action='store', default='', type=unicode,
      metavar='REGISTRY_KEYPATH',
      help=(u'A Registry key path that the tool should parse using all '
            u'available plugins.'))

  arg_parser.add_argument(
      'regfile', action='store', metavar='REGHIVE', nargs='?',
      help=(u'The Registry hive to read key from (not needed if running '
            u'using a plugin)'))

  # Parse the command line arguments.
  options = arg_parser.parse_args()

  if options.info:
    print front_end.GetListOfAllPlugins()
    return True

  try:
    front_end.ParseOptions(options)
  except errors.BadConfigOption as exception:
    arg_parser.print_usage()
    print u''
    logging.error('{0:s}'.format(exception))
    return False

  # Run the tool, using the run mode according to the options passed
  # to the tool.
  if front_end.run_mode == front_end.RUN_MODE_CONSOLE:
    RunModeConsole(front_end, options)
  if front_end.run_mode == front_end.RUN_MODE_REG_KEY:
    front_end.RunModeRegistryKey(options, options.plugin_names)
  elif front_end.run_mode == front_end.RUN_MODE_REG_PLUGIN:
    front_end.RunModeRegistryPlugin(options, options.plugin_names)
  elif front_end.run_mode == front_end.RUN_MODE_REG_FILE:
    front_end.RunModeRegistryFile(options, options.regfile)

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
