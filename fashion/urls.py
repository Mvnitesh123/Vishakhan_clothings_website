from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('top-rated/', views.top_rated, name='top_rated'),
    path('high-discount/', views.high_discount, name='high_discount'),
    path('product/review/', views.submit_review, name='submit_review'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('categories/', views.category_directory, name='category_directory'),
    path('subcategory/<slug:slug>/', views.subcategory_detail, name='subcategory_detail'),
    path('products/', views.product_list, name='product_list'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/get/', views.get_cart, name='get_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/', views.update_cart_quantity, name='update_cart_quantity'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/get/', views.get_wishlist, name='get_wishlist'),
    path('product/review/delete/', views.delete_review, name='delete_review'),
    path('profile/', views.profile_view, name='profile'),
]