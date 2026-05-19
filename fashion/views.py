from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg, Count, Q, F, Case, When, IntegerField, Prefetch
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import (
    Category,
    Product,
    Wishlist,
    Cart,
    CartItem,
    SubCategory,
    ProductVariant,
    Review,
    Address,
    Order,
    Payment,
    User,
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages

import asyncio
from asgiref.sync import sync_to_async

def _get_global_context_data(user):
    tops = list(Category.objects.filter(is_active=True).filter(
        Q(name__icontains='shirt') | Q(name__icontains='top')
    ).only('name', 'slug'))

    bottoms = list(Category.objects.filter(is_active=True).filter(
        Q(name__icontains='lower') | Q(name__icontains='bottom') | Q(name__icontains='pant') | Q(name__icontains='jeans')
    ).only('name', 'slug'))
    
    # Offers: Basic (<40% off) and Premium (>=40% off) (trending products only)
    basic_offers = list(Product.objects.filter(
        is_active=True, 
        is_trending=True,
        discount_price__isnull=False,
        discount_price__gt=F('price') * 0.6,
        discount_price__lt=F('price')
    ).only('name', 'slug', 'price', 'discount_price').order_by('-created_at')[:5])

    premium_offers = list(Product.objects.filter(
        is_active=True, 
        is_trending=True,
        discount_price__isnull=False,
        discount_price__lte=F('price') * 0.6,
        discount_price__gt=0
    ).only('name', 'slug', 'price', 'discount_price').order_by('-created_at')[:5])

    sport_wear_tops = list(SubCategory.objects.filter(name__icontains='Dry fit', is_active=True).only('name', 'slug'))
    sport_wear_bottoms = list(SubCategory.objects.filter(name__icontains='Shorts', is_active=True).only('name', 'slug'))

    wishlist_count = 0
    cart_count = 0
    wishlist_product_ids = []
    cart_items = []
    cart_subtotal = 0
    wishlist_items = []
    has_out_of_stock = False
    if user.is_authenticated:
        wishlist_count = Wishlist.objects.filter(user=user).count()
        wishlist_product_ids = list(Wishlist.objects.filter(user=user).values_list('product_id', flat=True))
        try:
            cart = Cart.objects.filter(user=user).first()
            if cart:
                cart_items = list(cart.items.all().select_related('product_variant__product'))
                cart_count = len(cart_items)
                has_out_of_stock = any(item.product_variant.stock <= 0 for item in cart_items)
                for item in cart_items:
                    if item.product_variant.stock > 0:
                        cart_subtotal += item.product_variant.final_price * item.quantity
            
            wishlist_items = list(Wishlist.objects.filter(user=user).select_related('product'))
        except Exception:
            pass

    return {
        'tops': tops,
        'bottoms': bottoms,
        'basic_offers': basic_offers,
        'premium_offers': premium_offers,
        'sport_wear_tops': sport_wear_tops,
        'sport_wear_bottoms': sport_wear_bottoms,
        'wishlist_count': wishlist_count,
        'cart_count': cart_count,
        'wishlist_product_ids': wishlist_product_ids,
        'cart_items': cart_items,
        'cart_subtotal': cart_subtotal,
        'wishlist_items': wishlist_items,
        'has_out_of_stock': has_out_of_stock,
    }

def get_global_context(request):
    """Helper to get data needed across all pages (navbar, etc.) (Synchronous)"""
    return _get_global_context_data(request.user)

@sync_to_async
def get_global_context_async(user):
    return _get_global_context_data(user)

@sync_to_async
def get_home_data():
    categories = list(Category.objects.filter(is_active=True).order_by('name')[:6])
    active_variants = Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True))
    
    new_arrivals = list(
        Product.objects.filter(is_active=True, variants__is_active=True, variants__stock__gt=0)
        .distinct()
        .select_related('category')
        .prefetch_related('reviews', active_variants)
        .annotate(avg_rating=Avg('reviews__rating'))
        .order_by('-created_at')[:4]
    )
    featured = list(
        Product.objects.filter(is_active=True, is_featured=True, variants__is_active=True, variants__stock__gt=0)
        .distinct()
        .select_related('category')
        .prefetch_related('reviews', active_variants)
        .annotate(avg_rating=Avg('reviews__rating'))
        .order_by('-created_at')[:4]
    )
    trending_products = list(
        Product.objects.filter(is_active=True, is_trending=True, variants__is_active=True, variants__stock__gt=0)
        .distinct()
        .select_related('category')
        .prefetch_related('reviews', active_variants)
        .annotate(avg_rating=Avg('reviews__rating'))
        .order_by('-created_at')[:4]
    )
    
    return categories, new_arrivals, featured, trending_products

