# -*- coding: utf-8 -*-
"""This file imports Python modules that register attribute container types."""

from plaso.containers import analysis_results
from plaso.containers import analyzer_result
from plaso.containers import artifacts
from plaso.containers import counts
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import tasks
from plaso.containers import warnings

# These modules define attribute containers that inherit from other attribute
# containers but do not register attribute containers themselves, so they are
# not imported here
# from plaso.containers import plist_event
# from plaso.containers import time_events
# from plaso.containers import windows_events
