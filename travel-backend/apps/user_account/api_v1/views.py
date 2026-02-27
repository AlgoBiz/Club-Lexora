from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model, logout, authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.user_account.models import (
    Hotel, Package, Houseboat, Cruise, IslandStay, FlightEnquiry, Enquiry,
    Destination, DestinationEnquiry
)
from apps.user_account.api_v1.serializers import (
    UserSerializer, UserDetailSerializer, ChangePasswordSerializer,
    HotelListSerializer, HotelDetailSerializer, HotelCreateUpdateSerializer,
    PackageListSerializer, PackageDetailSerializer, PackageCreateUpdateSerializer,
    HouseboatListSerializer, HouseboatDetailSerializer, HouseboatCreateUpdateSerializer,
    CruiseListSerializer, CruiseDetailSerializer, CruiseCreateUpdateSerializer,
    IslandStayListSerializer, IslandStayDetailSerializer, IslandStayCreateUpdateSerializer,
    FlightEnquiryListSerializer, FlightEnquiryDetailSerializer,
    FlightEnquiryCreateSerializer, FlightEnquiryUpdateSerializer,
    EnquiryListSerializer, EnquiryDetailSerializer,
    EnquiryCreateSerializer, EnquiryUpdateSerializer,
    DestinationListSerializer, DestinationDetailSerializer, DestinationCreateUpdateSerializer,
    DestinationEnquiryListSerializer, DestinationEnquiryDetailSerializer,
    DestinationEnquiryCreateSerializer, DestinationEnquiryUpdateSerializer,
)

User = get_user_model()


def success_response(message, data=None, status_code=status.HTTP_200_OK):
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status_code)


