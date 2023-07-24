from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SpecialistViewSet,
    StudentViewSet,
    ServiceCardIndividualViewSet,
    ServiceCardGroupViewSet,
    LogoutAPIView,
    RegisterView,
    activate_view,
    LoginAPIView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "activate/<str:activation_code>/", activate_view, name="activate-email"
    ),
    path("login/", LoginAPIView.as_view(), name="login"),
    path("logout/", LogoutAPIView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    path(
        "specialist/",
        SpecialistViewSet.as_view({"get": "list", "post": "create"}),
        name="specialist_list_create",
    ),
    path(
        "specialist/<int:pk>/",
        SpecialistViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
        name="specialist_detail",
    ),
    path(
        "student/",
        StudentViewSet.as_view({"get": "list", "post": "create"}),
        name="student_list_create",
    ),
    path(
        "student/<int:pk>/",
        StudentViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
        name="student_detail",
    ),
    path(
        "service_card/",
        ServiceCardIndividualViewSet.as_view({"get": "list", "post": "create"}),
        name="service_card",
    ),
    path(
        "service_card/<int:pk>/",
        ServiceCardIndividualViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
        name="service_card_detail",
    ),
    path(
        "api/service_card_individual/<int:pk>/mark_completed/",
        ServiceCardIndividualViewSet.as_view({"patch": "mark_completed"}),
        name="mark_completed",
    ),
    path(
        "service_card_group/",
        ServiceCardGroupViewSet.as_view({"get": "list", "post": "create"}),
        name="service_card_group",
    ),
    path(
        "service_card_group/<int:pk>/",
        ServiceCardGroupViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
        name="service_card_group_detail",
    ),
    path(
        "api/service_card_group/<int:pk>/mark_completed/",
        ServiceCardGroupViewSet.as_view({"patch": "mark_completed"}),
        name="mark_completed_group",
    ),
]
