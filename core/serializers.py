from rest_framework import serializers
from .models import (
    Specialist,
    Student,
    ServiceCardIndividual,
    ServiceCardGroup,
    ReviewIndividual,
    ReviewGroup,
    Account,
)
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class AccountSerializer(serializers.ModelSerializer):
    """Регистрация пользователя"""

    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=Account.objects.all())],
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        min_length=8,
        max_length=128,
    )
    password2 = serializers.CharField(
        min_length=8, max_length=128, required=True, write_only=True
    )

    class Meta:
        model = Account
        fields = (
            "first_name",
            "last_name",
            "email",
            "user_type",
            "password",
            "password2",
        )
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, data):
        pass1 = data.get("password")
        pass2 = data.pop("password2")
        if pass1 != pass2:
            raise serializers.ValidationError(
                {"password": "Passwords fields didn't match."}
            )
        return data

    def validate_email(self, email):
        if Account.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                "User with this email already exists"
            )
        return email

    def create(self, validated_data):
        if validated_data["user_type"] == "Репетитор":
            user = Account.objects.create_tutor(**validated_data)
        if validated_data["user_type"] == "Студент":
            user = Account.objects.create_user(**validated_data)
        if validated_data["user_type"] == "Админ":
            user = Account.objects.create_superuser(**validated_data)
        return user


class LoginUserSerializer(serializers.ModelSerializer):
    """Авторизация пользователя"""

    email = serializers.EmailField(max_length=150, required=True)
    password = serializers.CharField(
        max_length=160, min_length=8, write_only=True
    )

    tokens = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ("email", "password", "tokens")

    def get_tokens(self, instance):
        user = Account.objects.get(email=instance["email"])
        return {
            "refresh": user.tokens()["refresh"],
            "access": user.tokens()["access"],
        }
    

    def validate(self, data):
        email = data["email"]
        password = data["password"]
        user = authenticate(email=email, password=password)

        if not user:
            raise AuthenticationFailed("Invalid credentials, try again")
        if not user.is_active:
            raise AuthenticationFailed(
                "Account is not active, please contact your administrator"
            )

        return {"email": user.email, "tokens": user.tokens}

class LogoutUserSerializer(serializers.ModelSerializer):
    detail = serializers.CharField(default="Пользователь успешно вышел из системы.")

    class Meta:
        model = Account
        fields = ['detail']


class SpecialistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialist
        fields = "__all__"


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = "__all__"


class ServiceCardIndividualSerializer(serializers.ModelSerializer):
    specialist_name = serializers.CharField(
        source="specialist.user.last_name", read_only=True
    )
    rating = serializers.FloatField(source="specialist.rating", read_only=True)

    class Meta:
        model = ServiceCardIndividual
        fields = (
            "name",
            "image",
            "description",
            "specialist",
            "specialist_name",
            "price",
            "completed",
            "completed_by",
            "rating",
        )


class ServiceCardGroupSerializer(serializers.ModelSerializer):
    specialist_name = serializers.CharField(
        source="specialist.user.last_name", read_only=True
    )
    rating = serializers.FloatField(source="specialist.rating", read_only=True)

    class Meta:
        model = ServiceCardGroup
        fields = (
            "name",
            "image",
            "date",
            "specialist",
            "specialist_name",
            "rating",
            "price",
            "completed",
            "completed_by",
        )


class ReviewIndividualSerializer(serializers.ModelSerializer):
    completed_by = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), required=True
    )

    class Meta:
        model = ReviewIndividual
        fields = (
            "id",
            "service_card",
            "rating",
            "completed_by",
        )


class ReviewGroupSerializer(serializers.ModelSerializer):
    completed_by = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(), required=True
    )

    class Meta:
        model = ReviewGroup
        fields = (
            "id",
            "service_card_group",
            "rating",
            "completed_by",
        )


class PaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=3)
    description = serializers.CharField(max_length=255)
    payment_method = serializers.ChoiceField(choices=[("credit_card", "Credit Card")])

    class Meta:
        fields = ('amount', 'currency', 'description', 'payment_method', )

    def validate_currency(self, value):
        # Проверка на поддерживаемую валюту
        supported_currencies = ["usd", "eur", "kgs"]
        if value.lower() not in supported_currencies:
            raise serializers.ValidationError("Неподдерживаемая валюта. Допустимы: USD, EUR, KGS")
        return value.lower()