async def home(request):
    """
    Home page view — fetches all real data from the DB to
    replace every static / dummy placeholder in home.html.
    Runs queries in parallel using asyncio to improve TTFB.
    """
    # Execute DB queries concurrently
    global_context, (categories, new_arrivals, featured, trending_products) = await asyncio.gather(
        get_global_context_async(request.user),
        get_home_data()
    )

    # Combine into a single list with tags for the template filtering
    combined_products = []
    seen_ids = set()
    
    # Process New Arrivals (tag as 'all' only)
    for p in new_arrivals:
        if p.id not in seen_ids:
            p.filter_class = "all" 
            combined_products.append(p)
            seen_ids.add(p.id)
            
    # Process Featured (tag as 'best' only)
    for p in featured:
        if p.id not in seen_ids:
            p.filter_class = "best"
            combined_products.append(p)
            seen_ids.add(p.id)
        else:
            # If it's already in the list (as a new arrival), add 'best' tag to it
            for cp in combined_products:
                if cp.id == p.id:
                    cp.filter_class += " best"
                    break
    
    # Limit to exactly 4 products total for the section
    combined_products = combined_products[:4]

    context = global_context
    context.update({
        'categories':        categories,
        'featured_products': combined_products,
        'trending_products': trending_products,
    })

    return await sync_to_async(render)(request, 'home.html', context)



def product_detail(request, slug):
    # Define custom sort order for sizes
    size_order = Case(
        When(size='M', then=1),
        When(size='L', then=2),
        When(size='XL', then=3),
        When(size='2XL', then=4),
        When(size='3XL', then=5),
        When(size='4XL', then=6),
        When(size='5XL', then=7),
        When(size='28', then=8),
        When(size='30', then=9),
        When(size='32', then=10),
        When(size='34', then=11),
        When(size='36', then=12),
        When(size='40', then=13),
        When(size='42', then=14),
        When(size='44', then=15),
        When(size='CUSTOM', then=16),
        default=17,
        output_field=IntegerField(),
    )

    product = (
        Product.objects
        .filter(slug=slug, is_active=True)
        .prefetch_related(
            'reviews', 
            'reviews__user',
            Prefetch('variants', queryset=ProductVariant.objects.annotate(
                sort_order=size_order
            ).order_by('sort_order'))
        )
        .annotate(avg_rating=Avg('reviews__rating'))
        .first()
    )
    if not product:
        from django.http import Http404
        raise Http404("Product not found")

    product.views += 1
    product.save(update_fields=['views'])

    # Check if any variant of this product is already in the user's cart
    cart_variant_ids = []
    is_in_cart = False
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart_variant_ids = list(
                    CartItem.objects.filter(cart=cart, product_variant__product=product)
                    .values_list('product_variant_id', flat=True)
                )
                is_in_cart = len(cart_variant_ids) > 0
        except Exception:
            pass

    # Get unique sizes for the tiered selector
    unique_sizes = product.variants.values_list('size', flat=True).distinct()
    
    # Standard list for ordering
    all_possible_sizes = [
        'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL', 
        '28', '30', '32', '34', '36', '40', '42', '44', 
        'CUSTOM'
    ]
    ordered_sizes = [s for s in all_possible_sizes if s in unique_sizes]

    user_review = None
    if request.user.is_authenticated:
        user_review = Review.objects.filter(product=product, user=request.user).first()

    context = get_global_context(request)
    context.update({
        'product': product,
        'unique_sizes': ordered_sizes,
        'is_in_cart': is_in_cart,
        'cart_variant_ids': cart_variant_ids,
        'user_review': user_review,
    })
    return render(request, 'product_detail.html', context)


