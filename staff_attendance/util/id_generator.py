from django.utils.crypto import get_random_string


class IDGenerator:
    """
    IDを生成するユーティリティクラス
    """

    ID_LENGTH: int = 6
    ALLOWED_CHARS: str = "0123456789"

    @classmethod
    def create_id(cls) -> str:
        return get_random_string(cls.ID_LENGTH, allowed_chars=cls.ALLOWED_CHARS)
