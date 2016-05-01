from config import config
import transmissionrpc
from datetime import datetime as dt
from functools import reduce

TRANSMISSION_ENABLED = config['TRANSMISSION_ENABLED']
TRANS_HOST = config['TRANS_HOST']
TRANS_PORT = config['TRANS_PORT']
TRANS_USER = config['TRANS_USER']
TRANS_PASS = config['TRANS_PASS']
TRANS_PUBLIC_RATIO_LIMIT = config['TRANS_PUBLIC_RATIO_LIMIT']
TRANS_NYAA_RATIO_LIMIT = config['TRANS_NYAA_RATIO_LIMIT']


def update_nyaa_torrents(host, port, user, password, ratio):
    tc = transmissionrpc.Client(host, port=port, user=user, password=password)

    # All torrents
    torrents = tc.get_torrents()

    # Only public torrents
    torrents = filter(lambda t: not t.isPrivate, torrents)

    # Only torrents using nyaa.se tracker
    torrents = list(filter(lambda t: reduce(lambda result, x: result or 'nyaa' in x['announce'], t.trackers, False) is True, torrents))

    # Torrent ids
    ids = list(map(lambda t: t.id, torrents))

    # Update torrents seed ratio limit and mode
    if ids:
        tc.change_torrent(ids, seedRatioLimit=ratio, seedRatioMode=1)

    return ids


def update_global_ratio_public_torrents(host, port, user, password, ratio):
    tc = transmissionrpc.Client(host, port=port, user=user, password=password)

    # All torrents
    torrents = tc.get_torrents()

    # Only public torrents with a global seed ratio mode
    torrents = filter(lambda t: not t.isPrivate and t.seed_ratio_mode == 'global', torrents)

    # Torrent ids
    ids = list(map(lambda t: t.id, torrents))

    # Update torrents seed ratio limit and mode
    if ids:
        tc.change_torrent(ids, seedRatioLimit=ratio, seedRatioMode=1)

    return ids


def stop_completed_public_seeding_torrents(host, port, user, password):
    tc = transmissionrpc.Client(host, port=port, user=user, password=password)

    # All torrents
    torrents = tc.get_torrents()

    # Only public, seeding torrents
    torrents = filter(lambda t: not t.isPrivate and t.status == 'seeding' and t.seed_ratio_mode == 'global', torrents)

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


num_changed = len(update_global_ratio_public_torrents(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS, TRANS_PUBLIC_RATIO_LIMIT))
num_changed += len(update_nyaa_torrents(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS, TRANS_NYAA_RATIO_LIMIT))
num_stopped = len(stop_completed_public_seeding_torrents(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS))
num_deleted = len(delete_completed_public_stopped_torrents(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS))

print("[%s] Torrents changed: %d; stopped: %d; deleted: %d" % (dt.now().strftime('%Y-%m-%d %H:%M:%S'), num_changed, num_stopped, num_deleted))