def category_detail(request, slug):
    current_category = get_object_or_404(Category, slug=slug, is_active=True)
    all_categories = Category.objects.filter(is_active=True).prefetch_related('subcategories').order_by('name')

    context = get_global_context(request)
    context.update({
        'category': current_category,
        'all_categories': all_categories,
    })
    return render(request, 'category_detail.html', context)


def category_directory(request):
    all_categories = Category.objects.filter(is_active=True).prefetch_related('subcategories').order_by('name')

    context = get_global_context(request)
    context.update({
        'all_categories': all_categories,
        'page_title': 'Shop by Category',
    })
    return render(request, 'category_detail.html', context)


def search(request):
    query = request.GET.get('q', '').strip()
    category_group = request.GET.get('group', '')
    
    from .search_engine import parse_and_search
    products = parse_and_search(query, category_group=category_group)

    context = get_global_context(request)
    context.update({
        'products': products,
        'query': query,
    })
    return render(request, 'search_results.html', context)


def top_rated(request):
    """
    Redirect legacy top-rated endpoint to the main products page sorted by rating.
    """
    return redirect('/products/?sort=rating')


def high_discount(request):
    """
    Redirect legacy high-discount endpoint to the main products page sorted by high discount.
    """
    return redirect('/products/?sort=high_discount')


def subcategory_detail(request, slug):
    subcategory = get_object_or_404(SubCategory, slug=slug, is_active=True)
    products = Product.objects.filter(subcategory=subcategory, is_active=True)

    context = get_global_context(request)
    context.update({
        'subcategory': subcategory,
        'products': products,
        'category': subcategory,  # So it works with category_detail.html template
    })
    return render(request, 'category_detail.html', context)


def product_list(request):
    """
    Complete product catalog with sorting and filtering.
    """
    products = Product.objects.filter(is_active=True).select_related('category').prefetch_related(
        'reviews',
        Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True))
    )
    
    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    
    # Annotations
    products = products.annotate(
        current_price=Coalesce('discount_price', 'price'),
        avg_rating=Avg('reviews__rating')
    )
    
    if sort_by == 'price_low':
        products = products.order_by('current_price')
    elif sort_by == 'price_high':
        products = products.order_by('-current_price')
    elif sort_by == 'rating':
        products = products.order_by(F('avg_rating').desc(nulls_last=True))
    elif sort_by == 'high_discount':
        from django.db.models import ExpressionWrapper, DecimalField, Case, When
        products = products.annotate(
            discount_percent=ExpressionWrapper(
                Case(
                    When(discount_price__isnull=False, discount_price__lt=F('price'), then=(F('price') - F('discount_price')) * 100.0 / F('price')),
                    default=0.0,
                    output_field=DecimalField()
                ),
                output_field=DecimalField()
            )
        ).order_by('-discount_percent', '-created_at')
    else: # newest
        products = products.order_by('-created_at')
        
    # Filtering by Category
    cat_slugs = request.GET.get('category', '').split(',')
    cat_slugs = [s for s in cat_slugs if s and s != 'None']
    if cat_slugs:
        products = products.filter(category__slug__in=cat_slugs)
    
    # Filtering by Subcategory
    sub_cat_slugs = request.GET.get('subcategory', '').split(',')
    sub_cat_slugs = [s for s in sub_cat_slugs if s and s != 'None']
    if sub_cat_slugs:
        products = products.filter(subcategory__slug__in=sub_cat_slugs)
        
    # Additional Filters
    is_trending = request.GET.get('trending') == 'true'
    is_top_rated = request.GET.get('top_rated') == 'true'
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_rating = request.GET.get('min_rating')

    if is_trending:
        products = products.filter(is_trending=True)
    
    if is_top_rated:
        # Filter for products with avg_rating 4.0 or higher
        products = products.filter(avg_rating__gte=4)
    
    if min_price:
        products = products.filter(current_price__gte=min_price)
    if max_price:
        products = products.filter(current_price__lte=max_price)
    
    if min_rating:
        products = products.filter(avg_rating__gte=min_rating)

    # Filtering by Section (Tops/Bottoms)
    section = request.GET.get('section', '')
    if section == 'tops':
        products = products.filter(product_type__in=['Shirt', 'T-shirt'])
    elif section == 'bottoms':
        products = products.filter(product_type__in=['Pant', 'Shorts & Track'])

    categories = Category.objects.filter(is_active=True).order_by('name')
    
    # Available subcategories for the current category
    available_subcategories = []
    if cat_slugs:
        from .models import SubCategory
        available_subcategories = SubCategory.objects.filter(category__slug=cat_slugs[0], is_active=True).order_by('name')

    # Pagination
    paginator = Paginator(products, 16)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = get_global_context(request)
    context.update({
        'products': products,
        'all_categories': categories,
        'available_subcategories': available_subcategories,
        'current_sort': sort_by,
        'current_category': ','.join(cat_slugs),
        'current_subcategory': ','.join(sub_cat_slugs),
        'current_section': section,
        'current_trending': is_trending,
        'current_top_rated': is_top_rated,
        'current_min_price': min_price,
        'current_max_price': max_price,
        'current_min_rating': min_rating,
        'page_title': 'All Collections',
        'page_subtitle': 'Discover our complete range of meticulously crafted pieces.',
    })
    return render(request, 'product_list.html', context)


