import os, glob, re

template_dir = 'd:/WorkFiles/CodeFiles/Project/Vishakhan_clothings/vishakhan_clothings/fashion/templates/'
html_files = glob.glob(os.path.join(template_dir, '*.html'))

pattern = re.compile(r'\{\%\s*with product\.images\.all as images\s*\%\}.*?\{\%\s*endwith\s*\%\}', re.DOTALL)

replacement = '''{% if product.image %}
                  <img src=\"{{ product.image.url }}\" alt=\"{{ product.name }}\" class=\"product-img product-img--primary\" loading=\"lazy\" />
                {% else %}
                  <div class=\"product-img-placeholder\"></div>
                {% endif %}'''

for file_path in html_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if pattern.search(content):
        content = pattern.sub(replacement, content)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {os.path.basename(file_path)}')

