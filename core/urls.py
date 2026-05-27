from django.urls import path
from .views import sample_product_list_view, sample_signup_view

urlpatterns = [
    path('products/', sample_product_list_view, name='sample-products'),
    path('signup/', sample_signup_view, name='sample-signup'),
]
