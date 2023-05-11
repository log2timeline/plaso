# -*- coding: utf-8 -*-
"""This file imports Python modules that register parsers."""

from plaso.parsers import android_app_usage
from plaso.parsers import asl
from plaso.parsers import bencode_parser
from plaso.parsers import bodyfile
from plaso.parsers import bsm
from plaso.parsers import chrome_cache
from plaso.parsers import chrome_preferences
from plaso.parsers import cups_ipp
from plaso.parsers import custom_destinations
from plaso.parsers import czip
from plaso.parsers import esedb
from plaso.parsers import filestat
from plaso.parsers import firefox_cache
from plaso.parsers import fish_history
from plaso.parsers import fseventsd
from plaso.parsers import java_idx
from plaso.parsers import jsonl_parser
from plaso.parsers import locate
from plaso.parsers import macos_keychain
from plaso.parsers import mcafeeav
from plaso.parsers import msiecf
from plaso.parsers import networkminer
from plaso.parsers import ntfs
from plaso.parsers import olecf
from plaso.parsers import onedrive
from plaso.parsers import opera
from plaso.parsers import pe
from plaso.parsers import plist
from plaso.parsers import pls_recall
from plaso.parsers import recycler
from plaso.parsers import safari_cookies
from plaso.parsers import spotlight_storedb
from plaso.parsers import sqlite
from plaso.parsers import symantec
from plaso.parsers import systemd_journal
from plaso.parsers import text_parser
from plaso.parsers import trendmicroav
from plaso.parsers import unified_logging
from plaso.parsers import utmp
from plaso.parsers import utmpx
from plaso.parsers import wincc
from plaso.parsers import windefender_history
from plaso.parsers import winevt
from plaso.parsers import winevtx
from plaso.parsers import winjob
from plaso.parsers import winlnk
from plaso.parsers import winpca
from plaso.parsers import winprefetch
from plaso.parsers import winreg_parser
from plaso.parsers import winrestore

# Register parser plugins.
from plaso.parsers import bencode_plugins
from plaso.parsers import czip_plugins
from plaso.parsers import esedb_plugins
from plaso.parsers import jsonl_plugins
from plaso.parsers import olecf_plugins
from plaso.parsers import plist_plugins
from plaso.parsers import sqlite_plugins
from plaso.parsers import text_plugins
from plaso.parsers import winreg_plugins

# These modules do not register parsers themselves, but contain super classes
# used by parsers in other modules.
# from plaso.parsers import dsv_parser
