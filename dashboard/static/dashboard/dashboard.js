// dashboard.js - Dynamic Functions & AJAX Operations for Custom Admin Dashboard

document.addEventListener('DOMContentLoaded', function() {
    // 1. Mobile Sidebar Menu Toggle
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('dash-sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    function openSidebar() {
        sidebar.classList.add('open');
        if (sidebarOverlay) {
            sidebarOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        if (sidebarOverlay) {
            sidebarOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            if (sidebar.classList.contains('open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });

        // Close sidebar when clicking on overlay
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', function() {
                closeSidebar();
            });
        }

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
                if (!sidebar.contains(e.target) && e.target !== menuToggle) {
                    closeSidebar();
                }
            }
        });

        // Close on escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidebar.classList.contains('open')) {
                closeSidebar();
            }
        });
    }

    // 2. Light / Dark Theme Toggle
    const themeToggle = document.getElementById('dashThemeToggle');
    if (themeToggle) {
        // Initialize theme based on current localStorage or data attribute on HTML
        const currentTheme = localStorage.getItem('dash-theme') || document.documentElement.getAttribute('data-theme') || 'dark';
        document.documentElement.setAttribute('data-theme', currentTheme);
        
        themeToggle.addEventListener('click', function() {
            const activeTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', activeTheme);
            localStorage.setItem('dash-theme', activeTheme);
            showToast(`Switched to ${activeTheme} mode.`);
        });
    }

    // 3. Modals Open / Close Operations
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('open');
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('open');
        }
    };

    // Close modals when clicking on background overlay
    const modals = document.querySelectorAll('.modal-dash');
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('open');
            }
        });
    });

    // 4. AJAX: Toggle User Active Status
    window.toggleUserActive = function(userId, buttonElement) {
        const csrfToken = getCookie('csrftoken');
        const url = `/dashboard/users/${userId}/toggle-active/`;
        
        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast(data.message);
                
                // Update badge and button text inline
                const badge = document.getElementById(`user-status-badge-${userId}`);
                if (badge) {
                    if (data.is_active) {
                        badge.className = 'badge-pill badge-success';
                        badge.innerText = 'Active';
                        buttonElement.innerText = 'Deactivate';
                        buttonElement.className = 'btn-dash btn-outline btn-sm';
                    } else {
                        badge.className = 'badge-pill badge-danger';
                        badge.innerText = 'Suspended';
                        buttonElement.innerText = 'Activate';
                        buttonElement.className = 'btn-dash btn-accent btn-sm';
                    }
                }
            } else {
                showToast(data.message || 'Error occurred.', 'danger');
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Network error, please try again.', 'danger');
        });
    };

    // 5. Helper: Read Cookie by Name
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

    // 6. Inline Toast Notification System
    window.showToast = function(message, type = 'success') {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.style.position = 'fixed';
            container.style.bottom = '20px';
            container.style.right = '20px';
            container.style.zIndex = '9999';
            container.style.display = 'flex';
            container.style.flexDirection = 'column';
            container.style.gap = '10px';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.style.background = type === 'success' ? '#10b981' : type === 'danger' ? '#ef4444' : '#f59e0b';
        toast.style.color = '#ffffff';
        toast.style.padding = '12px 24px';
        toast.style.borderRadius = '6px';
        toast.style.fontSize = '0.85rem';
        toast.style.fontWeight = '600';
        toast.style.boxShadow = '0 10px 15px -3px rgba(0,0,0,0.1)';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
        toast.innerText = message;

        container.appendChild(toast);

        // Force reflow
        toast.offsetHeight;

        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 3000);
    };
});
