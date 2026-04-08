"""Django 服务层管理入口。"""

from __future__ import annotations

import os
import sys


def main() -> None:
    """执行 Django 管理命令。"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_service.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
