# -*- coding: utf-8 -*-
"""Plist parser plugin for Apple routined-related plist files."""
import datetime

from plaso.containers import events
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


class RoutinedEventData(events.EventData):
    """Routined plist event data.

    Attributes:
      key (str): The name of the plist key.
      value (str): The value associated with the key.
      timestamp_description (str): A description of what the timestamp represents.
    """

    DATA_TYPE = 'routined:plist:event'

    def __init__(self):
        """Initializes event data."""
        super(RoutinedEventData, self).__init__(data_type=self.DATA_TYPE)
        self.key = None
        self.value = None
        self.timestamp = None


class MyRoutinedPlistPlugin(interface.PlistPlugin):
    """Plist parser plugin for Apple routined plist files."""

    NAME = 'routined_plist'
    DATA_FORMAT = 'Apple routined plist file'

    PLIST_PATH_FILTERS = frozenset([
        interface.PlistPathFilter('com.apple.routined.plist')
    ])

    PLIST_KEYS = frozenset([
        'LastAssetUpdateDate',
        'LastExitDate.CoreRoutineHelperService',
        'LastLaunchDate.CoreRoutineHelperService',
        'LastLaunchDate.routined',
        'LastSuccessfulAssetUpdateDate',
        'LearnedLocationEngineTrainVisitsLastAttemptDate',
        'RTDefaultsPersistenceMirroringManagerBackgroundLastExportDate',
        'RTDefaultsPersistenceMirroringManagerBackgroundLastImportDate',
        'XPCActivityLastAttemptDate.com.apple.routined.assets',
        'XPCActivityLastAttemptDate.com.apple.routined.learnedLocationEngine.train',
        'XPCActivityLastAttemptDate.com.apple.routined.locationAwareness.heartbeat',
        'XPCActivityLastAttemptDate.com.apple.routined.locationAwareness.highAccuracyLocationRequest',
        'XPCActivityLastAttemptDate.com.apple.routined.metrics.daily',
        'XPCActivityLastAttemptDate.com.apple.routined.persistence.mirroring.background',
        'XPCActivityLastAttemptDate.com.apple.routined.persistence.mirroring.post-install',
        'XPCActivityLastAttemptDate.com.apple.routined.purge',
        'XPCActivityLastCompleteDate.com.apple.routined.assets',
        'XPCActivityLastCompleteDate.com.apple.routined.learnedLocationEngine.train',
        'XPCActivityLastCompleteDate.com.apple.routined.locationAwareness.heartbeat',
        'XPCActivityLastCompleteDate.com.apple.routined.locationAwareness.highAccuracyLocationRequest',
        'XPCActivityLastCompleteDate.com.apple.routined.metrics.daily',
        'XPCActivityLastCompleteDate.com.apple.routined.persistence.mirroring.background',
        'XPCActivityLastCompleteDate.com.apple.routined.persistence.mirroring.post-install',
        'XPCActivityLastCompleteDate.com.apple.routined.purge',
        'learnedLocationEngineTrainLocationsOfInterestLastCompletionDate'
    ])

    def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
        """Extract events from the routined plist.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components.
          match (Optional[dict[str, object]]): keys extracted from PLIST_KEYS.
        """
        # Produce an event for each key-value pair as a string, with no conversions.
        for key, value in match.items():
            event_data = RoutinedEventData()
            event_data.key = key
            event_data.value = str(value)
            event_data.timestamp = str(value)

            parser_mediator.ProduceEventData(event_data)


plist.PlistParser.RegisterPlugin(MyRoutinedPlistPlugin)
