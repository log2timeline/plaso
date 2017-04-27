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
