"""
開発サーバーで静的ファイルを配信するハンドラ
"""

from django.contrib.staticfiles.handlers import StaticFilesHandler


class NoCacheStaticFilesHandler(StaticFilesHandler):
    """
    静的ファイルの応答に Cache-Control: no-cache を付与する。
    ブラウザは毎回更新の有無を問い合わせるため、変更したファイルが即座に反映される。
    未変更の場合は 304 が返る。
    """

    def serve(self, request):
        response = super().serve(request)
        response["Cache-Control"] = "no-cache"
        return response
