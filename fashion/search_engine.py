import re
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import Q, F, Avg, Prefetch, Case, When, Value, FloatField
from django.db.models.functions import Coalesce
from .models import Category, SubCategory, Product, ProductVariant

# =========================================================
# FASHION THESAURUS & SYNONYMS
# =========================================================

SYNONYMS = {
    'hoodie': ['hoodie', 'hoodies', 'sweatshirt', 'sweatshirts', 'jacket', 'jackets'],
    'hoodies': ['hoodie', 'hoodies', 'sweatshirt', 'sweatshirts', 'jacket', 'jackets'],
    'sweatshirt': ['sweatshirt', 'sweatshirts', 'hoodie', 'hoodies', 'jacket', 'jackets'],
    'sweatshirts': ['sweatshirt', 'sweatshirts', 'hoodie', 'hoodies', 'jacket', 'jackets'],
    
    'partywear': ['party wear', 'partywear', 'party', 'dress', 'dresses', 'outfit', 'outfits', 'suit', 'suits'],
    'party': ['party wear', 'partywear', 'party', 'dress', 'dresses', 'outfit', 'outfits', 'suit', 'suits'],
    
    'sportswear': ['sports wear', 'sportswear', 'dry fit', 'dryfit', 'shorts', 'track', 'sports', 'athletic', 'gym'],
    'sports': ['sports wear', 'sportswear', 'dry fit', 'dryfit', 'shorts', 'track', 'sports', 'athletic', 'gym'],
    'dryfit': ['dry fit', 'dryfit', 'sportswear', 'sports wear', 'shorts', 'track'],
    
    'tshirt': ['tshirt', 't-shirt', 'tshirts', 't-shirts', 'tee', 'tees', 'oversized'],
    't-shirt': ['t-shirt', 'tshirt', 't-shirts', 'tshirts', 'tee', 'tees', 'oversized'],
    'tshirts': ['tshirts', 'tshirt', 't-shirts', 't-shirt', 'tee', 'tees', 'oversized'],
    't-shirts': ['t-shirts', 't-shirt', 'tshirts', 'tshirt', 'tee', 'tees', 'oversized'],
    'tee': ['tee', 'tees', 't-shirt', 'tshirt', 't-shirts', 'tshirts'],
    'tees': ['tees', 'tee', 't-shirt', 'tshirt', 't-shirts', 'tshirts'],
    
    'pant': ['pant', 'pants', 'trousers', 'trouser', 'jeans', 'jean', 'lower', 'lowers', 'cargo'],
    'pants': ['pants', 'pant', 'trousers', 'trouser', 'jeans', 'jean', 'lower', 'lowers', 'cargo'],
    'trousers': ['trousers', 'trouser', 'pant', 'pants', 'jeans', 'jean', 'lower', 'lowers', 'cargo'],
    'trouser': ['trouser', 'trousers', 'pant', 'pants', 'jeans', 'jean', 'lower', 'lowers', 'cargo'],
    'jeans': ['jeans', 'jean', 'pant', 'pants', 'trousers', 'trouser', 'lower', 'lowers', 'denim'],
    'jean': ['jean', 'jeans', 'pant', 'pants', 'trousers', 'trouser', 'lower', 'lowers', 'denim'],
    'lower': ['lower', 'lowers', 'pant', 'pants', 'trousers', 'trouser', 'jeans', 'jean'],
    'lowers': ['lowers', 'lower', 'pant', 'pants', 'trousers', 'trouser', 'jeans', 'jean'],
    
    'shorts': ['shorts', 'short', 'track', 'sportswear'],
    'shoes': ['shoes', 'sneakers', 'footwear'],
    'sneakers': ['sneakers', 'shoes', 'footwear'],
    
    'dresses': ['dresses', 'dress', 'outfit', 'outfits', 'party wear', 'partywear'],
    'dress': ['dress', 'dresses', 'outfit', 'outfits', 'party wear', 'partywear'],
    'outfit': ['outfit', 'outfits', 'dresses', 'dress', 'party wear', 'partywear'],
    'outfits': ['outfits', 'outfit', 'dresses', 'dress', 'party wear', 'partywear']
}

# =========================================================
# ATTRIBUTE DICTIONARIES
# =========================================================

GENDER_MAP = {
    'men': 'men', 'mens': 'men', 'man': 'men', 'male': 'men',
    'women': 'women', 'womens': 'women', 'woman': 'women', 'female': 'women', 'girl': 'women', 'girls': 'women',
    'unisex': 'unisex', 'neutral': 'unisex'
}

COLOR_LIST = [
    'black', 'red', 'green', 'yellow', 'brown', 'blue', 'white', 'grey', 'gray', 'pink', 'purple', 'orange', 'beige', 'navy', 'standard'
]

STYLE_KEYWORDS = [
    'baggy', 'oversized', 'linen', 'cargo', 'viscose', 'dry fit', 'dryfit', 'plain', 'collar', 'zipper', 'sleeve', 'regular', 'polo'
]

