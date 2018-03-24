# -*- coding: utf-8 -*-
"""This file imports source files that register an attribute container type."""

from plaso.containers import analyzer_result
from plaso.containers import artifacts
from plaso.containers import errors
from plaso.containers import event_sources
from plaso.containers import events
from plaso.containers import reports
from plaso.containers import sessions
from plaso.containers import storage_media
from plaso.containers import tasks

# These files define attribute container types, but don't register them.
# from plaso.containers import plist_event
# from plaso.containers import time_events
# from plaso.containers import shell_item_events
# from plaso.containers import windows_events