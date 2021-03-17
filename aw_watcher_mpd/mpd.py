#!/usr/bin/env python3

import sys

import logging
from time import sleep
from datetime import datetime, timedelta, timezone

from aw_core.models import Event
from aw_client.client import ActivityWatchClient

from math import floor

from .config import watcher_config

from mpd import MPDClient



logger = logging.getLogger(__name__)

class Settings:
    def __init__(self, config_section):
        self.host = config_section["host"]
        self.port = config_section.getint("port")
        self.poll_time = config_section.getfloat("poll_time")

class MPDWatcher:
    def __init__(self, testing=False):
        self.watcher_name="aw-watcher-mpd"
        self.event_type = "media.music.activity"

        configsect = self.watcher_name if not testing else f"{self.watcher_name}-testing"
        self.settings = Settings(watcher_config[configsect])
        self.client = ActivityWatchClient(self.watcher_name, testing=testing)
        self.bucket_name = "{}_{}".format(self.watcher_name,
                               self.client.client_hostname)

    def ping(self, data: dict, timestamp: datetime, duration: float = 0 ):
        e = Event(timestamp=timestamp, duration=duration, data=data)
        pulsetime = self.settings.poll_time + 1
        self.client.heartbeat(self.bucket_name, e, pulsetime=pulsetime, queued=True)

    def run(self):
        logger.info(f"{self.watcher_name} started")

        sleep(1)

        self.client.create_bucket(self.bucket_name, self.event_type, queued=True)

        self.init_mpd()

        with self.client:
            self.heartbeat_loop()

        self.mpd.close()
        self.mpd.disconnect()

    def heartbeat_loop(self):
        prev={'title': ""}
        oldstart=-1
        offset=timedelta(seconds=0)
        oldduration=0
        while True:
            try:
                songdata = self.get_data()
                if songdata == {}:
                    logger.info("Waiting for song to start")
                    self.mpd.idle("player")
                    songdata = self.get_data()
                    offset=timedelta(seconds=0)
                    continue

                now = datetime.now(timezone.utc)
                duration = self.get_duration()
                start = now - timedelta(seconds=duration)

                if oldstart == -1: oldstart = start

                if prev['title'] != songdata['title']:
                    logger.info(f"Now playing {songdata['title']} - {songdata['album']} - {songdata['artist']}")
                    if prev['title'] != '':
                        self.ping(prev, timestamp=oldstart, duration=oldduration)
                    prev = songdata
                    offset=timedelta(seconds=0)
                    oldduration=0
                    oldstart = start

                new=(start - oldstart).total_seconds() > 5

                if new:
                    logger.info(f"Playback has been resumed")
                    logger.info(f"Now playing {songdata['title']} - {songdata['album']} - {songdata['artist']}")
                    offset=timedelta(seconds=oldduration)

                oldstart = start
                oldduration = duration

                self.ping(songdata, timestamp= start + offset, duration=duration)

                sleep(self.settings.poll_time)
            except KeyboardInterrupt:
                logger.info(f"{self.watcher_name} stopped by keyboard interrupt")
                break


    def init_mpd(self) -> MPDClient:
        client = MPDClient()               # create client object
        client.timeout = 10                # network timeout in seconds (floats allowed), default: None
        client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default: None
        client.connect(self.settings.host, self.settings.port)
        self.mpd = client

    def get_duration(self) -> int:
        return floor(float(self.mpd.status()['elapsed']))

    def get_data(self) -> dict:
        status=self.mpd.status()

        state=status["state"]

        if state == "play":
            songid=status["songid"]
            song=self.mpd.playlistid(songid)[0]

            artists = song["artist"]
            albumartists = song["albumartist"]
            performers = song["performer"]

            if len(albumartists) == 0: albumartists = artists
            if len(performers) == 0: performers = artists


            return {"title": song["title"],
                    "artist": artists,
                    "album": song["album"],
                    "uri": song["file"],
                    "genre": song["genre"],
                    "performer": performers,
                    "albumartist": albumartists
                    }
        else: return {}
