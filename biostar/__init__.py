from __future__ import absolute_import
import subprocess
from datetime import datetime
from datetime import tzinfo, timedelta
import pytz
import dateutil.parser as dp

def get_git_revision_short_hash():
    out = subprocess.check_output(['git', 'show', '-s', '--format=%cI %h', 'HEAD']).decode('ascii').strip()
    return out.split()

git_info = get_git_revision_short_hash() 
VERSION ={
	'build_time': dp.parse(git_info[0]),
        'server_start_time': datetime.now(pytz.UTC),
	'build_hash': git_info[1],
    }