def error_response(message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    payload = {"message": message}
    if errors:
        payload["errors"] = errors
    return Response(payload, status=status_code)


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    errors = {}
    if not username:
        errors["username"] = ["This field is required."]
    if not password:
        errors["password"] = ["This field is required."]
    if errors:
        return error_response("Username and password are required.", errors)

    user = authenticate(username=username, password=password)

    if user is None:
        return error_response(
            "Invalid credentials.",
            {"non_field_errors": ["Unable to log in with provided credentials."]},
            status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        return error_response(
            "User account is disabled.",
            {"non_field_errors": ["This account has been disabled."]},
            status.HTTP_401_UNAUTHORIZED,
        )

    refresh = RefreshToken.for_user(user)

    return success_response(
        "Login successful.",
        {
            "user": UserDetailSerializer(user).data,
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        },
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token_view(request):
    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return error_response(
            "Refresh token is required.",
            {"refresh": ["This field is required."]},
        )

    try:
        refresh = RefreshToken(refresh_token)
        return success_response(
            "Token refreshed successfully.",
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
        )
    except TokenError as e:
        return error_response(
            "Invalid or expired refresh token.",
            {"refresh": [str(e)]},
            status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_token_view(request):
    return success_response(
        "Token is valid.",
        {"user": UserDetailSerializer(request.user).data},
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    refresh_token = request.data.get("refresh")

    if refresh_token:
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass

    logout(request)
    return success_response("Logged out successfully.")



class BaseModelViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering = ["-date_added"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [AllowAny()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            
            # Transform to custom format with results array
            return Response({
                "message": "Data retrieved successfully.",
                "data": {
                    "results": paginated_response.data.get("results", []),
                    "count": paginated_response.data.get("count", 0),
                    "next": paginated_response.data.get("next"),
                    "previous": paginated_response.data.get("previous"),
                }
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "message": "Data retrieved successfully.",
            "data": {
                "results": serializer.data,
                "count": len(serializer.data),
            }
        })

    def success_response(self, message, data=None, status_code=status.HTTP_200_OK):
        return success_response(message, data, status_code)

    def error_response(self, message, errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        return error_response(message, errors, status_code)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["username", "email", "full_name"]
    ordering = ["-date_joined"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        return UserSerializer

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = UserDetailSerializer(request.user, context={"request": request})
        return success_response("User profile retrieved successfully.", serializer.data)

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return error_response("Old password is incorrect.")

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return success_response("Password changed successfully.")

    @action(detail=False, methods=["post"])
    def logout(self, request):
        logout(request)
        return success_response("Logged out successfully.")


class HotelViewSet(BaseModelViewSet):
    search_fields = ["name", "location", "description"]
    ordering_fields = ["price_per_night", "rating", "date_added"]
    filterset_fields = ["rating", "is_featured", "is_trending", "is_premium", "is_active"]
    # permission_classes = [AllowAny]

    def get_queryset(self):
        return Hotel.objects.only(
            "id", "auto_id", "name", "slug", "location", "rating",
            "price_per_night", "image", "amenities", "is_featured",
            "is_trending", "is_premium", "is_active", "date_added",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return HotelListSerializer
        if self.action == "retrieve":
            return HotelDetailSerializer
        return HotelCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        hotel = serializer.save()
        return self.success_response(
            "Hotel created successfully.",
            HotelDetailSerializer(hotel, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        hotel = serializer.save()
        return self.success_response(
            "Hotel updated successfully.",
            HotelDetailSerializer(hotel, context={"request": request}).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return self.success_response("Hotel deleted successfully.")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        queryset = self.get_queryset().filter(is_featured=True, is_active=True)
        serializer = HotelListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Featured hotels retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        queryset = self.get_queryset().filter(is_trending=True, is_active=True)
        serializer = HotelListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending hotels retrieved successfully.", serializer.data)


class PackageViewSet(BaseModelViewSet):
    search_fields = ["title", "location", "description"]
    ordering_fields = ["price", "rating", "date_added"]
    filterset_fields = [
        "category", "type", "destination", "is_featured", "is_trending",
        "is_premium", "is_international", "is_kerala", "is_active",
    ]

    def get_queryset(self):
       return Package.objects.select_related('destination').only(
            "id", "auto_id", "title", "slug", "destination", "location", "duration",
            "group_size", "price", "original_price", "image", "rating",
            "reviews_count", "category", "type", "is_featured", "is_trending",
            "is_premium", "is_international", "is_kerala", "is_active", "date_added",
        )
        

    def get_serializer_class(self):
        if self.action == "list":
            return PackageListSerializer
        if self.action == "retrieve":
            return PackageDetailSerializer
        return PackageCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        package = serializer.save()
        return self.success_response(
            "Package created successfully.",
            PackageDetailSerializer(package, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        package = serializer.save()
        return self.success_response(
            "Package updated successfully.",
            PackageDetailSerializer(package, context={"request": request}).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return self.success_response("Package deleted successfully.")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        is_international = request.query_params.get("is_international")
        queryset = self.get_queryset().filter(is_featured=True, is_active=True)
        if is_international is not None:
            queryset = queryset.filter(is_international=is_international.lower() == "true")
        serializer = PackageListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Featured packages retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        is_international = request.query_params.get("is_international")
        queryset = self.get_queryset().filter(is_trending=True, is_active=True)
        if is_international is not None:
            queryset = queryset.filter(is_international=is_international.lower() == "true")
        serializer = PackageListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending packages retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def kerala(self, request):
        queryset = self.get_queryset().filter(is_kerala=True, is_active=True)
        serializer = PackageListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Kerala packages retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def international(self, request):
        queryset = self.get_queryset().filter(is_international=True, is_active=True)
        serializer = PackageListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("International packages retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"], url_path="destination/(?P<destination_id>[^/.]+)")
    def by_destination(self, request, destination_id=None):
        queryset = self.get_queryset().filter(destination_id=destination_id, is_active=True)
        serializer = PackageListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Packages by destination retrieved successfully.", serializer.data)

class HouseboatViewSet(BaseModelViewSet):
    search_fields = ["name", "route", "description"]
    ordering_fields = ["price", "bedrooms", "date_added"]
    filterset_fields = ["type", "is_featured", "is_trending", "is_premium", "is_active"]

    def get_queryset(self):
        return Houseboat.objects.only(
            "id", "auto_id", "name", "slug", "type", "capacity", "bedrooms",
            "route", "duration", "price", "image", "features", "is_featured",
            "is_trending", "is_premium", "is_active", "date_added",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return HouseboatListSerializer
        if self.action == "retrieve":
            return HouseboatDetailSerializer
        return HouseboatCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        houseboat = serializer.save()
        return self.success_response(
            "Houseboat created successfully.",
            HouseboatDetailSerializer(houseboat, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        houseboat = serializer.save()
        return self.success_response(
            "Houseboat updated successfully.",
            HouseboatDetailSerializer(houseboat, context={"request": request}).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return self.success_response("Houseboat deleted successfully.")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        queryset = self.get_queryset().filter(is_featured=True, is_active=True)
        serializer = HouseboatListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Featured houseboats retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        queryset = self.get_queryset().filter(is_trending=True, is_active=True)
        serializer = HouseboatListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending houseboats retrieved successfully.", serializer.data)


class CruiseViewSet(BaseModelViewSet):
    search_fields = ["name", "cruise_line", "route", "description"]
    ordering_fields = ["price", "date_added"]
    filterset_fields = ["is_featured", "is_trending", "is_premium", "is_active"]

    def get_queryset(self):
        return Cruise.objects.only(
            "id", "auto_id", "name", "slug", "cruise_line", "route",
            "duration", "departures", "price", "image", "highlights",
            "is_featured", "is_trending", "is_premium", "is_active", "date_added",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return CruiseListSerializer
        if self.action == "retrieve":
            return CruiseDetailSerializer
        return CruiseCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        cruise = serializer.save()
        return self.success_response(
            "Cruise created successfully.",
            CruiseDetailSerializer(cruise, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        cruise = serializer.save()
        return self.success_response(
            "Cruise updated successfully.",
            CruiseDetailSerializer(cruise, context={"request": request}).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return self.success_response("Cruise deleted successfully.")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        queryset = self.get_queryset().filter(is_featured=True, is_active=True)
        serializer = CruiseListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Featured cruises retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        queryset = self.get_queryset().filter(is_trending=True, is_active=True)
        serializer = CruiseListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending cruises retrieved successfully.", serializer.data)


class IslandStayViewSet(BaseModelViewSet):
    search_fields = ["name", "location", "description"]
    ordering_fields = ["price", "rating", "date_added"]
    filterset_fields = ["rating", "is_featured", "is_trending", "is_premium", "is_active"]

    def get_queryset(self):
        return IslandStay.objects.only(
            "id", "auto_id", "name", "slug", "location", "rating",
            "price", "duration", "image", "features", "is_featured",
            "is_trending", "is_premium", "is_active", "date_added",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return IslandStayListSerializer
        if self.action == "retrieve":
            return IslandStayDetailSerializer
        return IslandStayCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        island_stay = serializer.save()
        return self.success_response(
            "Island stay created successfully.",
            IslandStayDetailSerializer(island_stay, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        island_stay = serializer.save()
        return self.success_response(
            "Island stay updated successfully.",
            IslandStayDetailSerializer(island_stay, context={"request": request}).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return self.success_response("Island stay deleted successfully.")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        queryset = self.get_queryset().filter(is_featured=True, is_active=True)
        serializer = IslandStayListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Featured island stays retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        queryset = self.get_queryset().filter(is_trending=True, is_active=True)
        serializer = IslandStayListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending island stays retrieved successfully.", serializer.data)


class FlightEnquiryViewSet(BaseModelViewSet):
    search_fields = ["name", "email", "phone", "from_location", "to_location"]
    ordering_fields = ["departure_date", "date_added"]
    filterset_fields = ["status", "trip_type", "travel_class", "is_active"]

    def get_queryset(self):
        return FlightEnquiry.objects.select_related("assigned_to").only(
            "id", "auto_id", "name", "email", "phone", "from_location",
            "to_location", "departure_date", "return_date", "trip_type",
            "adults", "children", "travel_class", "status", "assigned_to",
            "date_added", "is_active",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return FlightEnquiryListSerializer
        if self.action == "retrieve":
            return FlightEnquiryDetailSerializer
        if self.action in ["update", "partial_update"]:
            return FlightEnquiryUpdateSerializer
        return FlightEnquiryCreateSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        enquiry = serializer.save()
        return self.success_response(
            "Flight enquiry submitted successfully. Our team will contact you within 24 hours.",
            FlightEnquiryDetailSerializer(enquiry, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        enquiry = serializer.save()
        return self.success_response(
            "Flight enquiry updated successfully.",
            FlightEnquiryDetailSerializer(enquiry, context={"request": request}).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return self.success_response("Flight enquiry deleted successfully.")

    @action(detail=False, methods=["get"])
    def pending(self, request):
        queryset = self.get_queryset().filter(status="pending", is_active=True)
        serializer = FlightEnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Pending enquiries retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def by_status(self, request):
        status_param = request.query_params.get("status", "pending")
        queryset = self.get_queryset().filter(status=status_param, is_active=True)
        serializer = FlightEnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response(
            f"{status_param.title()} enquiries retrieved successfully.", serializer.data
        )


class EnquiryViewSet(BaseModelViewSet):
    search_fields = ["name", "email", "phone", "service", "destination"]
    ordering_fields = ["travel_date", "date_added"]
    filterset_fields = ["status", "service", "is_active"]

    def get_queryset(self):
        return Enquiry.objects.select_related("assigned_to").only(
            "id", "auto_id", "name", "email", "phone", "service",
            "destination", "travel_date", "travelers", "status",
            "assigned_to", "date_added", "is_active",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return EnquiryListSerializer
        if self.action == "retrieve":
            return EnquiryDetailSerializer
        if self.action in ["update", "partial_update"]:
            return EnquiryUpdateSerializer
        return EnquiryCreateSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        enquiry = serializer.save()
        return self.success_response(
            "Enquiry submitted successfully. Our team will contact you within 24 hours.",
            EnquiryDetailSerializer(enquiry, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        enquiry = serializer.save()
        return self.success_response(
            "Enquiry updated successfully.",
            EnquiryDetailSerializer(enquiry, context={"request": request}).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return self.success_response("Enquiry deleted successfully.")

    @action(detail=False, methods=["get"])
    def pending(self, request):
        queryset = self.get_queryset().filter(status="pending", is_active=True)
        serializer = EnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Pending enquiries retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def by_status(self, request):
        status_param = request.query_params.get("status", "pending")
        queryset = self.get_queryset().filter(status=status_param, is_active=True)
        serializer = EnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response(
            f"{status_param.title()} enquiries retrieved successfully.", serializer.data
        )

    @action(detail=False, methods=["get"])
    def by_service(self, request):
        service_param = request.query_params.get("service")
        if not service_param:
            return self.error_response("Service parameter is required.")
        queryset = self.get_queryset().filter(service=service_param, is_active=True)
        serializer = EnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response(
            f"Enquiries for {service_param} retrieved successfully.", serializer.data
        )


class DestinationViewSet(BaseModelViewSet):
    search_fields = ["name", "location", "description"]
    ordering_fields = ["name", "date_added"]
    filterset_fields = ["is_international", "is_active"]

    def get_queryset(self):
        return Destination.objects.only(
            "id", "auto_id", "name", "slug", "location", "description",
            "is_international", "is_active", "date_added",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return DestinationListSerializer
        if self.action == "retrieve":
            return DestinationDetailSerializer
        return DestinationCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        destination = serializer.save()
        return self.success_response(
            "Destination created successfully.",
            DestinationDetailSerializer(destination, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        destination = serializer.save()
        return self.success_response(
            "Destination updated successfully.",
            DestinationDetailSerializer(destination, context={"request": request}).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return self.success_response("Destination deleted successfully.")

    @action(detail=False, methods=["get"])
    def international(self, request):
        queryset = self.get_queryset().filter(is_international=True, is_active=True)
        serializer = DestinationListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("International destinations retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def domestic(self, request):
        queryset = self.get_queryset().filter(is_international=False, is_active=True)
        serializer = DestinationListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Domestic destinations retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        queryset = self.get_queryset().filter(is_trending=True, is_active=True)
        serializer = DestinationListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending destinations retrieved successfully.", serializer.data)


class DestinationEnquiryViewSet(BaseModelViewSet):
    search_fields = ["full_name", "email", "phone", "destination__name"]
    ordering_fields = ["start_date", "date_added"]
    filterset_fields = ["status", "destination", "flight_ticket_required", "is_active"]

    def get_queryset(self):
        return DestinationEnquiry.objects.select_related("destination", "assigned_to").only(
            "id", "auto_id", "destination", "full_name", "email", "phone",
            "start_date", "end_date", "number_of_pax", "flight_ticket_required",
            "status", "assigned_to", "date_added", "is_active",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return DestinationEnquiryListSerializer
        if self.action == "retrieve":
            return DestinationEnquiryDetailSerializer
        if self.action in ["update", "partial_update"]:
            return DestinationEnquiryUpdateSerializer
        return DestinationEnquiryCreateSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        enquiry = serializer.save()
        return self.success_response(
            "Destination enquiry submitted successfully. Our team will contact you within 24 hours.",
            DestinationEnquiryDetailSerializer(enquiry, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        enquiry = serializer.save()
        return self.success_response(
            "Destination enquiry updated successfully.",
            DestinationEnquiryDetailSerializer(enquiry, context={"request": request}).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return self.success_response("Destination enquiry deleted successfully.")

    @action(detail=False, methods=["get"])
    def pending(self, request):
        queryset = self.get_queryset().filter(status="pending", is_active=True)
        serializer = DestinationEnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Pending enquiries retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def by_status(self, request):
        status_param = request.query_params.get("status", "pending")
        queryset = self.get_queryset().filter(status=status_param, is_active=True)
        serializer = DestinationEnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response(
            f"{status_param.title()} enquiries retrieved successfully.", serializer.data
        )

    @action(detail=False, methods=["get"])
    def by_destination(self, request):
        destination_id = request.query_params.get("destination_id")
        if not destination_id:
            return self.error_response("Destination ID parameter is required.")
        queryset = self.get_queryset().filter(destination_id=destination_id, is_active=True)
        serializer = DestinationEnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response(
            "Enquiries for destination retrieved successfully.", serializer.data
        )



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_stats_view(request):
    """
    Dashboard API endpoint that provides essential statistics for admin dashboard.
    Returns counts for hotels, packages, flight enquiries, general enquiries, 
    featured hotels, and trending hotels.
    """
    try:
        # Hotels count
        hotels_count = Hotel.objects.filter(is_active=True).count()
        
        # Packages count
        packages_count = Package.objects.filter(is_active=True).count()
        
        # Flight Enquiries count
        flight_enquiries_count = FlightEnquiry.objects.filter(is_active=True).count()
        
        # General Enquiries count
        general_enquiries_count = Enquiry.objects.filter(is_active=True).count()
        
        # Featured Hotels count
        featured_hotels_count = Hotel.objects.filter(is_active=True, is_featured=True).count()
        
        # Trending Hotels count
        trending_hotels_count = Hotel.objects.filter(is_active=True, is_trending=True).count()
        
        # Prepare response data
        data = {
            "hotels_count": hotels_count,
            "packages_count": packages_count,
            "flight_enquiries_count": flight_enquiries_count,
            "general_enquiries_count": general_enquiries_count,
            "featured_hotels_count": featured_hotels_count,
            "trending_hotels_count": trending_hotels_count,
        }
        
        return success_response("Dashboard statistics retrieved successfully.", data)
        
    except Exception as e:
        return error_response(
            "Failed to retrieve dashboard statistics.",
            {"error": str(e)},
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def package_category_list(request):
    """Get list of all package categories"""
    categories = [{"value": choice[0], "label": choice[1]} for choice in Package.CATEGORY_CHOICES]
    return success_response("Package categories retrieved successfully.", categories) 