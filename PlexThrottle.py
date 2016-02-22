from xml.etree import ElementTree
from config import config
from datetime import datetime as dt
import requests
import transmissionrpc

PMS_HOST = config['PMS_HOST']
PMS_PORT = config['PMS_PORT']
PMS_TOKEN = config['PMS_TOKEN']

SABNZBD_ENABLED = config['SABNZBD_ENABLED']
SAB_HOST = config['SAB_HOST']
SAB_PORT = config['SAB_PORT']
SAB_APIKEY = config['SAB_APIKEY']

TRANSMISSION_ENABLED = config['TRANSMISSION_ENABLED']
TRANS_HOST = config['TRANS_HOST']
TRANS_PORT = config['TRANS_PORT']
TRANS_USER = config['TRANS_USER']
TRANS_PASS = config['TRANS_PASS']


def get_active_streams(host, port, token):
    url = 'http://%s:%s/status/sessions' % (host, port)
    headers = {'X-Plex-Token': token}
    r = requests.get(url, headers=headers)
    tree = ElementTree.fromstring(r.content)
    stream_count = int(tree.attrib['size'])
    return stream_count


def get_active_remote_streams(host, port, token):
    url = 'http://%s:%s/status/sessions' % (host, port)
    headers = {'X-Plex-Token': token}
    r = requests.get(url, headers=headers)
    tree = ElementTree.fromstring(r.content)
    players = tree.findall(".//Player")
    count = 0
    for player in players:
        ip_address = player.attrib['address']
        if is_remote(ip_address):
            count += 1
    return count


def is_remote(ip_address):
    try:
        if ip_address.index('.') > -1:
            parts = ip_address.split(':')
            parts = parts[len(parts) - 1].split('.')
            if parts[0] == '10':
                return False
            if parts[0] == '172' and int(parts[1], 10) >= 16 and int(parts[1], 10) <= 31:
                return False
            if parts[0] == '192' and parts[1] == '168':
                return False
    except:
        pass
    return True


def set_sabnzbd_speed_limit(host, port, apikey, value):
    if not SABNZBD_ENABLED:
        return
    url = 'http://%s:%d/sabnzbd/api' % (host, port)
    params = {'mode': 'config', 'name': 'speedlimit', 'apikey': apikey, 'value': value[0]}
    requests.get(url, params=params)


def set_transmission_speed_limit(host, port, user, password, value):
    if not TRANSMISSION_ENABLED:
        return
    tc = transmissionrpc.Client(host, port=port, user=user, password=password)
    if value is not None:
        tc.set_session(alt_speed_enabled=True, alt_speed_down=value[0], alt_speed_up=value[1])
    else:
        tc.set_session(alt_speed_enabled=False)


active_streams = get_active_remote_streams(PMS_HOST, PMS_PORT, PMS_TOKEN)
print("[%s] Active Streams: %d" % (dt.now().strftime('%Y-%m-%d %H:%M:%S'), active_streams))

if active_streams < 1:
    speed = config['NONE']
    set_sabnzbd_speed_limit(SAB_HOST, SAB_PORT, SAB_APIKEY, speed)
    set_transmission_speed_limit(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS, speed)
elif active_streams < 3:
    speed = config['UNDER_THREE']
    set_sabnzbd_speed_limit(SAB_HOST, SAB_PORT, SAB_APIKEY, speed)
    set_transmission_speed_limit(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS, speed)
elif active_streams < 5:
    speed = config['UNDER_FIVE']
    set_sabnzbd_speed_limit(SAB_HOST, SAB_PORT, SAB_APIKEY, speed)
    set_transmission_speed_limit(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS, speed)
elif active_streams < 7:
    speed = config['UNDER_SEVEN']
    set_sabnzbd_speed_limit(SAB_HOST, SAB_PORT, SAB_APIKEY, speed)
    set_transmission_speed_limit(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS, speed)
else:
    speed = [0, 0]
    set_sabnzbd_speed_limit(SAB_HOST, SAB_PORT, SAB_APIKEY, speed)
    set_transmission_speed_limit(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS, speed)