BRANDS = [
    'nike', 'adidas', 'puma', 'zara', 'h&m', 'levis', 'under armour'
]

SEASONS = [
    'summer', 'winter', 'spring', 'autumn', 'monsoon'
]

# =========================================================
# LEVENSHTEIN spelling correction FOR SYLLABLE ENHANCEMENT
# =========================================================

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def build_vocabulary():
    vocab = set()
    vocab.update(SYNONYMS.keys())
    for syns in SYNONYMS.values():
        vocab.update(syns)
    vocab.update(GENDER_MAP.keys())
    vocab.update(COLOR_LIST)
    vocab.update(STYLE_KEYWORDS)
    vocab.update(BRANDS)
    vocab.update(SEASONS)
    
    try:
        categories = Category.objects.filter(is_active=True).values_list('name', flat=True)
        for cat in categories:
            vocab.update(cat.lower().split())
        subcategories = SubCategory.objects.filter(is_active=True).values_list('name', flat=True)
        for subcat in subcategories:
            vocab.update(subcat.lower().split())
        colors = ProductVariant.objects.filter(is_active=True).values_list('color', flat=True).distinct()
        for col in colors:
            vocab.update(col.lower().split())
        for pt_code, pt_label in Product.PRODUCT_TYPE:
            vocab.update(pt_label.lower().split())
    except Exception:
        pass
        
    return {v for v in vocab if len(v) > 1}


def correct_typos(tokens, vocab):
    corrected = []
    for token in tokens:
        if token in vocab or token.isdigit() or len(token) <= 2:
            corrected.append(token)
            continue
            
        max_allowed_dist = 1 if len(token) <= 4 else 2
        best_match = None
        min_dist = 999
        
        for vocab_word in vocab:
            if abs(len(token) - len(vocab_word)) > max_allowed_dist:
                continue
            dist = levenshtein_distance(token, vocab_word)
            if dist < min_dist and dist <= max_allowed_dist:
                min_dist = dist
                best_match = vocab_word
                
        if best_match:
            corrected.append(best_match)
        else:
            corrected.append(token)
    return corrected

# =========================================================
# POSTGRESQL SMART SEARCH
# =========================================================

