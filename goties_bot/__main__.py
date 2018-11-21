"""Main class for bot."""

from os import path

import botskeleton

import gb_query

# Delay between tweets in seconds.
DELAY = 7200 * 2

if __name__ == "__main__":
    SECRETS_DIR = path.join(gb_query.HERE, "SECRETS")
    BOT_SKELETON = botskeleton.BotSkeleton(SECRETS_DIR, bot_name="goties_bot", delay=DELAY)
    LOG = BOT_SKELETON.log

    while True:
        LOG.info("Determining goties.")
        GOTY_STORE = gb_query.GOTYStore()
        res = GOTY_STORE.get_goties()
        year = res["year"]

        LOG.info(f"Sending out goties for {year}.")
        TWEET = f"The Games of the Year for {year} are:"

        BOT_SKELETON.send_with_many_media(TWEET,
                                          *GOTY_STORE.filenames,
                                          captions=res["captions"],
                                          )

        BOT_SKELETON.nap()
