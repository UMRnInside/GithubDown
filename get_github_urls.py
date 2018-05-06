from sgmllib import SGMLParser
import urlparse
import requests
import logging

REGULAR_FILE = 0
DIR = 1
REF_DIR = 2
RAW_GITHUBUC = "https://raw.githubusercontent.com/"
ITEM_MARKS = ("css-truncate", "href", "span")


class GithubURLParser(SGMLParser):

    def reset(self):
        self.links = []
        self.pending_link = []
        SGMLParser.reset(self)

    def set_repo_info(self, repo_fullname):
        self.repo_fullname = repo_fullname
        self.repourl = "https://github.com/%s/" % (repo_fullname,)

    def determine_link_type(self, target_link):
        url_components = target_link.split('/')

        lc_repofullname = self.repo_fullname.lower()
        lc_targetname = "/".join(url_components[1:3]).lower()

        if lc_repofullname == lc_targetname:
            # Not a reference to other repos
            store_type = url_components[3]
            if store_type == "blob":
                # A file
                return REGULAR_FILE
            elif store_type == "tree":
                # A directory
                return DIR
            else:
                raise ValueError("%s is neither file nor folder"
                                 % (store_type,))
        else:
            # A reference to other repo
            return REF_DIR

    def start_a(self, attrs):
        urllist = [v for k, v in attrs if k == "href"]
        parsed_urllist = [(self.determine_link_type(v), v)
                          for v in urllist]

        self.pending_link.extend(parsed_urllist)

    def handle_data(self, text):
        if len(self.pending_link) == 0:
            return

        itemtype, url = self.pending_link[0]
        if itemtype == REF_DIR:
            logging.info("Handling git submodule...")
            pos = text.rfind(" @ ")
            name = text[:pos]
            logging.info("'@' is at %d, text '%s', name '%s'"
                         % (pos, text, name))
        else:
            name = text

        self.pending_link = []
        self.links.append((itemtype, url, name))


def get_raw_download_link(bloburl):
    url_components = bloburl.split('/')

    # url_components[4] is "blob"
    (repoowner, reponame) = url_components[1:3]
    blob = url_components[3]
    branch = url_components[4]
    filename = "/".join(url_components[5:])

    if blob != "blob":
        raise ValueError("only blob is accepted")

    location = "%s/%s/%s/%s" % (repoowner, reponame, branch, filename)
    final_link = urlparse.urljoin(RAW_GITHUBUC, location)

    return final_link


def get_item_list(target_link):
    resp = requests.get(target_link)

    content = resp.text.split("\n")
    for i in ITEM_MARKS:
        content = [line for line in content if i in line]

    # Redirection
    path_s = urlparse.urlparse(resp.url).path.split("/")
    (repoowner, reponame) = path_s[1:3]
    repo_fullname = "%s/%s" % (repoowner, reponame)

    gparser = GithubURLParser()
    gparser.reset()
    gparser.set_repo_info(repo_fullname)
    gparser.feed("\n".join(content))

    raw_links = gparser.links
    logging.debug("Dumping raw links...")
    logging.debug(repr(raw_links))

    anydirs = [(t, urlparse.urljoin("https://github.com/", u), name)
               for (t, u, name) in raw_links
               if t in (DIR, REF_DIR)]

    anyfiles = [(t, get_raw_download_link(u), name)
                for (t, u, name) in raw_links
                if t == REGULAR_FILE]

    logging.debug("Dumping result:")
    logging.debug(repr(anydirs + anyfiles))

    return anydirs + anyfiles
