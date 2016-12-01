"""Stuff related to interfacing with Giant Bomb API."""
import asyncio
import logging
from logging.handlers import RotatingFileHandler
import os
import random
import sys
from enum import Enum

import requests
from PIL import Image, ImageDraw, ImageFont

import util

HERE = os.path.abspath(os.path.dirname(__file__))
LOG = logging.getLogger("root")

GB_BASE_URL = "http://www.giantbomb.com/api/"
GB_GAMES_URL = GB_BASE_URL + "games/?format=json"

# Being a good citizen - produce a useful user_agent.
OWNER_URL = "https://github.com/andrewmichaud/goties_bot"
USER_AGENT = "goties_twitterbot/1.0 (" + OWNER_URL + ") " + \
             "(bots+goties@mail.andrewmichaud.com)"
HEADERS = {"User-Agent": USER_AGENT}

NUMBER_GOTIES = 10

with open("API_KEY", "r") as f:
    API_KEY = f.read().strip()


def year_filter_from_year(year):
    """Generate a filter for year based on a year."""
    filter_field = "original_release_date"
    filter_string = "{}:{}-1-1 00:00:00|{}-1-1 00:00:00".format(filter_field, year, year+1)
    LOG.debug("Year filter is {}.".format(filter_field))
    return filter_string


def get_query_uri(api_key, search_filter, sort_field=None, limit=1, offset=0):
    """Get query URI for games."""
    return GB_GAMES_URL + "&api_key={}&filter={}&sort={}&limit={}&offset={}".format(api_key,
                                                                                    search_filter,
                                                                                    sort_field,
                                                                                    limit,
                                                                                    offset)


async def get_count(api_key, year):
    """Return number of games known to the GB API in a given year."""
    year_filter = year_filter_from_year(year)
    query_uri = get_query_uri(api_key, year_filter)

    resp = await perform_gb_query(query_uri)
    print(resp)
    return resp["number_of_total_results"]


async def get_random_game(api_key):
    """Get a game from the GB API."""
    year = 2014
    year_filter = year_filter_from_year(year)
    query_url = GB_GAMES_URL + "?format=json&api_key={}&filter={}".format(api_key,
                                                                          year_filter)
    print("querying with {}".format(query_url))
    resp = requests.get(query_url, headers=HEADERS)

    resp_json = resp.json()

    result = random.choice(resp_json["results"])

    print("name: {}".format(result["name"]))
    print("release date: {}".format(result["original_release_date"]))
    print("killed_characters: {}".format(result["killed_characters"]))

    game = {}
    game["name"] = result["name"]

    # temp rate limiting to not get myself in trouble while testing.
    # time.sleep(18)

    return game

async def get_goties(api_key):
    """Get games of the year (10 of them)."""
    # TODO randomize year.
    year = 2014
    year_filter = year_filter_from_year(year)
    year_count = await get_count(api_key, year)

    # Make sure we do both ascending and descending order sorting.
    heads = random.choice([True, False])
    if heads:
        order = "asc"
    else:
        order = "desc"
    LOG.info("Chose order %s", order)

    method = PickMethods.chronological

    if method == PickMethods.chronological:
        LOG.info("Choosing chronologically.")
        offset = random.choice(range(0, year_count-NUMBER_GOTIES))
        query_uri = get_query_uri(api_key=api_key, search_filter=year_filter,
                                  sort_field="original_release_date:" + order,
                                  limit=NUMBER_GOTIES,
                                  offset=offset)
        resp = await perform_gb_query(query_uri)
        goties = resp["results"]

    out = "Game of the Year List for {}\n".format(year)
    for i in range(NUMBER_GOTIES):
        name = goties[i]["name"]
        out += "{}. {}\n".format(i+1, name)

    # Render text as image.
    img = Image.new("RGB", (1000, 500), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 40)
    draw.text((40, 40), out, font=font, fill=(0, 0, 0, 255))
    img.save("goties.png")

    LOG.info("Your goties are: \n %s", out)
    LOG.info("Length: %s", len(out))
    return out


@util.rate_limited(200)
async def perform_gb_query(query_uri):
    """Hit GB API. Perform rate limiting."""
    LOG.debug("Query URI is %s.", query_uri)
    resp = ""
    resp = requests.get(query_uri, headers=HEADERS)
    LOG.debug("Full response is: \n %s", resp.text)
    return resp.json()


# SECRET DON'T LOOK!
class PickMethods(Enum):
    """Ways we know to pick goties."""
    chronological = 100
    random = 200
    added = 300
    last_updated = 400
    num_user_reviews = 500
    gb_id = 700


def _setup_logging():
    log_filename = os.path.join(HERE, "log")

    logger = logging.getLogger("root")
    logger.setLevel(logging.DEBUG)

    # Provide a file handler that logs everything in a verbose format.
    file_handler = RotatingFileHandler(filename=log_filename, maxBytes=1024000000, backupCount=10)
    verbose_form = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s")
    file_handler.setFormatter(verbose_form)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Provide a stdout handler that only logs things the use (theoretically) cares about (INFO and
    # above).
    stream_handler = logging.StreamHandler(sys.stdout)
    simple_form = logging.Formatter(fmt="%(message)s")
    stream_handler.setFormatter(simple_form)

    # stream_handler.setLevel(logging.DEBUG)
    stream_handler.setLevel(logging.INFO)

    logger.addHandler(stream_handler)

    return logger

if __name__ == "__main__":
    _setup_logging()
    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(get_goties(API_KEY))
    LOOP.run_forever()
