#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains constants for making service keys more readable."""

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
    # Human readable strings for the error handling .
    'ErrorControl': {
        0: 'Ignore (0)',
        1: 'Normal (1)',
        2: 'Severe (2)',
        3: 'Critical (3)'
    }
}
