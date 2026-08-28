from util.id_generator import IDGenerator
from django.db import IntegrityError, transaction
from .domains import UserDomain
from .repositories import UserRepository, DepartmentRepository

class UserUseCase:
    user_repository = UserRepository()
    department_repository = DepartmentRepository()

    MAX_USER_ID_ATTEMPTS = 5

    @classmethod
    def generate_user_id(cls):
        while True:
            new_id = IDGenerator.create_id()
            if not cls.user_repository.user_id_exists(new_id):
                return new_id

    @classmethod
    def get_all_department_names(cls):
        return cls.department_repository.get_all_departments()

    @classmethod
    def create_user_entry(cls, cleaned_data):
        """
        ユーザーを登録する。
        user_idは主キーであり、事前確認と登録の間に他のリクエストが
        同一のIDを取得しうるため、一意制約違反を検知して再生成する。
        """
        for _ in range(cls.MAX_USER_ID_ATTEMPTS):
            user_entry = UserDomain(
                user_id=cls.generate_user_id(),
                username=cleaned_data["username"],
                email=cleaned_data["email"],
                password=cleaned_data["password1"],
                department=cleaned_data["department"],
            )

            try:
                with transaction.atomic():
                    cls.user_repository.save(user_entry)
                return
            except IntegrityError:
                if not cls.user_repository.user_id_exists(user_entry.user_id):
                    raise

        raise IntegrityError(
            f"Failed to generate a unique user id in {cls.MAX_USER_ID_ATTEMPTS} attempts."
        )
