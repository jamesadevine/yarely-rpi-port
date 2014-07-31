# Settings and configuration that is common across deployment helpers,
# no matter which protocol is used to access the codebase.

import os
import shutil
import sys
import time

# Common path to the Yarely root..
# ..via mercurial
YARELY_HG_ROOT = "https://fogbugz.lancs.ac.uk/kiln/Code/Yarely"
# ..via rsync
YARELY_RSYNC_ROOT = "rsync://pd-dev.lancs.ac.uk/yarely"

# A selection of codebases, keyed by their local path and describing
# which platforms they are required on and where the master versions can be
# found
CODEBASES = {
    os.path.join("misc", "deployment"):
        {'platform': "all",
         'hg_url': YARELY_HG_ROOT + "/Misc/Deployment",
         'rsync_url': YARELY_RSYNC_ROOT + "_misc_deployment",
         },
    os.path.join("misc", "scratch"):
        {'platform': "all",
         'hg_url': YARELY_HG_ROOT + "/Misc/Scratch",
         'rsync_url': YARELY_RSYNC_ROOT + "_misc_scratch",
         },
    os.path.join("frontend", "core"):
        {'platform': "all",
         'hg_url': YARELY_HG_ROOT + "/Frontend-Implementation/Core",
         'rsync_url': YARELY_RSYNC_ROOT + "_frontend_core",
         },
    os.path.join("frontend", "darwin"):
        {'platform': "darwin",
         'hg_url': YARELY_HG_ROOT + "/Frontend-Implementation/Mac-OS-X",
         'rsync_url': YARELY_RSYNC_ROOT + "_frontend_darwin",
         },
    os.path.join("frontend", "linux"):
        {'platform': "linux",
         'hg_url': YARELY_HG_ROOT + "/Frontend-Implementation/Linux",
         'rsync_url': YARELY_RSYNC_ROOT + "_frontend_linux",
         },
    os.path.join("frontend", "windows"):
        {'platform': "win32",
         'hg_url': YARELY_HG_ROOT + "/Frontend-Implementation/Windows",
         'rsync_url': YARELY_RSYNC_ROOT + "_frontend_windows",
         },
}

# Name of the directory to work in within yarely_parent.
PROJECT_NAME = "yarely"

# Name of the local (configuration, logs etc) directory within yarely_parent.
PROJECT_LOCAL = PROJECT_NAME + "-local"

# Unqualified path to the starters directory that should be symlinked for
# ease of access.
STARTERS_DIR = os.path.join("misc", "deployment", "starters")

# Unqualified paths to directories requiring __init__.py files to be created
# This list should only need changing when more repositories are added as
# __init__.py files should be hosted within repositories where possible.
DIRS_REQUIRING_INIT_PY_FILES = ["", "frontend"]

# Sample configuration unqualified source path
SAMPLE_CONFIG_PATH = os.path.join("misc", "deployment", "resources",
    "sample-config")

CODEBASE_CHANGE_INITIAL_TEMPLATE = \
    "Initial deployment of '{path}' to {revision!r}"
CODEBASE_CHANGE_TEMPLATE = \
    "Updated deployment of '{path}' to {revision!r} (was {pre_revision!r})"


class DeploymentError(Exception):
    """Raised when a deployment inconsistency is found."""
    pass


class DeploymentHelper:
    def start(self):
        self.codebase_changes = []
        arg_parser = self.build_argparser()
        args = arg_parser.parse_args()
        self.handle_args(args)

        self.verify_yarely_parent()
        self.deploy_codebases()
        self.record_codebase_changes()
        self.create_init_py_files()
        self.create_sample_config_if_required()

