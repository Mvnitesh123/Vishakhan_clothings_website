/**
 * LUXE — Premium Fashion
 * Main JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
  initPreloader();
  initNavbar();
  initTheme();
  initSearch();
  initMobileDrawer();
  initHeroSlider();
  initProductTabs();
  initCartDrawer();
  initWishlist();
  initWishlistDrawer();
  initScrollReveal();
  initCustomDropdowns();
  initReviewForm();
});

/* ========== CUSTOM DROPDOWNS ========== */
function initCustomDropdowns() {
  document.querySelectorAll('.custom-dropdown').forEach(dropdown => {
    const trigger = dropdown.querySelector('.dropdown-trigger');
    const menu = dropdown.querySelector('.dropdown-menu');
    if (!trigger || !menu) return;
    
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      document.querySelectorAll('.dropdown-menu').forEach(m => {
        if (m !== menu) m.style.display = 'none';
      });
      menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
    });

    menu.addEventListener('click', (e) => {
      e.stopPropagation();
    });
  });

  document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown-menu').forEach(m => m.style.display = 'none');
  });
}

/* ========== SCROLL REVEAL ========== */
function initScrollReveal() {
  const reveals = document.querySelectorAll('.reveal');
  if (!reveals.length) return;

  const observerOptions = {
    threshold: 0.15,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
        // Stop observing once revealed so it stays loaded
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  reveals.forEach(r => observer.observe(r));
}

/* ========== PRELOADER ========== */
function initPreloader() {
  const preloader = document.getElementById('preloader');
  const bar = document.querySelector('.preloader-fill');
  
  if (!preloader) return;

  // Simulate loading
  let width = 0;
  const interval = setInterval(() => {
    width += Math.random() * 30;
    if (width > 100) {
      width = 100;
      clearInterval(interval);
      setTimeout(() => {
        preloader.style.backgroundColor = 'transparent';
        preloader.style.opacity = '0';
        preloader.style.visibility = 'hidden';
      }, 500);
    }
    if (bar) bar.style.width = width + '%';
  }, 100);
}

/* ========== NAVBAR ========== */
function initNavbar() {
  const navbar = document.getElementById('mainNavbar');
  if (!navbar) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      navbar.classList.add('sticky');
    } else {
      navbar.classList.remove('sticky');
    }
  });
}

/* ========== THEME TOGGLE ========== */
function initTheme() {
  const themeToggle = document.getElementById('themeToggle');
  const mobileThemeToggle = document.getElementById('mobileThemeToggle'); // drawer checkbox toggle
  const mnavThemeToggle = document.getElementById('mnavThemeToggle');     // mobile nav button toggle
  const html = document.documentElement;

  const savedTheme = localStorage.getItem('theme') || 'light';
  html.setAttribute('data-theme', savedTheme);
  if (mobileThemeToggle) mobileThemeToggle.checked = savedTheme === 'dark';

  function toggle() {
    const current = html.getAttribute('data-theme');
    const target = current === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', target);
    localStorage.setItem('theme', target);
    if (mobileThemeToggle) mobileThemeToggle.checked = target === 'dark';
  }

  if (themeToggle) themeToggle.addEventListener('click', toggle);
  if (mnavThemeToggle) mnavThemeToggle.addEventListener('click', toggle);
  if (mobileThemeToggle) mobileThemeToggle.addEventListener('change', toggle);
}

/* ========== SEARCH OVERLAY ========== */
function initSearch() {
  const trigger = document.getElementById('searchTrigger');
  const overlay = document.getElementById('searchOverlay');
  const close = document.getElementById('searchClose');
  const input = overlay?.querySelector('.search-input');

  if (!trigger || !overlay) return;

  trigger.addEventListener('click', () => {
    overlay.classList.add('active');
    setTimeout(() => input?.focus(), 400);
  });

  close.addEventListener('click', () => {
    overlay.classList.remove('active');
  });

  // Close on Escape
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.classList.contains('active')) {
      overlay.classList.remove('active');
    }
  });
}

