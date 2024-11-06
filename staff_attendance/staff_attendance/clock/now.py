from django.utils import timezone

class Now:
    @staticmethod
    def date():
        return timezone.localtime().strftime("%Y-%m-%d")

    @staticmethod
    def time():
        return timezone.localtime().strftime("%H:%M:%S")

    @staticmethod
    def datetime():
        return f"{Now.date()} {Now.time()}"