## FIXME - this will probably fail on Windows.  Work out what we want to do
## about making the starters directory available when we target Windows.
        self.link_starters_if_required()

    def build_argparser(self, arg_parser):
        arg_parser.add_argument("-r", "--revision", default="tip",
            help="Revision tag or changeset to update all codebases to "
                "(default: %(default)s)")
        arg_parser.add_argument("--all-platforms", default=False,
            action='store_true',
            help="Deploy all codebases (even non-native platforms) "
                "(default: %(default)s)")
        arg_parser.add_argument("--without-sample-config", default=False,
            action='store_true',
            help="By default a sample configuration will be created within "
                "'<yarely_parent>/yarely-local' if the 'yarely-local' folder "
                "does not exist.  Specify --without-sample-config to prevent "
                "this from occuring.")
        arg_parser.add_argument("--change-log-file",
            help="If an existing file is supplied, a line will be written "
                "to it for each codebase that is changed")
        arg_parser.add_argument("yarely_parent",
            help="Path to the Yarely parent directory.  A 'yarely' directory "
                "will be created within this.")

    def handle_args(self, args):
        self.revision = args.revision
        self.all_platforms = args.all_platforms
        self.without_sample_config = args.without_sample_config

        self.change_log_file = args.change_log_file
        if self.change_log_file is not None:
            if not os.path.isfile(self.change_log_file):
                msg = "Change log file '{}' is not an existing file."
                raise DeploymentError(msg.format(self.change_log_file))

        self.yarely_parent = args.yarely_parent

    def verify_yarely_parent(self):
        """Verify the Yarely parent path supplied is an existing directory."""
        if not os.path.isdir(self.yarely_parent):
            msg = "Yarely parent '{}' is not an existing directory."
            raise DeploymentError(msg.format(self.yarely_parent))

    def deploy_codebases(self):
        """Deploy or update codebases from the master copy."""
        for (local_dir, details) in CODEBASES.items():
            platform = details['platform']
            if self.all_platforms or self.platform_is_native(platform):
                local_path = os.path.join(self.yarely_parent, PROJECT_NAME,
                    local_dir)
                self.deploy_codebase(local_path, details)

    def deploy_codebase(self, local_path, details):
        """Deploy or update a specific codebase from the master copy."""
        if os.path.isdir(local_path):
            pre_revision = self.get_existing_codebase_revision(local_path)
            self.update_existing_codebase(local_path, details)
            post_revision = self.get_existing_codebase_revision(local_path)

            if pre_revision != post_revision:
                change_msg = CODEBASE_CHANGE_TEMPLATE.format(path=local_path,
                    revision=post_revision, pre_revision=pre_revision)
                self.codebase_changes.append(change_msg)

        elif not os.path.exists(local_path):
            local_path_parent = os.path.split(local_path)[0]
            if not os.path.isdir(local_path_parent):
                os.makedirs(local_path_parent)

            self.deploy_initial_codebase(local_path, details)
            post_revision = self.get_existing_codebase_revision(local_path)

            change_msg = CODEBASE_CHANGE_INITIAL_TEMPLATE.format(
                path=local_path, revision=post_revision)
            self.codebase_changes.append(change_msg)
        else:
            msg = "Yarely codebase '{}' exists but is not a directory."
            raise DeploymentError(msg.format(local_path))

    def record_codebase_changes(self):
        """If applicable, record changed codebases to the change log file."""
        if self.change_log_file is None or len(self.codebase_changes) == 0:
            return

        with open(self.change_log_file, 'a') as change_log:
            change_log.write('\n'.join(self.codebase_changes))
            # Be neat - terminate with a new line
            change_log.write('\n')

    def create_init_py_files(self):
        """Create __init__.py files in non-repository directories."""
        project_path = os.path.join(self.yarely_parent, PROJECT_NAME)

        for dir_requiring_init_py_file in DIRS_REQUIRING_INIT_PY_FILES:
            dir_path = os.path.join(project_path, dir_requiring_init_py_file)
            self.create_init_py_file(dir_path)

    def create_init_py_file(self, dir_path):
        """Create an __init__.py file in the supplied directory path."""
        if not os.path.isdir(dir_path):
            msg = ("Expected to write __init__.py file to '{path}' but it is "
                "not an existing directory.")
            raise DeploymentError(msg.format(path=dir_path))

        init_py_path = os.path.join(dir_path, "__init__.py")

        if os.path.isfile(init_py_path):
            return

        elif not os.path.exists(init_py_path):
            msg = [
                "# Created automatically by Yarely's deployment helper",
                "# " + time.ctime(),
                ""
                ]

            with open(init_py_path, "w") as init_py:
                init_py.write("\n".join(msg))
        else:
            msg = "__init__.py '{path}' exists but is not a regular file."
            raise DeploymentError(msg.format(path=init_py_path))

    def create_sample_config_if_required(self):
        """Copy sample configuration into yarely-local if it does not exist."""
        if self.without_sample_config:
            return

        yarely_local_path = os.path.join(self.yarely_parent, PROJECT_LOCAL)

        if os.path.isdir(yarely_local_path):
            return

        os.mkdir(yarely_local_path)
        os.mkdir(os.path.join(yarely_local_path, "logs"))

        sample_config_src_path = os.path.join(self.yarely_parent, PROJECT_NAME,
                SAMPLE_CONFIG_PATH)
        sample_config_dst_path = os.path.join(yarely_local_path, "config")
        shutil.copytree(sample_config_src_path, sample_config_dst_path)

    def link_starters_if_required(self):
        """Create a symlink to the starters directory."""
        starters_link_path = os.path.join(self.yarely_parent, "yarely",
                "starters")

        if os.path.islink(starters_link_path):
            return

        elif not os.path.exists(starters_link_path):
            os.symlink(STARTERS_DIR, starters_link_path)

        else:
            msg = "Starters link '{}' exists but is not a symlink."
            raise DeploymentError(msg.format(starters_link_path))

    def platform_is_native(self, platform):
        platform_map = {
            "darwin": "darwin",

            "linux": "linux",
            "linux2": "linux",
            "linux3": "linux",

            "win32": "win32"
        }

        if platform == 'all':
            return True

        if sys.platform not in platform_map:
            msg = "Platform '{platform}' is not supported."
            raise NotImplementedError(msg.format(platform=sys.platform))

        return platform == platform_map[sys.platform]
