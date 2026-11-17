from django.utils import timezone


class Now:
    """
    現在の日付と時刻を扱うユーティリティクラス
    """

    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M"

    @classmethod
    def date_str(cls, dt: object = None) -> str:
        """
        日付を文字列として取得
        """
        dt = dt or timezone.localdate()
        return dt.strftime(cls.date_format)

    @classmethod
    def date_dt(cls, dt: object = None) -> object:
        """
        日付をdatetimeオブジェクトとして取得
        """
        dt = dt or timezone.localdate()
        return dt

    @classmethod
    def time_str(cls, dt: object = None) -> str:
        """
        時刻を文字列として取得
        """
        dt = dt or timezone.localtime().time()
        return dt.strftime(cls.time_format)

    @classmethod
    def time_dt(cls, dt: object = None) -> object:
        """
        時刻をdatetimeオブジェクトとして取得
        """
        dt = dt or timezone.localtime().time()
        return dt

    @classmethod
    def datetime_str(cls, dt: object = None) -> str:
        """
        日付と時刻を文字列として取得
        """
        return f"{cls.date_str(dt)} {cls.time_str(dt)}"

    @classmethod
    def datetime_dt(cls, dt: object = None) -> object:
        """
        日付と時刻をdatetimeオブジェクトとして取得
        """
        dt = dt or timezone.localtime()
        return dt
