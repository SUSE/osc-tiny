"""
OBS auto release helper
----------------------
"""
import argparse
import glob
import os
import tempfile
import typing
from datetime import datetime
from pathlib import Path
from pytz import _UTC
import requests
from osctiny import Osc
from osctiny.models.request import Action, ActionType, Source, Target
from osctiny.utils.changelog import Entry

def get_latest_release() -> typing.Tuple[str, str]:
    """
    Get latest release name and body
    """
    response = requests.get(
        "https://api.github.com/repos/suse/osc-tiny/releases?per_page=1",
        timeout=10)
    releases = response.json()
    return (releases[0]['tag_name'].strip('v'), releases[0]['body'])

def find_source(directory: str) -> typing.Union[str, None]:
    """
    Find file name in directory
    """
    file_path = glob.glob(f'{directory}/osc[-_]tiny-*.tar.gz')
    if file_path:
        return os.path.basename(file_path[0])
    return None

def read_file(filename: str) -> str:
    """
    Read file content
    """
    with open(filename, 'r') as fh:
        content = fh.readlines()
    return content

class Obs:
    """
    OBS instance
    """
    pproject = "openSUSE:Factory"
    package = "python-osc-tiny"
    project = None
    release_name = None
    release_body = None

    def __init__(self, **kwargs):
        """
        Initialize the obs instance
        """
        self.username = kwargs.get("username", "")
        self.osc = Osc(
            url="https://api.opensuse.org",
            username=self.username,
            password=kwargs.get("password", ""),
        )
        self.project = f"home:{self.username}:branches:devel:languages:python"
        self.destdir = Path(tempfile.mkdtemp())

    def branchco(self):
        """
        Branch from parent project and checkout paclage
        """
        params = {"force": 1,
                  "noservice": 1,
                  "autocleanup": 1,
                  "target_project": self.project}
        # Branch from parent project
        self.osc.packages.cmd(self.pproject, self.package, "branch", **params)
        self.osc.packages.checkout(self.project, self.package, self.destdir)
        self.release_name, self.release_body = get_latest_release()

    def modify_spec_file(self) -> None:
        """
        Modify spec file
        """
        lines = read_file(f"{self.destdir}/{self.package}.spec")
        data = ""
        for line in lines:
            if line.startswith("Version:"):
                data += f"Version:        {self.release_name}\n"
            else:
                data += line.replace("osc-tiny-%{version}", "osc_tiny-%{version}")
        self.osc.packages.push_file(self.project, self.package, f"{self.package}.spec", data)

    def modify_changes_file(self) -> None:
        """
        Modify change log
        """
        lines = read_file(f"{self.destdir}/{self.package}.changes")

        content = f"- Release {self.release_name}\n"
        for line in self.release_body.split("\r\n"):
            content += f"  {line}\n"
        entry = Entry(
            packager=self.username,
            content=content,
            timestamp=datetime.now(tz=_UTC())
        )
        data = str(entry)
        for line in lines:
            data += line
        self.osc.packages.push_file(self.project, self.package,
                                    f"{self.package}.changes", data)

    def replace_source_file(self) -> None:
        """
        Replace source file
        """
        old_file = find_source(self.destdir)
        new_file = find_source("./dist")
        if old_file and new_file:
            self.osc.packages.delete_file(self.project, self.package, old_file)
            with open(f"./dist/{new_file}", 'rb') as file:
                self.osc.packages.push_file(self.project, self.package, new_file, data=file)

    def commit(self) -> None:
        """
        Commit and create submit request
        """
        self.osc.packages.cmd(self.project, self.package, "commit",
                              comment=f"Release {self.release_name}")
        actions = [
            Action(
                type=ActionType.SUBMIT,
                source=Source(project=self.project, package=self.package),
                target=Target(project="devel:languages:python", package=self.package)
            )
        ]
        self.osc.requests.create(actions=actions)

    def __call__(self) -> None:
        self.branchco()
        self.modify_spec_file()
        self.modify_changes_file()
        self.replace_source_file()
        self.commit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Auto release package to OBS.')
    parser.add_argument('--username', required=True, help='Username for login')
    parser.add_argument('--password', required=True, help='Password for login')
    args = parser.parse_args()
    obs = Obs(username=args.username, password=args.password)
    obs()
