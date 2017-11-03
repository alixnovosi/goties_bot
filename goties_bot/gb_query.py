"""Stuff related to interfacing with Giant Bomb API."""

import logging
import random
from datetime import datetime
from enum import Enum
from os import path

import botskeleton
import requests
from PIL import Image, ImageDraw, ImageFont

# Path stuff and logging.
HERE = path.abspath(path.dirname(__file__))
SECRETS_DIR = path.join(HERE, "SECRETS")

LOG = logging.getLogger("root")

# Being a good citizen - produce a useful user_agent.
OWNER_EMAIL = "bots+goties@mail.andrewmichaud.com"
OWNER_URL = "https://github.com/andrewmichaud/goties_bot"

with open(path.join(path.join(HERE, ".."), "VERSION")) as f:
    VERSION = f.read().strip()

USER_AGENT = f"goties_twitterbot/{VERSION} ({OWNER_URL}) ({OWNER_EMAIL})"
HEADERS = {"User-Agent": USER_AGENT}

# GB info.
GB_BASE_URL = "http://www.giantbomb.com/api/"
GB_GAMES_URL = f"{GB_BASE_URL}games/?format=json"

# Bot config/housekeeping.
NUMBER_GOTIES = 10

GOTY_FILENAME = "goty.png"
GOTIES_FILENAME = "goties.png"

with open(path.join(SECRETS_DIR, "API_KEY"), "r") as f:
    API_KEY = f.read().strip()

def year_filter_from_year(year):
    """Generate a filter for year based on a year."""
    filter_field = "original_release_date"
    filter_string = f"{filter_field}:{year}-1-1 00:00:00|{year}-12-31 23:59:59"
    LOG.debug(f"Year filter is {filter_string}.")
    return filter_string

def get_query_uri(search_filter, sort_field=None, limit=1, offset=0):
    """Get query URI for games."""
    return f"{GB_GAMES_URL}&api_key={API_KEY}" +\
            f"&filter={search_filter}&sort={sort_field}&limit={limit}&offset={offset}"

def get_count(year_filter):
    """Return number of games known to the GB API in a given year."""
    query_uri = get_query_uri(search_filter=year_filter)

    resp = perform_gb_query(query_uri)
    return resp["number_of_total_results"]

def get_random_game(year_filter, year_count):
    """Get a game from the GB API."""
    LOG.info(f"Year count is {year_count}.")
    offset = random.choice(range(year_count))
    LOG.info(f"Choosing offset {offset}.")

    query_uri = get_query_uri(search_filter=year_filter, limit=1, offset=offset)

    resp = perform_gb_query(query_uri)

    # TODO handle better
    try:
        return random.choice(resp["results"])
    except IndexError as e:
        LOG.error(f"Got index error: {e}")
        return [{"name": "Video Games"}]

def get_goties():
    """Get games of the year (10 of them)."""
    current_year = datetime.today().year
    year = random.choice(range(1980, current_year+1))
    year_filter = year_filter_from_year(year)
    year_count = get_count(year_filter)

    # Make sure we do both ascending and descending order sorting.
    heads = random.choice([True, False])
    if heads:
        order = "asc"
    else:
        order = "desc"
    LOG.info(f"Chose order {order}.")

    # SECRET DON'T LOOK!
    method = random.choice(list(PickMethods))
    if method == PickMethods.chronological:
        LOG.info("Choosing chronologically.")
        goties = handle_offset_get(year_filter=year_filter,
                                   sort_field=f"original_release_date: {order}",
                                   year_count=year_count)

    elif method == PickMethods.added:
        LOG.info("Choosing by added date.")
        goties = handle_offset_get(year_filter=year_filter,
                                   sort_field=f"date_added: {order}",
                                   year_count=year_count)

    elif method == PickMethods.last_updated:
        LOG.info("Choosing by last updated date.")
        goties = handle_offset_get(year_filter=year_filter,
                                   sort_field=f"date_last_updated: {order}",
                                   year_count=year_count)

    elif method == PickMethods.num_user_reviews:
        LOG.info("Choosing by number of user reviews.")
        goties = handle_offset_get(year_filter=year_filter,
                                   sort_field=f"number_of_user_reviews: {order}",
                                   year_count=year_count)

    elif method == PickMethods.gb_id:
        LOG.info("Choosing by GB id.")
        goties = handle_offset_get(year_filter=year_filter,
                                   sort_field=f"id: {order}",
                                   year_count=year_count)

    elif method == PickMethods.random:
        LOG.info("Choosing at random.")
        goties = []
        for _ in range(NUMBER_GOTIES):
            goty = get_random_game(year_filter, year_count)
            goties.append(goty)

    out = f"Game of the Year List for {year}\n"
    for i in range(NUMBER_GOTIES):
        name = goties[i]["name"]
        out += f"{i+1}. {name}\n"

    # Render text as image.
    img = Image.new("RGB", (1200, 500), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(path.join(HERE, "FreeMono.ttf"), 40)
    draw.text((40, 40), out, font=font, fill=(0, 0, 0, 255))
    img.save(GOTIES_FILENAME)

    # Save image of first game we can find an image for.
    # TODO do top 3 or something
    url = None
    for i, goty in enumerate(goties):
        img_dict = goty["image"]

        # TODO figure out which of these is actually guaranteed instead of just guessing + if/elseing.
        if img_dict is None:
            continue

        if "medium_url" in img_dict:
            url = img_dict["medium_url"]
            break
        LOG.info(f"Cover art for #{i} GOTY: {url}")

    if url is not None:
        r = requests.get(url, headers=HEADERS, stream=True)

        chunks = r.iter_content(chunk_size=1024)

        open(GOTY_FILENAME, "a", encoding="UTF-8").close()
        with open(GOTY_FILENAME, "wb") as stream:
            for chunk in chunks:
                if not chunk:
                    return
                stream.write(chunk)
                stream.flush()

    LOG.info(f"Your goties are: \n{out}")
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

@botskeleton.rate_limited(200)
def perform_gb_query(query_uri):
    """Hit GB API. Perform rate limiting."""
    LOG.info(f"Query URI is {query_uri}.")
    resp = requests.get(query_uri, headers=HEADERS)
    print(resp.status_code)
    LOG.debug(f"Full response is: \n {resp.text}")
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
