import django_filters
import stripe
from rest_framework import viewsets, filters, status, generics
from .models import (
    Specialist,
    Student,
    ServiceCardIndividual,
    ServiceCardGroup,
    ReviewIndividual,
    ReviewGroup,
    Account,
)
from .serializers import (
    SpecialistSerializer,
    StudentSerializer,
    ServiceCardIndividualSerializer,
    ServiceCardGroupSerializer,
    ReviewIndividualSerializer,
    ReviewGroupSerializer,
    AccountSerializer,
    LoginUserSerializer,
    LogoutUserSerializer,
    PaymentSerializer
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
from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET_KEY


class RegistrationView(APIView):
    serializer_class = AccountSerializer

    @swagger_auto_schema(
        request_body=AccountSerializer,
        operation_summary="Регистрация пользователя",
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        email = serializer.data.get("email")

        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)
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
    method="POST",
    operation_summary="Запрос для активации аккаунта",
)
@api_view(["POST"])
def activate_view(request, activation_code):
    if request.method == "POST":
        user = get_object_or_404(Account, activation_code=activation_code)
        user.is_active = True
        user.activation_code = ""
        user.save()
        return redirect("login")
    else:
        return Response({"detail": "Method not allowed."}, status=405)
    


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


class LogoutAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutUserSerializer

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


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.rest_framework.DjangoFilterBackend,
    )


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
            card.completed_by_id = card.specialist
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
            card.completed_by_id = card.specialist
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
        try:
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
        except KeyError:
            return Response({"error": "Вы не прошли курс"})


class ReviewGroupViewSet(viewsets.ModelViewSet):
    queryset = ReviewGroup.objects.all()
    serializer_class = ReviewGroupSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid()

        # Проверяем является ли ученик оставляющий отзыв, учеником который прошел курс
        student = serializer.validated_data["completed_by"]
        service_card = serializer.validated_data["service_card_group"]
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
    

class PaymentAPIView(APIView):
    serializer_class = PaymentSerializer
    @swagger_auto_schema(
            request_body=PaymentSerializer
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        card_data = serializer.validated_data

        payment_method = card_data['payment_method']

        if payment_method == "credit_card":
            amount=card_data['amount']
            currency=card_data['currency']
            description = card_data['description']
            payment_method = card_data['payment_method']

            try:
                # Создаем платеж с помощью Stripe
                intent = stripe.PaymentIntent.create(
                    amount=amount,
                    currency=currency,
                    description=description,
                    payment_method=payment_method,
                    confirm=True,
                )

                # Проверяем прошел ли платеж
                if intent.status == 'succeeded':
                    return Response({"message": "Платеж успешно совершен."}, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Платеж откланен"}, status=status.HTTP_400_BAD_REQUEST)
            
            except stripe.error.StripeError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Некорректный метод оплаты"}, status=status.HTTP_400_BAD_REQUEST)
