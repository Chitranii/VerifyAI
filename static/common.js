/* ============================================================
   VerifyAI — Shared Interactive Features
   ============================================================ */

// ---- Toast notifications ----
function createToastContainer() {
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
    return document.getElementById('toast-container');
}

function showToast(message, type = 'info', duration = 3500) {
    const container = createToastContainer();
    const icons = {
        success: '✓',
        error:   '✕',
        info:    'ℹ'
    };

    const toast = document.createElement('div');
    toast.className = 'toast ' + type;
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || 'ℹ'}</div>
        <div>${message}</div>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ---- Confetti celebration ----
function launchConfetti() {
    const colors = ['#6366f1', '#8b5cf6', '#22d3ee', '#34d399', '#fbbf24', '#f87171', '#ffffff'];
    const count = 80;

    for (let i = 0; i < count; i++) {
        const piece = document.createElement('div');
        piece.className = 'confetti-piece';
        piece.style.left = Math.random() * 100 + 'vw';
        piece.style.background = colors[Math.floor(Math.random() * colors.length)];
        piece.style.width = (Math.random() * 10 + 6) + 'px';
        piece.style.height = (Math.random() * 10 + 6) + 'px';
        piece.style.animationDuration = (Math.random() * 3 + 2) + 's';
        piece.style.animationDelay = (Math.random() * 0.5) + 's';
        piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
        document.body.appendChild(piece);

        setTimeout(() => piece.remove(), 5000);
    }
}

// ---- Navbar scroll shadow ----
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    const onScroll = () => {
        navbar.classList.toggle('scrolled', window.scrollY > 10);
    };
    window.addEventListener('scroll', onScroll);
    onScroll();
}

// ---- 3D tilt effect on plan cards ----
function initTilt() {
    const cards = document.querySelectorAll('.plan-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            card.style.transform = `translateY(-6px) rotateY(${x * 8}deg) rotateX(${y * -8}deg)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });
}

// ---- Animated counter for metrics ----
function initCounters() {
    const values = document.querySelectorAll('.metric-value[data-count]');
    values.forEach(el => {
        const target = parseFloat(el.dataset.count);
        const prefix = el.dataset.prefix || '';
        const suffix = el.dataset.suffix || '';
        const duration = 1200;
        const start = performance.now();

        function update(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = prefix + Math.round(target * eased) + suffix;
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    });
}

// ---- Staggered check-item animation ----
function initStaggered(selector) {
    const items = document.querySelectorAll(selector);
    items.forEach((item, i) => {
        item.style.animationDelay = (i * 0.1) + 's';
    });
}

// ---- Initialize on DOM ready ----
document.addEventListener('DOMContentLoaded', () => {
    initNavbar();
    initTilt();
    initCounters();
    initStaggered('.check-item');
});
