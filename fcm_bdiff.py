#!/usr/bin/env python3
# *********************************COPYRIGHT************************************
# (C) Crown copyright Met Office. All rights reserved.
# For further details please refer to the file COPYRIGHT.txt
# which you should have received as part of this distribution.
# *********************************COPYRIGHT************************************
"""
This module provides the functionality to return a list of local files to
run tests on based on the branch-difference (to allow checking of only files
which a developer has actually modified on their branch)
"""

import os
import re
import subprocess
import time


# ------------------------------------------------------------------------------
class FCMError(Exception):
    """
    Exception class for FCM commands
    """

    def __str__(self):
        return '\nFCM command: "{0:s}"\nFailed with error: "{1:s}"'.format(
            " ".join(self.args[0]), self.args[1].strip()
        )


# ------------------------------------------------------------------------------
def is_trunk(url):
    """
    Given an FCM url, returns True if it appears to be pointing to the
    UM main trunk
    """
    search = re.search(
        r"""
                       (svn://fcm\d+/\w+_svn/\w+/trunk|
                       .*/svn/[\w\.]+/\w+/trunk|
                       ..*_svn/\w+/trunk)
                       """,
        url,
        flags=re.VERBOSE,
    )
    return search is not None


# ------------------------------------------------------------------------------
def text_decoder(bytes_type_string, codecs=["utf8", "cp1252"]):
    """
    Given a bytes type string variable, attempt to decode it using the codecs
    listed.
    """

    errors = []
    for codec in codecs:
        try:
            return bytes_type_string.decode(codec)
        except UnicodeDecodeError as err:
            errors.append(err)

    for error in errors:
        print(error)
        raise errors[0]


# ------------------------------------------------------------------------------
def get_branch_info(branch, snooze=300, retries=0):
    """
    Extract the output of the branch info command
    (if the branch is the mirror, allow for a few retries in case
     it hasn't picked up the latest commit yet)
    """

    command = ["fcm", "binfo", branch]
    return run_fcm_command(command, retries, snooze)


# ------------------------------------------------------------------------------
def get_bdiff_summarize(branch, snooze=300, retries=0):
    """
    Extract the output of the branch diff command
    (if the branch is the mirror, allow for a few retries in case
     it hasn't picked up the latest commit yet)
    """
    command = ["fcm", "bdiff", "--summarize", branch]
    return run_fcm_command(command, retries, snooze)


# ------------------------------------------------------------------------------
def get_branch_diff_filenames(branch=".", path_override=None):
    """
    The main routine of this module, given the path to a working copy or the
    URL of a branch (or simply run from within a working copy), returns a list
    of filenames based on the FCM branch diff.  In most cases it should try
    to resolve to local filenames;
    The base file path can be overridden, which may be helpful in suites.
    If no working copy exists and the base path was not overridden, it will
    return URLs in that case.
    """

    branch, retries = use_mirror(branch)

    # Get information about the branch
    info = get_branch_info(branch, retries=retries)

    branch_url = get_url(info)

    # The branch should not be the trunk (a branch-diff would make no sense)
    if is_trunk(branch_url):
        print("{} appears to be the trunk, nothing to do!".format(branch_url))
        return []

    # The branch parent should be the trunk; if it isn't assume this is a
    # branch-of-branch (a test branch), and redirect the request to point at
    # the parent branch
    parent = get_branch_parent(info)
    while not is_trunk(parent):
        branch = parent
        info = get_branch_info(branch, retries=retries)
        parent = get_branch_parent(info)

    # The command `fcm bdiff --summarize <branch_name>` returns a different
    # format if the branch has been reversed off the trunk. The expected format
    # is svn://fcm1/um.xm_svn/main/trunk/rose-stem/bin/suite_report.py
    # but if it has been reversed then we get
    # svn://fcm1/um.xm_svn/main/branches/dev/USER/BRANCH_NAME/PATH
    # This results in an invalid path provided by relative_paths
    bdiff = get_bdiff_summarize(branch, retries=retries)

    # Extract files from the bdiff that have been modified (M) or added (A).
    # Strip whitespace, and remove blank lines while turning the output into
    # a list of strings.
    bdiff_files = [x.strip() for x in bdiff.split("\n") if x.strip()]
    bdiff_files = [
        bfile.split()[1]
        for bfile in bdiff_files
        if bfile.split()[0].strip() == "M" or bfile.split()[0].strip() == "A"
    ]

    # Convert the file paths to be relative to the current URL; to do this
    # construct the base path of the trunk URL and compare it to the results
    # of the bdiff command above
    repos_root = get_repository_root(info)
    relative_paths = [
        os.path.relpath(bfile, os.path.join(repos_root, "main", "trunk"))
        for bfile in bdiff_files
    ]

    # These relative paths can be joined to an appropriate base to complete
    # the filenames to return
    base_source_key = "SOURCE_UM_BASE"
    if path_override is not None:
        # Allows for 'user directed' path reconstruction.
        # Particularly useful in rose stem.
        base = path_override
        bdiff_files = [os.path.join(base, bfile) for bfile in relative_paths]
    elif base_source_key in os.environ:
        # If running as a suite, the base path to the working copy can be used
        # However, unless the suite task is running on a machine with the same
        # path to the working copy, the task can't really make much use of
        # this.
        base = os.environ[base_source_key]
        bdiff_files = [os.path.join(base, bfile) for bfile in relative_paths]
    else:
        # Otherwise stick to the original path/URL to the branch
        bdiff_files = [os.path.join(branch, bfile) for bfile in relative_paths]

    return bdiff_files


