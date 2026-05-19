from django.utils.crypto import get_random_string


class IDGenerator:
    """
    IDを生成するユーティリティクラス
    """
    @classmethod
    def create_id(cls) -> str:
        return get_random_string(6)
