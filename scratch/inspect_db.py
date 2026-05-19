import os
import sys
import django

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vishakhan_clothings.settings')
django.setup()

from fashion.models import Product, Category, SubCategory, ProductVariant

print("--- CATEGORIES ---")
for c in Category.objects.all():
    print(f"Category: {c.name} (slug: {c.slug})")

print("\n--- SUB-CATEGORIES ---")
for sc in SubCategory.objects.all():
    print(f"SubCategory: {sc.name} (slug: {sc.slug}, category: {sc.category.name})")

print("\n--- PRODUCTS (first 30) ---")
for p in Product.objects.all()[:30]:
    colors = list(p.variants.values_list('color', flat=True).distinct())
    print(f"Product: {p.name} | Type: {p.product_type} | Category: {p.category.name if p.category else 'None'} | SubCategory: {p.subcategory.name if p.subcategory else 'None'} | Colors: {colors}")
