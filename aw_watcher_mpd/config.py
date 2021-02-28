from configparser import ConfigParser
from aw_core.config import load_config

default_settings = {
    "poll_time": "5",
    "host": "localhost",
    "port": "6600"
}

default_testing_settings = {
    "poll_time": "1",
    "host": "localhost",
    "port": "6600"
}

default_config = ConfigParser()
default_config['aw-watcher-mpd'] = default_settings
default_config['aw-watcher-mpd-testing'] = default_testing_settings
watcher_config = load_config("aw-watcher-mpd", default_config)
