from django.urls import path

from myauth.views import (
    SignInAPIView,
    SingOutAPIView,
    SignUpAPIView,
    ProfileAPIView,
    AvatarUpdateAPIView,
    ChangePasswordAPIView,
)

from shopapp.views import (
    CategoryAPIView,
    CatalogAPIView,
    BannerListAPIView,
    PopularListAPIView,
    LimitedListAPIView,
    ProductDetailsRetrieveAPIView,
    ProductReviewAPIView,
    TagListAPIView,
    SalesListAPIView,
    BasketItemsAPIView,
    OrdersAPIView,
    OrderRegistrationAPIView,
    PaymentAPIView,
)

urlpatterns = [
    path("sign-in", SignInAPIView.as_view()),
    path("sign-up", SignUpAPIView.as_view()),
    path("sign-out", SingOutAPIView.as_view()),
    path("profile", ProfileAPIView.as_view()),
    path("profile/password", ChangePasswordAPIView.as_view()),
    path("profile/avatar", AvatarUpdateAPIView.as_view()),

    path("categories", CategoryAPIView.as_view()),
    path("catalog", CatalogAPIView.as_view()),
    path('banners', BannerListAPIView.as_view()),
    path('products/popular', PopularListAPIView.as_view()),
    path('products/limited', LimitedListAPIView.as_view()),
    path('product/<int:id>', ProductDetailsRetrieveAPIView.as_view()),
    path('product/<int:id>/reviews', ProductReviewAPIView.as_view()),
    path('tags', TagListAPIView.as_view()),
    path('sales', SalesListAPIView.as_view()),
    path('basket', BasketItemsAPIView.as_view()),

    path('orders', OrdersAPIView.as_view()),
    path('order/<int:order_id>', OrderRegistrationAPIView.as_view()),
    path('payment/<int:order_id>', PaymentAPIView.as_view()),
]