/* ========== MOBILE DRAWER ========== */
function initMobileDrawer() {
  // Support both the desktop hamburger (#hamburgerBtn) and the new mobile nav hamburger (#mobileHamburger)
  const btns = [
    document.getElementById('hamburgerBtn'),
    document.getElementById('mobileHamburger'),
  ].filter(Boolean);

  const drawer = document.getElementById('mobileDrawer');
  const overlay = document.getElementById('mobileOverlay');
  const close = document.getElementById('drawerClose');

  if (!drawer) return;

  const openDrawer = () => {
    drawer.classList.add('active');
    overlay.classList.add('active');
  };

  btns.forEach(btn => btn.addEventListener('click', openDrawer));

  const closeDrawer = () => {
    drawer.classList.remove('active');
    overlay.classList.remove('active');
  };

  if (close) close.addEventListener('click', closeDrawer);
  if (overlay) overlay.addEventListener('click', closeDrawer);

  // Submenu toggles
  const subTriggers = drawer.querySelectorAll('.submenu-trigger');
  subTriggers.forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const parent = trigger.parentElement;
      parent.classList.toggle('open');
      
      // Close other submenus (optional, for accordion effect)
      subTriggers.forEach(other => {
        if (other !== trigger) other.parentElement.classList.remove('open');
      });
    });
  });
}

/* ========== HERO SLIDER ========== */
function initHeroSlider() {
  const slider = document.getElementById('heroSlider');
  if (!slider) return;

  const slides = slider.querySelectorAll('.hero-slide');
  const prev = document.getElementById('heroPrev');
  const next = document.getElementById('heroNext');
  const dots = document.querySelectorAll('.slider-dots .dot');
  
  let current = 0;
  let interval;

  function showSlide(index) {
    slides.forEach(s => s.classList.remove('active'));
    dots.forEach(d => d.classList.remove('active'));
    
    current = (index + slides.length) % slides.length;
    slides[current].classList.add('active');
    if (dots[current]) dots[current].classList.add('active');
  }

  function nextSlide() { showSlide(current + 1); }
  function prevSlide() { showSlide(current - 1); }

  if (next) next.addEventListener('click', () => {
    nextSlide();
    resetInterval();
  });
  
  if (prev) prev.addEventListener('click', () => {
    prevSlide();
    resetInterval();
  });

  dots.forEach(dot => {
    dot.addEventListener('click', () => {
      showSlide(parseInt(dot.dataset.index));
      resetInterval();
    });
  });

  function startInterval() {
    interval = setInterval(nextSlide, 6000);
  }

  function resetInterval() {
    clearInterval(interval);
    startInterval();
  }

  startInterval();
}

/* ========== PRODUCT TABS ========== */
function initProductTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  const grid = document.getElementById('productsGrid');
  
  if (!tabs.length || !grid) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const filter = tab.dataset.filter;
      
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const cards = grid.querySelectorAll('.product-card');
      cards.forEach(card => {
        const productFilters = card.dataset.filter ? card.dataset.filter.split(' ') : [];
        if (filter === 'all' || productFilters.includes(filter)) {
          card.style.display = 'block';
          card.style.animation = 'fadeInUp 0.6s ease forwards';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });
}

/* ========== COOKIE HELPER & AJAX ========== */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

async function ajaxPOST(url, data) {
  const csrftoken = getCookie('csrftoken');
  const formData = new FormData();
  for (const key in data) {
    formData.append(key, data[key]);
  }
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrftoken
      },
      body: formData
    });
    if (response.status === 401) {
      return { success: false, login_required: true, message: 'Sign in or sign up first' };
    }
    return await response.json();
  } catch (error) {
    console.error('AJAX Error:', error);
    return { success: false, message: 'Network error occurred' };
  }
}

// Update Cart Count indicators across navbar
function updateCartBadges(count) {
  const badges = document.querySelectorAll('.badge--cart');
  badges.forEach(b => {
    b.textContent = count;
    b.style.display = count > 0 ? 'flex' : 'none';
  });
}

// Update Wishlist Count indicators across navbar
function updateWishlistBadges(count) {
  const badges = document.querySelectorAll('.action-btn .badge:not(.badge--cart)');
  badges.forEach(b => {
    b.textContent = count;
    b.style.display = count > 0 ? 'flex' : 'none';
  });
}

// Auto open auth drawer helper
function triggerAuthDrawerOpen() {
  const authDrawer = document.getElementById('authDrawer');
  const authOverlay = document.getElementById('authOverlay');
  if (authDrawer && authOverlay) {
    authDrawer.classList.add('active');
    authOverlay.classList.add('active');
  }
}

