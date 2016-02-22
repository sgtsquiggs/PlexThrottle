from config import config
import transmissionrpc
from datetime import datetime as dt

TRANSMISSION_ENABLED = config['TRANSMISSION_ENABLED']
TRANS_HOST = config['TRANS_HOST']
TRANS_PORT = config['TRANS_PORT']
TRANS_USER = config['TRANS_USER']
TRANS_PASS = config['TRANS_PASS']


def update_global_ratio_public_torrents(host, port, user, password):
    tc = transmissionrpc.Client(host, port=port, user=user, password=password)

    # All torrents
    torrents = tc.get_torrents()

    # Only public torrents with a global seed ratio mode
    torrents = filter(lambda t: not t.isPrivate and t.seed_ratio_mode == 'global', torrents)

    # Torrent ids
    ids = list(map(lambda t: t.id, torrents))

    # Update torrents seed ratio limit and mode
    if ids:
        tc.change_torrent(ids, seedRatioLimit=0.001, seedRatioMode=1)

    return ids


def stop_completed_public_seeding_torrents(host, port, user, password):
    tc = transmissionrpc.Client(host, port=port, user=user, password=password)

    # All torrents
    torrents = tc.get_torrents()

    # Only public, seeding torrents
    torrents = filter(lambda t: not t.isPrivate and t.status == 'seeding', torrents)

    # Torrent ids
    ids = list(map(lambda t: t.id, torrents))

    # Stop torrents
    if ids:
        tc.stop_torrent(ids)

    return ids


def delete_completed_public_stopped_torrents(host, port, user, password):
    tc = transmissionrpc.Client(host, port=port, user=user, password=password)

    # All torrents
    torrents = tc.get_torrents()

    # Only public, seeding torrents
    torrents = filter(lambda t: not t.isPrivate and t.status == 'stopped', torrents)

    # Torrents that are at least 2 hours complete
    torrents = filter(lambda t: (dt.now() - t.date_done).seconds > 7200, torrents)

    # Torrent ids
    ids = list(map(lambda t: t.id, torrents))

    # Stop torrents
    if ids:
        tc.remove_torrent(ids, delete_data=True)

    return ids


num_changed = len(update_global_ratio_public_torrents(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS))
num_stopped = len(stop_completed_public_seeding_torrents(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS))
num_deleted = len(delete_completed_public_stopped_torrents(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS))

print("Torrents changed: %d" % num_changed)
print("Torrents stopped: %d" % num_stopped)
print("Torrents deleted: %d" % num_deleted)
