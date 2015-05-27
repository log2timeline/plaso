# -*- coding: utf-8 -*-
"""This file contains constants for making service keys more readable."""

SERVICE_ENUMS = {
    # Human readable strings for the service type.
    u'Type': {
        1: u'Kernel Device Driver (0x1)',
        2: u'File System Driver (0x2)',
        4: u'Adapter (0x4)',
        16: u'Service - Own Process (0x10)',
        32: u'Service - Share Process (0x20)'
    },
    # Human readable strings for the service start type.
    u'Start': {
        0: u'Boot (0)',
        1: u'System (1)',
        2: u'Auto Start (2)',
        3: u'Manual (3)',
        4: u'Disabled (4)'
    },
    # Human readable strings for the error handling.
    u'ErrorControl': {
        0: u'Ignore (0)',
        1: u'Normal (1)',
        2: u'Severe (2)',
        3: u'Critical (3)'
    }
}