/* ========== CART DRAWER RENDER ========== */
async function renderCart() {
  const cartItemsContainer = document.getElementById('cartItems');
  const cartItemCount = document.getElementById('cartItemCount');
  const cartTotal = document.getElementById('cartTotal');
  if (!cartItemsContainer) return;

  try {
    const response = await fetch('/cart/get/');
    if (response.status === 401) {
      cartItemsContainer.innerHTML = `
        <div class="cart-empty" style="text-align:center; padding:40px 20px;">
          <p>Please log in to view your bag.</p>
        </div>`;
      return;
    }
    const data = await response.json();
    if (data.success) {
      updateCartBadges(data.cart_count);
      if (cartItemCount) cartItemCount.textContent = `(${data.cart_count})`;
      if (cartTotal) cartTotal.textContent = `₹${data.subtotal}`;

      if (data.items.length === 0) {
        cartItemsContainer.innerHTML = `
          <div class="cart-empty">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
            <p>Your bag is empty</p>
            <a href="/products/" class="btn" style="text-decoration:none;">Start Shopping</a>
          </div>`;
      } else {
        let itemsHtml = '';
        data.items.forEach(item => {
          let itemControlsHtml = '';
          if (item.stock <= 0) {
            itemControlsHtml = `
              <span style="font-size: 0.7rem; font-weight: 700; color: var(--error); background: rgba(214, 40, 40, 0.1); padding: 4px 10px; border-radius: 4px; border: 1px solid var(--error); letter-spacing: 0.05em; text-transform: uppercase;">Out of Stock</span>
              <span style="font-size: 14px; font-weight: 700; color: var(--text-muted); text-decoration: line-through;">₹${item.total_price}</span>
            `;
          } else {
            itemControlsHtml = `
              <!-- Modern compact quantity selector -->
              <div class="cart-qty-selector" style="display: flex; align-items: center; border: 1px solid var(--border); border-radius: 4px; overflow: hidden; background: var(--bg-main);">
                <button class="cart-qty-btn cart-qty-minus" data-item-id="${item.id}" style="border: none; background: transparent; width: 24px; height: 24px; font-size: 14px; color: var(--text-main); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s;">−</button>
                <span class="cart-qty-val" style="width: 24px; text-align: center; font-size: 12px; font-weight: 600; color: var(--text-main);">${item.quantity}</span>
                <button class="cart-qty-btn cart-qty-plus" data-item-id="${item.id}" style="border: none; background: transparent; width: 24px; height: 24px; font-size: 14px; color: var(--text-main); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s;">+</button>
              </div>
              <div style="display: flex; flex-direction: column; align-items: flex-end;">
                <span style="font-size: 11px; color: var(--text-muted); margin-bottom: 2px;">${item.quantity} × ₹${item.price}</span>
                <span style="font-size: 14px; font-weight: 700; color: var(--text-main);">₹${item.total_price}</span>
              </div>
            `;
          }

          itemsHtml += `
            <div class="cart-item" style="display: flex; gap: 15px; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 15px; align-items: center; position: relative;">
              <div style="width: 70px; height: 90px; border-radius: 4px; overflow: hidden; flex-shrink: 0; background: var(--bg-offset, #f5f5f5);">
                <img src="${item.image_url}" alt="${item.product_name}" style="width: 100%; height: 100%; object-fit: cover;" />
              </div>
              <div style="flex: 1; min-width: 0;">
                <h4 style="font-weight: 600; font-size: 14px; color: var(--text-main); margin: 0 0 4px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                  <a href="/product/${item.product_slug}/" style="color: inherit; text-decoration: none; transition: color 0.2s;" onmouseover="this.style.color='var(--accent)'" onmouseout="this.style.color='inherit'">${item.product_name}</a>
                </h4>
                <p style="font-size: 11px; color: var(--text-muted); margin: 0 0 8px 0;">Size: ${item.size} | Color: ${item.color}</p>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px; gap: 10px; width: 100%;">
                  ${itemControlsHtml}
                </div>
              </div>
              <button class="remove-cart-item" data-id="${item.id}" style="position: absolute; top: 0; right: 0; background: transparent; border: none; font-size: 22px; line-height: 1; color: var(--text-muted); cursor: pointer; transition: color 0.2s;">&times;</button>
            </div>`;
        });
        cartItemsContainer.innerHTML = itemsHtml;
        bindCartQtyEvents(cartItemsContainer);

        // Wire remove buttons
        const removeBtns = cartItemsContainer.querySelectorAll('.remove-cart-item');
        removeBtns.forEach(btn => {
          btn.addEventListener('click', async function(e) {
            e.preventDefault();
            const itemId = this.getAttribute('data-id');
            const res = await ajaxPOST('/cart/remove/', { 'item_id': itemId });
            if (res.success) {
              showToast(res.message);
              renderCart();
            }
          });
        });
      }

      // Real-time synchronization of Product Details page indicators
      const productHeader = document.querySelector('.product-details h1');
      if (productHeader) {
        const currentProductName = productHeader.textContent.trim();
        const isProductInCart = data.items.some(item => item.product_name === currentProductName);
        const alertBlock = document.getElementById('cartStatusAlert');
        if (alertBlock) {
          alertBlock.style.display = isProductInCart ? 'flex' : 'none';
        }
        
        // Select all variant cards
        const variantCards = document.querySelectorAll('.selectable-variant');
        if (variantCards.length > 0) {
          const inCartVariantIds = data.items.map(item => String(item.variant_id));
          variantCards.forEach(card => {
            const vId = card.getAttribute('data-variant-id');
            const inBagBadge = card.querySelector('.in-bag-badge');
            if (inBagBadge) {
              if (inCartVariantIds.includes(vId)) {
                inBagBadge.style.display = 'inline-block';
                card.setAttribute('data-in-cart', 'true');
              } else {
                inBagBadge.style.display = 'none';
                card.setAttribute('data-in-cart', 'false');
              }
            }
          });
        }
      }
    }
  } catch (error) {
    console.error('Error fetching cart:', error);
  }
}

