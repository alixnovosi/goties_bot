"""Main class for bot."""

import subprocess
import time

import tweepy

import gb_query
import send
import util

# Delay between tweets in seconds.
DELAY = 7200

if __name__ == "__main__":
    API = send.auth_and_get_api()

    LOG = util.set_up_logging()

    while True:
        LOG.info("Determining goties.")
        (year, _) = gb_query.get_goties()

        LOG.info("Sending out goties for %s.", year)
        TXT = "The Games of the Year for {} are:".format(year)

        try:
            images = (gb_query.GOTY_FILENAME, gb_query.GOTIES_FILENAME)
            media_ids = [API.media_upload(i).media_id_string for i in images]
            LOG.debug("Media ids for uploaded images: {}".format(media_ids))
            API.update_status(status=TXT, media_ids=media_ids)
            # API.update_with_media(gb_query.GOTIES_FILENAME, status=TXT)

        except tweepy.TweepError as e:
            LOG.critical("A Tweepy error we don't know how to handle happened.")
            LOG.critical("Error reason: {}".format(e.reason))
            LOG.critical("Exiting.")
            break

        LOG.info("Sleeping for {} seconds.".format(DELAY))
        time.sleep(DELAY)
