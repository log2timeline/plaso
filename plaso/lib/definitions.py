# -*- coding: utf-8 -*-
"""The definitions."""

from __future__ import unicode_literals


MICROSECONDS_PER_SECOND = 1000000
MICROSECONDS_PER_MINUTE = 60000000

COMPRESSION_FORMAT_NONE = 'none'
COMPRESSION_FORMAT_ZLIB = 'zlib'

COMPRESSION_FORMATS = frozenset([
    COMPRESSION_FORMAT_NONE,
    COMPRESSION_FORMAT_ZLIB])

DEFAULT_WORKER_MEMORY_LIMIT = 2048 * 1024 * 1024

FAILURE_MODE_EXHAUST_MEMORY = 'exhaust_memory'
FAILURE_MODE_NOT_RESPONDING = 'not_responding'
FAILURE_MODE_TERMINATED = 'terminated'
FAILURE_MODE_TIME_OUT = 'time_out'

OPERATING_SYSTEM_FAMILY_LINUX = 'Linux'
OPERATING_SYSTEM_FAMILY_MACOS = 'MacOS'
OPERATING_SYSTEM_FAMILY_UNKNOWN = 'Unknown'
OPERATING_SYSTEM_FAMILY_WINDOWS_9x = 'Windows 9x/Me'
OPERATING_SYSTEM_FAMILY_WINDOWS_NT = 'Windows NT'

OPERATING_SYSTEM_FAMILIES = frozenset([
    OPERATING_SYSTEM_FAMILY_LINUX,
    OPERATING_SYSTEM_FAMILY_MACOS,
    OPERATING_SYSTEM_FAMILY_UNKNOWN,
    OPERATING_SYSTEM_FAMILY_WINDOWS_9x,
    OPERATING_SYSTEM_FAMILY_WINDOWS_NT])

# TODO: remove regvalue, which is kept for backwards compatibility.
RESERVED_VARIABLE_NAMES = frozenset([
    'body',
    'data_type',
    'display_name',
    'filename',
    'hostname',
    'http_headers',
    'inode',
    'mapped_files',
    'metadata',
    'offset',
    'parser',
    'pathspec',
    'query',
    'regvalue',
    'source_long',
    'source_short',
    'tag',
    'text_prepend',
    'timestamp',
    'timestamp_desc',
    'timezone',
    'username'])

SERIALIZER_FORMAT_JSON = 'json'

SERIALIZER_FORMATS = frozenset([SERIALIZER_FORMAT_JSON])

STATUS_INDICATOR_ABORTED = 'aborted'
STATUS_INDICATOR_ANALYZING = 'analyzing'
STATUS_INDICATOR_COLLECTING = 'collecting'
STATUS_INDICATOR_COMPLETED = 'completed'
STATUS_INDICATOR_ERROR = 'error'
STATUS_INDICATOR_EXPORTING = 'exporting'
STATUS_INDICATOR_EXTRACTING = 'extracting'
STATUS_INDICATOR_FINALIZING = 'finalizing'
STATUS_INDICATOR_HASHING = 'hashing'
STATUS_INDICATOR_IDLE = 'idle'
STATUS_INDICATOR_INITIALIZED = 'initialized'
STATUS_INDICATOR_KILLED = 'killed'
STATUS_INDICATOR_MERGING = 'merging'
STATUS_INDICATOR_NOT_RESPONDING = 'not responding'
STATUS_INDICATOR_REPORTING = 'reporting'
STATUS_INDICATOR_RUNNING = 'running'
STATUS_INDICATOR_YARA_SCAN = 'yara scan'

ERROR_STATUS_INDICATORS = frozenset([
    STATUS_INDICATOR_ABORTED,
    STATUS_INDICATOR_ERROR,
    STATUS_INDICATOR_NOT_RESPONDING,
    STATUS_INDICATOR_KILLED])

STORAGE_FORMAT_SQLITE = 'sqlite'

STORAGE_FORMATS = frozenset([STORAGE_FORMAT_SQLITE])

