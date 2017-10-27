"""Main class for bot."""

import time
from os import path

import botskeleton

import gb_query

# Delay between tweets in seconds.
DELAY = 7200

if __name__ == "__main__":

    SECRETS_DIR = path.join(path.abspath(path.dirname(__file__)), "SECRETS")
    BOT_SKELETON = botskeleton.BotSkeleton(SECRETS_DIR, bot_name="goties_bot")

    LOG = botskeleton.set_up_logging()

    while True:
        LOG.info("Determining goties.")
        (year, _) = gb_query.get_goties()

        LOG.info(f"Sending out goties for {year}.")
        TXT = f"The Games of the Year for {year} are:"

        images = [gb_query.GOTY_FILENAME, gb_query.GOTIES_FILENAME]
        media_ids = BOT_SKELETON.upload_media(*images)
        LOG.debug(f"Media ids for uploaded images: {media_ids}")
        BOT_SKELETON.send_with_media(TXT, media_ids)

        LOG.info(f"Sleeping for {DELAY} seconds.")
        time.sleep(DELAY)
