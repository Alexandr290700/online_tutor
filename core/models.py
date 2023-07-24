from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from .managers import *
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import RegexValidator
from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string


phone_validator = RegexValidator(
    regex=r"^\+996 \d{3} \d{3} \d{3}$",
    message="Номер телефона только в формате: +996 xxx xxx xxx",
)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        (TUTOR, "Репетитор"),
        (STUDENT, "Студент"),
        (ADMIN, "Админ"),
    )

    username = None
    first_name = models.CharField(_("first name"), max_length=100, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), unique=True)
    user_type = models.CharField(
        "Тип пользователя", max_length=20, choices=ROLE_CHOICES
    )

    is_superuser = models.BooleanField(
        _("superuser status"),
        default=False,
        help_text="Указывает, следует ли рассматривать этого пользователя как суперпользователя.",
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_(
            "Designates whether the user can log into this admin site."
        ),
    )
    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    created = models.DateTimeField("Дата создания", auto_now_add=True)
    updated = models.DateTimeField("Дата обновлении", auto_now=True)

    activation_code = models.CharField(max_length=17, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
    ]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """
        Возвращает first_name плюс last_name с пробелом между ними.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def create_activation_code(self):
        code = get_random_string(
            length=17,
            allowed_chars="qwertyuiopasdfghjklzxcvbnmQWERTYUIOPSDFGHJKLZXCVBNM1234567890",
        )
        self.activation_code = code

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}


class UserProfileBase(models.Model):
    user = models.OneToOneField(to=CustomUser, on_delete=models.CASCADE)
    profile_picture = models.ImageField(
        upload_to="profile_pics/", blank=True, null=True
    )
    education = models.CharField("Образование", max_length=150)
    social_media = models.URLField(blank=True)

    class Meta:
        abstract = True



class Specialist(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    age = models.PositiveIntegerField(verbose_name="Возраст")
    phone = models.CharField(
        max_length=100,
        validators=[phone_validator],
        verbose_name="Номер телефона",
    )
    email = models.EmailField(verbose_name="Email")
    services = models.TextField(verbose_name="Услуги")
    rating = models.FloatField(default=0, verbose_name="Рейтинг")
    education = models.TextField(verbose_name="Образование")
    consultation_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Стоимость почасовой консультации",
    )
    instagram = models.TextField(blank=True)

    class Meta:
        verbose_name = "Репетитор"
        verbose_name_plural = "Репетиторы"
        ordering = ["first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    phone = models.CharField(
        max_length=100,
        validators=[phone_validator],
        verbose_name="Номер телефона",
    )
    email = models.EmailField(verbose_name="Email")

    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"
        ordering = ["first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ServiceCardIndividual(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    image = models.ImageField(upload_to="service_card", verbose_name="Картинка")
    description = models.TextField(verbose_name="Описание")
    specialist = models.ForeignKey(
        Specialist, on_delete=models.CASCADE, verbose_name="Репетитор"
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Цена"
    )
    completed = models.BooleanField(default=False, verbose_name="Завершен")
    completed_by = models.ForeignKey(
        Specialist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="completed_card_individual",
        verbose_name="Завершено репетитором",
    )

    class Meta:
        verbose_name = "Индивидуальное занятие"
        verbose_name_plural = "Индивидуальные занятия"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ReviewIndividual(models.Model):
    service_card = models.ForeignKey(
        ServiceCardIndividual,
        on_delete=models.CASCADE,
        verbose_name="Карточка товара",
    )
    rating = models.FloatField()
    completed_by = models.ForeignKey(
        Student, on_delete=models.CASCADE, verbose_name="Прошедший курс"
    )

    def __str__(self):
        return f"Отзыв для {self.service_card} от {self.completed_by}"


@receiver(post_save, sender=ReviewIndividual)
def update_individual_specialist_rating(sender, instance, created, **kwargs):
    if created:
        service_card = instance.service_card
        specialist = service_card.specialist
        rating = ReviewIndividual.objects.filter(
            service_card__specialist=specialist
        ).aggregate(Avg("rating"))["rating__avg"]
        specialist.rating = min(rating, 5)
        specialist.save()
    else:
        service_card = instance.service_card
        specialist = service_card.specialist
        rating = (
            ReviewIndividual.objects.filter(service_card__specialist=specialist)
            .exclude(id=instance.id)
            .aggregate(Avg("rating"))["rating__avg"]
        )
        specialist.rating = min(rating, 5)
        specialist.save()


class ServiceCardGroup(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    image = models.ImageField(upload_to="service_card", verbose_name="Картинка")
    date = models.DateTimeField(verbose_name="Дата")
    description = models.TextField(verbose_name="Описание")
    specialist = models.ForeignKey(
        Specialist, on_delete=models.CASCADE, verbose_name="Репетитор"
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2, verbose_name="Цена"
    )
    completed = models.BooleanField(default=False, verbose_name="Завершен")
    completed_by = models.ForeignKey(
        Specialist,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="completed_card_group",
        verbose_name="Завершено репетитором",
    )

    class Meta:
        verbose_name = "Групповое занятие"
        verbose_name_plural = "Групповые занятия"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ReviewGroup(models.Model):
    service_card_group = models.ForeignKey(
        ServiceCardGroup,
        on_delete=models.CASCADE,
        verbose_name="Карточка товара",
    )
    rating = models.FloatField()
    completed_by = models.ForeignKey(
        Student, on_delete=models.CASCADE, verbose_name="Прошедший курс"
    )

    def __str__(self):
        return f"Отзыв для {self.service_card} от {self.completed_by}"


@receiver(post_save, sender=ReviewGroup)
def update_group_specialist_rating(sender, instance, created, **kwargs):
    if created:
        service_card = instance.service_card_group
        specialist = service_card.specialist
        rating = ReviewGroup.objects.filter(
            service_card_group__specialist=specialist
        ).aggregate(Avg("rating"))["rating__avg"]
        specialist.rating = min(rating, 5)
        specialist.save()
    else:
        service_card = instance.service_card_group
        specialist = service_card.specialist
        rating = (
            ReviewGroup.objects.filter(
                service_card_group__specialist=specialist
            )
            .exclude(id=instance.id)
            .aggregate(Avg("rating"))["rating__avg"]
        )
        specialist.rating = min(rating, 5)
        specialist.save()
