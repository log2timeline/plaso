# -*- coding: utf-8 -*-
"""Plist parser plugin for MacOS launchd plist files."""

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class MacOSLaunchdEventData(events.EventData):
  """MacOS launchd event data.

  Attributes:
    name (str): name.
    group_name (str): name of the group.
    program (str): program and arguments.
    user_name (str): name of the user.
  """

  DATA_TYPE = 'macos:launchd:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSLaunchdEventData, self).__init__(data_type=self.DATA_TYPE)
    self.name = None
    self.group_name = None
    self.program = None
    self.user_name = None


class MacOSLaunchdPlistPlugin(interface.PlistPlugin):
  """Plist parser plugin for MacOS launchd plist files.

  Further details about fields within the key:
    Label:
      the required key for uniquely identifying the launchd service.
    Program:
      absolute path to the executable. required in the absence of the
      ProgramArguments key.
    ProgramArguments:
      command-line flags for the executable. required in the absence of the
      Program key.
    UserName:
      the job run as the specified user.
    GroupName:
      the job run as the specified group.
  """

  NAME = 'launchd_plist'
  DATA_FORMAT = 'Launchd plist file'

  # The PLIST_PATH is dynamic, the prefix filename is, by default, named using
  # reverse-domain notation. For example, Chrome is com.google.chrome.plist.
  # /System/Library/LaunchDaemons/*.plist
  # /System/Library/LaunchAgents/*.plist
  # /Library/LaunchDaemons/*.plist
  # /Library/LaunchAgents/*.plist
  # ~/Library/LaunchAgents

  PLIST_KEYS = frozenset([
      'GroupName',
      'Label',
      'Program',
      'ProgramArguments',
      'UserName'])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts launchd information from the plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfVFS.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """
    program = top_level.get('Program', None)
    program_arguments = top_level.get('ProgramArguments', None)
    if program and program_arguments:
      program = ' '.join([program, ' '.join(program_arguments)])

    event_data = MacOSLaunchdEventData()
    event_data.group_name = top_level.get('GroupName')
    event_data.name = top_level.get('Label')
    event_data.program = program
    event_data.user_name = top_level.get('UserName')

    parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MacOSLaunchdPlistPlugin)