# ------------------------------------------------------------------------------
def run_fcm_command(command, max_retries, snooze):
    """
    Run an fcm command, optionally retrying on failure.
    """
    retries = 0
    while True:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout
        else:
            retries += 1
            if retries > max_retries:
                raise FCMError(command, result.stderr)
            else:
                time.sleep(snooze)


# ------------------------------------------------------------------------------
def use_mirror(branch):
    """
    Catch to work out if this is running as part of a suite using an
    FCM mirror, if it is then redirect the request to the mirror.
    If using the mirror then fcm calls can sometimes fail so specify a number
    of retries for other routines to use.

    Returns updated branch URL and a number of retries
    """

    mirror_key = "SOURCE_UM_MIRROR"
    if mirror_key in os.environ:
        branch = os.environ[mirror_key]
        retries = 2
        print(f"[INFO] Switching branch used for fcm command to: {branch}")
    else:
        retries = 0
    return branch, retries


# ------------------------------------------------------------------------------
def get_repository_root(branch_info):
    """
    Given the raw output from an fcm binfo command - which can be retrieved by
    calling get_branch_info() - returns the Repository Root field
    """
    repos_root = re.search(
        r"^Repository Root:\s*(?P<url>.*)\s*$", branch_info, flags=re.MULTILINE
    )
    if repos_root:
        repos_root = repos_root.group("url")
    else:
        raise Exception("Could not find Repository Root field")
    return repos_root


# ------------------------------------------------------------------------------
def get_branch_parent(branch_info):
    """
    Given the raw output from an fcm binfo command - which can be retrieved by
    calling get_branch_info() - returns the Branch Parent Field
    """
    parent = re.search(
        r"^Branch Parent:\s*(?P<parent>.*)$", branch_info, flags=re.MULTILINE
    )
    if parent:
        parent = parent.group("parent")
    else:
        raise Exception("Could not find Branch Parent field")
    return parent


# ------------------------------------------------------------------------------
def get_url(branch_info):
    """
    Given the raw output from an fcm binfo command - which can be retrieved by
    calling get_branch_info() - returns the URL field
    """
    url = re.search(r"^URL:\s*(?P<url>.*)$", branch_info, flags=re.MULTILINE)
    if url:
        url = url.group("url")
    else:
        raise Exception("Could not find URL field")
    return url




