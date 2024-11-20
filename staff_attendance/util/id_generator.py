from django.utils.crypto import get_random_string

class IDGenerator:
    @classmethod
    def create_id(cls):
        return get_random_string(6)
