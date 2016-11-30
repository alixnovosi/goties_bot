import random
import time

import requests

import util

GB_BASE_URL = "http://www.giantbomb.com/api/"
GB_GAMES_URL = GB_BASE_URL + "games/"

# Being a good citizen - produce a useful user_agent.
OWNER_URL = "https://github.com/andrewmichaud/goties_bot"
USER_AGENT = "goties_twitterbot/1.0 (" + OWNER_URL + ") (bots+goties@mail.andrewmichaud.com)"
HEADERS = {"User-Agent": USER_AGENT}

with open("API_KEY", "r") as f:
    API_KEY = f.read().strip()

def year_filter_from_year(year):
    """Generate a filter for year based on a year."""
    filter_field = "original_release_date"
    filter_sort = "original_release_date:asc"
    filter = "{}:{}-1-1 00:00:00|{}-1-1 00:00:00&sort={}".format(filter_field, year, year+1,
                                                                 filter_sort)
    print("filter is {}".format(filter))
    return filter

@util.rate_limited(200)
def get_game(api_key):
    """Get a game from the GB API."""
    year = 2014
    year_filter = year_filter_from_year(year)
    query_url = GB_GAMES_URL + "?format=json&api_key={}&filter={}".format(api_key,
                                                                          year_filter)
    print("querying with {}".format(query_url))
    resp = requests.get(query_url, headers=HEADERS)

    resp_json = resp.json()

    print("status code: {}".format(resp.status_code))
    for key in resp_json:
        print("A key in json is {}".format(key))

    result = random.choice(resp_json["results"])
    for key in result:
        print("A key in result is {}".format(key))

    print("name: {}".format(result["name"]))
    print("release year: {}".format(result["original_release_date"]))


    # temp rate limiting to not get myself in trouble while testing.
    time.sleep(18)

if __name__ == "__main__":
    get_game(API_KEY)
