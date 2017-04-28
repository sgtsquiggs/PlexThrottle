import logging
import re
from datetime import datetime as dt
from xml.etree import ElementTree

import requests
import transmissionrpc
from configobj import ConfigObj

LOGGER = logging.getLogger("plexpy")

CONFIG_DEFINITIONS = {
    'PMS_HOST': (str, 'Plex Media Server', 'localhost'),
    'PMS_PORT': (int, 'Plex Media Server', 32400),
    'PMS_TOKEN': (str, 'Plex Media Server', ''),
    'SABNZBD_HOST': (str, 'SABnzbd', 'localhost'),
    'SABNZBD_PORT': (str, 'SABnzbd', 8800),
    'SABNZBD_APIKEY': (str, 'SABnzbd', ''),
    'TRANSMISSION_HOST': (str, 'Transmission', 'localhost'),
    'TRANSMISSION_PORT': (str, 'Transmission', 9091),
    'TRANSMISSION_USER': (str, 'Transmission', ''),
    'TRANSMISSION_PASS': (str, 'Transmission', ''),
}


class Config(object):
    """Wraps access to configuration values"""

    def __init__(self, config_file):
        """Initializes object with values from the config file"""
        self._config_file = config_file
        self._config = ConfigObj(self._config_file, encoding='utf-8')
        for key in CONFIG_DEFINITIONS:
            self.check_setting(key)

    def _define(self, name):
        key = name.upper()
        ini_key = name.lower()
        definition_type, section, default = CONFIG_DEFINITIONS[key]
        return key, definition_type, section, ini_key, default

    def check_section(self, section):
        """Check if section exists and create it if it does not"""
        if section not in self._config:
            self._config[section] = {}
            return True
        else:
            return False

    def check_setting(self, key):
        """Return settings from the config or default if unusable"""
        key, definition_type, section, ini_key, default = self._define(key)
        self.check_section(section)
        try:
            my_val = definition_type(self._config[section][ini_key])
        except (KeyError, ValueError):
            my_val = definition_type(default)
            self._config[section][ini_key] = my_val
        return my_val

    def write(self):
        """Make a copy of the stored config and write it to the configured file"""
        new_config = ConfigObj(encoding="UTF-8")
        new_config.filename = self._config_file

        # first copy over everything from the old config, even if it is not
        # correctly defined to keep from losing data
        for key, subkeys in self._config.items():
            if key not in new_config:
                new_config[key] = {}
            for subkey, value in subkeys.items():
                new_config[key][subkey] = value

        # next make sure that everything we expect to have defined is so
        for key, _ in CONFIG_DEFINITIONS:
            key, _, section, ini_key, _ = self._define(key)
            self.check_setting(key)
            if section not in new_config:
                new_config[section] = {}
            new_config[section][ini_key] = self._config[section][ini_key]

        # Write it to file
        LOGGER.info("Manifold Config :: Writing configuration to file")

        try:
            new_config.write()
        except IOError as exc:
            LOGGER.error("Manifold Config :: Error writing configuration file: %s", exc)

        self._blacklist()

    def __getattr__(self, name):
        """
        Returns something from the ini unless it is a real property
        of the configuration object or is not all caps.
        """
        if not re.match(r'[A-Z_]+$', name):
            return super(Config, self).__getattr__(name)  # pylint: disable=E1101
        else:
            return self.check_setting(name)

    def __setattr__(self, name, value):
        """
        Maps all-caps properties to ini values unless they exist on the
        configuration object.
        """
        if not re.match(r'[A-Z_]+$', name):
            super(Config, self).__setattr__(name, value)
            return value
        else:
            _, definition_type, section, ini_key, _ = self._define(name)
            self._config[section][ini_key] = definition_type(value)
            return self._config[section][ini_key]

    def process_kwargs(self, kwargs):
        """
        Given a big bunch of key value pairs, apply them to the ini.
        """
        for name, value in kwargs.items():
            _, definition_type, section, ini_key, _ = self._define(name)
            self._config[section][ini_key] = definition_type(value)


# class Plex(object):
#     def __init__(self, host, port, token):
#         self.host = host
#         self.port = port
#         self.token = token

#     def get_session_tree(self):
#         url = 'http://{:s}:{:s}/status/sessions'.format(self.host, self.port)
#         headers = {'X-Plex-Token': self.token}
#         r = requests.get(url, headers=headers)
#         tree = ElementTree.fromstring(r.content)
#         return tree

#     def get_active_streams(self):
#         tree = self.get_session_tree()
#         stream_count = int(tree.attrib['size'])
#         return stream_count

#     def get_active_remote_streams(self):
#         tree = self.get_session_tree()
#         players = tree.findall(".//Player")
#         remote_stream_count = sum([is_remote_ip(player.attrib['address']) for player in players])
#         return remote_stream_count


# def is_remote_ip(ip_address):
#     try:
#         if ip_address.index('.') > -1:
#             parts = ip_address.split(':')
#             parts = parts[len(parts) - 1].split('.')
#             if parts[0] == '10':
#                 return False
#             if parts[0] == '172' and int(parts[1], 10) >= 16 and int(parts[1], 10) <= 31:
#                 return False
#             if parts[0] == '192' and parts[1] == '168':
#                 return False
#     except:
#         pass
#     return True


# def set_sabnzbd_speed_limit(host, port, apikey, value):
#     if not SABNZBD_ENABLED:
#         return
#     url = 'http://%s:%d/sabnzbd/api' % (host, port)
#     params = {'mode': 'config', 'name': 'speedlimit', 'apikey': apikey, 'value': value}
#     requests.get(url, params=params)


# def set_sabnzbd_max_speed_limit(host, port, apikey, value):
#     set_sabnzbd_config_value(host, port, apikey, 'misc', 'bandwidth_max', value)


# def set_sabnzbd_config_value(host, port, apikey, section, keyword, value):
#     if not SABNZBD_ENABLED:
#         return
#     url = 'http://%s:%d/sabnzbd/api' % (host, port)
#     params = {'mode': 'set_config', 'section': section, 'keyword': keyword, 'apikey': apikey, 'value': value}
#     requests.get(url, params=params)


# def set_transmission_speed_limit(host, port, user, password, value):
#     if not TRANSMISSION_ENABLED:
#         return
#     tc = transmissionrpc.Client(host, port=port, user=user, password=password)
#     if value is not None:
#         tc.set_session(alt_speed_enabled=True, alt_speed_down=value[0], alt_speed_up=value[1])
#     else:
#         tc.set_session(alt_speed_enabled=False)


# active_streams = get_active_remote_streams(PMS_HOST, PMS_PORT, PMS_TOKEN)
# print("[%s] Active Streams: %d" % (dt.now().strftime('%Y-%m-%d %H:%M:%S'), active_streams))

# if active_streams < 1:
#     speed = config['NONE']
# elif active_streams < 3:
#     speed = config['UNDER_THREE']
# elif active_streams < 5:
#     speed = config['UNDER_FIVE']
# elif active_streams < 7:
#     speed = config['UNDER_SEVEN']
# else:
#     speed = [0, 0]

# set_transmission_speed_limit(TRANS_HOST, TRANS_PORT, TRANS_USER, TRANS_PASS, speed)

# percent = '%d%%' % round(speed[0] / config['NONE'][0] * 100)
# max_MBps = '%dM' % round(config['NONE'][0] / 1024)

# set_sabnzbd_speed_limit(SAB_HOST, SAB_PORT, SAB_APIKEY, percent)
# set_sabnzbd_max_speed_limit(SAB_HOST, SAB_PORT, SAB_APIKEY, max_MBps)
