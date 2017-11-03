"""Main class for bot."""

from os import path

import botskeleton

import gb_query

# Delay between tweets in seconds.
DELAY = 7200

if __name__ == "__main__":
    SECRETS_DIR = path.join(gb_query.HERE, "SECRETS")
    BOT_SKELETON = botskeleton.BotSkeleton(SECRETS_DIR, bot_name="goties_bot", delay=DELAY)

    LOG = botskeleton.set_up_logging()

    while True:
        LOG.info("Determining goties.")
        (year, _) = gb_query.get_goties()

        LOG.info(f"Sending out goties for {year}.")
        TWEET = f"The Games of the Year for {year} are:"

        images = [gb_query.GOTY_FILENAME, gb_query.GOTIES_FILENAME]
        media_ids = BOT_SKELETON.upload_media(*images)
        LOG.debug(f"Media ids for uploaded images: {media_ids}")
        BOT_SKELETON.send_with_media(TWEET, media_ids)
