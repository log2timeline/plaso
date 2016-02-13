# -*- coding: utf-8 -*-
"""This file contains an import statement for each parser."""

from plaso.parsers import asl
from plaso.parsers import android_app_usage
from plaso.parsers import bencode_parser
from plaso.parsers import bsm
from plaso.parsers import chrome_cache
from plaso.parsers import chrome_preferences
from plaso.parsers import cups_ipp
from plaso.parsers import custom_destinations
from plaso.parsers import docker
from plaso.parsers import esedb
from plaso.parsers import filestat
from plaso.parsers import firefox_cache
from plaso.parsers import hachoir
from plaso.parsers import iis
from plaso.parsers import java_idx
from plaso.parsers import mac_appfirewall
from plaso.parsers import mac_keychain
from plaso.parsers import mac_securityd
from plaso.parsers import mac_wifi
from plaso.parsers import mactime
from plaso.parsers import mcafeeav
from plaso.parsers import msiecf
from plaso.parsers import ntfs
from plaso.parsers import olecf
from plaso.parsers import opera
from plaso.parsers import oxml
# Renable after rewrite as indicated in:
# https://github.com/log2timeline/plaso/issues/360
# from plaso.parsers import pcap
from plaso.parsers import pe
from plaso.parsers import plist
from plaso.parsers import popcontest
from plaso.parsers import pls_recall
from plaso.parsers import recycler
from plaso.parsers import safari_cookies
from plaso.parsers import sccm
from plaso.parsers import selinux
from plaso.parsers import skydrivelog
from plaso.parsers import sqlite
from plaso.parsers import symantec
from plaso.parsers import syslog
from plaso.parsers import utmp
from plaso.parsers import utmpx
from plaso.parsers import winevt
from plaso.parsers import winevtx
from plaso.parsers import winfirewall
from plaso.parsers import winjob
from plaso.parsers import winlnk
from plaso.parsers import winprefetch
from plaso.parsers import winreg
from plaso.parsers import winrestore
from plaso.parsers import xchatlog
from plaso.parsers import xchatscrollback

# Register plugins.
from plaso.parsers import bencode_plugins
from plaso.parsers import esedb_plugins
from plaso.parsers import olecf_plugins
from plaso.parsers import plist_plugins
from plaso.parsers import sqlite_plugins
from plaso.parsers import winreg_plugins
