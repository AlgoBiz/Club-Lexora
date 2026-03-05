from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.user_account.models import (
    Hotel, Package, Houseboat, Cruise, IslandStay, FlightEnquiry, Enquiry,
    Destination, DestinationEnquiry, OfferBanner
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "full_name", "country_code", "phone", "is_active", 
            "can_manage_enquiries", "can_manage_administration", "date_joined"
        ]
        read_only_fields = ["id", "date_joined"]
    
    def validate_country_code(self, value):
        """
        Validate country code - can be any length, allows any characters
        """
        if value is not None and value != "":
            # Convert to string and strip whitespace
            value = str(value).strip()
            # Allow any non-empty value
            if not value:
                return None
        return value


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "full_name", "country_code", "phone",
            "phone_verified", "email_verified", "is_active", "can_manage_enquiries",
            "can_manage_administration", "is_admin", "is_superuser", "date_joined",
        ]
        read_only_fields = ["id", "date_joined", "phone_verified", "email_verified"]
    
    def validate_country_code(self, value):
        """
        Validate country code - can be any length, allows any characters
        """
        if value is not None and value != "":
            # Convert to string and strip whitespace
            value = str(value).strip()
            # Allow any non-empty value
            if not value:
                return None
        return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            "username", "email", "full_name", "phone", "country_code",
            "password", "confirm_password", "can_manage_enquiries", 
            "can_manage_administration"
        ]
    
    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data
    
    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_country_code(self, value):
        """
        Validate country code - can be any length, allows any characters
        """
        if value is not None and value != "":
            # Convert to string and strip whitespace
            value = str(value).strip()
            # Allow any non-empty value
            if not value:
                return None
        return value
    
    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdatePermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["can_manage_enquiries", "can_manage_administration", "is_active"]


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
            "price_per_night", "image_url", "amenities_list", "youtube_link",
            "is_featured", "is_trending", "is_premium", "is_active", "is_international",
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

    def validate_name(self, value):
        # Check for duplicate name (case-insensitive)
        queryset = Hotel.objects.filter(name__iexact=value)
        # Exclude current instance during update
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A hotel with this name already exists.")
        return value

    def validate_price_per_night(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def update(self, instance, validated_data):
        """
        Custom update method to handle existing_gallery_image_X fields.
        """
        request = self.context.get('request')
        
        if request:
            # Collect existing gallery images from request data
            existing_images = {}
            for i in range(1, 6):
                field_name = f'existing_gallery_image_{i}'
                if field_name in request.data:
                    existing_url = request.data[field_name]
                    for j in range(1, 6):
                        gallery_field = f'gallery_image_{j}'
                        current_image = getattr(instance, gallery_field)
                        if current_image and current_image.url in existing_url:
                            existing_images[i] = current_image
                            break
            
            # Clear all gallery images first
            for i in range(1, 6):
                field_name = f'gallery_image_{i}'
                old_image = getattr(instance, field_name)
                if old_image and i not in existing_images:
                    is_kept = False
                    for kept_image in existing_images.values():
                        if old_image.name == kept_image.name:
                            is_kept = True
                            break
                    if not is_kept:
                        old_image.delete(save=False)
                
                setattr(instance, field_name, None)
            
            # Reassign existing images to sequential positions
            for idx, (position, image) in enumerate(sorted(existing_images.items()), start=1):
                field_name = f'gallery_image_{idx}'
                setattr(instance, field_name, image)
            
            # Handle new gallery image uploads
            next_position = len(existing_images) + 1
            for i in range(1, 6):
                field_name = f'gallery_image_{i}'
                if field_name in validated_data:
                    new_image = validated_data.pop(field_name)
                    if new_image and next_position <= 5:
                        setattr(instance, f'gallery_image_{next_position}', new_image)
                        next_position += 1
        
        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class PackageListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    destination_name = serializers.CharField(source='destination.name', read_only=True)

    class Meta:
        model = Package
        fields = [
            "id", "auto_id", "title", "slug", "destination", "destination_name",
            "location", "duration", "group_size", "price", "original_price",
            "discount_percentage", "image_url", "rating", "reviews_count",
            "category", "type", "season", "youtube_link", "is_featured", "is_trending", "is_premium",
            "is_international", "is_kerala", 
            "no_of_days", "no_of_nights", "pickup_location", "drop_location",
            "transportation_mode", "stay_type", "guide", "meals_included",
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
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    destination_location = serializers.CharField(source='destination.location', read_only=True)

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

    def validate_title(self, value):
        # Check for duplicate title (case-insensitive)
        queryset = Package.objects.filter(title__iexact=value)
        # Exclude current instance during update
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A package with this title already exists.")
        return value

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

    def update(self, instance, validated_data):
        """
        Custom update method to handle existing_gallery_image_X fields.
        The frontend sends existing images as existing_gallery_image_1, existing_gallery_image_2, etc.
        We need to:
        1. Clear all gallery images
        2. Reassign only the existing images that were sent
        3. Handle new gallery image uploads
        """
        request = self.context.get('request')
        
        if request:
            # Collect existing gallery images from request data
            existing_images = {}
            for i in range(1, 6):
                field_name = f'existing_gallery_image_{i}'
                if field_name in request.data:
                    # Extract the image number from the URL (e.g., gallery_image_3)
                    existing_url = request.data[field_name]
                    # Parse which gallery_image field this corresponds to
                    for j in range(1, 6):
                        gallery_field = f'gallery_image_{j}'
                        current_image = getattr(instance, gallery_field)
                        if current_image and current_image.url in existing_url:
                            existing_images[i] = current_image
                            break
            
            # Clear all gallery images first
            for i in range(1, 6):
                field_name = f'gallery_image_{i}'
                # Delete old image file if it's not in existing_images
                old_image = getattr(instance, field_name)
                if old_image and i not in existing_images:
                    # Check if this image is being kept
                    is_kept = False
                    for kept_image in existing_images.values():
                        if old_image.name == kept_image.name:
                            is_kept = True
                            break
                    if not is_kept:
                        old_image.delete(save=False)
                
                setattr(instance, field_name, None)
            
            # Reassign existing images to sequential positions
            for idx, (position, image) in enumerate(sorted(existing_images.items()), start=1):
                field_name = f'gallery_image_{idx}'
                setattr(instance, field_name, image)
            
            # Handle new gallery image uploads
            next_position = len(existing_images) + 1
            for i in range(1, 6):
                field_name = f'gallery_image_{i}'
                if field_name in validated_data:
                    new_image = validated_data.pop(field_name)
                    if new_image and next_position <= 5:
                        setattr(instance, f'gallery_image_{next_position}', new_image)
                        next_position += 1
        
        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class HouseboatListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    features_list = serializers.SerializerMethodField()

    class Meta:
        model = Houseboat
        fields = [
            "id", "auto_id", "name", "slug", "type", "capacity", "bedrooms",
            "route", "duration", "price", "image_url", "features_list",
            "youtube_link", "is_featured", "is_trending", "is_premium", "is_active",
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

    def validate_name(self, value):
        # Check for duplicate name (case-insensitive)
        queryset = Houseboat.objects.filter(name__iexact=value)
        # Exclude current instance during update
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A houseboat with this name already exists.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_bedrooms(self, value):
        if value < 1:
            raise serializers.ValidationError("Bedrooms must be at least 1.")
        return value

    def update(self, instance, validated_data):
        """
        Custom update method to handle gallery images.
        Supports two formats:
        1. New format: existing_gallery_images (JSON array) + deleted_gallery_images (JSON array)
        2. Legacy format: existing_gallery_image_1, existing_gallery_image_2, etc.
        """
        request = self.context.get('request')
        
        if request:
            import json
            
            # Check for new format: existing_gallery_images JSON field
            existing_gallery_images_json = request.data.get('existing_gallery_images')
            deleted_gallery_images_json = request.data.get('deleted_gallery_images')
            
            if existing_gallery_images_json:
                # New format: Parse JSON array of existing images
                try:
                    if isinstance(existing_gallery_images_json, str):
                        existing_urls = json.loads(existing_gallery_images_json)
                    else:
                        existing_urls = existing_gallery_images_json
                    
                    # Parse deleted images
                    deleted_urls = []
                    if deleted_gallery_images_json:
                        if isinstance(deleted_gallery_images_json, str):
                            deleted_urls = json.loads(deleted_gallery_images_json)
                        else:
                            deleted_urls = deleted_gallery_images_json
                    
                    # Collect existing images that should be kept
                    kept_images = []
                    for i in range(1, 6):
                        gallery_field = f'gallery_image_{i}'
                        current_image = getattr(instance, gallery_field)
                        if current_image:
                            image_url = current_image.url
                            # Keep if in existing_urls and not in deleted_urls
                            if any(url in image_url for url in existing_urls) and not any(url in image_url for url in deleted_urls):
                                kept_images.append(current_image)
                            else:
                                # Delete images that are not kept
                                current_image.delete(save=False)
                    
                    # Clear all gallery image fields
                    for i in range(1, 6):
                        setattr(instance, f'gallery_image_{i}', None)
                    
                    # Reassign kept images to sequential positions
                    for idx, image in enumerate(kept_images, start=1):
                        if idx <= 5:
                            setattr(instance, f'gallery_image_{idx}', image)
                    
                    # Add new gallery images after existing ones
                    next_position = len(kept_images) + 1
                    for i in range(1, 6):
                        field_name = f'gallery_image_{i}'
                        if field_name in validated_data:
                            new_image = validated_data.pop(field_name)
                            if new_image and next_position <= 5:
                                setattr(instance, f'gallery_image_{next_position}', new_image)
                                next_position += 1
                
                except (json.JSONDecodeError, TypeError) as e:
                    # If JSON parsing fails, fall back to legacy format
                    pass
            
            else:
                # Legacy format: existing_gallery_image_1, existing_gallery_image_2, etc.
                existing_images = {}
                for i in range(1, 6):
                    field_name = f'existing_gallery_image_{i}'
                    if field_name in request.data:
                        existing_url = request.data[field_name]
                        for j in range(1, 6):
                            gallery_field = f'gallery_image_{j}'
                            current_image = getattr(instance, gallery_field)
                            if current_image and current_image.url in existing_url:
                                existing_images[i] = current_image
                                break
                
                # Only process gallery images if existing_gallery_image fields are present
                has_existing_gallery_fields = any(
                    f'existing_gallery_image_{i}' in request.data for i in range(1, 6)
                )
                
                if has_existing_gallery_fields:
                    # Clear all gallery images first
                    for i in range(1, 6):
                        field_name = f'gallery_image_{i}'
                        old_image = getattr(instance, field_name)
                        if old_image and i not in existing_images:
                            is_kept = False
                            for kept_image in existing_images.values():
                                if old_image.name == kept_image.name:
                                    is_kept = True
                                    break
                            if not is_kept:
                                old_image.delete(save=False)
                        
                        setattr(instance, field_name, None)
                    
                    # Reassign existing images to sequential positions
                    for idx, (position, image) in enumerate(sorted(existing_images.items()), start=1):
                        field_name = f'gallery_image_{idx}'
                        setattr(instance, field_name, image)
                    
                    # Handle new gallery image uploads
                    next_position = len(existing_images) + 1
                    for i in range(1, 6):
                        field_name = f'gallery_image_{i}'
                        if field_name in validated_data:
                            new_image = validated_data.pop(field_name)
                            if new_image and next_position <= 5:
                                setattr(instance, f'gallery_image_{next_position}', new_image)
                                next_position += 1
                else:
                    # If no existing_gallery_image fields, only update if new images are provided
                    for i in range(1, 6):
                        field_name = f'gallery_image_{i}'
                        if field_name in validated_data:
                            new_image = validated_data.pop(field_name)
                            if new_image:
                                # Delete old image if exists
                                old_image = getattr(instance, field_name)
                                if old_image:
                                    old_image.delete(save=False)
                                setattr(instance, field_name, new_image)
        
        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance



class CruiseListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    highlights_list = serializers.SerializerMethodField()

    class Meta:
        model = Cruise
        fields = [
            "id", "auto_id", "name", "slug", "cruise_line", "route",
            "duration", "departures", "price", "image_url", "highlights_list",
            "youtube_link", "is_featured", "is_trending", "is_premium", "is_active", "is_international",
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

    def validate_name(self, value):
        # Check for duplicate name (case-insensitive)
        queryset = Cruise.objects.filter(name__iexact=value)
        # Exclude current instance during update
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A cruise with this name already exists.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def update(self, instance, validated_data):
        """
        Custom update method to handle existing_gallery_image_X fields.
        """
        request = self.context.get('request')
        
        if request:
            # Collect existing gallery images from request data
            existing_images = {}
            for i in range(1, 6):
                field_name = f'existing_gallery_image_{i}'
                if field_name in request.data:
                    existing_url = request.data[field_name]
                    for j in range(1, 6):
                        gallery_field = f'gallery_image_{j}'
                        current_image = getattr(instance, gallery_field)
                        if current_image and current_image.url in existing_url:
                            existing_images[i] = current_image
                            break
            
            # Clear all gallery images first
            for i in range(1, 6):
                field_name = f'gallery_image_{i}'
                old_image = getattr(instance, field_name)
                if old_image and i not in existing_images:
                    is_kept = False
                    for kept_image in existing_images.values():
                        if old_image.name == kept_image.name:
                            is_kept = True
                            break
                    if not is_kept:
                        old_image.delete(save=False)
                
                setattr(instance, field_name, None)
            
            # Reassign existing images to sequential positions
            for idx, (position, image) in enumerate(sorted(existing_images.items()), start=1):
                field_name = f'gallery_image_{idx}'
                setattr(instance, field_name, image)
            
            # Handle new gallery image uploads
            next_position = len(existing_images) + 1
            for i in range(1, 6):
                field_name = f'gallery_image_{i}'
                if field_name in validated_data:
                    new_image = validated_data.pop(field_name)
                    if new_image and next_position <= 5:
                        setattr(instance, f'gallery_image_{next_position}', new_image)
                        next_position += 1
        
        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class IslandStayListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    features_list = serializers.SerializerMethodField()

    class Meta:
        model = IslandStay
        fields = [
            "id", "auto_id", "name", "slug", "location", "rating",
            "price", "duration", "image_url", "features_list",
            "youtube_link", "is_featured", "is_trending", "is_premium", "is_active", "is_international",
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

    def validate_name(self, value):
        # Check for duplicate name (case-insensitive)
        queryset = IslandStay.objects.filter(name__iexact=value)
        # Exclude current instance during update
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("An island stay with this name already exists.")
        return value

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def update(self, instance, validated_data):
        """
        Custom update method to handle existing_gallery_image_X fields.
        """
        request = self.context.get('request')
        
        if request:
            # Collect existing gallery images from request data
            existing_images = {}
            for i in range(1, 6):
                field_name = f'existing_gallery_image_{i}'
                if field_name in request.data:
                    existing_url = request.data[field_name]
                    for j in range(1, 6):
                        gallery_field = f'gallery_image_{j}'
                        current_image = getattr(instance, gallery_field)
                        if current_image and current_image.url in existing_url:
                            existing_images[i] = current_image
                            break
            
            # Clear all gallery images first
            for i in range(1, 6):
                field_name = f'gallery_image_{i}'
                old_image = getattr(instance, field_name)
                if old_image and i not in existing_images:
                    is_kept = False
                    for kept_image in existing_images.values():
                        if old_image.name == kept_image.name:
                            is_kept = True
                            break
                    if not is_kept:
                        old_image.delete(save=False)
                
                setattr(instance, field_name, None)
            
            # Reassign existing images to sequential positions
            for idx, (position, image) in enumerate(sorted(existing_images.items()), start=1):
                field_name = f'gallery_image_{idx}'
                setattr(instance, field_name, image)
            
            # Handle new gallery image uploads
            next_position = len(existing_images) + 1
            for i in range(1, 6):
                field_name = f'gallery_image_{i}'
                if field_name in validated_data:
                    new_image = validated_data.pop(field_name)
                    if new_image and next_position <= 5:
                        setattr(instance, f'gallery_image_{next_position}', new_image)
                        next_position += 1
        
        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


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
            "assigned_to_name", "date_added", "is_active", "general", "tell_about_trip",
            "message", "follow_up_notes",
            # Hotel fields
            "check_in_date", "check_out_date", "rooms", "guests",
            # Island Stay fields
            "island_duration",
            # Houseboat fields
            "houseboat_duration", "bedrooms", "boarding_date",
            # Cruise fields
            "preferred_departure_date", "cruise_duration", "passengers", "cabin_type",
            # Flight fields
            "ending_date", "flight_ticket_required",
        ]


class EnquiryDetailSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source="assigned_to.full_name", read_only=True)

    class Meta:
        model = Enquiry
        fields = "__all__"


class EnquiryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = [
            "model_uuid", "name", "email", "phone", "service", "destination", "travel_date", 
            "travelers", "message", "general", "tell_about_trip",
            # Hotel fields
            "check_in_date", "check_out_date", "rooms", "guests",
            # Island Stay fields
            "island_duration",
            # Houseboat fields
            "houseboat_duration", "bedrooms", "boarding_date",
            # Cruise fields
            "preferred_departure_date", "cruise_duration", "passengers", "cabin_type",
            # Flight fields
            "ending_date", "flight_ticket_required",
        ]
        extra_kwargs = {
            "model_uuid": {"required": False},
            "name": {"required": False},
            "email": {"required": False},
            "phone": {"required": False},
            "service": {"required": False},
            "destination": {"required": False},
            "travel_date": {"required": False},
            "travelers": {"required": False},
            "message": {"required": False},
        }


class EnquiryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = [
            "status", "follow_up_notes", "assigned_to", "general", "tell_about_trip",
            # All enquiry fields for update
            "name", "email", "phone", "service", "destination", "travel_date", 
            "travelers", "message",
            # Hotel fields
            "check_in_date", "check_out_date", "rooms", "guests",
            # Island Stay fields
            "island_duration",
            # Houseboat fields
            "houseboat_duration", "bedrooms", "boarding_date",
            # Cruise fields
            "preferred_departure_date", "cruise_duration", "passengers", "cabin_type",
            # Flight fields
            "ending_date", "flight_ticket_required",
        ]


class DestinationListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = [
            "id", "auto_id", "name", "slug", "location", "description",
            "is_international", "is_active",
        ]


class DestinationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = "__all__"


class DestinationCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        exclude = ["auto_id", "date_added", "date_updated"]

    def validate_name(self, value):
        # Check for duplicate name (case-insensitive)
        queryset = Destination.objects.filter(name__iexact=value)
        # Exclude current instance during update
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A destination with this name already exists.")
        return value


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



class OfferBannerSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = OfferBanner
        fields = ["id", "auto_id", "name", "image", "image_url", "date_added"]
        read_only_fields = ["id", "auto_id", "date_added"]

    def validate_name(self, value):
        # Check for duplicate name (case-insensitive)
        queryset = OfferBanner.objects.filter(name__iexact=value)
        # Exclude current instance during update
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("An offer banner with this name already exists.")
        return value

    def get_image_url(self, obj):
        return _build_absolute_uri(self.context.get("request"), obj.image)
