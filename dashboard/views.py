from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q, Avg
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime

from fashion.models import (
    User, Category, SubCategory, Product, ProductVariant, Order, OrderItem, Payment
)
from .forms import (
    ProductForm, ProductVariantForm, CategoryForm, SubCategoryForm, StaffUserForm
)

# =========================================================
# STAFF ACCESS CONTROL MIXIN
# =========================================================

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to restrict access to dashboard to authenticated staff members.
    Redirects non-staff users back to storefront home page with an error toast message.
    """
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)

    def handle_no_permission(self):
        messages.error(self.request, "Access Denied: You do not have permissions to access the seller dashboard.")
        return redirect('/')


# =========================================================
# CORE DASHBOARD / ANALYTICS
# =========================================================

class DashboardHomeView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Total Metrics
        paid_orders = Order.objects.filter(payment_status='PAID')
        total_revenue = paid_orders.aggregate(sum=Sum('total_amount'))['sum'] or 0.00
        total_orders = Order.objects.count()
        total_customers = User.objects.filter(is_staff=False, is_superuser=False).count()
        total_products = Product.objects.count()

        # 2. Recent Orders
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:8]

        # 3. Top Selling Products
        top_variants = OrderItem.objects.values('product_variant__product_id').annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold')[:5]
        
        top_products = []
        for v in top_variants:
            p_id = v['product_variant__product_id']
            if p_id:
                try:
                    product = Product.objects.get(id=p_id)
                    product.total_sold = v['total_sold']
                    top_products.append(product)
                except Product.DoesNotExist:
                    pass

        # 4. Low Stock Products (stock < 5)
        # Prefetch variants to avoid N+1 queries when evaluating the stock property
        all_active_products = Product.objects.filter(is_active=True).prefetch_related('variants')
        low_stock_products = [p for p in all_active_products if p.stock < 5][:8]

        # 5. Category Performance
        category_stats = Category.objects.annotate(
            prod_count=Count('product'),
        ).order_by('-prod_count')[:6]

        # 6. Monthly Sales Chart Data (for current year)
        current_year = timezone.now().year
        monthly_sales_raw = Order.objects.filter(
            payment_status='PAID',
            created_at__year=current_year
        )
        
        # Simple Python-based monthly aggregation to support SQLite / Postgres compatibility cleanly
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        monthly_sales_data = [0.00] * 12
        for order in monthly_sales_raw:
            m_idx = order.created_at.month - 1
            monthly_sales_data[m_idx] += float(order.total_amount)

        # Build chart configurations
        context.update({
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'total_customers': total_customers,
            'total_products': total_products,
            'recent_orders': recent_orders,
            'top_products': top_products,
            'low_stock_products': low_stock_products,
            'category_stats': category_stats,
            'months_labels': months,
            'monthly_sales_data': monthly_sales_data,
            'current_year': current_year,
            'active_tab': 'dashboard',
        })
        return context


# =========================================================
# USER & STAFF MANAGEMENT
# =========================================================

class UserListView(StaffRequiredMixin, ListView):
    model = User
    template_name = 'dashboard/users.html'
    context_object_name = 'users'
    paginate_by = 15

    def get_queryset(self):
        queryset = User.objects.all().order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(username__icontains=q) | 
                Q(email__icontains=q) | 
                Q(first_name__icontains=q) | 
                Q(last_name__icontains=q)
            )
        role = self.request.GET.get('role', '')
        if role == 'staff':
            queryset = queryset.filter(is_staff=True)
        elif role == 'customer':
            queryset = queryset.filter(is_staff=False, is_superuser=False)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['role'] = self.request.GET.get('role', '')
        context['active_tab'] = 'users'
        return context


class UserDetailView(StaffRequiredMixin, DetailView):
    model = User
    template_name = 'dashboard/user_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Orders placed by this user
        context['orders'] = Order.objects.filter(user=self.object).order_by('-created_at')
        context['active_tab'] = 'users'
        return context


class UserToggleActiveView(StaffRequiredMixin, View):
    """AJAX View to toggle User is_active state"""
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            return JsonResponse({'success': False, 'message': 'You cannot deactivate your own account!'}, status=400)
        
        user.is_active = not user.is_active
        user.save()
        return JsonResponse({
            'success': True,
            'is_active': user.is_active,
            'message': f"Account for {user.username} has been {'activated' if user.is_active else 'deactivated'}."
        })


class StaffCreateView(StaffRequiredMixin, CreateView):
    model = User
    form_class = StaffUserForm
    template_name = 'dashboard/staff_form.html'
    success_url = reverse_lazy('dashboard:users')

    def form_valid(self, form):
        form.instance.is_staff = True
        response = super().form_valid(form)
        messages.success(self.request, f"Staff user {self.object.username} created successfully!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add New Staff Member"
        context['active_tab'] = 'users'
        return context


class StaffUpdateView(StaffRequiredMixin, UpdateView):
    model = User
    form_class = StaffUserForm
    template_name = 'dashboard/staff_form.html'
    success_url = reverse_lazy('dashboard:users')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Staff user {self.object.username} updated successfully!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Staff: {self.object.username}"
        context['active_tab'] = 'users'
        return context


class UserDeleteView(StaffRequiredMixin, DeleteView):
    model = User
    success_url = reverse_lazy('dashboard:users')

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect('dashboard:users')
        user.delete()
        messages.success(request, "Account deleted successfully.")
        return redirect(self.success_url)


# =========================================================
# CATEGORY MANAGEMENT
# =========================================================

class CategoryListView(StaffRequiredMixin, TemplateView):
    template_name = 'dashboard/categories.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().prefetch_related('subcategories').order_by('name')
        context['category_form'] = CategoryForm()
        context['subcategory_form'] = SubCategoryForm()
        context['active_tab'] = 'categories'
        return context


class CategoryCreateView(StaffRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy('dashboard:categories')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Category created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, f"Error creating category: {form.errors}")
        return redirect('dashboard:categories')


class CategoryUpdateView(StaffRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy('dashboard:categories')

    def form_valid(self, form):
        messages.success(self.request, "Category updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Failed to update category. Check details.")
        return redirect('dashboard:categories')


class CategoryDeleteView(StaffRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('dashboard:categories')

    def post(self, request, *args, **kwargs):
        category = self.get_object()
        category.delete()
        messages.success(request, "Category deleted successfully.")
        return redirect(self.success_url)


class SubCategoryCreateView(StaffRequiredMixin, CreateView):
    model = SubCategory
    form_class = SubCategoryForm
    success_url = reverse_lazy('dashboard:categories')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Subcategory created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, f"Error creating subcategory: {form.errors}")
        return redirect('dashboard:categories')


class SubCategoryUpdateView(StaffRequiredMixin, UpdateView):
    model = SubCategory
    form_class = SubCategoryForm
    success_url = reverse_lazy('dashboard:categories')

    def form_valid(self, form):
        messages.success(self.request, "Subcategory updated successfully!")
        return super().form_valid(form)


class SubCategoryDeleteView(StaffRequiredMixin, DeleteView):
    model = SubCategory
    success_url = reverse_lazy('dashboard:categories')

    def post(self, request, *args, **kwargs):
        subcat = self.get_object()
        subcat.delete()
        messages.success(request, "Subcategory deleted successfully.")
        return redirect(self.success_url)


# =========================================================
# PRODUCT & VARIANT MANAGEMENT
# =========================================================

class ProductListView(StaffRequiredMixin, ListView):
    model = Product
    template_name = 'dashboard/products.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        queryset = Product.objects.all().select_related('category', 'subcategory').prefetch_related('variants').order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | 
                Q(sku__icontains=q) | 
                Q(category__name__icontains=q)
            )
        cat_id = self.request.GET.get('category', '')
        if cat_id:
            queryset = queryset.filter(category_id=cat_id)
        
        status = self.request.GET.get('status', '')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().order_by('name')
        context['q'] = self.request.GET.get('q', '')
        context['cat_filter'] = self.request.GET.get('category', '')
        context['status'] = self.request.GET.get('status', '')
        context['active_tab'] = 'products'
        return context


class ProductCreateView(StaffRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:products')

    def get_success_url(self):
        from django.urls import reverse
        return reverse('dashboard:product_update', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Product {self.object.name} created successfully!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add New Product"
        context['active_tab'] = 'products'
        return context


class ProductUpdateView(StaffRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:products')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Product {self.object.name} updated successfully!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Product: {self.object.name}"
        context['variants'] = self.object.variants.all()
        context['variant_form'] = ProductVariantForm(product=self.object)
        context['variant_images'] = self.object.variant_images.all()
        context['active_tab'] = 'products'
        return context


class ProductDeleteView(StaffRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('dashboard:products')

    def post(self, request, *args, **kwargs):
        product = self.get_object()
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect(self.success_url)


class ProductVariantCreateView(StaffRequiredMixin, CreateView):
    model = ProductVariant
    form_class = ProductVariantForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        kwargs['product'] = product
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        form.instance.product = product
        return form

    def form_valid(self, form):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        form.instance.product = product
        try:
            form.save()
            messages.success(self.request, "Product variant added successfully!")
        except Exception as e:
            from django.core.exceptions import ValidationError
            if isinstance(e, ValidationError):
                messages.error(self.request, f"Error: {', '.join(e.messages)}")
            else:
                messages.error(self.request, f"Error adding variant: {str(e)}")
        return redirect('dashboard:product_update', pk=product.id)

    def form_invalid(self, form):
        product = get_object_or_404(Product, id=self.kwargs['product_id'])
        # Add error messages
        for field, errors in form.errors.items():
            messages.error(self.request, f"Error in variant field '{field}': {', '.join(errors)}")
        return redirect('dashboard:product_update', pk=product.id)


class ProductVariantUpdateView(StaffRequiredMixin, UpdateView):
    model = ProductVariant
    form_class = ProductVariantForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.object:
            kwargs['product'] = self.object.product
        return kwargs

    def form_valid(self, form):
        try:
            form.save()
            messages.success(self.request, "Variant updated successfully!")
        except Exception as e:
            from django.core.exceptions import ValidationError
            if isinstance(e, ValidationError):
                messages.error(self.request, f"Error: {', '.join(e.messages)}")
            else:
                messages.error(self.request, f"Error updating variant: {str(e)}")
        return redirect('dashboard:product_update', pk=self.object.product.id)

    def form_invalid(self, form):
        messages.error(self.request, "Failed to update variant. Check details.")
        return redirect('dashboard:product_update', pk=self.object.product.id)


class ProductVariantDeleteView(StaffRequiredMixin, DeleteView):
    model = ProductVariant

    def post(self, request, *args, **kwargs):
        variant = self.get_object()
        product_id = variant.product.id
        variant.delete()
        messages.success(request, "Variant deleted successfully.")
        return redirect('dashboard:product_update', pk=product_id)


# =========================================================
# ORDER & PAYMENT MANAGEMENT
# =========================================================

class OrderListView(StaffRequiredMixin, ListView):
    model = Order
    template_name = 'dashboard/orders.html'
    context_object_name = 'orders'
    paginate_by = 15

    def get_queryset(self):
        queryset = Order.objects.all().select_related('user').order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        if q:
            # Search by order_id uuid, username, email
            queryset = queryset.filter(
                Q(order_id__icontains=q) | 
                Q(user__username__icontains=q) | 
                Q(user__email__icontains=q)
            )
        status = self.request.GET.get('status', '')
        if status:
            queryset = queryset.filter(order_status=status)
            
        pay_status = self.request.GET.get('payment_status', '')
        if pay_status:
            queryset = queryset.filter(payment_status=pay_status)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['pay_filter'] = self.request.GET.get('payment_status', '')
        context['order_statuses'] = Order.ORDER_STATUS
        context['payment_statuses'] = Order.PAYMENT_STATUS
        context['active_tab'] = 'orders'
        return context


class OrderDetailView(StaffRequiredMixin, DetailView):
    model = Order
    template_name = 'dashboard/order_detail.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all().select_related('product_variant__product')
        # Check if transaction exists
        try:
            context['payment'] = Payment.objects.filter(order=self.object).first()
        except Payment.DoesNotExist:
            context['payment'] = None
            
        context['order_statuses'] = Order.ORDER_STATUS
        context['payment_statuses'] = Order.PAYMENT_STATUS
        context['active_tab'] = 'orders'
        return context


class OrderUpdateStatusView(StaffRequiredMixin, View):
    """AJAX / Post View to update Order Status"""
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get('order_status')
        
        valid_statuses = [status[0] for status in Order.ORDER_STATUS]
        if new_status in valid_statuses:
            order.order_status = new_status
            order.save()
            
            # Dynamic Stock Return logic if cancelled
            if new_status == 'CANCELLED':
                for item in order.items.all():
                    if item.product_variant:
                        item.product_variant.stock += item.quantity
                        item.product_variant.save()
            
            return JsonResponse({
                'success': True,
                'order_status': order.get_order_status_display(),
                'message': f"Order status updated to {order.get_order_status_display()} successfully."
            })
        return JsonResponse({'success': False, 'message': 'Invalid status provided.'}, status=400)


class OrderUpdatePaymentView(StaffRequiredMixin, View):
    """AJAX / Post View to update Payment Status"""
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        new_status = request.POST.get('payment_status')
        
        valid_statuses = [status[0] for status in Order.PAYMENT_STATUS]
        if new_status in valid_statuses:
            order.payment_status = new_status
            order.save()
            
            # Sync standard Payment model if exists
            try:
                payment = Payment.objects.filter(order=order).first()
                if payment:
                    if new_status == 'PAID':
                        payment.status = 'SUCCESS'
                        payment.paid_at = timezone.now()
                    elif new_status == 'FAILED':
                        payment.status = 'FAILED'
                    else:
                        payment.status = 'PENDING'
                    payment.save()
            except Exception:
                pass
                
            return JsonResponse({
                'success': True,
                'payment_status': order.get_payment_status_display(),
                'message': f"Payment status updated to {order.get_payment_status_display()} successfully."
            })
        return JsonResponse({'success': False, 'message': 'Invalid payment status provided.'}, status=400)