/* ========== BIND CART QUANTITY EVENTS ========== */
function bindCartQtyEvents(container) {
  if (!container) return;

  // Plus Buttons
  container.querySelectorAll('.cart-qty-plus').forEach(btn => {
    btn.addEventListener('click', async function(e) {
      e.preventDefault();
      const itemId = this.getAttribute('data-item-id');
      const valSpan = this.parentElement.querySelector('.cart-qty-val');
      const currentQty = parseInt(valSpan.textContent) || 1;
      const newQty = currentQty + 1;
      
      const res = await ajaxPOST('/cart/update/', { 'item_id': itemId, 'quantity': newQty });
      if (res.success) {
        valSpan.textContent = newQty;
        renderCart();
        if (window.location.pathname.includes('/profile/')) {
          setTimeout(() => { window.location.reload(); }, 500);
        }
      } else {
        showToast(res.message);
      }
    });
  });

  // Minus Buttons
  container.querySelectorAll('.cart-qty-minus').forEach(btn => {
    btn.addEventListener('click', async function(e) {
      e.preventDefault();
      const itemId = this.getAttribute('data-item-id');
      const valSpan = this.parentElement.querySelector('.cart-qty-val');
      const currentQty = parseInt(valSpan.textContent) || 1;
      if (currentQty <= 1) {
        const res = await ajaxPOST('/cart/remove/', { 'item_id': itemId });
        if (res.success) {
          showToast(res.message);
          renderCart();
          if (window.location.pathname.includes('/profile/')) {
            setTimeout(() => { window.location.reload(); }, 500);
          }
        }
        return;
      }
      
      const newQty = currentQty - 1;
      const res = await ajaxPOST('/cart/update/', { 'item_id': itemId, 'quantity': newQty });
      if (res.success) {
        valSpan.textContent = newQty;
        renderCart();
        if (window.location.pathname.includes('/profile/')) {
          setTimeout(() => { window.location.reload(); }, 500);
        }
      } else {
        showToast(res.message);
      }
    });
  });
}

