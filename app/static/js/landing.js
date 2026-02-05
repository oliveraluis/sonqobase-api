// Smooth scroll para links de navegación
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href === '#' || !href) return; // Ignorar # vacíos

        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Animación de aparición al hacer scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observar elementos para animación
document.querySelectorAll('.feature-card, .step, .pricing-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});

// Navbar transparente al hacer scroll
let lastScroll = 0;
const nav = document.querySelector('.nav');

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 100) {
        nav.style.background = 'rgba(10, 10, 15, 0.95)';
    } else {
        nav.style.background = 'rgba(10, 10, 15, 0.8)';
    }

    lastScroll = currentScroll;
});

// Copiar código al hacer click
document.querySelectorAll('.hero-code pre').forEach(pre => {
    pre.style.cursor = 'pointer';
    pre.title = 'Click to copy';

    pre.addEventListener('click', async () => {
        const code = pre.textContent;
        try {
            await navigator.clipboard.writeText(code);

            // Feedback visual
            const originalBorder = pre.parentElement.style.borderColor;
            pre.parentElement.style.borderColor = '#00ff88';

            setTimeout(() => {
                pre.parentElement.style.borderColor = originalBorder;
            }, 1000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    });
});

// ============================================
// CONTACT MODAL
// ============================================

const modal = document.getElementById('contact-modal');
const modalClose = document.querySelector('.modal-close');
const contactForm = document.getElementById('contact-form');
const formMessage = document.getElementById('form-message');

// Abrir modal
document.querySelectorAll('.open-contact-modal').forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        // Si el botón tiene data-plan, pre-seleccionar el plan
        const plan = btn.getAttribute('data-plan');
        if (plan) {
            document.getElementById('plan').value = plan;
        }
    });
});

// Cerrar modal
modalClose.addEventListener('click', () => {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
});

// Cerrar modal al hacer click fuera
window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
});

// Enviar formulario
contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value || null,
        country: document.getElementById('country').value || null,
        company: document.getElementById('company').value || null,
        interest: document.getElementById('interest').value,
        plan_interest: document.getElementById('plan').value,
    };

    try {
        const response = await fetch('/contact', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData),
        });

        const data = await response.json();

        if (response.ok) {
            // Éxito
            formMessage.textContent = data.message;
            formMessage.className = 'form-message success';
            formMessage.style.display = 'block';

            // Limpiar formulario
            contactForm.reset();

            // Cerrar modal después de 3 segundos
            setTimeout(() => {
                modal.style.display = 'none';
                document.body.style.overflow = 'auto';
                formMessage.style.display = 'none';
            }, 3000);
        } else {
            // Error
            formMessage.textContent = data.detail || 'Error al enviar el formulario';
            formMessage.className = 'form-message error';
            formMessage.style.display = 'block';
        }
    } catch (error) {
        console.error('Error:', error);
        formMessage.textContent = 'Error de conexión. Por favor intenta de nuevo.';
        formMessage.className = 'form-message error';
        formMessage.style.display = 'block';
    }
});

// ============================================
// LOAD PRICING DYNAMICALLY
// ============================================

async function loadPricing() {
    try {
        const response = await fetch('/pricing-data');
        const data = await response.json();

        if (data.plans && data.plans.length > 0) {
            updatePricingCards(data.plans);
        }
    } catch (error) {
        console.error('Error loading pricing:', error);
        // Mantener pricing hardcodeado si falla
    }
}

function updatePricingCards(plans) {
    const pricingGrid = document.getElementById('pricing-grid');
    if (!pricingGrid) return;

    // Mapear planes por nombre
    const planMap = {};
    plans.forEach(plan => {
        planMap[plan.name] = plan;
    });

    // Actualizar cada tarjeta
    const cards = pricingGrid.querySelectorAll('.pricing-card');
    cards.forEach((card, index) => {
        const planName = ['free', 'starter', 'pro'][index];
        const plan = planMap[planName];

        if (!plan) return;

        // Actualizar features dinámicamente
        const featuresList = card.querySelector('.plan-features');
        if (featuresList) {
            const retentionDays = Math.floor(plan.limits.retention_hours / 24);

            featuresList.innerHTML = `
                <li>✓ ${plan.limits.projects === 999999 ? 'Proyectos ilimitados' : plan.limits.projects + ' proyecto' + (plan.limits.projects > 1 ? 's' : '') + ' activo' + (plan.limits.projects > 1 ? 's' : '')}</li>
                <li>✓ ${plan.limits.reads_per_month.toLocaleString()} lecturas/mes</li>
                <li>✓ ${plan.limits.writes_per_month.toLocaleString()} escrituras/mes</li>
                <li>✓ ${plan.limits.rag_queries_per_month.toLocaleString()} consultas RAG/mes</li>
                <li>✓ PDFs hasta ${plan.limits.pdf_max_size_mb}MB</li>
                <li>✓ Duración: ${retentionDays} días</li>
                ${plan.features.includes('webhooks') ? '<li>✓ Webhooks</li>' : ''}
                ${plan.features.includes('priority_support') ? '<li>✓ Soporte prioritario</li>' : ''}
            `;
        }
    });
}

// Cargar pricing al cargar la página
document.addEventListener('DOMContentLoaded', loadPricing);

// ============================================
// CODE LANGUAGE TABS
// ============================================

document.querySelectorAll('.code-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const lang = tab.getAttribute('data-lang');
        const container = tab.closest('.hero-code');

        // Update active tab
        container.querySelectorAll('.code-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // Update active panel
        container.querySelectorAll('.code-panel').forEach(panel => {
            if (panel.getAttribute('data-lang') === lang) {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });
    });
});
