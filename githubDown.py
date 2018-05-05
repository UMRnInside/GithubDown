#!/usr/bin/env python

import os
import sys
import logging
import argparse
import urlparse
import requests
from get_github_urls import get_item_list, REGULAR_FILE, DIR, REF_DIR

LOG_FORMAT = "%(levelname)s %(filename)s[%(lineno)d]:%(message)s"
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
    logging.debug("Using method " + method)
    return real_dlfunc(target_link, full_filename)


def smart_file_download(target_link, full_filename, method="default"):
    dirname, filename = os.path.split(full_filename)
    logging.info("Downloading %s" % (filename,))
    if not os.path.isdir(dirname):
        if os.path.exists(dirname):
            raise
        logging.info("mkdirs %s" % (dirname,))
        os.makedirs(dirname)

    file_download(target_link, full_filename, method)


def recursive_download(target_link, store_path=".", git_recursive=True):
    logging.info("Recursively downloading %s" % (target_link,))

    dirtypes = (DIR, REF_DIR) if git_recursive else (DIR,)
    current_path = store_path
    path_s = urlparse.urlparse(target_link).path.split("/")

    # ''/'repoowner'/'reponame'/'tree'/'branchname'/'dirname'
    if len(path_s) >= 6:
        local_path = path_s[5:]
        current_path = os.path.join(store_path, *local_path)
        if not os.path.isdir(current_path):
            logging.info("mkdir %s" % (current_path,))
            os.makedirs(current_path)
    logging.info("current store path is %s" % (current_path,))

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


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-u", "--url", type=str,
                        dest="repourl", required=True,
                        help="Github repo url")
    parser.add_argument("-C", "--directory", type=str,
                        dest="dir", default=".",
                        help="work directory set to DIR")
    parser.add_argument("-d", "--debuglevel", type=int,
                        dest="debuglevel", default=logging.INFO,
                        help="logging debug level")
    parser.add_argument("-r", "--recursive", action="store_const",
                        dest="recursive", default=False, const=True,
                        help="act like git clone --recursive (default no)")

    args = parser.parse_args()

    logging.basicConfig(format=LOG_FORMAT, level=args.debuglevel)
    recursive_download(args.repourl, args.dir, args.recursive)


if __name__ == "__main__":
    main()
