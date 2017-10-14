# -*- coding: utf-8 -*-
"""This file contains constants for making service keys more readable."""

from __future__ import unicode_literals


SERVICE_ENUMS = {
    # Human readable strings for the service type.
    'Type': {
        1: 'Kernel Device Driver (0x1)',
        2: 'File System Driver (0x2)',
        4: 'Adapter (0x4)',
        16: 'Service - Own Process (0x10)',
        32: 'Service - Share Process (0x20)'
    },
    # Human readable strings for the service start type.
    'Start': {
        0: 'Boot (0)',
        1: 'System (1)',
        2: 'Auto Start (2)',
        3: 'Manual (3)',
        4: 'Disabled (4)'
    },
    # Human readable strings for the error handling.
    'ErrorControl': {
        0: 'Ignore (0)',
        1: 'Normal (1)',
        2: 'Severe (2)',
        3: 'Critical (3)'
    }
}
