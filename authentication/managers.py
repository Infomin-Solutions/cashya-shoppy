from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password, **extra_fields):
        """
        Creates and saves a User with the given phone_number, date of
        birth and password.
        """
        if not phone_number:
            raise ValueError('Users must have an email address')

        user = self.model(
            phone_number=phone_number,
            **extra_fields
        )

        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            phone_number,
            password=password,
            **extra_fields
        )
