from django.conf import settings
from django.urls import path
from apps.user_account.api_v1.views import (
    UserViewSet, HotelViewSet, PackageViewSet, HouseboatViewSet,
    CruiseViewSet, IslandStayViewSet, FlightEnquiryViewSet, EnquiryViewSet,
    DestinationViewSet, DestinationEnquiryViewSet, OfferBannerViewSet,
    login_view, refresh_token_view, verify_token_view, logout_view,
    register_user_view, dashboard_stats_view, package_category_list
)


from rest_framework.routers import DefaultRouter, SimpleRouter

                                            


if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register(r"users", UserViewSet, basename="user")
router.register(r"hotels", HotelViewSet, basename="hotel")
router.register(r"packages", PackageViewSet, basename="package")
router.register(r"houseboats", HouseboatViewSet, basename="houseboat")
router.register(r"cruises", CruiseViewSet, basename="cruise")
router.register(r"island-stays", IslandStayViewSet, basename="island-stay")
router.register(r"flight-enquiries", FlightEnquiryViewSet, basename="flight-enquiry")
router.register(r"enquiries", EnquiryViewSet, basename="enquiry")
router.register(r"destinations", DestinationViewSet, basename="destination")
router.register(r"destination-enquiries", DestinationEnquiryViewSet, basename="destination-enquiry")
router.register(r"offer-banners", OfferBannerViewSet, basename="offer-banner")


urlpatterns = [
    # Authentication endpoints
    path('auth/login/', login_view, name='login'),
    path('auth/refresh/', refresh_token_view, name='token_refresh'),
    path('auth/verify/', verify_token_view, name='token_verify'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/register/', register_user_view, name='register'),
    
    # Dashboard endpoint
    path('dashboard/stats/', dashboard_stats_view, name='dashboard_stats'),
    
    # Package categories endpoint
    path('package-categories/', package_category_list, name='package_categories'),
]

app_name = "api_v1"
urlpatterns += router.urls