TASK_STORAGE_FORMATS = frozenset([STORAGE_FORMAT_SQLITE])

DEFAULT_STORAGE_FORMAT = STORAGE_FORMAT_SQLITE

# The session storage contains the results of one or more sessions.
# A typical session is e.g. a single run of a tool (log2timeline.py).
# The task storage contains the results of one or more tasks. Tasks
# are used to split work within a session. A typical task is e.g.
# a single run of a worker process.
STORAGE_TYPE_SESSION = 'session'
STORAGE_TYPE_TASK = 'task'

STORAGE_TYPES = frozenset([STORAGE_TYPE_SESSION, STORAGE_TYPE_TASK])

TIME_DESCRIPTION_ACCOUNT_CREATED = 'Account Created'
TIME_DESCRIPTION_ADDED = 'Creation Time'
TIME_DESCRIPTION_BACKUP = 'Backup Time'
TIME_DESCRIPTION_CHANGE = 'Metadata Modification Time'
TIME_DESCRIPTION_CONNECTION_ESTABLISHED = 'Connection Established'
TIME_DESCRIPTION_CONNECTION_FAILED = 'Connection Failed'
TIME_DESCRIPTION_CREATION = TIME_DESCRIPTION_ADDED
TIME_DESCRIPTION_DELETED = 'Content Deletion Time'
TIME_DESCRIPTION_END = 'End Time'
TIME_DESCRIPTION_ENTRY_MODIFICATION = TIME_DESCRIPTION_CHANGE
TIME_DESCRIPTION_EXIT = 'Exit Time'
TIME_DESCRIPTION_EXPIRATION = 'Expiration Time'
TIME_DESCRIPTION_FILE_DOWNLOADED = 'File Downloaded'
TIME_DESCRIPTION_FIRST_CONNECTED = 'First Connection Time'
TIME_DESCRIPTION_INSTALLATION = 'Installation Time'
TIME_DESCRIPTION_LAST_ACTIVE = 'Last Active Time'
TIME_DESCRIPTION_LAST_ACCESS = 'Last Access Time'
TIME_DESCRIPTION_LAST_CHECKED = 'Last Checked Time'
TIME_DESCRIPTION_LAST_CONNECTED = 'Last Connection Time'
TIME_DESCRIPTION_LAST_LOGIN = 'Last Login Time'
TIME_DESCRIPTION_LAST_PASSWORD_RESET = 'Last Password Reset'
TIME_DESCRIPTION_LAST_PRINTED = 'Last Printed Time'
TIME_DESCRIPTION_LAST_RESUME = 'Last Resume Time'
TIME_DESCRIPTION_LAST_RUN = 'Last Time Executed'
TIME_DESCRIPTION_LAST_SHUTDOWN = 'Last Shutdown Time'
TIME_DESCRIPTION_LAST_USED = 'Last Used Time'
TIME_DESCRIPTION_LAST_VISITED = 'Last Visited Time'
TIME_DESCRIPTION_MODIFICATION = 'Content Modification Time'
TIME_DESCRIPTION_RECORDED = 'Event Recorded'
TIME_DESCRIPTION_SAMPLE = 'Sample Time'
TIME_DESCRIPTION_SCHEDULED_TO_END = 'Scheduled to end'
TIME_DESCRIPTION_SCHEDULED_TO_START = 'Scheduled to start'
TIME_DESCRIPTION_SENT = 'Sent Time'
TIME_DESCRIPTION_START = 'Start Time'
TIME_DESCRIPTION_UPDATE = 'Update Time'
TIME_DESCRIPTION_WRITTEN = TIME_DESCRIPTION_MODIFICATION

# The timestamp does not represent a date and time value.
TIME_DESCRIPTION_NOT_A_TIME = 'Not a time'

# Note that the unknown time is used for date and time values
# of which the exact meaning is unknown and being researched.
# For most cases do not use this timestamp description.
TIME_DESCRIPTION_UNKNOWN = 'Unknown Time'