/* ========== CART DRAWER ========== */
function initCartDrawer() {
  const cartBtns = document.querySelectorAll('.cart-btn');
  const drawer = document.getElementById('cartDrawer');
  const overlay = document.getElementById('cartOverlay');
  const close = document.getElementById('cartClose');
  const addBtns = document.querySelectorAll('.add-to-cart-btn');
  const detailAddBtn = document.querySelector('.detail-add-to-bag');

  if (!drawer) return;

  const openDrawer = (e) => {
    if (e) e.preventDefault();
    drawer.classList.add('active');
    overlay.classList.add('active');
    renderCart();
  };

  const closeDrawer = () => {
    drawer.classList.remove('active');
    overlay.classList.remove('active');
  };

  cartBtns.forEach(btn => btn.addEventListener('click', openDrawer));
  if (close) close.addEventListener('click', closeDrawer);
  if (overlay) overlay.addEventListener('click', closeDrawer);

  // Wire any initial server-rendered remove buttons
  const initialRemoveBtns = document.querySelectorAll('.remove-cart-item');
  initialRemoveBtns.forEach(btn => {
    btn.addEventListener('click', async function(e) {
      e.preventDefault();
      const itemId = this.getAttribute('data-id');
      const res = await ajaxPOST('/cart/remove/', { 'item_id': itemId });
      if (res.success) {
        showToast(res.message);
        renderCart();
        if (window.location.pathname.includes('/profile/')) {
          setTimeout(() => {
            window.location.reload();
          }, 500);
        }
      }
    });
  });

  // Wire any initial server-rendered quantity buttons
  const cartItemsContainer = document.getElementById('cartItems');
  if (cartItemsContainer) {
    bindCartQtyEvents(cartItemsContainer);
  }
  const profileTabContent = document.querySelector('.profile-tab-content');
  if (profileTabContent) {
    bindCartQtyEvents(profileTabContent);
  }

  // Listing Pages Direct Add to Bag Button Handler
  addBtns.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const productId = btn.getAttribute('data-product-id');
      
      const res = await ajaxPOST('/cart/add/', { 'product_id': productId, 'quantity': 1 });
      if (res.success) {
        showToast(res.message);
        updateCartBadges(res.cart_count);
        openDrawer();
      } else {
        showToast(res.message);
        if (res.login_required) {
          setTimeout(triggerAuthDrawerOpen, 500);
        }
      }
    });
  });

  // Product Details Page Custom Add to Bag Button Handler
  if (detailAddBtn) {
    detailAddBtn.addEventListener('click', async function(e) {
      e.preventDefault();
      const productId = detailAddBtn.getAttribute('data-product-id');

      // Step 1: Validate size is selected
      const activeSizeCapsule = document.querySelector('.size-capsule.active');
      if (!activeSizeCapsule) {
        showToast('Please select a size first');
        return;
      }

      // Step 2: Resolve size value (handle CUSTOM)
      let size = activeSizeCapsule.getAttribute('data-size');
      if (size === 'CUSTOM') {
        const customInput = document.getElementById('customSizeInput');
        if (!customInput || !customInput.value.trim()) {
          showToast('Please enter your custom size details');
          return;
        }
        size = customInput.value.trim();
      }

      // Step 3: Validate color/variant is selected
      const variantInput = document.getElementById('selectedVariantId');
      const variantId = variantInput ? variantInput.value : '';
      if (!variantId) {
        showToast('Please select a color first');
        return;
      }

      const qtyInput = document.getElementById('productQty');
      const quantity = qtyInput ? parseInt(qtyInput.value) || 1 : 1;

      const res = await ajaxPOST('/cart/add/', {
        'variant_id': variantId,
        'product_id': productId,
        'quantity': quantity,
        'size': size
      });

      if (res.success) {
        showToast(res.message);
        updateCartBadges(res.cart_count);
        openDrawer();
      } else {
        showToast(res.message);
        if (res.login_required) {
          setTimeout(triggerAuthDrawerOpen, 500);
        }
      }
    });
  }
}

/* ========== TOAST NOTIFICATION ========== */
function showToast(message) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  
  container.appendChild(toast);
  
  // Trigger animation
  setTimeout(() => toast.classList.add('active'), 10);
  
  // Remove after 3s
  setTimeout(() => {
    toast.classList.remove('active');
    setTimeout(() => toast.remove(), 400);
  }, 3000);
}

/* ========== WISHLIST ========== */
function initWishlist() {
  const btns = document.querySelectorAll('.wishlist-btn, .detail-wishlist-btn');
  btns.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const productId = btn.getAttribute('data-product-id');
      if (!productId) return;

      const res = await ajaxPOST('/wishlist/toggle/', { 'product_id': productId });
      if (res.success) {
        showToast(res.message);
        updateWishlistBadges(res.wishlist_count);
        
        // Dynamic Wishlist Drawer refresh
        if (typeof renderWishlist === 'function') {
          renderWishlist();
        }
        
        // Toggle visual active state
        btn.classList.toggle('active', res.added);
        const svg = btn.querySelector('svg');
        if (svg) {
          svg.style.fill = res.added ? 'var(--error)' : 'none';
          svg.style.stroke = res.added ? 'var(--error)' : 'currentColor';
        }
      } else {
        showToast(res.message);
        if (res.login_required) {
          setTimeout(triggerAuthDrawerOpen, 500);
        }
      }
    });
  });
}

