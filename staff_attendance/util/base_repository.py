from django.db.models import Model
from typing import Type, TypeVar

T = TypeVar("T", bound=Model)

class BaseRepository:
    model = Type[T]

    @classmethod
    def get_all(cls):
        return cls.model.objects.all()

    @classmethod
    def filter(cls, **kwargs):
        return cls.model.objects.filter(**kwargs)
