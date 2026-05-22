from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Core Dashboard / Analytics
    path('', views.DashboardHomeView.as_view(), name='home'),

    # User Management
    path('users/', views.UserListView.as_view(), name='users'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/toggle-active/', views.UserToggleActiveView.as_view(), name='user_toggle_active'),
    path('users/staff/add/', views.StaffCreateView.as_view(), name='staff_create'),
    path('users/staff/<int:pk>/edit/', views.StaffUpdateView.as_view(), name='staff_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),

    # Category & Subcategory Management
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('subcategories/create/', views.SubCategoryCreateView.as_view(), name='subcategory_create'),
    path('subcategories/<int:pk>/update/', views.SubCategoryUpdateView.as_view(), name='subcategory_update'),
    path('subcategories/<int:pk>/delete/', views.SubCategoryDeleteView.as_view(), name='subcategory_delete'),

    # Product & Variant Management
    path('products/', views.ProductListView.as_view(), name='products'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<uuid:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('products/<uuid:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('products/<uuid:product_id>/variants/create/', views.ProductVariantCreateView.as_view(), name='product_variant_create'),
    path('variants/<int:pk>/update/', views.ProductVariantUpdateView.as_view(), name='product_variant_update'),
    path('variants/<int:pk>/delete/', views.ProductVariantDeleteView.as_view(), name='product_variant_delete'),

    # Order Management
    path('orders/', views.OrderListView.as_view(), name='orders'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/update-status/', views.OrderUpdateStatusView.as_view(), name='order_update_status'),
    path('orders/<int:pk>/update-payment/', views.OrderUpdatePaymentView.as_view(), name='order_update_payment'),
]
