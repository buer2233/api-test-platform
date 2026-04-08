"""V2 服务层 WSGI 入口。"""

from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_service.settings")

application = get_wsgi_application()
