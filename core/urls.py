from django.urls import path

from .views import (AddCoupon, CheckoutView, HomeView, ItemByCategory,
                    ItemDetailView, OrderDetailView, OrderSummaryView,
                    PaymentView, RequestRefundView, Search, UserProfileView,
                    add_to_cart, remove_from_cart,
                    remove_single_item_from_cart)

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("products/<slug>/", ItemDetailView.as_view(), name="product"),
    path("add-to-cart/<slug>/", add_to_cart, name="add-to-cart"),
    path("remove-from-cart/<slug>/", remove_from_cart,
         name="remove-from-cart"),
    path("remove_single_item_from_cart/<slug>/", remove_single_item_from_cart,
         name="remove_single_item_from_cart",
         ),
    path("order-summary/", OrderSummaryView.as_view(), name="order-summary"),
    path("payment/<payment_option>/", PaymentView.as_view(), name="payment"),
    path("add-coupon/", AddCoupon.as_view(), name="add-coupon"),
    path("request-refund/", RequestRefundView.as_view(),
         name="request-refund"),
    path("category/<slug:slug>/", ItemByCategory.as_view(), name="category"),
    path("search/", Search.as_view(), name="search"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("order-detail/<slug:ref_code>/", OrderDetailView.as_view(),
         name="order-detail"
         ),
]
