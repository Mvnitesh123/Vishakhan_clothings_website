import os, glob

template_dir = 'd:/WorkFiles/CodeFiles/Project/Vishakhan_clothings/vishakhan_clothings/fashion/templates/'
html_files = glob.glob(os.path.join(template_dir, '*.html'))

old_pattern = '''              {% with product.images.all as images %}
                {% if images %}
                  <img src=\"{{ images.0.image.url }}\" alt=\"{{ product.name }}\" class=\"product-img product-img--primary\" loading=\"lazy\" />
                  {% if images|length > 1 %}
                    <img src=\"{{ images.1.image.url }}\" alt=\"{{ product.name }}\" class=\"product-img product-img--hover\" loading=\"lazy\" />
                  {% endif %}
                {% else %}
                  <div class=\"product-img-placeholder\">
                    <span>No Image</span>
                  </div>
                {% endif %}
              {% endwith %}'''

new_pattern = '''              {% if product.image %}
                <img src=\"{{ product.image.url }}\" alt=\"{{ product.name }}\" class=\"product-img product-img--primary\" loading=\"lazy\" />
              {% else %}
                <div class=\"product-img-placeholder\">
                  <span>No Image</span>
                </div>
              {% endif %}'''

for file_path in html_files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '{% with product.images.all as images %}' in content:
        content = content.replace(old_pattern, new_pattern)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {os.path.basename(file_path)}')

