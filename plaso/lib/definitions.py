# -*- coding: utf-8 -*-
"""The definitions."""

OS_LINUX = u'Linux'
OS_MACOSX = u'MacOSX'
# TODO: keeping this compatible with the existing code for now.
# Rename None to Unknown in the future.
OS_UNKNOWN = u'None'
OS_WINDOWS = u'Windows'

PROCESS_TYPE_COLLECTOR = u'collector'
PROCESS_TYPE_STORAGE_WRITER = u'storage_writer'
PROCESS_TYPE_WORKER = u'worker'

PROCESSING_STATUS_ABORTED = u'aborted'
PROCESSING_STATUS_COMPLETED = u'completed'
PROCESSING_STATUS_ERROR = u'error'
PROCESSING_STATUS_HASHING = u'hashing'
PROCESSING_STATUS_INITIALIZED = u'initialized'
PROCESSING_STATUS_KILLED = u'killed'
PROCESSING_STATUS_PARSING = u'parsing'
PROCESSING_STATUS_RUNNING = u'running'
PROCESSING_STATUS_WAITING = u'waiting'

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
    u'store_index',
    u'store_number',
    u'tag',
    u'text_prepend',
    u'timestamp',
    u'timestamp_desc',
    u'timezone',
    u'username',
    u'uuid'])

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
