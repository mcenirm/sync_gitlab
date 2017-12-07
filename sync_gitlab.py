from __future__ import print_function

import itertools
import os
import subprocess
import sys
import urlparse

import gitlab


class LocalCopyOfProject():
    def __init__(self, gitlab_project, spot):
        self.original = gitlab_project
        self.spot = spot
        self.local_repo_location = os.path.join(
            self.spot,
            self.original.path_with_namespace + u'.git',
        )

    def _run_git(self, *args, **kwargs):
        command = [u'git'] + list(args)
        with open(os.devnull, 'w') as ignore_output:
            rv = subprocess.call(
                command,
                stdout=ignore_output,
            )
            return rv

    def _run_git_in_local_repo(self, *args, **kwargs):
        modified_args = [
            u'--git-dir=' + self.local_repo_location,
        ] + list(args)
        return self._run_git(
            *modified_args,
            **kwargs
        )

    def already_cloned(self):
        if not os.path.isdir(self.local_repo_location):
            return False
        if 0 != self._run_git_in_local_repo(u'rev-parse'):
            return False
        return True

    def sync(self):
        if self.already_cloned():
            rv = self.update()
        else:
            rv = self.clone()
        return rv

    def clone(self):
        return self._run_git(
            u'clone',
            u'--quiet',
            u'--mirror',
            self.original.ssh_url_to_repo,
            self.local_repo_location,
        )

    def update(self):
        return self._run_git_in_local_repo(
            u'remote',
            u'update',
            u'--prune',
        )

    def show_branches(self):
        return self._run_git_in_local_repo(
            u'branch',
            u'-v',
            u'-a',
        )


gl = gitlab.Gitlab.from_config()
gl.auth()

spot = os.path.join(
    os.getcwdu(),
    u'spot',
    urlparse.urlparse(unicode(gl._url)).hostname,
)
if not os.path.isdir(spot):
    os.makedirs(spot)

projects = gl.projects.list(membership=True, as_list=False)

failures = []

for project in projects:
    project = next(projects)
    mirror = LocalCopyOfProject(project, spot)
    if 0 != mirror.sync():
        failures.append(mirror)

if len(failures) > 0:
    print(unicode(len(failures)) + u' failed:', file=sys.stderr)
    for failed in failures:
        print(failed.original.path_with_namespace, file=sys.stderr)