def parse_and_search(query_str, category_group=None):
    """
    Highly optimized PostgreSQL search utilizing SearchVector, SearchQuery,
    SearchRank, and TrigramSimilarity to perform smart ranking and typo
    tolerance directly on the database server.
    """
    query_str = query_str.strip()
    
    # 1. Base Query with select_related, prefetch_related, and annotations to optimize queries
    products = Product.objects.filter(is_active=True).select_related(
        'category', 'subcategory'
    ).prefetch_related(
        'reviews',
        Prefetch('variants', queryset=ProductVariant.objects.filter(is_active=True))
    ).annotate(
        avg_rating=Coalesce(Avg('reviews__rating'), 0.0)
    )

    # Apply category_group filters
    if category_group == 'tops':
        products = products.filter(Q(category__name__icontains='shirt') | Q(category__name__icontains='top'))
    elif category_group == 'bottoms':
        products = products.filter(Q(category__name__icontains='lower') | Q(category__name__icontains='bottom') | Q(category__name__icontains='pant') | Q(category__name__icontains='jeans'))
    elif category_group == 'offers':
        products = products.filter(discount_price__isnull=False, discount_price__lte=F('price') * 0.5)

    if not query_str:
        return list(products)

    # 2. Query Preprocessing and Spelling Correction
    cleaned_query = re.sub(r'[^\w\s-]', '', query_str.lower())
    original_tokens = cleaned_query.split()
    
    vocab = build_vocabulary()
    corrected_tokens = correct_typos(original_tokens, vocab)
    corrected_query = " ".join(corrected_tokens)

    # 3. Extract attributes from query
    extracted_genders = [GENDER_MAP[t] for t in corrected_tokens if t in GENDER_MAP]
    extracted_colors = [t for t in corrected_tokens if t in COLOR_LIST]
    extracted_styles = [t for t in corrected_tokens if t in STYLE_KEYWORDS]
    extracted_brands = [t for t in corrected_tokens if t in BRANDS]
    extracted_seasons = [t for t in corrected_tokens if t in SEASONS]

    # Special handling for composite keywords
    if 'party' in corrected_tokens or 'wear' in corrected_tokens:
        extracted_styles.append('party wear')
    if 'sports' in corrected_tokens or 'wear' in corrected_tokens:
        extracted_styles.append('sports wear')

    # 4. Synonym Expansion & Raw FTS SearchQuery construction
    # We combine each corrected token and its synonyms into OR groups, joined by AND.
    # E.g., "black tshirt" -> '(black) & (t-shirt | tshirt | tee | tees)'
    fts_groups = []
    for token in corrected_tokens:
        syns = [token]
        if token in SYNONYMS:
            syns = list(set(syns + SYNONYMS[token]))
            
        escaped_syns = [f"'{s}'" for s in syns if s]
        fts_groups.append(f"({' | '.join(escaped_syns)})")
        
    fts_query_str = " | ".join(fts_groups)
    search_query = SearchQuery(fts_query_str, search_type='raw')

    # 5. Define FTS SearchVector and SQL Annotations
    search_vector = (
        SearchVector('name', weight='A') +
        SearchVector('product_type', weight='B') +
        SearchVector('category__name', weight='B') +
        SearchVector('subcategory__name', weight='B') +
        SearchVector('description', weight='C')
    )

    # FTS and Trigram Similarity Expressions
    rank_expr = SearchRank(search_vector, search_query)
    similarity_expr = TrigramSimilarity('name', query_str)
    cat_similarity_expr = Coalesce(TrigramSimilarity('category__name', query_str), 0.0)
    subcat_similarity_expr = Coalesce(TrigramSimilarity('subcategory__name', query_str), 0.0)

    # 6. Database Case/When Attribute-Scoring Bonuses
    # A. Color Match Bonus (matches parsed color directly with active variants color!)
    color_q = Q()
    if extracted_colors:
        color_q = Q(variants__color__iexact=extracted_colors[0], variants__is_active=True)
        for col in extracted_colors[1:]:
            color_q |= Q(variants__color__iexact=col, variants__is_active=True)
        color_bonus = Case(
            When(color_q, then=Value(50.0)),
            default=Value(0.0),
            output_field=FloatField()
        )
    else:
        color_bonus = Value(0.0, output_field=FloatField())

    # B. Gender Match Bonus
    if extracted_genders:
        gender_q = Q()
        for g in extracted_genders:
            gender_q |= Q(name__icontains=g) | Q(category__name__icontains=g) | Q(subcategory__name__icontains=g)
        gender_bonus = Case(
            When(gender_q, then=Value(40.0)),
            default=Value(0.0),
            output_field=FloatField()
        )
    else:
        gender_bonus = Value(0.0, output_field=FloatField())

    # C. Brand Match Bonus
    if extracted_brands:
        brand_q = Q()
        for b in extracted_brands:
            brand_q |= Q(name__icontains=b) | Q(description__icontains=b)
        brand_bonus = Case(
            When(brand_q, then=Value(80.0)),
            default=Value(0.0),
            output_field=FloatField()
        )
    else:
        brand_bonus = Value(0.0, output_field=FloatField())

    # D. Style Match Bonus
    if extracted_styles:
        style_q = Q()
        for s in extracted_styles:
            style_q |= Q(name__icontains=s) | Q(subcategory__name__icontains=s) | Q(description__icontains=s)
        style_bonus = Case(
            When(style_q, then=Value(45.0)),
            default=Value(0.0),
            output_field=FloatField()
        )
    else:
        style_bonus = Value(0.0, output_field=FloatField())

    # E. Season Match Bonus
    if extracted_seasons:
        season_q = Q()
        for s in extracted_seasons:
            season_q |= Q(subcategory__name__icontains=s) | Q(description__icontains=s)
        season_bonus = Case(
            When(season_q, then=Value(30.0)),
            default=Value(0.0),
            output_field=FloatField()
        )
    else:
        season_bonus = Value(0.0, output_field=FloatField())

    # F. Catalog Signals (Trending, Featured, Offers)
    trending_bonus = Case(
        When(is_trending=True, then=Value(15.0)),
        default=Value(0.0),
        output_field=FloatField()
    )
    featured_bonus = Case(
        When(is_featured=True, then=Value(10.0)),
        default=Value(0.0),
        output_field=FloatField()
    )
    discount_bonus = Case(
        When(discount_price__isnull=False, discount_price__lt=F('price'), then=Value(10.0)),
        default=Value(0.0),
        output_field=FloatField()
    )

    # 7. Final Composite Database Search Score
    score_expression = (
        rank_expr * 60.0 +
        similarity_expr * 40.0 +
        cat_similarity_expr * 30.0 +
        subcat_similarity_expr * 30.0 +
        color_bonus +
        gender_bonus +
        brand_bonus +
        style_bonus +
        season_bonus +
        trending_bonus +
        featured_bonus +
        discount_bonus +
        (F('avg_rating') * 2.0)
    )

    # 8. Fetch Candidates via FTS / Trigrams, Score, and Sort
    # By filtering using a broad OR of FTS matching or Trigram similarity lookups,
    # we ensure incredibly fast execution while preserving maximum recall.
    candidate_filter = (
        Q(search_vector=search_query) |
        Q(name__trigram_similar=query_str) |
        Q(category__name__trigram_similar=query_str) |
        Q(subcategory__name__trigram_similar=query_str)
    )
    if extracted_colors:
        candidate_filter |= color_q

    products = (
        products.annotate(search_vector=search_vector)
        .filter(candidate_filter)
        .annotate(search_score=score_expression)
        .order_by('-search_score')
        .distinct()
    )

    return list(products)
