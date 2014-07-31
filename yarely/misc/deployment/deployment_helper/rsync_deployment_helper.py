#!/usr/bin/env python3.2

# Deploy Yarely from the rsync server (or update an existing deployment).
#
# This is probably useful in most 'live' deployments where development
# won't be happening.

from argparse import ArgumentParser
import os
import subprocess

import common


class RsyncDeploymentHelper(common.DeploymentHelper):
    def build_argparser(self):
        arg_parser = ArgumentParser(
            description="Deploy Yarely from master rsync server")
        super().build_argparser(arg_parser)
        return arg_parser

    def update_existing_codebase(self, local_path, details):
        """Pull local_path and update to revision."""
        src_path = "{url}/{revision}/".format(url=details['rsync_url'],
            revision=self.revision)
        cmd = ["rsync", "--archive", "--no-owner", "--no-group"]
        cmd.extend(["--no-devices", "--no-specials", "--itemize-changes"])
        cmd.extend(["--delete", "--verbose", "--exclude", "__pycache__/"])
        cmd.extend([src_path, local_path])

        subprocess.check_call(cmd)

    def deploy_initial_codebase(self, local_path, details):
        """Clone details[hg_url] to local_path."""
        self.update_existing_codebase(local_path, details)

    def get_existing_codebase_revision(self, local_path):
        """Describe the revision of the codebase at local_path.

        The return value is a string that can be compared to
        see whether the codebase revision has altered.
        """
        hg_archival_path = os.path.join(local_path, '.hg_archival.txt')

        node = None
        tags = []

        with open(hg_archival_path, 'r') as hg_archival:
            for line in hg_archival.readlines():
                if line.startswith("node: "):
                    node = line[6:].strip()
                elif line.startswith("tag: "):
                    tags.append(line[5:].strip())

        if node is None:
            msg = "Didn't find 'node' specification in '{}'"
            raise common.DeploymentError(msg.format(hg_archival_path))

        if len(tags) == 0:
            return node

        return "{node} {tags}".format(node=node, tags='/'.join(tags))

if __name__ == "__main__":
    deployment_helper = RsyncDeploymentHelper()
    deployment_helper.start()
