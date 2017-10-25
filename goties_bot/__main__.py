"""Main class for bot."""

import os
import time

import gb_query
import util

import botskeleton

# Delay between tweets in seconds.
DELAY = 7200

if __name__ == "__main__":

    SECRETS_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "SECRETS")
    api = botskeleton.BotSkeleton(SECRETS_DIR, bot_name="goties_bot")

    LOG = util.set_up_logging()

    while True:
        LOG.info("Determining goties.")
        (year, _) = gb_query.get_goties()

        LOG.info("Sending out goties for %s.", year)
        TXT = "The Games of the Year for {} are:".format(year)

        images = [gb_query.GOTY_FILENAME, gb_query.GOTIES_FILENAME]
        media_ids = api.upload_media(*images)
        LOG.debug("Media ids for uploaded images: {}".format(media_ids))
        api.send_with_media(TXT, media_ids)

        LOG.info("Sleeping for {} seconds.".format(DELAY))
        time.sleep(DELAY)
