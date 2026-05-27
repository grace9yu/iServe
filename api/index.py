import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "iserve_project.config.settings")

import django
from django.core.asgi import get_asgi_application

django.setup()
application = get_asgi_application()
