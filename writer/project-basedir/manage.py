#!/usr/bin/env python
import os
import sys
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIVE_DIR = '{}/live'.format(BASE_DIR)

def create_live_dir():
    LIVE_DIR_ACCESS_RIGHTS = 0o755
    
    try:  
        os.mkdir(LIVE_DIR, LIVE_DIR_ACCESS_RIGHTS)
    except FileExistsError:
        pass
    else:  
        print('Created new directory {}'.format(LIVE_DIR))

if __name__ == '__main__':
    create_live_dir()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biostar_writer.settings.dev')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # workaround for https://github.com/arteria/django-background-tasks/issues/181
    if 'migrate' in sys.argv and '-h' not in sys.argv and '--help' not in sys.argv:
        file_list = glob.glob('{}/../../writer-env/lib/python*/site-packages/background_task/migrations/0003_auto_*.py'.format(BASE_DIR))
        for f in file_list:
            os.remove(f)

    execute_from_command_line(sys.argv)
