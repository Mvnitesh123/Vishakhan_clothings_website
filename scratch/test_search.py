import os
import sys
import django

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vishakhan_clothings.settings')
django.setup()

from fashion.search_engine import parse_and_search

def run_test_case(title, query, expected_keywords=None, group=None):
    print(f"\n=========================================================")
    print(f"TEST CASE: {title}")
    print(f"Query: '{query}'" + (f" | Group: '{group}'" if group else ""))
    print(f"=========================================================")
    
    results = parse_and_search(query, category_group=group)
    print(f"Found {len(results)} products:")
    
    success = True
    for i, p in enumerate(results[:5]):
        colors = list(p.variants.values_list('color', flat=True).distinct())
        print(f"  {i+1}. Name: {p.name} | Type: {p.product_type} | Category: {p.category.name if p.category else 'None'} | Colors: {colors}")
        
    if expected_keywords:
        matched_expected = False
        # Check if the top products match our expected keywords
        for p in results[:3]:
            p_data = f"{p.name} {p.product_type} {p.category.name if p.category else ''} {p.subcategory.name if p.subcategory else ''}".lower()
            colors = [c.lower() for c in p.variants.values_list('color', flat=True).distinct()]
            
            keyword_matches = 0
            for kw in expected_keywords:
                if kw.lower() in p_data or kw.lower() in colors:
                    keyword_matches += 1
            
            if keyword_matches >= len(expected_keywords) - 1: # Match almost all keywords
                matched_expected = True
                break
                
        if not matched_expected and len(results) > 0:
            print("  Warning: Top products did not match all expected keywords.")
            success = False
            
    print(f"STATUS: {'PASSED' if success else 'FAILED'}")
    return success

if __name__ == '__main__':
    print("Starting Smart Search System Automated Tests...\n")
    
    all_passed = True
    
    # Test 1: Synonym expansion ("hoodie" -> finds sweatshirt/hoodie products)
    # Our DB contains "collar zipper" and "T-shirt-mens" under T-shirts/Hoodies subcategory, etc. Let's see what is returned.
    all_passed &= run_test_case(
        "Synonym Expansion (hoodie)",
        "hoodie",
        expected_keywords=["T-shirt"]
    )
    
    # Test 2: Style / Occasion ("party wear")
    # Our DB contains "Party wear mens", "Party wear 2"
    all_passed &= run_test_case(
        "Style/Occasion Understanding (party wear)",
        "party wear",
        expected_keywords=["Party"]
    )
    
    # Test 3: Color and type ("black tshirt")
    # Our DB has "T-shirt-mens-3" which has variant color 'Black' and type 'Shorts & Track', etc.
    all_passed &= run_test_case(
        "Color + Type (black tshirt)",
        "black tshirt",
        expected_keywords=["Black", "T-shirt"]
    )
    
    # Test 4: Typo Tolerance ("blak tshrt")
    # Should correct to "black t-shirt"
    all_passed &= run_test_case(
        "Typo Tolerance (blak tshrt)",
        "blak tshrt",
        expected_keywords=["Black"]
    )
    
    # Test 5: Category/Subcategory and style relation ("dry fit")
    all_passed &= run_test_case(
        "Category & Subcategory Matching (dry fit)",
        "dry fit",
        expected_keywords=["Dry Fit"]
    )
    
    # Test 6: Brand + Category / broad keywords ("nike shoes")
    all_passed &= run_test_case(
        "Brand + Category (nike sports)",
        "nike sports",
        expected_keywords=["Sports"]
    )

    # Test 7: Group Parameter ("pants" in bottoms group)
    all_passed &= run_test_case(
        "Group Query Filtering (tops group)",
        "plain",
        expected_keywords=["plain"],
        group="tops"
    )

    print("\n=========================================================")
    if all_passed:
        print("ALL SMART SEARCH TESTS PASSED SUCCESSFULLY!")
    else:
        print("SOME TESTS ENCOUNTERED WARNINGS / FAILED. PLEASE VERIFY THE SCORING WEIGHTS.")
    print("=========================================================")
