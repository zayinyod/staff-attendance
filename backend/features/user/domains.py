from dataclasses import dataclass

@dataclass
class UserDomain:
    user_id: str = None
    username: str = None
    email: str = None
    password: str = None
    department: str = None
