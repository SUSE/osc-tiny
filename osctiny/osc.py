import gc
from ssl import get_default_verify_paths

from lxml.objectify import fromstring
from requests import Session, Request
from requests.auth import HTTPBasicAuth

from .packages import Package
from .projects import Project
from .bs_requests import Request as BsRequest
from .search import Search


class Osc:
    """
    Build service API client
    """
    url = 'https://api.opensuse.org'
    username = ''
    password = ''
    session = None
    _registered = {}

    def __init__(self, url=None, username=None, password=None, verify=None):
        # Basic URL and authentication settings
        self.url = url or self.url
        self.username = username or self.username
        self.password = password or self.password
        self.session = Session()
        self.session.verify = verify or get_default_verify_paths().capath
        self.auth = HTTPBasicAuth(self.username, self.password)

        # API endpoints
        self.packages = Package(osc_obj=self)
        self.projects = Project(osc_obj=self)
        self.requests = BsRequest(osc_obj=self)
        self.search = Search(osc_obj=self)

    def __del__(self):
        # Just in case ;-)
        gc.collect()

    def request(self, url, data=None, method="GET", stream=False):
        data = data or {}
        req = Request(method, url, auth=self.auth, data=data)
        prepped_req = self.session.prepare_request(req)
        settings = self.session.merge_environment_settings(
            prepped_req.url, None, None, None, None
        )
        settings["stream"] = stream
        response = self.session.send(prepped_req, **settings)
        response.raise_for_status()
        return response

    @staticmethod
    def get_objectified_xml(response):
        return fromstring(response.text)




