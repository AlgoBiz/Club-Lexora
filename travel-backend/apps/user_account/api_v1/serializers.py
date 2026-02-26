from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.user_account.models import (
    Hotel, Package, Houseboat, Cruise, IslandStay, FlightEnquiry, Enquiry,
    Destination, DestinationEnquiry
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "full_name", "phone", "is_active", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "full_name", "country_code", "phone",
            "phone_verified", "email_verified", "is_active", "date_joined",
        ]
        read_only_fields = ["id", "date_joined", "phone_verified", "email_verified"]


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data


def _build_absolute_uri(request, file_field):
    if file_field and request:
        return request.build_absolute_uri(file_field.url)
    return None


def _parse_comma_separated(value):
    if value:
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _build_gallery_images(obj, request, count):
    images = []
    for i in range(1, count + 1):
        field = getattr(obj, f"gallery_image_{i}", None)
        url = _build_absolute_uri(request, field)
        if url:
            images.append(url)
    return images


class HotelListSerializer(serializers.ModelSerializer):
    amenities_list = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = [
            "id", "auto_id", "name", "slug", "location", "rating",
            "price_per_night", "image_url", "amenities_list",
            "is_featured", "is_trending", "is_premium", "is_active",
        ]

    def get_amenities_list(self, obj):
        return _parse_comma_separated(obj.amenities)

    def get_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image)


class HotelDetailSerializer(serializers.ModelSerializer):
    amenities_list = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    gallery_images = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = "__all__"

    def get_amenities_list(self, obj):
        return _parse_comma_separated(obj.amenities)

    def get_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image)

    def get_gallery_images(self, obj):
        return _build_gallery_images(obj, self.context.get("request"), 5)


class HotelCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        exclude = ["auto_id", "date_added", "date_updated"]

    def validate_price_per_night(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value


class PackageListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = [
            "id", "auto_id", "title", "slug", "location", "duration",
            "group_size", "price", "original_price", "discount_percentage",
            "image_url", "rating", "reviews_count", "category", "type",
            "is_featured", "is_trending", "is_premium", "is_international",
            "is_kerala", "is_active",
        ]

    def get_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image)

    def get_discount_percentage(self, obj):
        if obj.original_price and obj.original_price > obj.price:
            return round(((obj.original_price - obj.price) / obj.original_price) * 100, 0)
        return 0


class PackageDetailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    hero_image_url = serializers.SerializerMethodField()
    gallery_images = serializers.SerializerMethodField()
    inclusions_list = serializers.SerializerMethodField()
    exclusions_list = serializers.SerializerMethodField()
    highlights_list = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = "__all__"

    def get_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image)

    def get_hero_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.hero_image)

    def get_gallery_images(self, obj):
        return _build_gallery_images(obj, self.context.get("request"), 5)

    def get_inclusions_list(self, obj):
        return _parse_comma_separated(obj.inclusions)

    def get_exclusions_list(self, obj):
        return _parse_comma_separated(obj.exclusions)

    def get_highlights_list(self, obj):
        return _parse_comma_separated(obj.highlights)

    def get_discount_percentage(self, obj):
        if obj.original_price and obj.original_price > obj.price:
            return round(((obj.original_price - obj.price) / obj.original_price) * 100, 0)
        return 0


class PackageCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        exclude = ["auto_id", "date_added", "date_updated"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate(self, data):
        original_price = data.get("original_price")
        price = data.get("price")
        if original_price and price and original_price < price:
            raise serializers.ValidationError(
                {"original_price": "Original price cannot be less than current price."}
            )
        return data


class HouseboatListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    features_list = serializers.SerializerMethodField()

    class Meta:
        model = Houseboat
        fields = [
            "id", "auto_id", "name", "slug", "type", "capacity", "bedrooms",
            "route", "duration", "price", "image_url", "features_list",
            "is_featured", "is_trending", "is_premium", "is_active",
        ]

    def get_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image)

    def get_features_list(self, obj):
        return _parse_comma_separated(obj.features)


class HouseboatDetailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    gallery_images = serializers.SerializerMethodField()
    features_list = serializers.SerializerMethodField()

    class Meta:
        model = Houseboat
        fields = "__all__"

    def get_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image)

    def get_gallery_images(self, obj):
        return _build_gallery_images(obj, self.context.get("request"), 5)

    def get_features_list(self, obj):
        return _parse_comma_separated(obj.features)


class HouseboatCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Houseboat
        exclude = ["auto_id", "date_added", "date_updated"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_bedrooms(self, value):
        if value < 1:
            raise serializers.ValidationError("Bedrooms must be at least 1.")
        return value


class CruiseListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    highlights_list = serializers.SerializerMethodField()

    class Meta:
        model = Cruise
        fields = [
            "id", "auto_id", "name", "slug", "cruise_line", "route",
            "duration", "departures", "price", "image_url", "highlights_list",
            "is_featured", "is_trending", "is_premium", "is_active",
        ]

    def get_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image)

    def get_highlights_list(self, obj):
        return _parse_comma_separated(obj.highlights)


class CruiseDetailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    gallery_images = serializers.SerializerMethodField()
    highlights_list = serializers.SerializerMethodField()

    class Meta:
        model = Cruise
        fields = "__all__"

    def get_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image)

    def get_gallery_images(self, obj):
        return _build_gallery_images(obj, self.context.get("request"), 5)

    def get_highlights_list(self, obj):
        return _parse_comma_separated(obj.highlights)


class CruiseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cruise
        exclude = ["auto_id", "date_added", "date_updated"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value


class IslandStayListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    features_list = serializers.SerializerMethodField()

    class Meta:
        model = IslandStay
        fields = [
            "id", "auto_id", "name", "slug", "location", "rating",
            "price", "duration", "image_url", "features_list",
            "is_featured", "is_trending", "is_premium", "is_active",
        ]

    def get_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image)

    def get_features_list(self, obj):
        return _parse_comma_separated(obj.features)


class IslandStayDetailSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    gallery_images = serializers.SerializerMethodField()
    features_list = serializers.SerializerMethodField()

    class Meta:
        model = IslandStay
        fields = "__all__"

    def get_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image)

    def get_gallery_images(self, obj):
        return _build_gallery_images(obj, self.context.get("request"), 5)

    def get_features_list(self, obj):
        return _parse_comma_separated(obj.features)


class IslandStayCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = IslandStay
        exclude = ["auto_id", "date_added", "date_updated"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value


class FlightEnquiryListSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)

    class Meta:
        model = FlightEnquiry
        fields = [
            "id", "auto_id", "name", "email", "phone", "from_location",
            "to_location", "departure_date", "return_date", "trip_type",
            "adults", "children", "travel_class", "status", "assigned_to_name",
            "date_added", "is_active",
        ]


class FlightEnquiryDetailSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)

    class Meta:
        model = FlightEnquiry
        fields = "__all__"


class FlightEnquiryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightEnquiry
        fields = [
            "trip_type", "from_location", "to_location", "departure_date",
            "return_date", "adults", "children", "travel_class", "name",
            "phone", "email",
        ]

    def validate(self, data):
        if data["trip_type"] == "roundtrip" and not data.get("return_date"):
            raise serializers.ValidationError(
                {"return_date": "Return date is required for round trip."}
            )
        if data.get("return_date") and data.get("departure_date"):
            if data["return_date"] < data["departure_date"]:
                raise serializers.ValidationError(
                    {"return_date": "Return date cannot be before departure date."}
                )
        if data["adults"] < 1:
            raise serializers.ValidationError({"adults": "At least one adult is required."})
        return data


class FlightEnquiryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightEnquiry
        fields = ["status", "follow_up_notes", "assigned_to"]


class EnquiryListSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)

    class Meta:
        model = Enquiry
        fields = [
            "id", "auto_id", "name", "email", "phone", "service",
            "destination", "travel_date", "travelers", "status",
            "assigned_to_name", "date_added", "is_active",
        ]


class EnquiryDetailSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)

    class Meta:
        model = Enquiry
        fields = "__all__"


class EnquiryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = ["name", "email", "phone", "service", "destination", "travel_date", "travelers", "message"]

    def validate_message(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        return value


class EnquiryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = ["status", "follow_up_notes", "assigned_to"]


class DestinationListSerializer(serializers.ModelSerializer):
    image_1_url = serializers.SerializerMethodField()
    image_2_url = serializers.SerializerMethodField()
    image_3_url = serializers.SerializerMethodField()
    destinations_list = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = [
            "id", "auto_id", "name", "slug", "location", "number_of_days",
            "number_of_nights", "pickup_location", "drop_location",
            "transportation_mode", "stay_type", "guide", "destinations_list",
            "image_1_url", "image_2_url", "image_3_url", "is_featured",
            "is_trending", "is_active",
        ]

    def get_image_1_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image_1)

    def get_image_2_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image_2)

    def get_image_3_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image_3)

    def get_destinations_list(self, obj):
        return _parse_comma_separated(obj.destinations)


class DestinationDetailSerializer(serializers.ModelSerializer):
    image_1_url = serializers.SerializerMethodField()
    image_2_url = serializers.SerializerMethodField()
    image_3_url = serializers.SerializerMethodField()
    destinations_list = serializers.SerializerMethodField()
    inclusions_list = serializers.SerializerMethodField()
    exclusions_list = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = "__all__"

    def get_image_1_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image_1)

    def get_image_2_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image_2)

    def get_image_3_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image_3)

    def get_destinations_list(self, obj):
        return _parse_comma_separated(obj.destinations)

    def get_inclusions_list(self, obj):
        return _parse_comma_separated(obj.inclusions)

    def get_exclusions_list(self, obj):
        return _parse_comma_separated(obj.exclusions)


class DestinationCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        exclude = ["auto_id", "date_added", "date_updated"]

    def validate_number_of_days(self, value):
        if value < 1:
            raise serializers.ValidationError("Number of days must be at least 1.")
        return value

    def validate_number_of_nights(self, value):
        if value < 0:
            raise serializers.ValidationError("Number of nights cannot be negative.")
        return value

    def validate(self, data):
        number_of_days = data.get("number_of_days")
        number_of_nights = data.get("number_of_nights")
        if number_of_days and number_of_nights:
            if number_of_nights > number_of_days:
                raise serializers.ValidationError(
                    {"number_of_nights": "Number of nights cannot exceed number of days."}
                )
        return data


class DestinationEnquiryListSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)

    class Meta:
        model = DestinationEnquiry
        fields = [
            "id", "auto_id", "destination", "destination_name", "full_name",
            "email", "phone", "start_date", "end_date", "number_of_pax",
            "flight_ticket_required", "status", "assigned_to_name",
            "date_added", "is_active",
        ]


class DestinationEnquiryDetailSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)

    class Meta:
        model = DestinationEnquiry
        fields = "__all__"


class DestinationEnquiryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationEnquiry
        fields = [
            "destination", "full_name", "email", "phone", "start_date",
            "end_date", "number_of_pax", "flight_ticket_required",
        ]

    def validate(self, data):
        if data.get("end_date") and data.get("start_date"):
            if data["end_date"] < data["start_date"]:
                raise serializers.ValidationError(
                    {"end_date": "End date cannot be before start date."}
                )
        if data.get("number_of_pax", 0) < 1:
            raise serializers.ValidationError(
                {"number_of_pax": "At least one passenger is required."}
            )
        return data


class DestinationEnquiryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationEnquiry
        fields = ["status", "follow_up_notes", "assigned_to"]