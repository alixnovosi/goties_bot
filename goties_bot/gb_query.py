"""Stuff related to interfacing with Giant Bomb API."""

import logging
import random
from datetime import datetime
from enum import Enum
from os import path

import botskeleton
import requests
import yaml
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
GB_BASE_URL = "https://www.giantbomb.com/api/"
GB_GAMES_URL = f"{GB_BASE_URL}games/"
GB_GAME_URL = f"{GB_BASE_URL}game/"

# Bot config/housekeeping.
NUMBER_GOTIES = 10

TOP_THREE_FILENAMES = ["goty_1.png", "goty_2.png", "goty_3.png"]
GOTIES_FILENAME = "goties.png"
YEAR_END_SPECIAL_FILENAME = path.join(SECRETS_DIR, "YEAR_END_SPECIAL.yaml")

with open(path.join(SECRETS_DIR, "API_KEY"), "r") as f:
    API_KEY = f.read().strip()

def get_goties():
    """Get goties (or year-end goties)."""
    if datetime.now().month >= 11:
        return get_goties_year_end_special()
    else:
        return get_gometies_regular()

def get_goties_year_end_special():
    with open(YEAR_END_SPECIAL_FILENAME, "r") as f:
        year_end_special_contents = yaml.safe_load(f)

    year = year_end_special_contents["year"]
    all_games = year_end_special_contents["games"]

    LOG.info(year_end_special_contents)

    LOG.info("Loaded games for YEAR END SPECIAL.")

    # Pick ten games randomly from the list.
    games = random.sample(all_games, NUMBER_GOTIES)
    print(len(games))

    LOG.info(f"Chose winners!")

    processed = {}
    goties = []
    for i, game_yaml in enumerate(games):
        game_name = game_yaml["name"]
        game_id = game_yaml["id"]

        # Just need to process the top three games right now, so make life easy for us and the API.
        if i < 3:
            # Don't query GB API multiple times if we have duplicates in the list for whatever reason.
            if game_name in processed.keys():
                LOG.info(f"Skipping going to GB for '{game_name}', we have it already.")
                goties.append(processed[game_name])
            else:
                LOG.info(f"Looking up '{game_name}' by id.")
                goty = get_named_game(game_id)

                # Ensure that names will be right even if query wasn't good enough and we got the
                # wrong game and therefore art.
                goty["name"] = game_name
                processed[game_name] = goty
                goties.append(goty)

        else:
            LOG.info(f"Skipping going to GB for '{game_name}', it's not top 3.")
            goties.append({"name": game_name})

    out = render_and_save_images(year, goties)

    LOG.info(f"Your goties are: \n{out}")
    return (year, out)

def get_goties_regular():
    """Get games of the year (10 of them)."""
    current_year = datetime.today().year

    # Trying out different distributions
    year = int(random.triangular(1985, current_year, 2005))
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

    out = render_and_save_images(year, goties)

    LOG.info(f"Your goties are: \n{out}")
    return (year, out)

def render_and_save_images(year, goties):
    """Render images and output tweet text."""
    out = f"Game of the Year List for {year}\n"
    for i, goty in enumerate(goties):
        num = f"{i+1}".zfill(len(str(NUMBER_GOTIES)))
        out += f"{num}. {goty['name']}\n"

    font = ImageFont.truetype(path.join(HERE, "FreeMono.ttf"), 40)

    save_goties(year, out, font)
    save_game_images(goties)

    return out

def save_game_images(goties):
    """Save game images to files."""
    for i, goty in enumerate(goties[:3]):
        img_dict = goty["image"]

        if img_dict is not None:

            for item in ["original_url", "super_url", "medium_url", "small_url", "thumb_url",
                         "tiny_url"]:
                if item in img_dict:
                    url = img_dict[item]
                    break

            LOG.info(f"Cover art for #{i} GOTY: {url}")

        # Ensure exists and then clear.
        filename = TOP_THREE_FILENAMES[i]
        open(filename, "a", encoding="UTF-8").close()
        open(filename, "w", encoding="UTF-8").close()
        if url is not None:
            r = requests.get(url, headers=HEADERS, stream=True)

            chunks = r.iter_content(chunk_size=1024)
            with open(filename, "wb") as stream:
                for chunk in chunks:
                    if not chunk:
                        return
                    stream.write(chunk)
                    stream.flush()

def save_goties(year, out, font):
    """Save Goties to an image file."""
    img = Image.new("RGB", (1200, 500), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), out, font=font, fill=(0, 0, 0, 255))
    img.save(GOTIES_FILENAME)

def get_named_game(id):
    """Get specific game from GB API."""
    query_uri = f"{GB_GAME_URL}{id}?format=json&api_key={API_KEY}"
    return query_for_goty(query_uri, expect_list=False, always_return_something=False)

def get_random_game(year_filter, year_count):
    """Get a game from the GB API."""
    LOG.info(f"Year count is {year_count}.")
    offset = random.choice(range(year_count))
    LOG.info(f"Choosing offset {offset}.")

    query_uri = get_query_uri(search_filter=year_filter, limit=1, offset=offset)
    return query_for_goty(query_uri)

def query_for_goty(query_uri, expect_list=True, always_return_something=True):
    """Perform query, get GOTY."""
    resp = perform_gb_query(query_uri)

    if not expect_list:
        return resp["results"]

    if len(resp["results"]) == 0 and always_return_something:
        return {"name": "Video Games"}
    elif len(resp["results"]) == 0:
        return {}
    else:
        return random.choice(resp["results"])

def year_filter_from_year(year):
    """Generate a filter for year based on a year."""
    filter_field = "original_release_date"
    filter_string = f"{filter_field}:{year}-1-1 00:00:00|{year}-12-31 23:59:59"
    LOG.debug(f"Year filter is {filter_string}.")
    return filter_string

def handle_offset_get(year_filter, sort_field, year_count):
    """Handle indexing at a random offset into GB API results to get games."""
    offset = random.choice(range(0, year_count-NUMBER_GOTIES))
    query_uri = get_query_uri(search_filter=year_filter,
                              sort_field=sort_field,
                              limit=NUMBER_GOTIES,
                              offset=offset)
    resp = perform_gb_query(query_uri)
    return resp["results"]

def get_query_uri(search_filter, sort_field=None, limit=1, offset=0):
    """Get query URI for games."""
    return f"{GB_GAMES_URL}?format=json&api_key={API_KEY}" +\
            f"&filter={search_filter}&sort={sort_field}&limit={limit}&offset={offset}"

def get_count(year_filter):
    """Return number of games known to the GB API in a given year."""
    query_uri = get_query_uri(search_filter=year_filter)

    resp = perform_gb_query(query_uri)
    return resp["number_of_total_results"]

@botskeleton.rate_limited(200)
def perform_gb_query(query_uri):
    """Hit GB API. Perform rate limiting."""
    LOG.info(f"Query URI is '{query_uri}'.")
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
