from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from apps.user_account.models import (
    User, Hotel, Package, Houseboat, Cruise, IslandStay, FlightEnquiry, Enquiry, OfferBanner
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("full_name", "email", "country_code", "phone")}),
        (_("Verification"), {"fields": ("phone_verified", "email_verified")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active", "is_staff", "is_admin", "is_superuser",
                    "groups", "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )
    list_display = ("username", "email", "full_name", "phone", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined")
    search_fields = ("username", "full_name", "email", "phone")
    ordering = ("-date_joined",)
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = (
        "auto_id", "name", "location", "rating", "price_per_night",
        "is_featured", "is_trending", "is_premium", "is_active", "date_added",
    )
    list_filter = ("rating", "is_featured", "is_trending", "is_premium", "is_active", "date_added")
    search_fields = ("name", "location", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_featured", "is_trending", "is_premium", "is_active")
    readonly_fields = ("id", "auto_id", "date_added", "date_updated")

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "slug", "location", "description", "rating", "price_per_night")
        }),
        ("Images", {
            "fields": (
                "image",
                "gallery_image_1", "gallery_image_2", "gallery_image_3",
                "gallery_image_4", "gallery_image_5",
            )
        }),
        ("Amenities", {
            "fields": (
                "has_wifi", "has_pool", "has_spa", "has_restaurant",
                "has_beach_access", "has_parking", "has_ski_access", "amenities",
            )
        }),
        ("Flags", {
            "fields": ("is_featured", "is_trending", "is_premium", "is_active")
        }),
        ("System Fields", {
            "fields": ("id", "auto_id", "date_added", "date_updated"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        "auto_id", "title", "location", "category", "type", "price",
        "rating", "is_featured", "is_trending", "is_premium", "is_active", "date_added",
    )
    list_filter = (
        "category", "type", "is_featured", "is_trending", "is_premium",
        "is_international", "is_kerala", "is_active", "date_added",
    )
    search_fields = ("title", "location", "description")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_featured", "is_trending", "is_premium", "is_active")
    readonly_fields = ("id", "auto_id", "date_added", "date_updated")

    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "slug", "location", "description", "duration", "group_size")
        }),
        ("Pricing", {
            "fields": ("price", "original_price")
        }),
        ("Images", {
            "fields": (
                "image", "hero_image",
                "gallery_image_1", "gallery_image_2", "gallery_image_3",
                "gallery_image_4", "gallery_image_5",
            )
        }),
        ("Classification", {
            "fields": ("rating", "reviews_count", "category", "type")
        }),
        ("Flags", {
            "fields": (
                "is_featured", "is_trending", "is_premium",
                "is_international", "is_kerala", "is_active",
            )
        }),
        ("Details", {
            "fields": ("inclusions", "exclusions", "highlights")
        }),
        ("System Fields", {
            "fields": ("id", "auto_id", "date_added", "date_updated"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Houseboat)
class HouseboatAdmin(admin.ModelAdmin):
    list_display = (
        "auto_id", "name", "type", "capacity", "bedrooms", "route",
        "price", "is_featured", "is_trending", "is_premium", "is_active", "date_added",
    )
    list_filter = ("type", "is_featured", "is_trending", "is_premium", "is_active", "date_added")
    search_fields = ("name", "route", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_featured", "is_trending", "is_premium", "is_active")
    readonly_fields = ("id", "auto_id", "date_added", "date_updated")

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "slug", "type", "capacity", "bedrooms", "route", "duration", "price", "description")
        }),
        ("Images", {
            "fields": (
                "image",
                "gallery_image_1", "gallery_image_2", "gallery_image_3",
                "gallery_image_4", "gallery_image_5",
            )
        }),
        ("Features", {
            "fields": ("features",)
        }),
        ("Flags", {
            "fields": ("is_featured", "is_trending", "is_premium", "is_active")
        }),
        ("System Fields", {
            "fields": ("id", "auto_id", "date_added", "date_updated"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Cruise)
class CruiseAdmin(admin.ModelAdmin):
    list_display = (
        "auto_id", "name", "cruise_line", "route", "duration",
        "price", "is_featured", "is_trending", "is_premium", "is_active", "date_added",
    )
    list_filter = ("is_featured", "is_trending", "is_premium", "is_active", "date_added")
    search_fields = ("name", "cruise_line", "route", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_featured", "is_trending", "is_premium", "is_active")
    readonly_fields = ("id", "auto_id", "date_added", "date_updated")

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "slug", "cruise_line", "route", "duration", "departures", "price", "description")
        }),
        ("Images", {
            "fields": (
                "image",
                "gallery_image_1", "gallery_image_2", "gallery_image_3",
                "gallery_image_4", "gallery_image_5",
            )
        }),
        ("Details", {
            "fields": ("highlights",)
        }),
        ("Flags", {
            "fields": ("is_featured", "is_trending", "is_premium", "is_active")
        }),
        ("System Fields", {
            "fields": ("id", "auto_id", "date_added", "date_updated"),
            "classes": ("collapse",),
        }),
    )


