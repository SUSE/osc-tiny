"""
OBS auto release helper
----------------------
"""
import argparse
import glob
import os
import re
import typing
from datetime import datetime


from pytz import _UTC
import requests
from osctiny import Osc
from osctiny.models.request import Action, ActionType, Source, Target
from osctiny.utils.changelog import Entry

def find_source(directory: str) -> typing.Union[str, None]:
    """
    Find file name in directory
    """
    file_path = glob.glob(f'{directory}/osc[-_]tiny-*.tar.gz')
    if file_path:
        return os.path.basename(file_path[0])
    return None

class Obs:
    """
    OBS instance
    """
    project = "devel:languages:python"
    target = "openSUSE:Factory"
    package = "python-osc-tiny"
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

    def get_latest_release(self) -> None:
        """
        Get latest release name and body
        """
        response = requests.get(
            "https://api.github.com/repos/suse/osc-tiny/releases?per_page=1",
            timeout=10)
        releases = response.json()
        self.release_name = releases[0]['tag_name'].strip('v')
        self.release_body = releases[0]['body']

    def modify_spec_file(self) -> None:
        """
        Modify spec file
        """
        version_pattern = r"\nVersion:\s+[\d\.]+\n"
        response = self.osc.packages.get_file(self.project, self.package,
                                              f"{self.package}.spec")
        response.encoding = 'utf-8'
        data = response.text.replace("osc-tiny-%{version}", "osc_tiny-%{version}")
        data = re.sub(version_pattern, f"\nVersion:        {self.release_name}\n", data)
        self.osc.packages.push_file(self.project, self.package, f"{self.package}.spec", data)

    def modify_changes_file(self) -> None:
        """
        Modify change log
        """
        response = self.osc.packages.get_file(self.project, self.package,
                                              f"{self.package}.changes")
        response.encoding = 'utf-8'
        lines = [f"  {line}" for line in self.release_body.strip().split("\r\n") if line]
        content = f"- Release {self.release_name}\n" + "\n".join(lines)
        entry = Entry(
            packager=f"{self.username} <maintenance-automation-team@suse.de>",
            content=content,
            timestamp=datetime.now(tz=_UTC())
        )
        data = str(entry) + response.text
        self.osc.packages.push_file(self.project, self.package,
                                    f"{self.package}.changes", data)

    def replace_source_file(self) -> None:
        """
        Replace source file
        """
        source_pattern = re.compile(r"osc[-_]tiny-[\d\.]+.tar.gz")
        entries = self.osc.packages.get_files(self.project, self.package, expand=True)
        files = [e.get("name") for e in entries.findall("entry")
                 if source_pattern.match(e.get("name"))]
        old_file = files[0] if files else None
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
                target=Target(project=self.target, package=self.package)
            )
        ]
        self.osc.requests.create(actions=actions)

    def __call__(self) -> None:
        self.get_latest_release()
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
