from util.id_generator import IDGenerator
from .domains import UserDomain
from .repositories import UserRepository, DepartmentRepository

class UserUseCase:
    user_repository = UserRepository()
    department_repository = DepartmentRepository()

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
        user_entry = UserDomain(
            user_id=cls.generate_user_id(),
            username=cleaned_data["username"],
            email=cleaned_data["email"],
            password=cleaned_data["password1"],
            department=cleaned_data["department"],
        )
        cls.user_repository.save(user_entry)
