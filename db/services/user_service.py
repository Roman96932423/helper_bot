from db.repositories import UserRepository

from db.models import User


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
