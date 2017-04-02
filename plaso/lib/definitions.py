# -*- coding: utf-8 -*-
"""The definitions."""

OPERATING_SYSTEM_LINUX = u'Linux'
OPERATING_SYSTEM_MACOSX = u'MacOSX'
OPERATING_SYSTEM_UNKNOWN = u'Unknown'
OPERATING_SYSTEM_WINDOWS = u'Windows'

OPERATING_SYSTEMS = frozenset([
    OPERATING_SYSTEM_LINUX,
    OPERATING_SYSTEM_MACOSX,
    OPERATING_SYSTEM_UNKNOWN,
    OPERATING_SYSTEM_WINDOWS])

PROCESSING_STATUS_ABORTED = u'aborted'
PROCESSING_STATUS_ANALYZING = u'analyzing'
PROCESSING_STATUS_COLLECTING = u'collecting'
PROCESSING_STATUS_COMPLETED = u'completed'
PROCESSING_STATUS_ERROR = u'error'
PROCESSING_STATUS_EXPORTING = u'exporting'
PROCESSING_STATUS_EXTRACTING = u'extracting'
PROCESSING_STATUS_FINALIZING = u'finalizing'
PROCESSING_STATUS_HASHING = u'hashing'
PROCESSING_STATUS_IDLE = u'idle'
PROCESSING_STATUS_INITIALIZED = u'initialized'
PROCESSING_STATUS_KILLED = u'killed'
PROCESSING_STATUS_MERGING = u'merging'
PROCESSING_STATUS_NOT_RESPONDING = u'not responding'
PROCESSING_STATUS_REPORTING = u'reporting'
PROCESSING_STATUS_RUNNING = u'running'
PROCESSING_STATUS_YARA_SCAN = u'yara scan'

PROCESSING_ERROR_STATUS = frozenset([
    PROCESSING_STATUS_ABORTED,
    PROCESSING_STATUS_ERROR,
    PROCESSING_STATUS_KILLED])

RESERVED_VARIABLE_NAMES = frozenset([
    u'body',
    u'data_type',
    u'display_name',
    u'filename',
    u'hostname',
    u'http_headers',
    u'inode',
    u'mapped_files',
    u'metadata',
    u'offset',
    u'parser',
    u'pathspec',
    u'query',
    u'regvalue',
    u'source_long',
    u'source_short',
    u'tag',
    u'text_prepend',
    u'timestamp',
    u'timestamp_desc',
    u'timezone',
    u'username'])

SERIALIZER_FORMAT_JSON = u'json'

SERIALIZER_FORMATS = frozenset([SERIALIZER_FORMAT_JSON])

# The session storage contains the results of one or more sessions.
# A typical session is e.g. a single run of a tool (log2timeline.py).
# The task storage contains the results of one or more tasks. Tasks
# are used to split work within a session. A typical task is e.g.
# a single run of a worker process.
STORAGE_TYPE_SESSION = u'session'
STORAGE_TYPE_TASK = u'task'

STORAGE_TYPES = frozenset([STORAGE_TYPE_SESSION, STORAGE_TYPE_TASK])

TIME_DESCRIPTION_ACCOUNT_CREATED = u'Account Created'
TIME_DESCRIPTION_ADDED = u'Creation Time'
TIME_DESCRIPTION_CHANGE = u'Metadata Modification Time'
TIME_DESCRIPTION_CONNECTION_ESTABLISHED = 'Connection Established'
TIME_DESCRIPTION_CONNECTION_FAILED = 'Connection Failed'
TIME_DESCRIPTION_CREATION = TIME_DESCRIPTION_ADDED
TIME_DESCRIPTION_DELETED = u'Content Deletion Time'
TIME_DESCRIPTION_END = u'End Time'
TIME_DESCRIPTION_ENTRY_MODIFICATION = TIME_DESCRIPTION_CHANGE
TIME_DESCRIPTION_EXIT = u'Exit Time'
TIME_DESCRIPTION_EXPIRATION = u'Expiration Time'
TIME_DESCRIPTION_FILE_DOWNLOADED = u'File Downloaded'
TIME_DESCRIPTION_FIRST_CONNECTED = u'First Connection Time'
TIME_DESCRIPTION_INSTALLATION = u'Installation Time'
TIME_DESCRIPTION_LAST_ACCESS = u'Last Access Time'
TIME_DESCRIPTION_LAST_CHECKED = u'Last Checked Time'
TIME_DESCRIPTION_LAST_CONNECTED = u'Last Connection Time'
TIME_DESCRIPTION_LAST_LOGIN = u'Last Login Time'
TIME_DESCRIPTION_LAST_PASSWORD_RESET = u'Last Password Reset'
TIME_DESCRIPTION_LAST_PRINTED = u'Last Printed Time'
TIME_DESCRIPTION_LAST_RESUME = u'Last Resume Time'
TIME_DESCRIPTION_LAST_RUN = u'Last Time Executed'
TIME_DESCRIPTION_LAST_SHUTDOWN = u'Last Shutdown Time'
TIME_DESCRIPTION_LAST_VISITED = u'Last Visited Time'
TIME_DESCRIPTION_MODIFICATION = u'Content Modification Time'
TIME_DESCRIPTION_START = u'Start Time'
TIME_DESCRIPTION_UPDATE = u'Update Time'
TIME_DESCRIPTION_WRITTEN = TIME_DESCRIPTION_MODIFICATION

# The timestamp does not represent a date and time value.
TIME_DESCRIPTION_NOT_A_TIME = u'Not a time'

# Note that the unknown time is used for date and time values
# of which the exact meaning is unknown and being researched.
# For most cases do not use this timestamp description.
TIME_DESCRIPTION_UNKNOWN = u'Unknown Time'
