from django.contrib.auth.base_user import BaseUserManager


TUTOR: str = "Репетитор"
STUDENT: str = "Студент"
ADMIN: str = "Админ"


class MyAccountManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.create_activation_code()
        user.save(self._db)

        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault("user_type", STUDENT)
        return self._create_user(email, password, **extra_fields)

    def create_tutor(self, email, password, **extra_fields):
        extra_fields.setdefault("user_type", TUTOR)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("user_type", ADMIN)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        return self._create_user(email, password, **extra_fields)
