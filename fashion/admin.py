from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from .models import *

# Register your models here.

class ProductVariantFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        count = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                count += 1
        if count < 1:
            raise ValidationError("You must associate at least one variant with this product.")

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    formset = ProductVariantFormSet
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductVariantInline]

admin.site.register(User)
admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductVariant)

class ProductVariantImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'color', 'image']
    search_fields = ['product__name', 'color']

admin.site.register(ProductVariantImage, ProductVariantImageAdmin)

admin.site.register(Address)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Payment)
admin.site.register(Review)
admin.site.register(Wishlist)


