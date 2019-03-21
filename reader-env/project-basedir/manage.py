#!/usr/bin/env python
import os
import sys
import errno

def create_live_dir():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LIVE_DIR = '{}/live'.format(BASE_DIR)
    LIVE_DIR_ACCESS_RIGHTS = 0o755

    try:
        os.mkdir(LIVE_DIR, LIVE_DIR_ACCESS_RIGHTS)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    else:
        print('Created new directory {}'.format(LIVE_DIR))


if __name__ == "__main__":
    create_live_dir()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biostar.settings.debug')

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
