from django.db.models import Model
from typing import Type, TypeVar


T = TypeVar("T", bound=Model)


class BaseRepository:
    """
    DjangoのModelを操作するための基底クラス
    """

    model = Type[T]

    @classmethod
    def get(cls, **kwargs) -> T:
        return cls.model.objects.get(**kwargs)

    @classmethod
    def get_all(cls) -> list[T]:
        return cls.model.objects.all()

    @classmethod
    def filter(cls, **kwargs) -> list[T]:
        return cls.model.objects.filter(**kwargs)

    @classmethod
    def create(cls, **kwargs) -> T:
        return cls.model.objects.create(**kwargs)
