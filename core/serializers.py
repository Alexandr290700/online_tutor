from rest_framework import serializers
from .models import (
    Specialist,
    Student,
    ServiceCardIndividual,
    ServiceCardGroup,
    ReviewIndividual,
    ReviewGroup,
)


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
        source="specialist.user.username", read_only=True
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
        source="specialist.user.username", read_only=True
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
            "service_card",
            "rating",
            "completed_by",
        )
