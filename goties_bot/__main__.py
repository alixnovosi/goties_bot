"""Main class for bot."""

import os
import time

import botskeleton

import gb_query

# Delay between tweets in seconds.
DELAY = 7200

if __name__ == "__main__":

    SECRETS_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "SECRETS")
    api = botskeleton.BotSkeleton(SECRETS_DIR, bot_name="goties_bot")

    LOG = botskeleton.set_up_logging()

    while True:
        LOG.info("Determining goties.")
        (year, _) = gb_query.get_goties()

        LOG.info(f"Sending out goties for {year}.")
        TXT = f"The Games of the Year for {year} are:"

        images = [gb_query.GOTY_FILENAME, gb_query.GOTIES_FILENAME]
        media_ids = api.upload_media(*images)
        LOG.debug(f"Media ids for uploaded images: {media_ids}")
        api.send_with_media(TXT, media_ids)

        LOG.info(f"Sleeping for {DELAY} seconds.")
        time.sleep(DELAY)