/* ========== WISHLIST DRAWER ========== */
function initWishlistDrawer() {
  const wishlistBtns = document.querySelectorAll('.nav-wishlist-btn');
  const drawer = document.getElementById('wishlistDrawer');
  const overlay = document.getElementById('wishlistOverlay');
  const close = document.getElementById('wishlistClose');

  if (!drawer) return;

  const openDrawer = (e) => {
    if (e) e.preventDefault();
    drawer.classList.add('active');
    overlay.classList.add('active');
    renderWishlist();
  };

  const closeDrawer = () => {
    drawer.classList.remove('active');
    overlay.classList.remove('active');
  };

  wishlistBtns.forEach(btn => btn.addEventListener('click', openDrawer));
  if (close) close.addEventListener('click', closeDrawer);
  if (overlay) overlay.addEventListener('click', closeDrawer);

  // Wire any initial server-rendered remove buttons
  const initialRemoveBtns = document.querySelectorAll('#wishlistItems .remove-wishlist-item');
  initialRemoveBtns.forEach(btn => {
    btn.addEventListener('click', async function(e) {
      e.preventDefault();
      const productId = this.getAttribute('data-product-id');
      const res = await ajaxPOST('/wishlist/toggle/', { 'product_id': productId });
      if (res.success) {
        showToast(res.message);
        renderWishlist();
        // Update product detail page active state if matching this product
        const detailBtn = document.querySelector(`.detail-wishlist-btn[data-product-id="${productId}"]`);
        if (detailBtn) {
          detailBtn.classList.remove('active');
          const svg = detailBtn.querySelector('svg');
          if (svg) {
            svg.style.fill = 'none';
            svg.style.stroke = 'currentColor';
          }
        }
      }
    });
  });
}

/* ========== WISHLIST DRAWER RENDER ========== */
async function renderWishlist() {
  const container = document.getElementById('wishlistItems');
  const itemCount = document.getElementById('wishlistItemCount');
  if (!container) return;

  try {
    const response = await fetch('/wishlist/get/');
    if (response.status === 401) {
      container.innerHTML = `
        <div class="cart-empty" style="text-align:center; padding:40px 20px;">
          <p>Please log in to view your wishlist.</p>
        </div>`;
      return;
    }
    const data = await response.json();
    if (data.success) {
      updateWishlistBadges(data.wishlist_count);
      if (itemCount) itemCount.textContent = `(${data.wishlist_count})`;

      if (data.items.length === 0) {
        container.innerHTML = `
          <div class="cart-empty">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
            <p>Your wishlist is empty</p>
            <a href="/products/" class="btn" style="text-decoration: none;">Explore Products</a>
          </div>`;
      } else {
        let html = '';
        data.items.forEach(item => {
          html += `
            <div class="cart-item wishlist-item" style="display: flex; gap: 15px; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 15px; align-items: center; position: relative;" data-product-id="${item.product_id}">
              <div style="width: 70px; height: 90px; border-radius: 4px; overflow: hidden; flex-shrink: 0; background: var(--bg-offset, #f5f5f5);">
                <img src="${item.image_url}" alt="${item.product_name}" style="width: 100%; height: 100%; object-fit: cover;" />
              </div>
              <div style="flex: 1; min-width: 0;">
                <h4 style="font-weight: 600; font-size: 14px; color: var(--text-main); margin: 0 0 4px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                  <a href="/product/${item.product_slug}/" style="color: inherit; text-decoration: none; transition: color 0.2s;" onmouseover="this.style.color='var(--accent)'" onmouseout="this.style.color='inherit'">${item.product_name}</a>
                </h4>
                <p style="font-size: 11px; color: var(--text-muted); margin: 0 0 8px 0;">Stock: ${item.stock_status}</p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-size: 14px; font-weight: 700; color: var(--text-main);">₹${item.price}</span>
                </div>
              </div>
              <button class="remove-wishlist-item" data-product-id="${item.product_id}" style="position: absolute; top: 0; right: 0; background: transparent; border: none; font-size: 22px; line-height: 1; color: var(--text-muted); cursor: pointer; transition: color 0.2s;">&times;</button>
            </div>`;
        });
        container.innerHTML = html;

        // Wire remove buttons
        const removeBtns = container.querySelectorAll('.remove-wishlist-item');
        removeBtns.forEach(btn => {
          btn.addEventListener('click', async function(e) {
            e.preventDefault();
            const productId = this.getAttribute('data-product-id');
            const res = await ajaxPOST('/wishlist/toggle/', { 'product_id': productId });
            if (res.success) {
              showToast(res.message);
              renderWishlist();
              
              // Update product detail page active state if matching this product
              const detailBtn = document.querySelector(`.detail-wishlist-btn[data-product-id="${productId}"]`);
              if (detailBtn) {
                detailBtn.classList.remove('active');
                const svg = detailBtn.querySelector('svg');
                if (svg) {
                  svg.style.fill = 'none';
                  svg.style.stroke = 'currentColor';
                }
              }
            }
          });
        });
      }
    }
  } catch (error) {
    console.error('Error fetching wishlist:', error);
  }
}

