from django.contrib import admin
from .models import (
    Specialist,
    Student,
    ServiceCardIndividual,
    ServiceCardGroup,
    Account,
)


@admin.register(Account)
class AccountRegisterAdmin(admin.ModelAdmin):
    list_display = ("get_full_name", "email", "user_type", "created", "updated")
    search_fields = (
        "get_full_name",
        "email",
    )
    list_filter = ("user_type",)


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "first_name",
        "last_name",
        "age",
        "phone",
        "email",
        "services",
        "rating",
        "education",
        "consultation_price",
        "instagram",
    )
    list_display_links = (
        "user",
        "first_name",
        "last_name",
        "age",
        "phone",
        "email",
        "services",
        "rating",
        "education",
        "consultation_price",
    )
    list_filter = (
        "id",
        "first_name",
        "last_name",
        "age",
    )
    search_fields = (
        "id",
        "first_name",
        "last_name",
        "age",
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "first_name",
        "last_name",
        "phone",
        "email",
    )
    list_display_links = (
        "user",
        "first_name",
        "last_name",
        "phone",
        "email",
    )
    list_filter = (
        "id",
        "first_name",
        "last_name",
    )
    search_fields = (
        "id",
        "first_name",
        "last_name",
    )


@admin.register(ServiceCardIndividual)
class ServieCardIndividualAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "image",
        "description",
        "specialist",
        "price",
        "completed",
        "completed_by",
    )
    list_display_links = (
        "id",
        "name",
        "image",
        "description",
        "specialist",
        "price",
        "completed",
    )
    list_filter = ("id", "price", "name", "completed")


@admin.register(ServiceCardGroup)
class ServiceCardGroup(admin.ModelAdmin):
    list_display = ("name", "image", "date", "specialist", "price", "completed", "completed_by")
    list_display_links = ("name", "date", "specialist", "price", "completed")
    list_filter = ("id", "name", "date", "price", "completed")
