import django_filters
from rest_framework import viewsets, filters, status
from .models import (
    Specialist,
    Student,
    ServiceCardIndividual,
    ServiceCardGroup,
    ReviewIndividual,
    ReviewGroup,
    CustomUser
)
from .serializers import (
    SpecialistSerializer,
    StudentSerializer,
    ServiceCardIndividualSerializer,
    ServiceCardGroupSerializer,
    ReviewIndividualSerializer,
    ReviewGroupSerializer,
    RegisterCustomUserSerializers,
    LoginUserSerializer,
)
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .tasks import send_activation_code


class RegisterView(APIView):
    serializer_class = RegisterCustomUserSerializers

    @swagger_auto_schema(
        request_body=RegisterCustomUserSerializers,
        operation_summary="Регистрация пользователя",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        email = serializer.data.get("email")

        if CustomUser.objects.filter(email=email).exists():
            user = CustomUser.objects.get(email=email)
            current_site = get_current_site(request=request).domain
            relative_link = reverse(
                "activate-email",
                kwargs={"activation_code": user.activation_code},
            )
            absolute_link = "http://" + current_site + relative_link
            send_activation_code.delay(absolute_link, user.email)
        return Response(
            {
                "success": "Вы успешно зарегистрировались",
                "message": "Вам отправлено электронное письмо для активации аккаунта.",
            },
            status=status.HTTP_201_CREATED,
        )


@swagger_auto_schema(
    method="GET",
    operation_summary="Запрос для активации аккаунта",
)
@api_view(["GET"])
def activate_view(request, activation_code):
    user = get_object_or_404(CustomUser, activation_code=activation_code)
    user.is_active = True  # делаем активым
    user.activation_code = ""  # удаляем активационный код
    user.save()
    return redirect("login")


class LoginAPIView(APIView):
    serializer_class = LoginUserSerializer

    @swagger_auto_schema(
        request_body=LoginUserSerializer,
        operation_summary="Авторизация пользователя",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Выход пользователя из системы.",
    )
    def get(self, request):
        try:
            request.user.auth_token.delete()
            return Response(
                {"detail": "User successfully logged out."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )




class SpecialistViewSet(viewsets.ModelViewSet):
    queryset = Specialist.objects.all()
    serializer_class = SpecialistSerializer
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend,
    )

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     if serializer.is_valid():
    #         user = User.objects.create_user(
    #             username=request.data["username"],
    #             password=request.data["password"],
    #             email=request.data["email"],
    #         )
    #         serializer.save(user=user)
    #         return Response({"success": "Регистрация прошла успешно!"})
    #     else:
    #         return Response(serializer.errors, status=400)


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend,
    )

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     if serializer.is_valid():
    #         user = User.objects.create_user(
    #             username=request.data["username"],
    #             password=request.data["password"],
    #             email=request.data["email"],
    #         )
    #         serializer.save(user=user)
    #         return Response({"success": "Регистрация прошла успешно!"})
    #     else:
    #         return Response(serializer.errors, status=400)


class ServiceCardIndividualViewSet(viewsets.ModelViewSet):
    queryset = ServiceCardIndividual.objects.all()
    serializer_class = ServiceCardIndividualSerializer
    filter_backends = (
        filters.OrderingFilter,
        filters.SearchFilter,
        django_filters.rest_framework.DjangoFilterBackend,
    )
    ordering_fields = (
        "rating",
        "price",
    )

    @action(detail=True, methods=["POST"])
    def mark_completed(self, request, pk=None):
        try:
            card = ServiceCardIndividual.objects.get(pk=pk)
        except ServiceCardIndividual.DoesNotExist:
            return Response({"message": "Такого курса нет"})

        # Проверяем является ли юзер репетитором
        if card.specialist.user == request.user:
            card.completed = True
            card.completed_by = card.specialist
            card.save()
            return Response({"message": "Курс отмечен как завершенный."})
        else:
            return Response(
                {"message": "Вы не являетесь репетитором для данной карточки"},
                status=status.HTTP_403_FORBIDDEN,
            )

    @action(detail=True, methods=["POST"])
    def create_review(self, request, pk=None):
        service_card = ServiceCardIndividual.objects.get(pk=pk)

        if service_card.completed:
            # Если курс завершен можно оставлять отзыв
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Если курс не завершен, отзывы оставлять нельзя
            return Response(
                {"message": "Нельзя оставлять отзыв до окончания курса!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_queryset(self):
        queryset = super().get_queryset()
        min_rating = self.request.query_params.get("min_rating")
        max_price = self.request.query_params.get("max_price")

        if min_rating:
            queryset = queryset.filter(specialist__rating__gte=min_rating)

        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset


class ServiceCardGroupViewSet(viewsets.ModelViewSet):
    queryset = ServiceCardGroup.objects.all()
    serializer_class = ServiceCardGroupSerializer
    filter_backends = (
        filters.OrderingFilter,
        filters.SearchFilter,
        django_filters.rest_framework.DjangoFilterBackend,
    )
    ordering_fields = (
        "rating",
        "price",
    )

    @action(detail=True, methods=["POST"])
    def mark_completed(self, request, pk=None):
        try:
            card = ServiceCardGroup.objects.get(pk=pk)
        except ServiceCardGroup.DoesNotExist:
            return Response({"message": "Такого курса нет"})

        # Проверяем является ли юзер репетитором
        if card.specialist.user == request.user:
            card.completed = True
            card.completed_by = card.specialist
            card.save()
            return Response({"message": "Курс отмечен как завершенный."})
        else:
            return Response(
                {"message": "Вы не являетесь репетитором для данной карточки"},
                status=status.HTTP_403_FORBIDDEN,
            )

    @action(detail=True, methods=["POST"])
    def create_review(self, request, pk=None):
        service_card = ServiceCardGroup.objects.get(pk=pk)

        if service_card.completed:
            # Если курс завершен можно оставлять отзыв
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Если курс не завершен, отзывы оставлять нельзя
            return Response(
                {"message": "Нельзя оставлять отзыв до окончания курса!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_queryset(self):
        queryset = super().get_queryset()
        min_rating = self.request.query_params.get("min_rating")
        max_price = self.request.query_params.get("max_price")

        if min_rating:
            queryset = queryset.filter(specialist__rating__gte=min_rating)

        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        return queryset


class ReviewIndividualViewSet(viewsets.ModelViewSet):
    queryset = ReviewIndividual.objects.all()
    serializer_class = ReviewIndividualSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()

        # Проверяем является ли ученик оставляющий отзыв, учеником который прошел курс
        student = serializer.validated_data["completed_by"]
        service_card = serializer.validated_data["service_card"]
        if not service_card.specialist.student_set.filter(
            id=student.id
        ).exist():
            return Response(
                {
                    "detail": "Вы не можете оставлять отзыв для этого курса, так как не проходили соотвутствующий курс"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ReviewGroupViewSet(viewsets.ModelViewSet):
    queryset = ReviewGroup.objects.all()
    serializer_class = ReviewGroupSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()

        # Проверяем является ли ученик оставляющий отзыв, учеником который прошел курс
        student = serializer.validated_data["completed_by"]
        service_card = serializer.validated_data["service_card"]
        if not service_card.specialist.student_set.filter(
            id=student.id
        ).exist():
            return Response(
                {
                    "detail": "Вы не можете оставлять отзыв для этого курса, так как не проходили соотвутствующий курс"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )
