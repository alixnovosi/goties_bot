"""Stuff related to interfacing with Giant Bomb API."""
import logging
import os
import random
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

GOTIES_FILENAME = "goties.png"

with open("API_KEY", "r") as f:
    API_KEY = f.read().strip()


def year_filter_from_year(year):
    """Generate a filter for year based on a year."""
    filter_field = "original_release_date"
    filter_string = "{}:{}-1-1 00:00:00|{}-1-1 00:00:00".format(filter_field, year, year+1)
    LOG.debug("Year filter is %s.", filter_field)
    return filter_string


def get_query_uri(search_filter, sort_field=None, limit=1, offset=0):
    """Get query URI for games."""
    return GB_GAMES_URL + "&api_key={}&filter={}&sort={}&limit={}&offset={}".format(API_KEY,
                                                                                    search_filter,
                                                                                    sort_field,
                                                                                    limit,
                                                                                    offset)


def get_count(year_filter):
    """Return number of games known to the GB API in a given year."""
    query_uri = get_query_uri(search_filter=year_filter)

    resp = perform_gb_query(query_uri)
    print(resp)
    return resp["number_of_total_results"]


def get_random_game(year_filter, year_count):
    """Get a game from the GB API."""
    LOG.info("Year count is %s.", year_count)
    offset = random.choice(range(year_count))
    LOG.info("Choosing offset %s.", offset)

    query_uri = get_query_uri(search_filter=year_filter, limit=1, offset=offset)

    resp = perform_gb_query(query_uri)

    # TODO handle better
    try:
        return random.choice(resp["results"])
    except IndexError as e:
        LOG.error("Got index error: %s", e)
        return [{"name": "Video Games"}]


def get_goties():
    """Get games of the year (10 of them)."""
    year = random.choice(range(1980, 2017))
    year_filter = year_filter_from_year(year)
    year_count = get_count(year_filter)

    # Make sure we do both ascending and descending order sorting.
    heads = random.choice([True, False])
    if heads:
        order = "asc"
    else:
        order = "desc"
    LOG.info("Chose order %s", order)

    # SECRET DON'T LOOK!
    method = random.choice(list(PickMethods))
    if method == PickMethods.chronological:
        LOG.info("Choosing chronologically.")
        goties = handle_offset_get(year_filter=year_filter,
                                   sort_field="original_release_date:" + order,
                                   year_count=year_count)

    elif method == PickMethods.added:
        LOG.info("Choosing by added date.")
        goties = handle_offset_get(year_filter=year_filter,
                                   sort_field="date_added:" + order, year_count=year_count)

    elif method == PickMethods.last_updated:
        LOG.info("Choosing by last updated date.")
        goties = handle_offset_get(year_filter=year_filter,
                                   sort_field="date_last_updated:" + order,
                                   year_count=year_count)

    elif method == PickMethods.num_user_reviews:
        LOG.info("Choosing by number of user reviews.")
        goties = handle_offset_get(year_filter=year_filter,
                                   sort_field="number_of_user_reviews:" + order,
                                   year_count=year_count)

    elif method == PickMethods.gb_id:
        LOG.info("Choosing by GB id.")
        goties = handle_offset_get(year_filter=year_filter,
                                   sort_field="id:" + order,
                                   year_count=year_count)
    elif method == PickMethods.random:
        LOG.info("Choosing at random.")
        goties = []
        for _ in range(NUMBER_GOTIES):
            goty = get_random_game(year_filter, year_count)
            goties.append(goty)

    out = "Game of the Year List for {}\n".format(year)
    for i in range(NUMBER_GOTIES):
        name = goties[i]["name"]
        out += "{}. {}\n".format(i+1, name)

    # Render text as image.
    img = Image.new("RGB", (1200, 500), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 40)
    draw.text((40, 40), out, font=font, fill=(0, 0, 0, 255))
    img.save(GOTIES_FILENAME)

    LOG.info("Your goties are: \n%s", out)
    return (year, out)


def handle_offset_get(year_filter, sort_field, year_count):
    """Handle indexing at a random offset into GB API results to get games."""
    offset = random.choice(range(0, year_count-NUMBER_GOTIES))
    query_uri = get_query_uri(search_filter=year_filter,
                              sort_field=sort_field,
                              limit=NUMBER_GOTIES,
                              offset=offset)
    resp = perform_gb_query(query_uri)
    return resp["results"]


@util.rate_limited(200)
def perform_gb_query(query_uri):
    """Hit GB API. Perform rate limiting."""
    LOG.info("Query URI is %s.", query_uri)
    resp = requests.get(query_uri, headers=HEADERS)
    print(resp.status_code)
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
