from django.contrib.auth.models import PermissionsMixin, AbstractBaseUser, BaseUserManager
from django.db import models
from django.apps import apps
from django.contrib import auth
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import UnicodeUsernameValidator
import uuid


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError("The given username must be set")
        email = self.normalize_email(email)
        GlobalUserModel = apps.get_model(self.model._meta.app_label, self.model._meta.object_name)
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_admin", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        if not username:
            raise ValueError("Superuser must have a username.")

        if email is None:
            email = username

        return self._create_user(username, email, password, **extra_fields)

    def with_perm(self, perm, is_active=True, include_superusers=True, backend=None, obj=None):
        if backend is None:
            backends = auth._get_backends(return_tuples=True)
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                raise ValueError(
                    "You have multiple authentication backends configured and "
                    "therefore must provide the `backend` argument."
                )
        elif not isinstance(backend, str):
            raise TypeError("backend must be a dotted import path string (got %r)." % backend)
        else:
            backend = auth.load_backend(backend)

        if hasattr(backend, "with_perm"):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()


class User(AbstractBaseUser, PermissionsMixin):
    username_validator = UnicodeUsernameValidator()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(unique=True, max_length=255)
    full_name = models.CharField(_("Name of User"), blank=True, max_length=255)
    country_code = models.CharField(max_length=10, null=True, blank=True, default="91")
    phone = models.CharField(max_length=30, null=True, blank=True)
    phone_verified = models.BooleanField(default=False)
    email = models.EmailField(_("email address"), blank=True)
    email_verified = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into this admin site.",
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    
    # Role-based permissions
    can_manage_enquiries = models.BooleanField(
        default=False,
        help_text="User can create, update, and delete enquiries (Flight, General, Destination enquiries)."
    )
    can_manage_administration = models.BooleanField(
        default=False,
        help_text="User can manage all resources (Hotels, Packages, Houseboats, Cruises, Island Stays, Destinations, Offer Banners)."
    )

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        swappable = "AUTH_USER_MODEL"

    def __str__(self):
        return str(self.get_username())

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auto_id = models.PositiveIntegerField(unique=True, db_index=True, editable=False)
    is_active = models.BooleanField(default=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.auto_id:
            max_id = self.__class__.objects.aggregate(models.Max("auto_id"))["auto_id__max"]
            self.auto_id = (max_id or 0) + 1
        super().save(*args, **kwargs)


class Hotel(BaseModel):
    STAR_RATING_CHOICES = [
        (1, "1 Star"),
        (2, "2 Stars"),
        (3, "3 Stars"),
        (4, "4 Stars"),
        (5, "5 Stars"),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    location = models.CharField(max_length=255)
    description = models.TextField()
    rating = models.IntegerField(choices=STAR_RATING_CHOICES, default=5)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="hotels/", null=True, blank=True)
    gallery_image_1 = models.ImageField(upload_to="hotels/gallery/", null=True, blank=True)
    gallery_image_2 = models.ImageField(upload_to="hotels/gallery/", null=True, blank=True)
    gallery_image_3 = models.ImageField(upload_to="hotels/gallery/", null=True, blank=True)
    gallery_image_4 = models.ImageField(upload_to="hotels/gallery/", null=True, blank=True)
    gallery_image_5 = models.ImageField(upload_to="hotels/gallery/", null=True, blank=True)
    has_wifi = models.BooleanField(default=False)
    has_pool = models.BooleanField(default=False)
    has_spa = models.BooleanField(default=False)
    has_restaurant = models.BooleanField(default=False)
    has_beach_access = models.BooleanField(default=False)
    has_parking = models.BooleanField(default=False)
    has_ski_access = models.BooleanField(default=False)
    amenities = models.TextField(help_text="Comma-separated amenities", blank=True)
    youtube_link = models.URLField(max_length=500, blank=True, null=True, help_text="YouTube video link")
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    is_international = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_added"]
        verbose_name = "Hotel/Resort"
        verbose_name_plural = "Hotels/Resorts"

    def __str__(self):
        return self.name

class Destination(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    is_international = models.BooleanField(default=False)
    
    class Meta:
        ordering = ["-date_added"]
        verbose_name = "Destination"
        verbose_name_plural = "Destinations"

    def __str__(self):
        return self.name

class Category(BaseModel):
    """Package Category Model"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Package(BaseModel):
    TYPE_CHOICES = [
        ("international", "International"),
        ("kerala", "Kerala"),
    ]

    SEASON_CHOICES = [
        ("all", "All"),
        ("monsoon", "Monsoon"),
        ("winter", "Winter"),
        ("summer", "Summer"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='packages')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='packages', null=True, blank=True)
    location = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.CharField(max_length=100, help_text="e.g., 5 Days / 4 Nights")
    group_size = models.CharField(max_length=100, help_text="e.g., 2-6 Pax")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to="packages/", null=True, blank=True)
    hero_image = models.ImageField(upload_to="packages/hero/", null=True, blank=True)
    gallery_image_1 = models.ImageField(upload_to="packages/gallery/", null=True, blank=True)
    gallery_image_2 = models.ImageField(upload_to="packages/gallery/", null=True, blank=True)
    gallery_image_3 = models.ImageField(upload_to="packages/gallery/", null=True, blank=True)
    gallery_image_4 = models.ImageField(upload_to="packages/gallery/", null=True, blank=True)
    gallery_image_5 = models.ImageField(upload_to="packages/gallery/", null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    reviews_count = models.IntegerField(default=0)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    season = models.CharField(max_length=50, choices=SEASON_CHOICES, default="all", help_text="Best season to visit")
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    is_international = models.BooleanField(default=False)
    is_kerala = models.BooleanField(default=False)
    inclusions = models.TextField(help_text="Comma-separated inclusions", blank=True)
    exclusions = models.TextField(help_text="Comma-separated exclusions", blank=True)
    highlights = models.TextField(help_text="Comma-separated highlights", blank=True)
    youtube_link = models.URLField(max_length=500, blank=True, null=True, help_text="YouTube video link")
    
    # Additional package details
    no_of_days = models.IntegerField(null=True, blank=True, help_text="Number of days")
    no_of_nights = models.IntegerField(null=True, blank=True, help_text="Number of nights")
    pickup_location = models.CharField(max_length=255, null=True, blank=True, help_text="e.g., Airport / Hotel")
    drop_location = models.CharField(max_length=255, null=True, blank=True, help_text="e.g., Airport / Hotel")
    transportation_mode = models.CharField(max_length=255, null=True, blank=True, help_text="e.g., AC Vehicle")
    stay_type = models.CharField(max_length=255, null=True, blank=True, help_text="e.g., 4-Star Resort")
    guide = models.BooleanField(default=False, help_text="Guide included")
    meals_included = models.CharField(max_length=255, null=True, blank=True, help_text="e.g., Breakfast & Dinner")

    class Meta:
        ordering = ["-date_added"]
        verbose_name = "Package"
        verbose_name_plural = "Packages"

    def __str__(self):
        return self.title


class Houseboat(BaseModel):
    TYPE_CHOICES = [
        ("standard", "Standard"),
        ("deluxe", "Deluxe"),
        ("premium", "Premium"),
        ("luxury", "Luxury"),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    capacity = models.CharField(max_length=100, help_text="e.g., 4-6 Guests")
    bedrooms = models.IntegerField()
    route = models.CharField(max_length=255, help_text="e.g., Alleppey - Kumarakom")
    duration = models.CharField(max_length=100, help_text="e.g., 1 Night / 2 Days")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="houseboats/", null=True, blank=True)
    gallery_image_1 = models.ImageField(upload_to="houseboats/gallery/", null=True, blank=True)
    gallery_image_2 = models.ImageField(upload_to="houseboats/gallery/", null=True, blank=True)
    gallery_image_3 = models.ImageField(upload_to="houseboats/gallery/", null=True, blank=True)
    gallery_image_4 = models.ImageField(upload_to="houseboats/gallery/", null=True, blank=True)
    gallery_image_5 = models.ImageField(upload_to="houseboats/gallery/", null=True, blank=True)
    features = models.TextField(help_text="Comma-separated features", blank=True)
    description = models.TextField(blank=True)
    youtube_link = models.URLField(max_length=500, blank=True, null=True, help_text="YouTube video link")
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_added"]
        verbose_name = "Houseboat"
        verbose_name_plural = "Houseboats"

    def __str__(self):
        return self.name


class Cruise(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    cruise_line = models.CharField(max_length=255)
    route = models.CharField(max_length=255, help_text="e.g., Italy - Greece - Turkey")
    duration = models.CharField(max_length=100, help_text="e.g., 7 Nights")
    departures = models.CharField(max_length=255, help_text="e.g., April - October")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="cruises/", null=True, blank=True)
    gallery_image_1 = models.ImageField(upload_to="cruises/gallery/", null=True, blank=True)
    gallery_image_2 = models.ImageField(upload_to="cruises/gallery/", null=True, blank=True)
    gallery_image_3 = models.ImageField(upload_to="cruises/gallery/", null=True, blank=True)
    gallery_image_4 = models.ImageField(upload_to="cruises/gallery/", null=True, blank=True)
    gallery_image_5 = models.ImageField(upload_to="cruises/gallery/", null=True, blank=True)
    highlights = models.TextField(help_text="Comma-separated highlights", blank=True)
    description = models.TextField(blank=True)
    youtube_link = models.URLField(max_length=500, blank=True, null=True, help_text="YouTube video link")
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    is_international = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_added"]
        verbose_name = "Cruise"
        verbose_name_plural = "Cruises"

    def __str__(self):
        return self.name


class IslandStay(BaseModel):
    STAR_RATING_CHOICES = [(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    location = models.CharField(max_length=255)
    rating = models.IntegerField(choices=STAR_RATING_CHOICES, default=5)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=100, help_text="e.g., 4 Nights")
    image = models.ImageField(upload_to="island_stays/", null=True, blank=True)
    gallery_image_1 = models.ImageField(upload_to="island_stays/gallery/", null=True, blank=True)
    gallery_image_2 = models.ImageField(upload_to="island_stays/gallery/", null=True, blank=True)
    gallery_image_3 = models.ImageField(upload_to="island_stays/gallery/", null=True, blank=True)
    gallery_image_4 = models.ImageField(upload_to="island_stays/gallery/", null=True, blank=True)
    gallery_image_5 = models.ImageField(upload_to="island_stays/gallery/", null=True, blank=True)
    features = models.TextField(help_text="Comma-separated features", blank=True)
    description = models.TextField(blank=True)
    youtube_link = models.URLField(max_length=500, blank=True, null=True, help_text="YouTube video link")
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    is_international = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_added"]
        verbose_name = "Island Stay"
        verbose_name_plural = "Island Stays"

    def __str__(self):
        return self.name


class FlightEnquiry(BaseModel):
    TRIP_TYPE_CHOICES = [
        ("roundtrip", "Round Trip"),
        ("oneway", "One Way"),
        ("multicity", "Multi-city"),
    ]

    CLASS_CHOICES = [
        ("economy", "Economy"),
        ("premium", "Premium Economy"),
        ("business", "Business"),
        ("first", "First Class"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("contacted", "Contacted"),
        ("quoted", "Quoted"),
        ("booked", "Booked"),
        ("cancelled", "Cancelled"),
    ]

    trip_type = models.CharField(max_length=20, choices=TRIP_TYPE_CHOICES)
    from_location = models.CharField(max_length=255)
    to_location = models.CharField(max_length=255)
    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    adults = models.IntegerField(default=1)
    children = models.IntegerField(default=0)
    travel_class = models.CharField(max_length=20, choices=CLASS_CHOICES, default="economy")
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    follow_up_notes = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flight_enquiries",
    )

    class Meta:
        ordering = ["-date_added"]
        verbose_name = "Flight Enquiry"
        verbose_name_plural = "Flight Enquiries"

    def __str__(self):
        return f"{self.name} - {self.from_location} to {self.to_location}"


class Enquiry(BaseModel):
    SERVICE_CHOICES = [
        ("flights", "Flights"),
        ("hotels", "Hotels & Resorts"),
        ("packages-kerala", "Kerala Tourism Packages"),
        ("packages-international", "International Packages"),
        ("houseboats", "Houseboats"),
        ("cruises", "Cruises"),
        ("island-stays", "Island Stays"),
        ("adventure", "Adventure Activities"),
        ("bus", "Bus Services"),
        ("insurance", "Travel Insurance"),
        ("forex", "Forex Services"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("contacted", "Contacted"),
        ("quoted", "Quoted"),
        ("converted", "Converted"),
        ("cancelled", "Cancelled"),
    ]

    # Basic fields
    model_uuid = models.UUIDField(null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    service = models.CharField(max_length=50, choices=SERVICE_CHOICES, null=True, blank=True)
    destination = models.CharField(max_length=255, null=True, blank=True)
    travel_date = models.DateField(null=True, blank=True)
    travelers = models.CharField(max_length=50, null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    follow_up_notes = models.TextField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enquiries",
    )

    # Hotel-specific fields
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    rooms = models.CharField(max_length=50, null=True, blank=True)
    guests = models.CharField(max_length=50, null=True, blank=True)

    # Island Stay-specific fields
    island_duration = models.CharField(max_length=100, null=True, blank=True)

    # Houseboat-specific fields
    houseboat_duration = models.CharField(max_length=100, null=True, blank=True)
    bedrooms = models.CharField(max_length=50, null=True, blank=True)
    boarding_date = models.DateField(null=True, blank=True)

    # Cruise-specific fields
    preferred_departure_date = models.DateField(null=True, blank=True)
    cruise_duration = models.CharField(max_length=100, null=True, blank=True)
    passengers = models.CharField(max_length=50, null=True, blank=True)
    cabin_type = models.CharField(max_length=100, null=True, blank=True)

    # Additional fields
    general = models.BooleanField(default=False)
    tell_about_trip = models.TextField(null=True, blank=True)
    
    # Flight-specific fields
    ending_date = models.DateField(null=True, blank=True)
    flight_ticket_required = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        ordering = ["-date_added"]
        verbose_name = "Enquiry"
        verbose_name_plural = "Enquiries"

    def __str__(self):
        return f"{self.name} - {self.service}"


class DestinationEnquiry(BaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("contacted", "Contacted"),
        ("quoted", "Quoted"),
        ("booked", "Booked"),
        ("cancelled", "Cancelled"),
    ]

    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name="enquiries",
    )
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_pax = models.IntegerField(default=1)
    flight_ticket_required = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    follow_up_notes = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="destination_enquiries",
    )

    class Meta:
        ordering = ["-date_added"]
        verbose_name = "Destination Enquiry"
        verbose_name_plural = "Destination Enquiries"

    def __str__(self):
        return f"{self.full_name} - {self.destination.name}"


class OfferBanner(BaseModel):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to="offer_banners/")

    class Meta:
        ordering = ["-date_added"]
        verbose_name = "Offer Banner"
        verbose_name_plural = "Offer Banners"

    def __str__(self):
        return self.name
