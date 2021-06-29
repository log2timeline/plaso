# -*- coding: utf-8 -*-
"""Plist parser plugin for launchd plist files."""

from dfdatetime import semantic_time as dfdatetime_semantic_time

from plaso.containers import plist_event
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class LaunchdPlugin(interface.PlistPlugin):
  """Plist parser plugin for launchd plist files.

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
      'Label',
      'Program',
      'ProgramArguments',
      'UserName',
      'GroupName',
  ])

  # pylint: disable=arguments-differ
  def _ParsePlist(self, parser_mediator, top_level=None, **unused_kwargs):
    """Extracts launchd information from the plist.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfvfs.
      top_level (Optional[dict[str, object]]): plist top-level item.
    """

    label = top_level.get('Label')
    command = top_level.get('Program', '')
    program_arguments = top_level.get('ProgramArguments')
    for argument in program_arguments:
      command += " %s" % argument

    user_name = top_level.get('UserName')
    group_name = top_level.get('GroupName')

    event_data = plist_event.PlistTimeEventData()
    event_data.desc = ('Launchd service config {0:s} points to {1:s} with '
                       'user:{2:s} group:{3:s}').format(label, command,
                                                        user_name, group_name)
    event_data.key = 'launchdServiceConfig'
    event_data.root = '/'

    date_time = dfdatetime_semantic_time.NotSet()
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_NOT_A_TIME)

    parser_mediator.ProduceEventWithEventData(event, event_data)


plist.PlistParser.RegisterPlugin(LaunchdPlugin)
