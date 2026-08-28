from attendance.models import User, Department
from util.base_repository import BaseRepository
from .domains import UserDomain

class UserRepository(BaseRepository):
    model = User

    @classmethod
    def save(cls, user_entry: UserDomain):
        user = cls.model(
            user_id=user_entry.user_id,
            username=user_entry.username,
            email=user_entry.email,
            department=user_entry.department,
        )
        user.set_password(user_entry.password)
        # user_idは自動採番でない主キーであり、save()は既存行のUPDATEを試みる。
        # 重複時に既存ユーザーを上書きしないよう、INSERTを強制する。
        user.save(force_insert=True)

    @classmethod
    def user_id_exists(cls, user_id):
        return cls.filter(user_id=user_id).exists()

class DepartmentRepository(BaseRepository):
    model = Department

    @classmethod
    def get_all_departments(cls):
        return cls.get_all()
