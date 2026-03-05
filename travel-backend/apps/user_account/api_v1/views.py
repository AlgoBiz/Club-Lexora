from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model, logout, authenticate
from django.http import HttpResponse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from datetime import date
from django.db.models import Count
from django.db.models.functions import TruncMonth


from apps.user_account.models import (
    Hotel, Package, Houseboat, Cruise, IslandStay, FlightEnquiry, Enquiry,
    Destination, DestinationEnquiry, OfferBanner
)
from apps.user_account.api_v1.serializers import (
    UserSerializer, UserDetailSerializer, ChangePasswordSerializer,
    UserRegistrationSerializer, UserUpdatePermissionsSerializer,
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
    OfferBannerSerializer,
)
from apps.user_account.api_v1.permissions import (
    CanManageEnquiries, CanManageAdministration, IsAdminOrHasBothPermissions
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
        # Validate the refresh token
        refresh = RefreshToken(refresh_token)
        
        # Generate new tokens (token rotation for security)
        user_id = refresh.payload.get('user_id')
        user = User.objects.get(id=user_id)
        new_refresh = RefreshToken.for_user(user)
        
        return success_response(
            "Token refreshed successfully.",
            {
                "access": str(new_refresh.access_token),
                "refresh": str(new_refresh),
            },
        )
    except TokenError as e:
        return error_response(
            "Invalid or expired refresh token.",
            {"refresh": [str(e)]},
            status.HTTP_401_UNAUTHORIZED,
        )
    except User.DoesNotExist:
        return error_response(
            "User not found.",
            {"refresh": ["User associated with this token does not exist."]},
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


@api_view(["POST"])
@permission_classes([IsAdminUser])
def register_user_view(request):
    """
    Register a new user with role-based permissions.
    Only admins can create new users.
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return error_response("Validation failed.", serializer.errors)
    
    user = serializer.save()
    return success_response(
        "User registered successfully.",
        UserDetailSerializer(user).data,
        status.HTTP_201_CREATED,
    )



class BaseModelViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering = ["-date_added"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [CanManageAdministration()]
        return [AllowAny()]
    
    def get_queryset(self):
        """
        Authenticated users see all records (active and inactive).
        Unauthenticated users only see active records.
        """
        queryset = super().get_queryset()
        
        # If user is not authenticated, filter to only active records
        if not self.request.user.is_authenticated:
            if hasattr(queryset.model, 'is_active'):
                queryset = queryset.filter(is_active=True)
        
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Check if there are any query parameters (including 'page')
        has_query_params = bool(request.query_params)
        
        # Apply pagination only if there are query parameters
        if has_query_params:
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
        
        # No pagination when there are no query parameters
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

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "update_permissions"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in ["retrieve", "update", "partial_update"]:
            return UserDetailSerializer
        if self.action == "update_permissions":
            return UserUpdatePermissionsSerializer
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

    @action(detail=True, methods=["patch"], permission_classes=[IsAdminUser])
    def update_permissions(self, request, pk=None):
        """
        Update user permissions (can_manage_enquiries, can_manage_administration).
        Only admins can update permissions.
        """
        user = self.get_object()
        serializer = UserUpdatePermissionsSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        
        serializer.save()
        return success_response(
            "User permissions updated successfully.",
            UserDetailSerializer(user).data,
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update user profile (PUT).
        """
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)
        
        user = serializer.save()
        return success_response(
            "User updated successfully.",
            UserDetailSerializer(user, context={"request": request}).data,
        )
    
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update user profile (PATCH).
        """
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class HotelViewSet(BaseModelViewSet):
    search_fields = ["name", "location", "description"]
    ordering_fields = ["price_per_night", "rating", "date_added"]
    filterset_fields = ["rating", "is_featured", "is_trending", "is_premium", "is_active", "is_international"]
    # permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Hotel.objects.all().only(
            "id", "auto_id", "name", "slug", "location", "rating",
            "price_per_night", "image", "amenities", "is_featured",
            "is_trending", "is_premium", "is_active", "is_international", "date_added",
        )
        
        # Filter by active status for unauthenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        # Filter by is_international query parameter
        is_international = self.request.query_params.get('is_international')
        if is_international is not None:
            if is_international.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_international=True)
            elif is_international.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_international=False)
        
        # Location filtering
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Featured filtering
        is_featured = self.request.query_params.get('is_featured')
        if is_featured is not None:
            is_featured_bool = is_featured.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_featured=is_featured_bool)
        
        # Price filtering
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            try:
                queryset = queryset.filter(price_per_night__gte=float(min_price))
            except (ValueError, TypeError):
                pass
        
        if max_price:
            try:
                queryset = queryset.filter(price_per_night__lte=float(max_price))
            except (ValueError, TypeError):
                pass
        
        # Rating filtering
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            try:
                queryset = queryset.filter(rating__gte=float(min_rating))
            except (ValueError, TypeError):
                pass
        
        return queryset

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
        instance.delete()
        return self.success_response("Hotel deleted successfully.")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        queryset = self.get_queryset().filter(is_featured=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        # Filter by is_international if provided
        is_international = request.query_params.get('is_international')
        if is_international is not None:
            if is_international.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_international=True)
            elif is_international.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_international=False)
        
        serializer = HotelListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Featured hotels retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        queryset = self.get_queryset().filter(is_trending=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        # Filter by is_international if provided
        is_international = request.query_params.get('is_international')
        if is_international is not None:
            if is_international.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_international=True)
            elif is_international.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_international=False)
        
        serializer = HotelListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending hotels retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def locations(self, request):
        """Get unique hotel locations"""
        locations = Hotel.objects.filter(
            is_active=True
        ).values_list('location', flat=True).distinct().order_by('location')
        
        # Filter out empty locations
        unique_locations = [loc for loc in locations if loc]
        
        return self.success_response(
            "Hotel locations retrieved successfully.",
            {"locations": unique_locations}
        )


class PackageViewSet(BaseModelViewSet):
    search_fields = ["title", "location", "description"]
    ordering_fields = ["price", "rating", "date_added"]
    filterset_fields = [
        "category", "type", "destination", "season", "is_featured", "is_trending",
        "is_premium", "is_international", "is_kerala", "is_active", "duration",
    ]

    def get_queryset(self):
        from django.db.models import Q
        from django.conf import settings
        
        queryset = Package.objects.all().select_related('destination').only(
            "id", "auto_id", "title", "slug", "destination", "location", "duration",
            "group_size", "price", "original_price", "image", "rating",
            "reviews_count", "category", "type", "season", "is_featured", "is_trending",
            "is_premium", "is_international", "is_kerala", "is_active", "date_added",
        )
        
        # Filter by active status for unauthenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        # Get query parameters
        search_query = self.request.query_params.get('search')
        destination = self.request.query_params.get('destination')
        
        # Destination filtering by UUID or name (priority filter)
        if destination:
            try:
                # Try to parse as UUID
                import uuid
                uuid.UUID(destination)
                queryset = queryset.filter(destination__id=destination)
            except (ValueError, AttributeError):
                # Otherwise filter by destination name (case-insensitive)
                queryset = queryset.filter(destination__name__icontains=destination)
        
        # Fuzzy search implementation (only if search query is provided)
        # If destination is specified, search within that destination
        if search_query:
            # Use case-insensitive contains for fuzzy matching
            # This works across all databases (SQLite, PostgreSQL, MySQL)
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(destination__name__icontains=search_query)
            )
        
        # Price filtering
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except (ValueError, TypeError):
                pass
        
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except (ValueError, TypeError):
                pass
        
        # Season filtering (exclude 'all' season filter)
        season = self.request.query_params.get('season')
        if season and season.lower() != 'all':
            queryset = queryset.filter(season=season.lower())
        
        return queryset
    def get_object(self):
        """
        Retrieve package by slug, UUID (id), or auto_id.
        Supports /packages/{slug}/, /packages/{uuid}/, and /packages/{auto_id}/ endpoints.
        """
        from django.shortcuts import get_object_or_404
        import uuid

        lookup_value = self.kwargs.get(self.lookup_field)

        # Try to parse as UUID first (id field)
        try:
            uuid_obj = uuid.UUID(lookup_value)
            return get_object_or_404(self.get_queryset(), id=uuid_obj)
        except (ValueError, AttributeError):
            pass
        
        # Try to parse as integer (auto_id field)
        try:
            auto_id = int(lookup_value)
            return get_object_or_404(self.get_queryset(), auto_id=auto_id)
        except (ValueError, TypeError):
            pass
        
        # Otherwise treat as slug
        return get_object_or_404(self.get_queryset(), slug=lookup_value)

        

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
        instance.delete()
        return self.success_response("Package deleted successfully.")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        is_international = request.query_params.get("is_international")
        queryset = self.get_queryset().filter(is_featured=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        if is_international is not None:
            queryset = queryset.filter(is_international=is_international.lower() == "true")
        serializer = PackageListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Featured packages retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        is_international = request.query_params.get("is_international")
        queryset = self.get_queryset().filter(is_trending=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        if is_international is not None:
            queryset = queryset.filter(is_international=is_international.lower() == "true")
        serializer = PackageListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending packages retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def kerala(self, request):
        queryset = self.get_queryset().filter(is_kerala=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = PackageListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Kerala packages retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def international(self, request):
        queryset = self.get_queryset().filter(is_international=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = PackageListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("International packages retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"], url_path="destination/(?P<destination_id>[^/.]+)")
    def by_destination(self, request, destination_id=None):
        queryset = self.get_queryset().filter(destination_id=destination_id)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = PackageListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Packages by destination retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def discounted(self, request):
        from django.db.models import F
        
        # Filter packages where original_price > price (discounted packages)
        queryset = self.get_queryset().filter(
            original_price__isnull=False,
            original_price__gt=F('price')
        )
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        serializer = PackageListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Discounted packages retrieved successfully.", serializer.data)

class HouseboatViewSet(BaseModelViewSet):
    search_fields = ["name", "route", "description"]
    ordering_fields = ["price", "bedrooms", "date_added"]
    filterset_fields = ["type", "is_featured", "is_trending", "is_premium", "is_active", "duration"]

    def get_queryset(self):
        queryset = Houseboat.objects.all().only(
            "id", "auto_id", "name", "slug", "type", "capacity", "bedrooms",
            "route", "duration", "price", "image", "features", "is_featured",
            "is_trending", "is_premium", "is_active", "date_added",
        )
        
        # Filter by active status for unauthenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        return queryset

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
        instance.delete()
        return self.success_response("Houseboat deleted successfully.")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        queryset = self.get_queryset().filter(is_featured=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = HouseboatListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Featured houseboats retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        queryset = self.get_queryset().filter(is_trending=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = HouseboatListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending houseboats retrieved successfully.", serializer.data)


class CruiseViewSet(BaseModelViewSet):
    search_fields = ["name", "cruise_line", "route", "description"]
    ordering_fields = ["price", "date_added"]
    filterset_fields = ["is_featured", "is_trending", "is_premium", "is_active", "is_international"]

    def get_queryset(self):
        queryset = Cruise.objects.all().only(
            "id", "auto_id", "name", "slug", "cruise_line", "route",
            "duration", "departures", "price", "image", "highlights",
            "is_featured", "is_trending", "is_premium", "is_active", "is_international", "date_added",
        )
        
        # Filter by active status for unauthenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        # Filter by is_international query parameter
        is_international = self.request.query_params.get('is_international')
        if is_international is not None:
            if is_international.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_international=True)
            elif is_international.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_international=False)
        
        # Filter by duration (integer only)
        duration = self.request.query_params.get('duration')
        if duration:
            try:
                duration_int = int(duration)
                queryset = queryset.filter(duration__icontains=str(duration_int))
            except (ValueError, TypeError):
                pass
        
        return queryset

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
        instance.delete()
        return self.success_response("Cruise deleted successfully.")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        queryset = self.get_queryset().filter(is_featured=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = CruiseListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Featured cruises retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        queryset = self.get_queryset().filter(is_trending=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = CruiseListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending cruises retrieved successfully.", serializer.data)


class IslandStayViewSet(BaseModelViewSet):
    search_fields = ["name", "location", "description"]
    ordering_fields = ["price", "rating", "date_added"]
    filterset_fields = ["rating", "is_featured", "is_trending", "is_premium", "is_active", "is_international"]

    def get_queryset(self):
        queryset = IslandStay.objects.all().only(
            "id", "auto_id", "name", "slug", "location", "rating",
            "price", "duration", "image", "features", "is_featured",
            "is_trending", "is_premium", "is_active", "is_international", "date_added",
        )
        
        # Filter by active status for unauthenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        # Filter by is_international query parameter
        is_international = self.request.query_params.get('is_international')
        if is_international is not None:
            if is_international.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_international=True)
            elif is_international.lower() in ['false', '0', 'no']:
                queryset = queryset.filter(is_international=False)
        
        # Filter by duration (integer only)
        duration = self.request.query_params.get('duration')
        if duration:
            try:
                duration_int = int(duration)
                queryset = queryset.filter(duration__icontains=str(duration_int))
            except (ValueError, TypeError):
                pass
        
        return queryset

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
        instance.delete()
        return self.success_response("Island stay deleted successfully.")

    @action(detail=False, methods=["get"])
    def featured(self, request):
        queryset = self.get_queryset().filter(is_featured=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = IslandStayListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Featured island stays retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        queryset = self.get_queryset().filter(is_trending=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = IslandStayListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending island stays retrieved successfully.", serializer.data)


class FlightEnquiryViewSet(BaseModelViewSet):
    search_fields = ["name", "email", "phone", "from_location", "to_location"]
    ordering_fields = ["departure_date", "date_added"]
    filterset_fields = ["status", "trip_type", "travel_class", "is_active"]

    def get_queryset(self):
        queryset = FlightEnquiry.objects.all().select_related("assigned_to").only(
            "id", "auto_id", "name", "email", "phone", "from_location",
            "to_location", "departure_date", "return_date", "trip_type",
            "adults", "children", "travel_class", "status", "assigned_to",
            "date_added", "is_active",
        )
        
        # Filter by active status for unauthenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        return queryset

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
            return [CanManageEnquiries()]
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
        instance.delete()
        return self.success_response("Flight enquiry deleted successfully.")

    @action(detail=False, methods=["get"])
    def pending(self, request):
        queryset = self.get_queryset().filter(status="pending")
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = FlightEnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Pending enquiries retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def by_status(self, request):
        status_param = request.query_params.get("status", "pending")
        queryset = self.get_queryset().filter(status=status_param)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = FlightEnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response(
            f"{status_param.title()} enquiries retrieved successfully.", serializer.data
        )


class EnquiryViewSet(BaseModelViewSet):
    search_fields = ["name", "email", "phone", "service", "destination"]
    ordering_fields = ["travel_date", "date_added"]
    filterset_fields = ["status", "service", "is_active", "general"]
    ordering = ["-date_added"]  # Most recent first

    def get_queryset(self):
        queryset = Enquiry.objects.all().select_related("assigned_to").order_by("-date_added")
        
        # Filter by active status for unauthenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        # Filter by general parameter
        general = self.request.query_params.get("general")
        if general is not None:
            if general.lower() in ["true", "1"]:
                queryset = queryset.filter(general=True)
            elif general.lower() in ["false", "0"]:
                queryset = queryset.filter(general=False)
        
        # Filter by date range
        from_date = self.request.query_params.get("from_date")
        to_date = self.request.query_params.get("to_date")
        
        if from_date:
            queryset = queryset.filter(travel_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(travel_date__lte=to_date)
        
        return queryset

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
            return [CanManageEnquiries()]
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
        instance.delete()
        return self.success_response("Enquiry deleted successfully.")

    @action(detail=False, methods=["get"])
    def pending(self, request):
        queryset = self.get_queryset().filter(status="pending")
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = EnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Pending enquiries retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def by_status(self, request):
        status_param = request.query_params.get("status", "pending")
        queryset = self.get_queryset().filter(status=status_param)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = EnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response(
            f"{status_param.title()} enquiries retrieved successfully.", serializer.data
        )

    @action(detail=False, methods=["get"])
    def by_service(self, request):
        service_param = request.query_params.get("service")
        if not service_param:
            return self.error_response("Service parameter is required.")
        queryset = self.get_queryset().filter(service=service_param)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = EnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response(
            f"Enquiries for {service_param} retrieved successfully.", serializer.data
        )

    @action(detail=False, methods=["get"], url_path="related-item")
    def related_item(self, request):
        """
        Get the related model item (Hotel, Package, Houseboat, Cruise, IslandStay) for an enquiry.
        
        Query params:
        - enquiry_id: The ID of the enquiry (required)
        
        Returns the detailed view of the related model item if:
        - general = False
        - model_uuid is not null
        - service field maps to a valid model
        """
        enquiry_id = request.query_params.get("enquiry_id")
        if not enquiry_id:
            return self.error_response("Enquiry ID parameter is required.")
        
        try:
            enquiry = Enquiry.objects.get(id=enquiry_id)
        except Enquiry.DoesNotExist:
            return self.error_response("Enquiry not found.", status_code=status.HTTP_404_NOT_FOUND)
        
        # Check if it's a general enquiry
        if enquiry.general:
            return self.error_response("This is a general enquiry with no related item.")
        
        # Check if model_uuid exists
        if not enquiry.model_uuid:
            return self.error_response("No related item found for this enquiry.")
        
        # Map service to model and serializer
        service_model_map = {
            "hotels": (Hotel, HotelDetailSerializer),
            "packages-kerala": (Package, PackageDetailSerializer),
            "packages-international": (Package, PackageDetailSerializer),
            "houseboats": (Houseboat, HouseboatDetailSerializer),
            "cruises": (Cruise, CruiseDetailSerializer),
            "island-stays": (IslandStay, IslandStayDetailSerializer),
        }
        
        if enquiry.service not in service_model_map:
            return self.error_response(
                f"Service '{enquiry.service}' does not have a related model item."
            )
        
        model_class, serializer_class = service_model_map[enquiry.service]
        
        try:
            related_item = model_class.objects.get(id=enquiry.model_uuid)
            serializer = serializer_class(related_item, context={"request": request})
            return self.success_response(
                f"Related {enquiry.service} item retrieved successfully.",
                serializer.data
            )
        except model_class.DoesNotExist:
            return self.error_response(
                f"Related {enquiry.service} item not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def download_excel(self, request):
        """
        Download enquiries as Excel file.
        Defaults to today's data if no date range specified.
        Only includes fields with non-null values.
        
        Query params:
        - from_date: Start date (YYYY-MM-DD)
        - to_date: End date (YYYY-MM-DD)
        - service: Filter by service
        - status: Filter by status
        - general: Filter by general (true/false)
        """
        # Get queryset with filters
        queryset = self.get_queryset()
        
        # Default to today's data if no date range specified
        from_date = request.query_params.get("from_date")
        to_date = request.query_params.get("to_date")
        
        if not from_date and not to_date:
            today = date.today()
            queryset = queryset.filter(date_added__date=today)
            filename_date = today.strftime("%Y-%m-%d")
        else:
            if from_date:
                queryset = queryset.filter(travel_date__gte=from_date)
            if to_date:
                queryset = queryset.filter(travel_date__lte=to_date)
            filename_date = f"{from_date or 'start'}_to_{to_date or 'end'}"
        
        # Apply additional filters
        service = request.query_params.get("service")
        if service:
            queryset = queryset.filter(service=service)
        
        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        general = request.query_params.get("general")
        if general is not None:
            if general.lower() in ["true", "1"]:
                queryset = queryset.filter(general=True)
            elif general.lower() in ["false", "0"]:
                queryset = queryset.filter(general=False)
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Enquiries"
        
        # Define all possible fields with readable headers
        field_mapping = {
            "auto_id": "ID",
            "name": "Name",
            "email": "Email",
            "phone": "Phone",
            "service": "Service",
            "destination": "Destination",
            "travel_date": "Travel Date",
            "travelers": "Travelers",
            "message": "Message",
            "status": "Status",
            "general": "General Enquiry",
            "tell_about_trip": "Trip Details",
            "follow_up_notes": "Follow-up Notes",
            "assigned_to__full_name": "Assigned To",
            # Hotel fields
            "check_in_date": "Check-in Date",
            "check_out_date": "Check-out Date",
            "rooms": "Rooms",
            "guests": "Guests",
            # Island Stay fields
            "island_duration": "Island Duration",
            # Houseboat fields
            "houseboat_duration": "Houseboat Duration",
            "bedrooms": "Bedrooms",
            "boarding_date": "Boarding Date",
            # Cruise fields
            "preferred_departure_date": "Preferred Departure",
            "cruise_duration": "Cruise Duration",
            "passengers": "Passengers",
            "cabin_type": "Cabin Type",
            "date_added": "Date Added",
            "is_active": "Active",
        }
        
        # Get data
        enquiries = list(queryset.values(
            "auto_id", "name", "email", "phone", "service", "destination",
            "travel_date", "travelers", "message", "status", "general",
            "tell_about_trip", "follow_up_notes", "assigned_to__full_name",
            "check_in_date", "check_out_date", "rooms", "guests",
            "island_duration", "houseboat_duration", "bedrooms", "boarding_date",
            "preferred_departure_date", "cruise_duration", "passengers", "cabin_type",
            "date_added", "is_active"
        ))
        
        if not enquiries:
            return self.error_response("No data found for the specified filters.")
        
        # Determine which fields have data (at least one non-null value)
        fields_with_data = []
        for field in field_mapping.keys():
            if any(row.get(field) not in [None, "", []] for row in enquiries):
                fields_with_data.append(field)
        
        # Write headers
        headers = [field_mapping[field] for field in fields_with_data]
        ws.append(headers)
        
        # Style headers
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
        
        # Write data rows
        for enquiry in enquiries:
            row = []
            for field in fields_with_data:
                value = enquiry.get(field)
                
                # Format values
                if value is None:
                    value = ""
                elif isinstance(value, bool):
                    value = "Yes" if value else "No"
                elif isinstance(value, (date, timezone.datetime)):
                    value = value.strftime("%Y-%m-%d")
                
                row.append(value)
            ws.append(row)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Create response
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = f'attachment; filename="enquiries_{filename_date}.xlsx"'
        
        wb.save(response)
        return response


class DestinationViewSet(BaseModelViewSet):
    search_fields = ["name", "location", "description"]
    ordering_fields = ["name", "date_added"]
    filterset_fields = ["is_international", "is_active"]

    def get_queryset(self):
        queryset = Destination.objects.all().only(
            "id", "auto_id", "name", "slug", "location", "description",
            "is_international", "is_active", "date_added",
        )
        
        # Filter by active status for unauthenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        return queryset

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
        instance.delete()
        return self.success_response("Destination deleted successfully.")

    @action(detail=False, methods=["get"])
    def international(self, request):
        queryset = self.get_queryset().filter(is_international=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = DestinationListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("International destinations retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def domestic(self, request):
        queryset = self.get_queryset().filter(is_international=False)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = DestinationListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Domestic destinations retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        queryset = self.get_queryset().filter(is_trending=True)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = DestinationListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Trending destinations retrieved successfully.", serializer.data)


class DestinationEnquiryViewSet(BaseModelViewSet):
    search_fields = ["full_name", "email", "phone", "destination__name"]
    ordering_fields = ["start_date", "date_added"]
    filterset_fields = ["status", "destination", "flight_ticket_required", "is_active"]

    def get_queryset(self):
        queryset = DestinationEnquiry.objects.all().select_related("destination", "assigned_to").only(
            "id", "auto_id", "destination", "full_name", "email", "phone",
            "start_date", "end_date", "number_of_pax", "flight_ticket_required",
            "status", "assigned_to", "date_added", "is_active",
        )
        
        # Filter by active status for unauthenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        return queryset

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
            return [CanManageEnquiries()]
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
        instance.delete()
        return self.success_response("Destination enquiry deleted successfully.")

    @action(detail=False, methods=["get"])
    def pending(self, request):
        queryset = self.get_queryset().filter(status="pending")
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = DestinationEnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response("Pending enquiries retrieved successfully.", serializer.data)

    @action(detail=False, methods=["get"])
    def by_status(self, request):
        status_param = request.query_params.get("status", "pending")
        queryset = self.get_queryset().filter(status=status_param)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        serializer = DestinationEnquiryListSerializer(queryset, many=True, context={"request": request})
        return self.success_response(
            f"{status_param.title()} enquiries retrieved successfully.", serializer.data
        )

    @action(detail=False, methods=["get"])
    def by_destination(self, request):
        destination_id = request.query_params.get("destination_id")
        if not destination_id:
            return self.error_response("Destination ID parameter is required.")
        queryset = self.get_queryset().filter(destination_id=destination_id)
        if not request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
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
    
    Query Parameters:
    - month: Filter enquiries by month number (1-12)
    - year: Filter enquiries by year (e.g., 2026)
    
    Note: Month and year filters only apply to enquiry counts (flight_enquiries_count and general_enquiries_count).
    Other counts (hotels, packages, featured, trending) are not affected by date filters.
    """
    try:
        # Get query parameters
        month_param = request.query_params.get('month')
        year_param = request.query_params.get('year')
        
        # Hotels count (not affected by date filters)
        hotels_count = Hotel.objects.all().count()
        
        # Packages count (not affected by date filters)
        packages_count = Package.objects.all().count()
        
        # Featured Hotels count (not affected by date filters)
        featured_hotels_count = Hotel.objects.filter(is_featured=True).count()
        
        # Trending Hotels count (not affected by date filters)
        trending_hotels_count = Hotel.objects.filter(is_trending=True).count()
        
        # Base querysets for enquiries
        flight_enquiry_queryset = FlightEnquiry.objects.all()
        general_enquiry_queryset = Enquiry.objects.all()
        
        # Apply date filters to enquiries if provided
        if year_param:
            try:
                year = int(year_param)
                flight_enquiry_queryset = flight_enquiry_queryset.filter(date_added__year=year)
                general_enquiry_queryset = general_enquiry_queryset.filter(date_added__year=year)
            except (ValueError, TypeError):
                pass
        
        if month_param:
            try:
                month = int(month_param)
                if 1 <= month <= 12:
                    flight_enquiry_queryset = flight_enquiry_queryset.filter(date_added__month=month)
                    general_enquiry_queryset = general_enquiry_queryset.filter(date_added__month=month)
            except (ValueError, TypeError):
                pass
        
        # Flight Enquiries count (filtered by date)
        flight_enquiries_count = flight_enquiry_queryset.count()
        
        # General Enquiries count (filtered by date)
        general_enquiries_count = general_enquiry_queryset.count()
        
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
@permission_classes([IsAuthenticated])
def dashboard_analytics_view(request):
    """
    Dashboard Analytics API endpoint that provides:
    - Monthly enquiry counts for all months (or filtered by month/year)
    - Top services by enquiry count (in decreasing order)
    - 5 latest recent enquiries
    
    Query Parameters:
    - month: Filter by month number (1-12)
    - year: Filter by year (e.g., 2026)
    """
    try:
        from django.db.models import Q
        from datetime import datetime
        
        # Get query parameters
        month_param = request.query_params.get('month')
        year_param = request.query_params.get('year')
        
        # Base queryset for enquiries
        enquiry_queryset = Enquiry.objects.all()
        
        # Apply date filters if provided
        if year_param:
            try:
                year = int(year_param)
                enquiry_queryset = enquiry_queryset.filter(date_added__year=year)
            except (ValueError, TypeError):
                pass
        
        if month_param:
            try:
                month = int(month_param)
                if 1 <= month <= 12:
                    enquiry_queryset = enquiry_queryset.filter(date_added__month=month)
            except (ValueError, TypeError):
                pass
        
        # 1. Monthly Analytics - Get enquiry counts by month
        monthly_data = (
            enquiry_queryset
            .annotate(month=TruncMonth('date_added'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        # Format monthly data
        monthly_analytics = []
        for item in monthly_data:
            if item['month']:
                monthly_analytics.append({
                    'month': item['month'].strftime('%B %Y'),
                    'year': item['month'].year,
                    'month_number': item['month'].month,
                    'count': item['count']
                })

        # 2. Top Services by Enquiry Count (in decreasing order)
        service_counts = (
            enquiry_queryset
            .values('service')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Format service data with readable names
        service_analytics = []
        service_dict = dict(Enquiry.SERVICE_CHOICES)
        for item in service_counts:
            if item['service']:
                service_analytics.append({
                    'service': item['service'],
                    'service_name': service_dict.get(item['service'], item['service']),
                    'count': item['count']
                })

        # 3. Latest 5 Recent Enquiries (filtered by date if params provided)
        recent_enquiries = (
            enquiry_queryset
            .select_related('assigned_to')
            .order_by('-date_added')[:5]
        )

        recent_enquiries_data = []
        for enquiry in recent_enquiries:
            recent_enquiries_data.append({
                'id': enquiry.id,
                'auto_id': enquiry.auto_id,
                'name': enquiry.name,
                'email': enquiry.email,
                'phone': enquiry.phone,
                'service': enquiry.service,
                'service_name': service_dict.get(enquiry.service, enquiry.service) if enquiry.service else None,
                'destination': enquiry.destination,
                'travel_date': enquiry.travel_date.strftime('%Y-%m-%d') if enquiry.travel_date else None,
                'status': enquiry.status,
                'date_added': enquiry.date_added.strftime('%Y-%m-%d %H:%M:%S'),
                'assigned_to': enquiry.assigned_to.full_name if enquiry.assigned_to else None,
            })

        # 4. Total Enquiry Count (filtered)
        total_enquiries = enquiry_queryset.count()

        # Prepare response data
        data = {
            'total_enquiries': total_enquiries,
            'monthly_analytics': monthly_analytics,
            'top_services': service_analytics,
            'recent_enquiries': recent_enquiries_data,
        }

        return success_response("Dashboard analytics retrieved successfully.", data)

    except Exception as e:
        return error_response(
            "Failed to retrieve dashboard analytics.",
            {"error": str(e)},
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def package_category_list(request):
    """Get list of all package categories"""
    categories = [{"value": choice[0], "label": choice[1]} for choice in Package.CATEGORY_CHOICES]
    return success_response("Package categories retrieved successfully.", categories) 



class OfferBannerViewSet(BaseModelViewSet):
    serializer_class = OfferBannerSerializer
    search_fields = ["name"]
    ordering_fields = ["date_added", "name"]
    
    def get_queryset(self):
        queryset = OfferBanner.objects.all()
        
        # Filter by active status for unauthenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def get_permissions(self):
        """
        GET (list, retrieve) - Allow any
        POST, PUT, PATCH, DELETE - Require authentication
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        banner = serializer.save()
        return self.success_response(
            "Offer banner created successfully.",
            OfferBannerSerializer(banner, context={"request": request}).data,
            status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.error_response("Validation failed.", serializer.errors)
        banner = serializer.save()
        return self.success_response(
            "Offer banner updated successfully.",
            OfferBannerSerializer(banner, context={"request": request}).data,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return self.success_response("Offer banner deleted successfully.")
