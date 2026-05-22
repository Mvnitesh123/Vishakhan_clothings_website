from django import forms
from fashion.models import Category, SubCategory, Product, ProductVariant, User

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'category', 'subcategory', 'product_type', 'name', 
            'image', 'short_description', 'description', 'price', 
            'discount_price', 'sku', 'is_featured', 'is_trending', 'is_active'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select select-styled'}),
            'subcategory': forms.Select(attrs={'class': 'form-select select-styled'}),
            'product_type': forms.Select(attrs={'class': 'form-select select-styled'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter product name'}),
            'image': forms.FileInput(attrs={'class': 'form-file-input'}),
            'short_description': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Brief summary (max 300 chars)'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4, 'placeholder': 'Full HTML or text description'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),
            'sku': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter unique SKU'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_trending': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        discount_price = cleaned_data.get('discount_price')

        if price is not None and discount_price is not None:
            if discount_price >= price:
                self.add_error('discount_price', "Discount price must be less than the original price.")
        return cleaned_data


class ProductVariantForm(forms.ModelForm):
    size = forms.ChoiceField(
        choices=ProductVariant.SIZE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select select-styled'}),
        required=True
    )
    image = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-file-input'}),
        required=False
    )

    class Meta:
        model = ProductVariant
        fields = ['size', 'color', 'stock', 'price', 'is_active', 'allow_discount']
        widgets = {
            'color': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Midnight Blue'}),
            'stock': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': 'Override price (optional)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'allow_discount': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        
        if not product and self.instance and hasattr(self.instance, 'product') and self.instance.product:
            product = self.instance.product
            
        if product:
            p_type = product.product_type
            rules = {
                'Shirt': ['M', 'L', 'XL', '2XL'],
                'Pant': ['28', '30', '32', '34', '36', '40', '42', '44'],
                'Shorts & Track': ['M', 'L', 'XL', '2XL', '3XL', '5XL'],
                'T-shirt': ['M', 'L', 'XL', '2XL', '3XL', '5XL'],
            }
            allowed = rules.get(p_type, [])
            self.fields['size'].choices = [(s, s) for s in allowed]

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()

        # Handle color-grouped image saving
        image_file = self.cleaned_data.get('image')
        if image_file:
            from fashion.models import ProductVariantImage
            variant_image, created = ProductVariantImage.objects.get_or_create(
                product=instance.product,
                color=instance.color
            )
            variant_image.image = image_file
            variant_image.save()

        return instance


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter category name'}),
            'image': forms.FileInput(attrs={'class': 'form-file-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['category', 'name', 'image', 'is_active']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select select-styled'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter subcategory name'}),
            'image': forms.FileInput(attrs={'class': 'form-file-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class StaffUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password'}), 
        required=False, 
        help_text="Leave blank to keep existing password for edits."
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'is_staff', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Enter email address'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last name'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone number'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("Email is required.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
