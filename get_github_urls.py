from sgmllib import SGMLParser
import urlparse

REGULAR_FILE = 0
FOLDER = 1
REF_FOLDER = 2


class GithubURLParser(SGMLParser):

    def reset(self):
        self.links = []
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
                # A folder
                return FOLDER
            else:
                raise ValueError("%s is neither file nor folder"
                                 % (store_type,))
        else:
            # A reference to other repo
            return REF_FOLDER

    def start_a(self, attrs):
        urllist = [v for k, v in attrs if k == "href"]
        parsed_urllist = [(self.determine_link_type(v), v)
                          for v in urllist]

        self.links.extend(parsed_urllist)