# =========================================================
# AJAX CART & WISHLIST VIEWS
# =========================================================

from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET

@require_POST
def add_to_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Sign in or sign up first'}, status=401)
        
    product_id = request.POST.get('product_id')
    variant_id = request.POST.get('variant_id')
    quantity = int(request.POST.get('quantity', 1))
    
    # Resolve the variant
    variant = None
    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id)
    elif product_id:
        # Find the first active/available variant of the product
        variant = ProductVariant.objects.filter(product_id=product_id, is_active=True).first()
        if not variant:
            return JsonResponse({'success': False, 'message': 'Product is currently out of stock.'}, status=400)
            
    if not variant:
        return JsonResponse({'success': False, 'message': 'Please select a size and color first.'}, status=400)
        
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Check current quantity in cart to enforce stock limits accurately
    cart_item = CartItem.objects.filter(cart=cart, product_variant=variant).first()
    current_qty = cart_item.quantity if cart_item else 0
    total_requested = current_qty + quantity
    
    max_allowed = variant.stock - 1 if variant.stock > 1 else 1
    
    if total_requested > max_allowed:
        return JsonResponse({
            'success': False,
            'message': f'Cannot add requested quantity. Maximum allowed order limit is {max_allowed} items (must be less than available stock).'
        }, status=400)
        
    if not cart_item:
        cart_item = CartItem.objects.create(cart=cart, product_variant=variant, quantity=quantity)
    else:
        cart_item.quantity = total_requested
        cart_item.save()
    
    # Calculate cart total item count
    cart_count = CartItem.objects.filter(cart=cart).count()
    
    return JsonResponse({
        'success': True,
        'cart_count': cart_count,
        'message': 'Added to bag successfully!'
    })

@require_GET
def get_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Sign in or sign up first'}, status=401)
        
    cart = Cart.objects.filter(user=request.user).first()
    items_data = []
    subtotal = 0
    
    if cart:
        for item in cart.items.all().select_related('product_variant__product'):
            final_price = item.product_variant.final_price
            if item.product_variant.stock > 0:
                total_item_price = final_price * item.quantity
                subtotal += total_item_price
            else:
                total_item_price = 0
            
            image_url = ''
            if item.product_variant.image:
                image_url = item.product_variant.image.url
            elif item.product_variant.product.image:
                image_url = item.product_variant.product.image.url
                
            items_data.append({
                'id': item.id,
                'variant_id': item.product_variant.id,
                'product_name': item.product_variant.product.name,
                'product_slug': item.product_variant.product.slug,
                'size': item.product_variant.size,
                'color': item.product_variant.color,
                'price': float(final_price),
                'quantity': item.quantity,
                'total_price': float(total_item_price),
                'image_url': image_url,
                'stock': item.product_variant.stock
            })
            
    return JsonResponse({
        'success': True,
        'items': items_data,
        'subtotal': float(subtotal),
        'cart_count': len(items_data),
        'has_out_of_stock': any(item['stock'] <= 0 for item in items_data)
    })

