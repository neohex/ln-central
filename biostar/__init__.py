from __future__ import absolute_import
import subprocess

def get_git_revision_short_hash():
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()

VERSION = get_git_revision_short_hash()
