# coding=utf-8
import os
import json

from six import string_types
from urllib.parse import urlencode, urlunparse

import requests

ACCESS_TOKEN = "63ce543a676f71d860aa415af50ffe5cb89f1d6b"
PATH = "/open_api/v1.3/oauth2/advertiser/get/"


def build_url(path, query=""):
    # type: (str, str) -> str
    """
    Build request URL
    :param path: Request path
    :param query: Querystring
    :return: Request URL
    """
    scheme, netloc = "https", "business-api.tiktok.com"
    return urlunparse((scheme, netloc, path, "", query, ""))

def get(json_str):
    # type: (str) -> dict
    """
    Send GET request
    :param json_str: Args in JSON format
    :return: Response in JSON format
    """
    args = json.loads(json_str)
    query_string = urlencode({k: v if isinstance(v, string_types) else json.dumps(v) for k, v in args.items()})
    url = build_url(PATH, query_string)
    headers = {
        "Access-Token": ACCESS_TOKEN,
    }
    rsp = requests.get(url,  headers=headers)
    return rsp.json()

if __name__ == '__main__':
    secret = "01fe5c05bf14a9cb67b1d2e4cbc79b8d73e555bc"
    app_id = "7480734449341038609"
    # secret = os.getenv('SECRET', '')
    # app_id = os.getenv('APP_ID', '')

    # Args in JSON format
    my_args = "{\"secret\": \"%s\", \"app_id\": \"%s\"}" % (secret, app_id)
    print(get(my_args))