@admin.register(IslandStay)
class IslandStayAdmin(admin.ModelAdmin):
    list_display = (
        "auto_id", "name", "location", "rating", "price", "duration",
        "is_featured", "is_trending", "is_premium", "is_active", "date_added",
    )
    list_filter = ("rating", "is_featured", "is_trending", "is_premium", "is_active", "date_added")
    search_fields = ("name", "location", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("is_featured", "is_trending", "is_premium", "is_active")
    readonly_fields = ("id", "auto_id", "date_added", "date_updated")

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "slug", "location", "rating", "price", "duration", "description")
        }),
        ("Images", {
            "fields": (
                "image",
                "gallery_image_1", "gallery_image_2", "gallery_image_3",
                "gallery_image_4", "gallery_image_5",
            )
        }),
        ("Features", {
            "fields": ("features",)
        }),
        ("Flags", {
            "fields": ("is_featured", "is_trending", "is_premium", "is_active")
        }),
        ("System Fields", {
            "fields": ("id", "auto_id", "date_added", "date_updated"),
            "classes": ("collapse",),
        }),
    )


@admin.register(FlightEnquiry)
class FlightEnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "auto_id", "name", "email", "phone", "from_location", "to_location",
        "departure_date", "trip_type", "status", "assigned_to", "date_added",
    )
    list_filter = ("status", "trip_type", "travel_class", "is_active", "date_added")
    search_fields = ("name", "email", "phone", "from_location", "to_location")
    list_editable = ("status", "assigned_to")
    readonly_fields = ("id", "auto_id", "date_added", "date_updated")
    date_hierarchy = "departure_date"

    fieldsets = (
        ("Contact Information", {
            "fields": ("name", "email", "phone")
        }),
        ("Trip Details", {
            "fields": (
                "trip_type", "from_location", "to_location", "departure_date",
                "return_date", "adults", "children", "travel_class",
            )
        }),
        ("Status & Follow-up", {
            "fields": ("status", "follow_up_notes", "assigned_to", "is_active")
        }),
        ("System Fields", {
            "fields": ("id", "auto_id", "date_added", "date_updated"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("assigned_to")


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "auto_id", "name", "email", "phone", "service", "destination",
        "travel_date", "status", "assigned_to", "date_added",
    )
    list_filter = ("status", "service", "is_active", "date_added")
    search_fields = ("name", "email", "phone", "service", "destination", "message")
    list_editable = ("status", "assigned_to")
    readonly_fields = ("id", "auto_id", "date_added", "date_updated")
    date_hierarchy = "date_added"

    fieldsets = (
        ("Contact Information", {
            "fields": ("name", "email", "phone")
        }),
        ("Enquiry Details", {
            "fields": ("service", "destination", "travel_date", "travelers", "message")
        }),
        ("Status & Follow-up", {
            "fields": ("status", "follow_up_notes", "assigned_to", "is_active")
        }),
        ("System Fields", {
            "fields": ("id", "auto_id", "date_added", "date_updated"),
            "classes": ("collapse",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("assigned_to")



@admin.register(OfferBanner)
class OfferBannerAdmin(admin.ModelAdmin):
    list_display = ("auto_id", "name", "image", "date_added")
    search_fields = ("name",)
    readonly_fields = ("id", "auto_id", "date_added", "date_updated")
    
    fieldsets = (
        ("Banner Information", {
            "fields": ("name", "image")
        }),
        ("System Fields", {
            "fields": ("id", "auto_id", "date_added", "date_updated"),
            "classes": ("collapse",),
        }),
    )
