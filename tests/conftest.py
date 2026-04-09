from __future__ import annotations

import django
from django.conf import settings

if not settings.configured:
    settings.DJANGO_SETTINGS_MODULE = "tests.settings"
    django.setup()
