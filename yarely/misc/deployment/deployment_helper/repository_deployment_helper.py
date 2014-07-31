#!/usr/bin/env python3.2

# Deploy Yarely from the repositories (or update an existing deployment).
#
# This is probably only of use in UoL development environments.

from argparse import ArgumentParser
import subprocess

import common


class RepositoryDeploymentHelper(common.DeploymentHelper):
    def build_argparser(self):
        arg_parser = ArgumentParser(
            description="Deploy Yarely from development repositories")
        arg_parser.add_argument("--noninteractive", default=False,
            action='store_true',
            help="Do not prompt, assume 'yes' for any required answers (i.e. "
                "pass --noninteractive on hg command lines) "
                "(default: %(default)s)")
        super().build_argparser(arg_parser)
        return arg_parser

    def handle_args(self, args):
        super().handle_args(args)
        self.noninteractive = args.noninteractive

    def update_existing_codebase(self, local_path, details):
        """Pull local_path and update to revision."""
        cmd = ["hg", "pull"]
        if self.noninteractive:
            cmd.append("--noninteractive")
        cmd.extend(["--repository", local_path])
        subprocess.check_call(cmd)

        cmd = ["hg", "update"]
        if self.noninteractive:
            cmd.append("--noninteractive")
        cmd.extend(["--check", "--repository", local_path])
        cmd.extend(["--rev", self.revision])
        subprocess.check_call(cmd)

    def deploy_initial_codebase(self, local_path, details):
        """Clone details[hg_url] to local_path."""
        cmd = ["hg", "clone"]
        if self.noninteractive:
            cmd.append("--noninteractive")
        cmd.extend(["--noupdate", details['hg_url'], local_path])
        subprocess.check_call(cmd)

        self.update_existing_codebase(local_path, details)

    def get_existing_codebase_revision(self, local_path):
        """Describe the revision of the codebase at local_path.

        The return value is a bytes instance that can be compared to
        see whether the codebase revision has altered.
        """
        cmd = ["hg", "identify"]
        if self.noninteractive:
            cmd.append("--noninteractive")
        cmd.extend(["--repository", local_path])
        return subprocess.check_output(cmd).strip()

if __name__ == "__main__":
    deployment_helper = RepositoryDeploymentHelper()
    deployment_helper.start()
