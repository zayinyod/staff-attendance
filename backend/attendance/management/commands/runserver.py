"""
runserver の拡張。静的ファイルをキャッシュさせずに配信する。

同名のコマンドは INSTALLED_APPS で先に記載したアプリが優先されるため、
attendance は django.contrib.staticfiles より前に記載する。
"""

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.contrib.staticfiles.management.commands.runserver import (
    Command as StaticFilesRunserverCommand,
)
from util.static_handlers import NoCacheStaticFilesHandler


class Command(StaticFilesRunserverCommand):

    def get_handler(self, *args, **options):
        handler = super().get_handler(*args, **options)
        if isinstance(handler, StaticFilesHandler):
            return NoCacheStaticFilesHandler(handler.application)
        return handler