class FCMBDiff:
    """Class which generates a branch diff."""
    """This a modified (mangled) copy of the one Sam made in bdiff/git_bdiff.py, to
    allow current scripts to try and migrate to getting information from an
    instance of the same class. 
    Note that the version for Git has a small handful of methods, mostly internal
    and some propeties. These are kept as close as possible to version in git_bdiff.py.
    Attributes used to navigate the horros of FCM and thus used in this package are
    therefore preceded with an '_' and shouldn't be what is being referred to outwith
    this class. Nor should the original 'functions'..."""

    # Name of primary branch - default is ~~main~~ Trunk
    primary_branch = "trunk"

    #=- # Match hex commit IDs
    #=- _hash_pattern = re.compile(r"^\s*([0-9a-f]{40})\s*$")

    # Match branch names.  This should catch all valid names but may
    # also some invalid names through.  This should matter given that
    # it is being used to match git command output.  For a complete
    # overview of the naming scheme, see man git check-ref-format
    _branch_pattern = re.compile(r"^\s*([^\s~\^\:\?\*\[]+[^.])\s*$")

    def __init__(self, parent=None, repo=None):
        """The 'git' version of this get's to assume 'repo' is a directory, presumably
        containing a local 'clone' (of a fork of a repos). That is not how we have 
        worked previously with FCM, to which you could give a path to a working copy,
        or a URL to a branch or the trunk on the remote server. So, much of the initial
        stages here replicate the kind of 'discovery' that was neccessary for FCM that
        is hoped to become outdated with Git"""

        # The git version uses this as user provided to compare the clone to
        # to see if it's a branch of that and has diverged from it.
        # We've previously used the 'parent' property reorted by fcm to see
        # what the WC or URL is a version of. For the 'real' parent in an FCM sense,
        # try self.ancestor
        self.parent = parent or self.primary_branch

        self._branch, self._retries = use_mirror(branch)
        self._branch_info = get_branch_info(branch, retries=self._retries)

        _branch_url = get_url(self._branch_info)

        # The branch should not be the trunk (a branch-diff would make no sense)
        if is_trunk(_branch_url):
            print("{} appears to be the trunk, nothing to do!".format(branch_url))
            # Need to work out what the response here should be ?
            # is_branch would be False, but what other properties would have a value.
            return [] # Probably need to return an object, but with what properties ?
    

        # The branch parent(ancestor) should be the trunk(main); if it isn't assume this is a
        # branch-of-branch (a test branch), and redirect the request to point at
        # the parent branch
        self.ancestor = get_branch_parent(self._branch_info)
        while not is_trunk(self.ancestor):
            self._branch = self.ancestor
            self._branch_info = get_branch_info(self._branch, retries=self._retries)
            parent = get_branch_parent(self._branch_info)
        self.is_trunk  = is_trunk(self._branch):
            # Ask Sam if the is_branch property should be is_trunk to match
            # historic behaviour - or if there should be 'both' sides of this
            # one logical test ?
        self.is_branch = not self.is_trunk

        # Commenting this out, as it only sets an internal attribute, which I think is
        # the Git equivalent of either _branch_url, or _branch...(ain't inconsistent
        # use of terminology a swine ?)
        #=- if repo is None:
        #=-     self._repo = None
        #=- else:
        #=-     self._repo = Path(repo)
        #=-     if not self._repo.is_dir():
        #=-         raise GitBDiffError(f"{repo} is not a directory")

        self.current = 42 # Curious to see what this might be used for in the fcm world
                          # meanwhile 42 is the answer to life the universe and everything...
        self.branch = os.path.basename(_branch_url) # again, not sure we use this in fcm world.

        self.has_diverged =  # Boolean

        def files(self):
            """Iterate over files changed on the branch."""
            dem_danged_files = self._get_files()
            for line in dem_danged_files:
                if line != "":
                    yield line


        def _get_files(self, path_override=None):
        # Ohhh...
        # The command `fcm bdiff --summarize <branch_name>` returns a different
        # format if the branch has been reversed off the trunk. The expected format
        # is svn://fcm1/um.xm_svn/main/trunk/rose-stem/bin/suite_report.py
        # but if it has been reversed then we get
        # svn://fcm1/um.xm_svn/main/branches/dev/USER/BRANCH_NAME/PATH
        # This results in an invalid path provided by relative_paths
        bdiff = get_bdiff_summarize(self._branch, retries=self._retries)

        # Extract files from the bdiff that have been modified (M) or added (A).
        # Strip whitespace, and remove blank lines while turning the output into
        # a list of strings.
        bdiff_files = [x.strip() for x in bdiff.split("\n") if x.strip()]
        bdiff_files = [
            bfile.split()[1]
            for bfile in bdiff_files
            if bfile.split()[0].strip() == "M" or bfile.split()[0].strip() == "A"
        ]

        # Convert the file paths to be relative to the current URL; to do this
        # construct the base path of the trunk URL and compare it to the results
        # of the bdiff command above
        repos_root = get_repository_root((self._branch_info)
        relative_paths = [
            os.path.relpath(bfile, os.path.join(repos_root, "main", "trunk"))
            for bfile in bdiff_files
        ]

        # These relative paths can be joined to an appropriate base to complete
        # the filenames to return
        base_source_key = "SOURCE_UM_BASE"
        if path_override is not None:
            # Allows for 'user directed' path reconstruction.
            # Particularly useful in rose stem.
            base = path_override
            bdiff_files = [os.path.join(base, bfile) for bfile in relative_paths]
        elif base_source_key in os.environ:
            # If running as a suite, the base path to the working copy can be used
            # However, unless the suite task is running on a machine with the same
            # path to the working copy, the task can't really make much use of
            # this.
            base = os.environ[base_source_key]
            bdiff_files = [os.path.join(base, bfile) for bfile in relative_paths]
        else:
            # Otherwise stick to the original path/URL to the branch
            bdiff_files = [os.path.join(branch, bfile) for bfile in relative_paths]

        return bdiff_files