/* ========== INTERACTIVE REVIEW FORM ========== */
function initReviewForm() {
  const writeReviewBtn = document.getElementById('writeReviewBtn');
  const cancelReviewBtn = document.getElementById('cancelReviewBtn');
  const formContainer = document.getElementById('writeReviewFormContainer');
  const reviewForm = document.getElementById('reviewSubmitForm');
  const rateStars = document.querySelectorAll('.rate-star');
  const ratingInput = document.getElementById('selectedReviewRating');

  if (!reviewForm) return;

  // Toggle form
  if (writeReviewBtn && formContainer) {
    writeReviewBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const isHidden = window.getComputedStyle(formContainer).display === 'none';
      formContainer.style.display = isHidden ? 'block' : 'none';
      if (isHidden) {
        formContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  }

  if (cancelReviewBtn && formContainer) {
    cancelReviewBtn.addEventListener('click', (e) => {
      e.preventDefault();
      formContainer.style.display = 'none';
    });
  }

  // Star selector logic
  let currentSelectedRating = parseInt(ratingInput.value) || 0;

  const updateStarColors = (rating) => {
    rateStars.forEach(star => {
      const starVal = parseInt(star.getAttribute('data-rating')) || 0;
      if (rating > 0 && starVal <= rating) {
        star.style.color = '#fbbf24';
      } else {
        star.style.color = '#ddd';
      }
    });
  };

  // Initial colors
  updateStarColors(currentSelectedRating);

  rateStars.forEach(star => {
    // Hover in
    star.addEventListener('mouseover', function() {
      const rating = parseInt(this.getAttribute('data-rating')) || 0;
      updateStarColors(rating);
    });

    // Hover out (revert to clicked)
    star.addEventListener('mouseout', function() {
      updateStarColors(currentSelectedRating);
    });

    // Click to select
    star.addEventListener('click', function() {
      currentSelectedRating = parseInt(this.getAttribute('data-rating')) || 0;
      ratingInput.value = currentSelectedRating;
      updateStarColors(currentSelectedRating);
    });
  });

  // Submit form via AJAX
  reviewForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    const commentField = document.getElementById('reviewCommentField');
    const comment = commentField ? commentField.value.trim() : '';
    const rating = ratingInput ? ratingInput.value : '';
    const productId = reviewForm.querySelector('input[name="product_id"]').value;

    const res = await ajaxPOST('/product/review/', {
      'product_id': productId,
      'rating': rating,
      'comment': comment
    });

    if (res.success) {
      showToast(res.message);
      if (formContainer) formContainer.style.display = 'none';
      if (commentField) commentField.value = '';
      
      // Smooth page refresh after a short delay so the toast is visible
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    } else {
      showToast(res.message);
    }
  });

  // Handle review deletion
  const deleteBtns = document.querySelectorAll('.delete-review-btn');
  deleteBtns.forEach(btn => {
    btn.addEventListener('click', async function(e) {
      e.preventDefault();
      if (!confirm('Are you sure you want to delete your review? This action cannot be undone.')) {
        return;
      }
      
      const productId = this.getAttribute('data-product-id');
      const res = await ajaxPOST('/product/review/delete/', {
        'product_id': productId
      });
      
      if (res.success) {
        showToast(res.message);
        setTimeout(() => {
          window.location.reload();
        }, 1200);
      } else {
        showToast(res.message);
      }
    });
  });
}



