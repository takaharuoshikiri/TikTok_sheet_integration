# coding=utf-8
import os
import json

from six import string_types
from urllib.parse import urlencode, urlunparse

import requests

ACCESS_TOKEN = "act.CT1xYxEuLnB05mGXjKJfpSGOo3Wa1WIDm2a3TFo74awXFJ5M1XmSWXkzVfL3!5342.va"
PATH = "/open_api/v1.3/tt_user/token_info/get/"


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

    # レスポンスの情報を表示
    print("=== レスポンス情報 ===")
    print("URL:", url)
    print("Status Code:", rsp.status_code)
    print("Headers:", rsp.headers)
    print("Response Text:", rsp.text)
    print("======================")

    return rsp.json()

if __name__ == '__main__':
    secret = "6eda48ddfdda858b36d9d2aa372d935e3bc00510"
    app_id = "7493061298511413249"
    # secret = os.getenv('SECRET', '')
    # app_id = os.getenv('APP_ID', '')

    # Args in JSON format


    my_args = "{\"secret\": \"%s\", \"app_id\": \"%s\"}" % (secret, app_id)
    print(get(my_args))