@require_POST
def remove_from_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Sign in or sign up first'}, status=401)
        
    item_id = request.POST.get('item_id')
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    
    # Get updated total and count
    cart = Cart.objects.filter(user=request.user).first()
    cart_count = 0
    subtotal = 0
    if cart:
        cart_count = cart.items.count()
        for item in cart.items.all():
            if item.product_variant.stock > 0:
                subtotal += item.product_variant.final_price * item.quantity
            
    has_out_of_stock = any(item.product_variant.stock <= 0 for item in cart.items.all()) if cart else False
    return JsonResponse({
        'success': True,
        'message': 'Item removed from bag',
        'cart_count': cart_count,
        'subtotal': float(subtotal),
        'has_out_of_stock': has_out_of_stock
    })

@require_POST
def toggle_wishlist(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Sign in or sign up first'}, status=401)
        
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id)
    
    wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
    added = False
    if wishlist_item:
        wishlist_item.delete()
        message = 'Removed from wishlist'
    else:
        Wishlist.objects.create(user=request.user, product=product)
        added = True
        message = 'Added to wishlist'
        
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    
    return JsonResponse({
        'success': True,
        'added': added,
        'wishlist_count': wishlist_count,
        'message': message
    })

@require_GET
def get_wishlist(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Sign in or sign up first'}, status=401)
        
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    items_data = []
    
    for item in wishlist_items:
        product = item.product
        final_price = product.discount_price if product.discount_price else product.price
        image_url = product.image.url if product.image else ''
        
        items_data.append({
            'id': item.id,
            'product_id': product.id,
            'product_name': product.name,
            'product_slug': product.slug,
            'price': float(final_price),
            'image_url': image_url,
            'stock_status': product.stock_status,
        })
        
    return JsonResponse({
        'success': True,
        'items': items_data,
        'wishlist_count': len(items_data)
    })

@require_POST
def update_cart_quantity(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Sign in or sign up first'}, status=401)
        
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity < 1:
        return JsonResponse({'success': False, 'message': 'Quantity must be at least 1'}, status=400)
        
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    variant = cart_item.product_variant
    
    # Enforce stock limits
    max_allowed = variant.stock - 1 if variant.stock > 1 else 1
    if quantity > max_allowed:
        return JsonResponse({
            'success': False,
            'message': f'Cannot add requested quantity. Maximum allowed order limit is {max_allowed} items (must be less than available stock).'
        }, status=400)
        
    cart_item.quantity = quantity
    cart_item.save()
    
    # Get updated total and count
    cart = Cart.objects.filter(user=request.user).first()
    cart_count = 0
    subtotal = 0
    if cart:
        cart_count = cart.items.count()
        for item in cart.items.all():
            if item.product_variant.stock > 0:
                subtotal += item.product_variant.final_price * item.quantity
            
    has_out_of_stock = any(item.product_variant.stock <= 0 for item in cart.items.all()) if cart else False
    return JsonResponse({
        'success': True,
        'message': 'Quantity updated successfully',
        'cart_count': cart_count,
        'subtotal': float(subtotal),
        'item_total_price': float(cart_item.product_variant.final_price * cart_item.quantity),
        'has_out_of_stock': has_out_of_stock
    })

@require_POST
def submit_review(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Sign in or sign up first'}, status=401)
        
    product_id = request.POST.get('product_id')
    rating_val = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()
    
    if not product_id:
        return JsonResponse({'success': False, 'message': 'Product ID is required'}, status=400)
        
    product = get_object_or_404(Product, id=product_id)
    
    existing_review = Review.objects.filter(product=product, user=request.user).first()
    
    rating = None
    if rating_val and rating_val != '0':
        try:
            rating = int(rating_val)
            if rating < 1 or rating > 5:
                raise ValueError()
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Rating must be an integer between 1 and 5'}, status=400)
    else:
        # Rating is missing or 0 in this submission
        if existing_review and existing_review.rating:
            rating = existing_review.rating
        else:
            return JsonResponse({'success': False, 'message': 'Please select a star rating for the product!'}, status=400)
            
    review, created = Review.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={
            'rating': rating,
            'comment': comment
        }
    )
    
    # Recalculate and update the average rating on the Product model!
    reviews = product.reviews.all()
    if reviews.exists():
        total_rating = sum(r.rating for r in reviews if r.rating)
        avg_rating = round(total_rating / reviews.count())
        product.avg_rating = avg_rating
        product.save()
        
    message = 'Review submitted successfully!' if created else 'Review updated successfully!'
    
    user_name = request.user.get_full_name() or request.user.username
    created_date = review.created_at.strftime('%b %d, %Y')
    
    return JsonResponse({
        'success': True,
        'message': message,
        'created': created,
        'review': {
            'user_name': user_name,
            'rating': rating,
            'comment': comment,
            'created_at': created_date
        }
    })

@require_POST
def delete_review(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Sign in or sign up first'}, status=401)
        
    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({'success': False, 'message': 'Product ID is required'}, status=400)
        
    product = get_object_or_404(Product, id=product_id)
    review = Review.objects.filter(product=product, user=request.user).first()
    
    if not review:
        return JsonResponse({'success': False, 'message': 'No review found to delete'}, status=404)
        
    review.delete()
    
    # Recalculate average rating
    reviews = product.reviews.all()
    if reviews.exists():
        total_rating = sum(r.rating for r in reviews if r.rating)
        avg_rating = round(total_rating / reviews.count())
        product.avg_rating = avg_rating
    else:
        product.avg_rating = 0
    product.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Review deleted successfully!'
    })

@login_required
def profile_view(request):
    user = request.user
    
    # Get user's default address or first address
    address = Address.objects.filter(user=user, is_default=True).first()
    if not address:
        address = Address.objects.filter(user=user).first()
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            username = request.POST.get('username', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            
            if not username:
                messages.error(request, 'Username is required.')
            else:
                if User.objects.filter(username=username).exclude(id=user.id).exists():
                    messages.error(request, 'Username is already taken.')
                else:
                    user.username = username
                    user.first_name = first_name
                    user.last_name = last_name
                    user.phone = phone
                    user.save()
                    messages.success(request, 'Profile details updated successfully!')
                    
        elif action == 'update_address':
            full_name = request.POST.get('full_name', '').strip()
            address_phone = request.POST.get('phone', '').strip()
            address_line = request.POST.get('address_line', '').strip()
            city = request.POST.get('city', '').strip()
            state = request.POST.get('state', '').strip()
            country = request.POST.get('country', '').strip()
            postal_code = request.POST.get('postal_code', '').strip()
            
            if address:
                address.full_name = full_name
                address.phone = address_phone
                address.address_line = address_line
                address.city = city
                address.state = state
                address.country = country
                address.postal_code = postal_code
                address.save()
                messages.success(request, 'Shipping address updated successfully!')
            else:
                Address.objects.create(
                    user=user,
                    full_name=full_name,
                    phone=address_phone,
                    address_line=address_line,
                    city=city,
                    state=state,
                    country=country,
                    postal_code=postal_code,
                    is_default=True
                )
                messages.success(request, 'Shipping address added successfully!')
                
        elif action == 'update_photo':
            profile_image = request.FILES.get('profile_image')
            if profile_image:
                user.profile_image = profile_image
                user.save()
                messages.success(request, 'Profile photo updated successfully!')
            else:
                messages.error(request, 'No image file was uploaded.')
                
        return redirect('profile')

    # Fetch active sessions & cart
    cart = Cart.objects.filter(user=user).first()
    cart_items = cart.items.all().select_related('product_variant__product') if cart else []
    
    # Fetch wishlist
    wishlist_items = Wishlist.objects.filter(user=user).select_related('product')
    
    # Fetch active orders
    active_orders = Order.objects.filter(user=user).exclude(order_status__in=['DELIVERED', 'CANCELLED', 'RETURNED']).order_by('-created_at')
    
    # Fetch order history
    order_history = Order.objects.filter(user=user, order_status__in=['DELIVERED', 'CANCELLED', 'RETURNED']).order_by('-created_at')
    
    context = get_global_context(request)
    context.update({
        'profile_user': user,
        'address': address,
        'profile_cart_items': cart_items,
        'profile_wishlist_items': wishlist_items,
        'active_orders': active_orders,
        'order_history': order_history,
    })
    return render(request, 'profile.html', context)