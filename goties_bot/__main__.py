"""Main class for bot."""

import math
import os

import botskeleton

import gb_query

# Delay between tweets in seconds.
DELAY = math.ceil(3600 * 3.5)

if __name__ == "__main__":
    SECRETS_DIR = os.path.join(gb_query.HERE, "SECRETS")
    BOT_SKELETON = botskeleton.BotSkeleton(SECRETS_DIR, bot_name="goties_bot", delay=DELAY)
    LOG = BOT_SKELETON.log

    while True:
        LOG.info("Determining goties.")
        res = gb_query.get_goties()
        year = res["year"]

        LOG.info(f"Sending out goties for {year}.")
        TWEET = f"The Games of the Year for {year} are:"

        BOT_SKELETON.send_with_many_media(TWEET,
                                          gb_query.TOP_THREE_FILENAMES[0],
                                          gb_query.TOP_THREE_FILENAMES[1],
                                          gb_query.TOP_THREE_FILENAMES[2],
                                          gb_query.GOTIES_FILENAME,
                                          captions=res["captions"],
                                          )

        for f in gb_query.TOP_THREE_FILENAMES + [gb_query.GOTIES_FILENAME]:
            os.remove(f)

        BOT_SKELETON.nap()
