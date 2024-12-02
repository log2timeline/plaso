import logging
from plaso.containers import events
from plaso.parsers.plist_plugins import interface
from plaso.parsers.plist import PlistParser
from dfdatetime import posix_time as dfdatetime_posix_time

# Setup logging
logging.basicConfig(level=logging.DEBUG)


class IOSSIMInfoEventData(events.EventData):
    """Event data untuk iOS SIM Info."""
    DATA_TYPE = 'ios:sim:info'

    def __init__(self):
        """Inisialisasi event data."""
        super(IOSSIMInfoEventData, self).__init__(data_type=self.DATA_TYPE)
        self.mdn = None
        self.eap_aka = None
        self.sim_type = None
        self.cb_ver = None
        self.label_id = None
        self.timestamp = None


class IOSSIMInfoPlugin(interface.PlistPlugin):
    """Plugin untuk memproses iOS SIM Info plist."""
    NAME = 'ios_siminfo'
    DATA_FORMAT = 'iOS SIM Info plist file'

    PLIST_PATH_FILTERS = frozenset([
        interface.PlistPathFilter('com.apple.commcenter.data.plist')
    ])
    PLIST_KEYS = frozenset(['PersonalWallet'])

    def _ParsePlist(self, parser_mediator, match=None, **unused_kwargs):
        """Memproses file plist."""
        personal_wallet = match.get('PersonalWallet', {})

        if not personal_wallet:
            logging.warning('PersonalWallet kosong atau tidak ditemukan di match.')
            return

        for sim_id, sim_data in personal_wallet.items():
            info = sim_data.get('info', {})
            if not info:
                logging.warning(f'Tidak ada info untuk SIM ID: {sim_id}')
                continue

            event_data = IOSSIMInfoEventData()
            event_data.mdn = info.get('mdn')
            event_data.eap_aka = info.get('eap_aka')
            event_data.sim_type = info.get('type')
            event_data.cb_ver = info.get('cb_ver')
            event_data.label_id = info.get('label-id')
            event_data.timestamp = dfdatetime_posix_time.PosixTime(
                timestamp=info.get('ts', 0)
            )

            # Debugging untuk memastikan data diproduksi
            logging.debug(
                f'Memproduksi event data: MDN={event_data.mdn}, '
                f'SIM Type={event_data.sim_type}, CB Ver={event_data.cb_ver}'
            )

            # Pastikan data penting ada sebelum menghasilkan event
            if event_data.mdn:
                parser_mediator.ProduceEventData(event_data)
            else:
                logging.warning(f'MDN tidak ditemukan untuk SIM ID: {sim_id}')


# Registrasi plugin
PlistParser.RegisterPlugin(IOSSIMInfoPlugin)
