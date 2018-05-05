#!/usr/bin/env python

import os
import sys
import argparse
import urlparse
import requests
from get_github_urls import get_item_list, REGULAR_FILE, DIR, REF_DIR

CHUNK_SIZE = 1024


def default_file_download(target_link, full_filename):
    resp = requests.get(target_link, stream=True)
    with open(full_filename, "wb") as f:
        for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)


download_methods = {
        "default": default_file_download,
        "python-requests": default_file_download,
        }


def file_download(target_link, full_filename, method):
    real_dlfunc = download_methods[method]
    return real_dlfunc(target_link, full_filename)


def smart_file_download(target_link, full_filename, method="default"):
    dirname, filename = os.path.split(full_filename)
    if not os.path.isdir(dirname):
        if os.path.exists(dirname):
            raise
        os.makedirs(dirname)

    file_download(target_link, full_filename, method)


def recursive_download(target_link, store_path=".", git_recursive=True):
    dirtypes = (DIR, REF_DIR) if git_recursive else (DIR,)
    current_path = "."
    path_s = urlparse.urlparse(target_link).path.split("/")

    # ''/'repoowner'/'reponame'/'tree'/'branchname'/'dirname'
    if len(path_s) >= 6:
        local_path = path_s[5:]
        current_path = os.path.join(store_path, local_path)
        if not os.path.isdir(current_path):
            os.makedirs(current_path)

    itemlist = get_item_list(target_link)
    fileurls = [u for (t, u) in itemlist
                if t == REGULAR_FILE]
    dirurls = [u for (t, u) in itemlist
               if t in dirtypes]

    for url in fileurls:
        url_s = urlparse.urlparse(url).path.split("/")
        filename = url_s[-1]
        file_storepath = os.path.join(current_path, filename)

        smart_file_download(url, file_storepath)

    for d in dirurls:
        recursive_download(d, store_path, git_recursive)
