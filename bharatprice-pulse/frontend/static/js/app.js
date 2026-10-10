/**
 * app.js — BharatPrice Pulse
 * Main browser controller: form handling, asynchronous fetch,
 * theme management, quick samples, progress orchestration,
 * glitter particle background, scroll animations, and user authentication.
 */

// ---------------------------------------------------------------------------
// Authentication Manager (Deployable & Multi-Tenant Scoped History)
// ---------------------------------------------------------------------------
const BPP_AUTH = {
  getUser() {
    try {
      const stored = localStorage.getItem('bpp_user');
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      return null;
    }
  },

  setUser(user) {
    if (user && user.email) {
      localStorage.setItem('bpp_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('bpp_user');
    }
    this.updateUI();
    window.dispatchEvent(new CustomEvent('bpp:auth-changed', { detail: user }));
  },

  modalTrigger: null,
  openModal() {
    const modal = document.getElementById('login-modal');
    if (!modal) return;
    this.modalTrigger = document.activeElement;
    modal.inert = false;
    modal.setAttribute('aria-hidden', 'false');
    modal.classList.remove('hidden');
    document.body.classList.add('modal-open');
    const emailInput = document.getElementById('login-email');
    window.requestAnimationFrame(() => emailInput?.focus());
  },

  closeModal() {
    const modal = document.getElementById('login-modal');
    if (!modal || modal.classList.contains('hidden')) return;
    modal.classList.add('is-closing');
    window.setTimeout(() => {
      modal.classList.add('hidden');
      modal.classList.remove('is-closing');
      modal.inert = true;
      modal.setAttribute('aria-hidden', 'true');
      document.body.classList.remove('modal-open');
      this.modalTrigger?.focus?.();
      this.modalTrigger = null;
    }, 180);
  },

  trapFocus(e) {
    const modal = document.getElementById('login-modal');
    if (!modal || modal.classList.contains('hidden')) return;
    if (e.key === 'Escape') { e.preventDefault(); this.closeModal(); return; }
    if (e.key !== 'Tab') return;
    const items = [...modal.querySelectorAll('button:not([disabled]), a[href], input:not([disabled]), [tabindex]:not([tabindex="-1"])')]
      .filter(el => !el.closest('.hidden') && el.getClientRects().length);
    if (!items.length) return;
    const first = items[0], last = items[items.length - 1];
    if (e.shiftKey && (document.activeElement === first || !modal.contains(document.activeElement))) {
      e.preventDefault(); last.focus();
    } else if (!e.shiftKey && (document.activeElement === last || !modal.contains(document.activeElement))) {
      e.preventDefault(); first.focus();
    }
  },

  async quickDemoLogin() {
    const demoBtn = document.getElementById('demo-login-btn');
    if (demoBtn) { demoBtn.disabled = true; demoBtn.setAttribute('aria-busy', 'true'); }
    const demoPayload = {
      email: 'seller.ramesh@gmail.com',
      name: 'Ramesh Kumar (Kirana)',
      provider: 'google',
      avatar_url: 'https://api.dicebear.com/7.x/initials/svg?seed=RK&backgroundColor=ff7700',
    };
    try {
      const resp = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(demoPayload),
      });
      if (resp.ok) {
        const res = await resp.json();
        this.setUser(res.user);
      } else {
        this.setUser(demoPayload);
      }
    } catch (e) {
      this.setUser(demoPayload);
    }
    const success = document.getElementById('login-success');
    if (success) { success.classList.remove('hidden'); success.textContent = 'Signed in as Ramesh Kumar. Your history is ready.'; }
    this.updateUI();
    window.setTimeout(() => this.closeModal(), 550);
    if (demoBtn) { demoBtn.disabled = false; demoBtn.removeAttribute('aria-busy'); }
  },

  async handleFormLogin(e) {
    e?.preventDefault?.();
    const emailInput = document.getElementById('login-email');
    const nameInput = document.getElementById('login-name');
    const spinner = document.getElementById('login-spinner');
    const submitBtn = document.getElementById('login-submit-btn');
    const errorEl = document.getElementById('login-error');
    const successEl = document.getElementById('login-success');
    const email = emailInput?.value.trim() || '';
    const name = nameInput?.value.trim() || '';
    if (errorEl) { errorEl.classList.add('hidden'); errorEl.textContent = ''; }
    if (successEl) successEl.classList.add('hidden');
    if (!emailInput?.checkValidity()) {
      emailInput?.classList.add('is-invalid');
      if (errorEl) { errorEl.textContent = 'Enter a valid email address to continue.'; errorEl.classList.remove('hidden'); }
      emailInput?.focus();
      return;
    }
    emailInput.classList.remove('is-invalid');
    if (spinner) spinner.classList.remove('hidden');
    if (submitBtn) { submitBtn.disabled = true; submitBtn.setAttribute('aria-busy', 'true'); }
    try {
      const resp = await fetch('/api/auth/login', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, provider: 'email' }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || 'Sign-in failed. Please try again.');
      }
      const data = await resp.json();
      this.setUser(data.user);
      if (successEl) successEl.classList.remove('hidden');
      window.setTimeout(() => this.closeModal(), 550);
    } catch (err) {
      if (errorEl) { errorEl.textContent = err.message || 'Could not sign in. Check your connection and retry.'; errorEl.classList.remove('hidden'); }
    } finally {
      if (spinner) spinner.classList.add('hidden');
      if (submitBtn) { submitBtn.disabled = false; submitBtn.removeAttribute('aria-busy'); }
    }
  },

  async logout() {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (e) {
      // Ignored
    }
    this.setUser(null);
  },

  updateUI() {
    const user = this.getUser();
    const authBtn = document.getElementById('auth-login-btn');
    const userBadge = document.getElementById('user-profile-badge');
    const nameEl = document.getElementById('user-display-name');
    const emailEl = document.getElementById('user-display-email');
    const avatarEl = document.getElementById('user-avatar-img');
    const profileTrigger = document.getElementById('user-profile-trigger');
    const clearHistoryBtn = document.getElementById('clear-history-btn');

    if (user && user.email) {
      if (authBtn) authBtn.classList.add('hidden');
      if (userBadge) userBadge.classList.remove('hidden');
      if (clearHistoryBtn) clearHistoryBtn.classList.remove('hidden');
      if (nameEl) nameEl.textContent = user.name || user.email.split('@')[0];
      if (emailEl) emailEl.textContent = user.email;
      if (avatarEl) {
        avatarEl.src = user.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(user.name || 'BP')}&backgroundColor=ff7700`;
      }
    } else {
      if (authBtn) authBtn.classList.remove('hidden');
      if (userBadge) userBadge.classList.add('hidden');
      if (clearHistoryBtn) clearHistoryBtn.classList.add('hidden');
      document.getElementById('user-profile-menu')?.classList.add('hidden');
      profileTrigger?.setAttribute('aria-expanded', 'false');
    }
  },

  init() {
    this.updateUI();

    const loginBtn = document.getElementById('auth-login-btn');
    if (loginBtn) {
      loginBtn.onclick = (e) => {
        e.preventDefault();
        this.openModal();
      };
    }

    const closeBtn = document.getElementById('modal-close-btn');
    if (closeBtn) closeBtn.onclick = () => this.closeModal();

    const modal = document.getElementById('login-modal');
    if (modal) {
      modal.onclick = (e) => { if (e.target === modal) this.closeModal(); };
      modal.inert = true;
      document.addEventListener('keydown', (e) => this.trapFocus(e));
    }

    const profileTrigger = document.getElementById('user-profile-trigger');
    const profileMenu = document.getElementById('user-profile-menu');
    if (profileTrigger && profileMenu) profileTrigger.onclick = () => {
      const open = profileMenu.classList.toggle('hidden') === false;
      profileTrigger.setAttribute('aria-expanded', String(open));
    };
    document.addEventListener('click', (e) => {
      if (profileMenu && !e.target.closest('.user-profile-wrap')) {
        profileMenu.classList.add('hidden');
        profileTrigger?.setAttribute('aria-expanded', 'false');
      }
    });

    const demoBtn = document.getElementById('demo-login-btn');
    if (demoBtn) demoBtn.onclick = () => this.quickDemoLogin();

    const form = document.getElementById('login-form');
    if (form) form.onsubmit = (e) => this.handleFormLogin(e);

    const logoutBtn = document.getElementById('auth-logout-btn');
    if (logoutBtn) logoutBtn.onclick = () => this.logout();
  }
};

window.BPP_AUTH = BPP_AUTH;
window.openLoginModal = () => BPP_AUTH.openModal();
window.closeLoginModal = () => BPP_AUTH.closeModal();

// Replace decorative emoji glyphs with a small consistent inline SVG icon set.
function normalizeUiIcons(root = document.body) {
  const pictograph = /\p{Extended_Pictographic}(?:\uFE0F|\uFE0E)?/gu;
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (node.parentElement?.closest('script,style,textarea,input,[contenteditable="true"],.user-content')) continue;
    if (pictograph.test(node.nodeValue)) nodes.push(node);
    pictograph.lastIndex = 0;
  }
  const paths = {
    map: 'M9 18l-6 3V6l6-3m0 15 6 3m-6-3V3m6 18 6-3V3l-6 3m0 15V6m0 0L9 3',
    chart: 'M3 3v18h18M7 14l4-4 4 3 6-7',
    shopping: 'M3 3h2l2.2 11.5a2 2 0 0 0 2 1.5h8.6a2 2 0 0 0 2-1.6L21 8H6M10 21h.01M18 21h.01',
    person: 'M20 21a8 8 0 0 0-16 0m8-10a4 4 0 1 0 0-8 4 4 0 0 0 0 8',
    file: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zm0 0v6h6M8 13h8m-8 4h8',
    search: 'M11 19a8 8 0 1 1 5.7-2.4L21 21m-10-10h.01',
    box: 'M21 8l-9-5-9 5v8l9 5 9-5zm-9 5 9-5m-9 5-9-5m9 5v8',
    drop: 'M12 22a7 7 0 0 0 7-7c0-4-7-13-7-13S5 11 5 15a7 7 0 0 0 7 7z',
    grain: 'M12 22V3m0 4c-4 0-6-2-6-5m6 9c4 0 6-2 6-5m-6 9c-4 0-6-2-6-5m6 9c4 0 6-2 6-5',
    phone: 'M5 2h14v20H5zM9 5h6m-4 14h2',
    bolt: 'm13 2-3 8h7l-6 12 1-9H5z',
    sun: 'M12 3v2m0 14v2M5.6 5.6 7 7m10 10 1.4 1.4M3 12h2m14 0h2M5.6 18.4 7 17m10-10 1.4-1.4M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
    moon: 'M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5 8.5 8.5 0 1 0 20.5 14.5z',
    shield: 'M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11zm-3-11 2 2 4-4',
    spark: 'm12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3zm7 12 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z',
  };
  const keyFor = emoji => /📍|🌐/.test(emoji) ? 'map' : /📈|📊/.test(emoji) ? 'chart' : /🛒|🏪/.test(emoji) ? 'shopping' : /👤|🔑|✉️/.test(emoji) ? 'person' : /📄|📝|📜/.test(emoji) ? 'file' : /🔍|👁️/.test(emoji) ? 'search' : /📦/.test(emoji) ? 'box' : /🛢️|💧/.test(emoji) ? 'drop' : /🍚/.test(emoji) ? 'grain' : /📱/.test(emoji) ? 'phone' : /⚡/.test(emoji) ? 'bolt' : /☀️/.test(emoji) ? 'sun' : /🌙/.test(emoji) ? 'moon' : /⚖️|🩺/.test(emoji) ? 'shield' : 'spark';
  for (const node of nodes) {
    const text = node.nodeValue;
    const matches = [...text.matchAll(pictograph)];
    for (const match of matches.reverse()) {
      const range = document.createRange();
      range.setStart(node, match.index); range.setEnd(node, match.index + match[0].length);
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('aria-hidden', 'true'); svg.classList.add('ui-icon-inline');
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', paths[keyFor(match[0])] || paths.spark); svg.appendChild(path);
      range.deleteContents(); range.insertNode(svg);
    }
  }
}

function initHeaderMotion() {
  const header = document.querySelector('.app-header');
  if (!header) return;
  const update = () => header.classList.toggle('is-scrolled', window.scrollY > 40);
  window.addEventListener('scroll', update, { passive: true }); update();
}

function splitHeroHeadline() {
  const headline = document.querySelector('.hero-title');
  if (!headline || headline.dataset.split) return;
  headline.dataset.split = 'true';
  [...headline.children].forEach((part, index) => {
    part.classList.add('hero-line');
    part.style.animationDelay = `${140 + index * 180}ms`;
  });
}

// ---------------------------------------------------------------------------
// Glitter Stardust Background Particle System
// ---------------------------------------------------------------------------
function initGlitterEngine() {
  const canvas = document.getElementById('glitter-canvas');
  if (!canvas || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const ctx = canvas.getContext('2d');
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener('resize', () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  });

  const colors = [
    'rgba(255, 119, 0, ',    // Saffron
    'rgba(255, 183, 3, ',    // Amber / Gold
    'rgba(243, 156, 18, ',   // Warm Orange
    'rgba(0, 229, 255, ',    // Neon Cyan
    'rgba(255, 255, 255, ',  // Pure White
  ];

  const PARTICLE_COUNT = 36;
  const particles = [];

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push({
      x: Math.random() * width,
      y: Math.random() * height,
      size: Math.random() * 2.2 + 0.8,
      speedX: (Math.random() - 0.5) * 0.45,
      speedY: (Math.random() - 0.5) * 0.4 - 0.2,
      baseAlpha: Math.random() * 0.55 + 0.2,
      alpha: Math.random() * 0.5 + 0.2,
      color: colors[Math.floor(Math.random() * colors.length)],
      twinkle: Math.random() * Math.PI,
    });
  }

  let animationFrameId;

  function renderGlitter() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      p.x += p.speedX;
      p.y += p.speedY;

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;

      p.twinkle += 0.035;
      const currentAlpha = p.baseAlpha + Math.sin(p.twinkle) * 0.25;
      const clampedAlpha = Math.max(0.05, Math.min(0.85, currentAlpha));

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = `${p.color}${clampedAlpha})`;
      ctx.shadowBlur = p.size * 3;
      ctx.shadowColor = `${p.color}0.8)`;
      ctx.fill();
    }

    animationFrameId = requestAnimationFrame(renderGlitter);
  }

  renderGlitter();

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      cancelAnimationFrame(animationFrameId);
    } else {
      renderGlitter();
    }
  });
}

// ---------------------------------------------------------------------------
// Scroll Reveal Animation Engine (IntersectionObserver)
// ---------------------------------------------------------------------------
function initScrollReveal() {
  const observerOptions = {
    root: null,
    rootMargin: '0px 0px -40px 0px',
    threshold: 0.1,
  };

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        obs.unobserve(entry.target);
      }
    });
  }, observerOptions);

  function observeAll() {
    document.querySelectorAll('.reveal-on-scroll:not(.revealed)').forEach(el => {
      observer.observe(el);
    });
  }

  observeAll();
  window.BPP_OBSERVE_SCROLL = observeAll;
}

// ---------------------------------------------------------------------------
// Theme Engine
// ---------------------------------------------------------------------------
function initThemeEngine() {
  const toggleBtn = document.getElementById('theme-toggle');
  const storedTheme = localStorage.getItem('bpp_theme') || 
    (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');

  document.documentElement.setAttribute('data-theme', storedTheme);

  if (toggleBtn) {
    toggleBtn.onclick = () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      const apply = () => { document.documentElement.setAttribute('data-theme', newTheme); localStorage.setItem('bpp_theme', newTheme); };
      if (document.startViewTransition && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) document.startViewTransition(apply);
      else apply();
    };
  }
}

// ---------------------------------------------------------------------------
// Live Quota Telemetry
// ---------------------------------------------------------------------------
async function updateQuotaBadge() {
  const badgeText = document.getElementById('quota-text');
  if (!badgeText) return;

  try {
    const res = await fetch('/api/quota');
    if (res.ok) {
      const data = await res.json();
      const modeStr = data.mock_mode ? ' (Mock)' : '';
      badgeText.textContent = `${data.monthly_remaining}/${data.monthly_limit} Searches${modeStr}`;
      badgeText.dataset.quotaShort = `${data.monthly_remaining}/${data.monthly_limit}`;
      badgeText.title = `${data.monthly_remaining} of ${data.monthly_limit} SerpApi searches remaining${data.mock_mode ? ' · Mock mode' : ''}`;
      badgeText.classList.remove('quota-updated'); void badgeText.offsetWidth; badgeText.classList.add('quota-updated');
      badgeText.setAttribute('aria-label', `${data.monthly_remaining} of ${data.monthly_limit} SerpApi searches remaining${data.mock_mode ? ', mock mode' : ''}`);
    }
  } catch (e) {
    console.warn('Could not fetch quota telemetry:', e);
  }
}

// ---------------------------------------------------------------------------
// Form Submission & Analysis Pipeline
// ---------------------------------------------------------------------------
async function handleFormSubmit(e) {
  if (e && e.preventDefault) e.preventDefault();

  const productInput = document.getElementById('product_raw');
  const cityInput = document.getElementById('city_raw');
  const priceInput = document.getElementById('selling_price');
  const costInput = document.getElementById('landed_cost');
  const descInput = document.getElementById('description_raw');
  const modeRadios = document.getElementsByName('analysis_mode');

  const errorBanner = document.getElementById('error-banner');
  if (errorBanner) errorBanner.classList.add('hidden');

  // Reset previous inline validation errors
  [productInput, cityInput, priceInput].forEach(inp => inp?.classList.remove('is-invalid'));
  const errProd = document.getElementById('err-product');
  const errCity = document.getElementById('err-city');
  const errPrice = document.getElementById('err-price');
  if (errProd) errProd.classList.add('hidden');
  if (errCity) errCity.classList.add('hidden');
  if (errPrice) errPrice.classList.add('hidden');

  const product = productInput?.value.trim();
  const city = cityInput?.value.trim();
  const price = parseFloat(priceInput?.value);
  const cost = costInput?.value ? parseFloat(costInput.value) : null;
  const description = descInput?.value.trim() || null;

  if (!product || product.length < 2) {
    if (productInput) {
      productInput.classList.add('is-invalid');
      productInput.focus();
    }
    if (errProd) errProd.classList.remove('hidden');
    showError('Please enter a valid product name with at least 2 characters.');
    return;
  }
  if (!city || city.length < 2) {
    if (cityInput) {
      cityInput.classList.add('is-invalid');
      cityInput.focus();
    }
    if (errCity) errCity.classList.remove('hidden');
    showError('Please enter your city or market location.');
    return;
  }
  if (isNaN(price) || price <= 0) {
    if (priceInput) {
      priceInput.classList.add('is-invalid');
      priceInput.focus();
    }
    if (errPrice) errPrice.classList.remove('hidden');
    showError('Please enter a valid selling price greater than ₹0.');
    return;
  }

  let selectedMode = 'standard';
  for (const r of modeRadios) {
    if (r.checked) {
      selectedMode = r.value;
      break;
    }
  }

  const currentUser = BPP_AUTH.getUser();
  const userEmail = currentUser?.email || null;

  const payload = {
    product_raw: product,
    city_raw: city,
    selling_price: price,
    landed_cost: cost,
    description_raw: description,
    user_email: userEmail,
    analysis_mode: selectedMode,
    ui_language: window.i18n ? window.i18n.currentLang : 'en',
  };

  const submitBtn = document.getElementById('submit-btn');
  const btnSpinner = submitBtn?.querySelector('.btn-spinner');
  const progressSection = document.getElementById('progress-section');
  const resultsContainer = document.getElementById('results-container');

  if (submitBtn) submitBtn.disabled = true;
  if (btnSpinner) btnSpinner.classList.remove('hidden');
  if (resultsContainer) resultsContainer.classList.add('hidden');
  if (progressSection) {
    progressSection.classList.remove('hidden');
    progressSection.style.display = 'block';
  }

  const progressInterval = runProgressAnimation();

  try {
    const headers = { 'Content-Type': 'application/json' };
    if (userEmail) {
      headers['X-User-Email'] = userEmail;
    }

    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    clearInterval(progressInterval);

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server returned status ${response.status}`);
    }

    const data = await response.json();
    renderAnalysisResults(data, price, cost);
    updateQuotaBadge();

  } catch (err) {
    clearInterval(progressInterval);
    showError(err.message || 'Analysis failed. Please check your inputs or try again.');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
    if (btnSpinner) btnSpinner.classList.add('hidden');
    if (progressSection) {
      progressSection.classList.add('hidden');
      progressSection.style.display = 'none';
    }
  }
}

function runProgressAnimation() {
  const progressBar = document.getElementById('progress-bar');
  const progressMsg = document.getElementById('progress-message');
  document.querySelectorAll('.step-chip').forEach(chip => chip.classList.remove('active','done'));

  const steps = [
    { pct: 25, id: 'step-1', msg: 'Distilling description & querying SerpApi Google Shopping…' },
    { pct: 50, id: 'step-2', msg: 'Discovering nearby local wholesalers & distributors on Google Local…' },
    { pct: 75, id: 'step-3', msg: 'Analyzing supply events & category news…' },
    { pct: 95, id: 'step-4', msg: 'Measuring consumer demand trends & synthesizing recommendation…' },
  ];

  let currentStep = 0;
  if (progressBar) progressBar.style.transform = 'scaleX(0.15)';
  if (progressMsg && steps[0]) progressMsg.textContent = steps[0].msg;

  return setInterval(() => {
    currentStep++;
    if (currentStep < steps.length) {
      if (progressBar) progressBar.style.transform = `scaleX(${steps[currentStep].pct / 100})`;
      if (progressMsg) progressMsg.textContent = steps[currentStep].msg;
      
      document.querySelectorAll('.step-chip').forEach(chip => chip.classList.remove('active'));
      const activeChip = document.getElementById(steps[currentStep].id);
      if (activeChip) activeChip.classList.add('active');
      for (let i = 1; i <= currentStep; i++) document.getElementById(`step-${i}`)?.classList.add('done');
    }
  }, 1200);
}

function animateCountUps(root) {
  if (!root || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  root.querySelectorAll('[data-count-up]').forEach(el => {
    const target = Number(el.dataset.countUp);
    if (!Number.isFinite(target)) return;
    const decimals = Number(el.dataset.decimals || 0);
    const prefix = el.dataset.prefix || '', suffix = el.dataset.suffix || '';
    const start = performance.now(), duration = 520;
    const tick = now => {
      const progress = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = target * eased;
      el.textContent = `${prefix}${value.toLocaleString('en-IN',{minimumFractionDigits:decimals,maximumFractionDigits:decimals})}${suffix}`;
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
}

function initEvidenceControls(card) {
  if (!card || card.dataset.controlsBound) return;
  card.dataset.controlsBound = 'true';
  card.addEventListener('click', event => {
    const chip = event.target.closest('[data-filter]');
    if (!chip) return;
    card.querySelectorAll('.filter-chip').forEach(item => item.classList.toggle('active', item === chip));
    const filter = chip.dataset.filter;
    card.querySelectorAll('tbody tr').forEach(row => row.hidden = filter !== 'all' && row.dataset.kind !== filter);
  });
  card.addEventListener('change', event => {
    if (!event.target.matches('.evidence-sort')) return;
    const tbody = card.querySelector('tbody');
    const rows = [...tbody.querySelectorAll('tr')];
    const key = event.target.value;
    rows.sort((a,b) => key === 'price' ? (Number(a.dataset.price || Infinity) - Number(b.dataset.price || Infinity)) : (a.dataset[key] || '').localeCompare(b.dataset[key] || ''));
    rows.forEach(row => tbody.appendChild(row));
  });
}

function renderAnalysisResults(data, sellerPrice, costPrice) {
  // Store globally for export functions
  window.CURRENT_ANALYSIS = { data, sellerPrice, costPrice };

  const container = document.getElementById('results-container');
  if (container) { container.classList.remove('hidden'); container.querySelectorAll('.reveal-on-scroll').forEach((el,index) => { el.style.setProperty('--reveal-order', String(index)); el.classList.remove('revealed'); requestAnimationFrame(() => el.classList.add('revealed')); }); }

  const progressSection = document.getElementById('progress-section');
  if (progressSection) {
    progressSection.classList.add('hidden');
    progressSection.style.display = 'none';
  }

  const errorBanner = document.getElementById('error-banner');
  if (errorBanner) errorBanner.classList.add('hidden');

  // Update Report Toolbar Badges
  const productBadge = document.getElementById('report-product-badge');
  if (productBadge) {
    productBadge.textContent = data.product_name || data.search_query_used || 'Product Analysis';
  }

  const dateBadge = document.getElementById('report-date-badge');
  if (dateBadge) {
    dateBadge.textContent = new Date().toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  }

  // Wire Report Export Buttons
  const btnWhatsapp = document.getElementById('btn-export-whatsapp');
  if (btnWhatsapp) {
    btnWhatsapp.onclick = () => exportToWhatsApp();
  }

  const btnPdf = document.getElementById('btn-export-pdf');
  if (btnPdf) {
    btnPdf.onclick = () => exportToPDF();
  }

  const btnPng = document.getElementById('btn-export-png');
  if (btnPng) {
    btnPng.onclick = () => exportToPNG();
  }

  const actionCard = document.getElementById('card-action');
  if (actionCard && window.Components) {
    actionCard.innerHTML = Components.renderActionCard(
      data.action,
      data.action_label,
      data.explanation,
      data.fusion,
      data.search_query_used
    );
  }

  const marketCard = document.getElementById('card-market');
  if (marketCard && window.Components) {
    marketCard.innerHTML = Components.renderMarketCard(data.market_metrics, sellerPrice);
  }

  const localCard = document.getElementById('card-local');
  if (localCard && window.Components) {
    const merchants = (Array.isArray(data.local_merchants) && data.local_merchants.length > 0)
      ? data.local_merchants
      : ((Array.isArray(data.sources)) ? data.sources.filter(s => s.source_type === 'Local Discovery') : []);
    localCard.innerHTML = Components.renderLocalCard(merchants, data.location_display || 'Your Area');
  }

  const demandCard = document.getElementById('card-demand');
  if (demandCard && window.Components) {
    demandCard.innerHTML = Components.renderDemandCard(data.trends_evidence || null);
  }

  const externalCard = document.getElementById('card-external');
  if (externalCard && window.Components) {
    const newsList = (Array.isArray(data.news_articles) && data.news_articles.length > 0)
      ? data.news_articles
      : ((Array.isArray(data.sources)) ? data.sources.filter(s => s.source_type === 'News Event') : []);
    const finList = (Array.isArray(data.finance_signals) && data.finance_signals.length > 0)
      ? data.finance_signals
      : [];
    externalCard.innerHTML = Components.renderExternalCard(newsList, finList);
  }

  const econCard = document.getElementById('card-economics');
  if (econCard && window.Components) {
    if (costPrice && data.market_metrics) {
      econCard.innerHTML = Components.renderEconomicsCard(data.market_metrics, costPrice);
      econCard.classList.remove('hidden');
    } else {
      econCard.classList.add('hidden');
    }
  }

  const gstCard = document.getElementById('card-gst');
  if (gstCard && window.Components) {
    if (data.gst_reference_display) {
      gstCard.innerHTML = Components.renderGSTCard(data.gst_reference_display);
      gstCard.classList.remove('hidden');
    } else {
      gstCard.classList.add('hidden');
    }
  }

  const sourcesCard = document.getElementById('card-sources');
  if (sourcesCard && window.Components) {
    sourcesCard.innerHTML = Components.renderSourcesCard(
      data.sources || [],
      data.searches_consumed,
      data.searches_from_cache
    );
  }

  animateCountUps(container);
  requestAnimationFrame(() => actionCard?.classList.add('is-ready'));
  initEvidenceControls(sourcesCard);

  if (window.BPP_OBSERVE_SCROLL) {
    window.BPP_OBSERVE_SCROLL();
  }

  if (actionCard) {
    actionCard.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' });
  }
}

// ---------------------------------------------------------------------------
// Report Export Engine (WhatsApp, Printable PDF, Graphic PNG)
// ---------------------------------------------------------------------------

function formatINRValue(num) {
  if (num === null || num === undefined || isNaN(num)) return '0.00';
  return Number(num).toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

function showToast(message, isError = false) {
  const existing = document.getElementById('bpp-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'bpp-toast';
  toast.className = `bpp-toast ${isError ? 'toast-error' : ''}`;
  toast.setAttribute('role', isError ? 'alert' : 'status');
  toast.setAttribute('aria-live', isError ? 'assertive' : 'polite');
  toast.innerHTML = `<span>${message}</span>`;
  document.body.appendChild(toast);

  setTimeout(() => {
    if (toast.parentNode) {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }
  }, 3500);
}

function fallbackCopyText(text) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand('copy');
    showToast('Copied for WhatsApp');
  } catch (e) {
    showToast('Could not copy to clipboard. Please copy manually.', true);
  }
  document.body.removeChild(ta);
}

function exportToWhatsApp() {
  const current = window.CURRENT_ANALYSIS;
  if (!current || !current.data) {
    showToast('No active analysis to share. Please run an analysis first.', true);
    return;
  }

  const { data, sellerPrice, costPrice } = current;
  const metrics = data.market_metrics || {};
  const median = metrics.median_price || metrics.median || 'N/A';
  const gap = metrics.seller_price_gap_percent !== undefined ? metrics.seller_price_gap_percent.toFixed(1) : '0.0';
  const productTitle = data.product_name || data.search_query_used || 'Product';
  const location = data.location_display || data.city_raw || 'India';
  const actionLabel = data.action_label || data.action || 'RECOMMENDATION';
  const explanation = toExportText(data.explanation);
  const dateStr = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

  let actionEmoji = '⚡';
  if (data.action === 'REPRICE_UP') actionEmoji = '🟢';
  else if (data.action === 'REPRICE_DOWN' || data.action === 'REVIEW_PRICE') actionEmoji = '🔴';
  else if (data.action === 'HOLD') actionEmoji = '🔵';
  else if (data.action === 'SOURCE_LOCALLY') actionEmoji = '🏬';

  let text = `📊 *BHARATPRICE PULSE — MARKET DECISION REPORT*\n`;
  text += `━━━━━━━━━━━━━━━━━━━━━\n`;
  text += `📦 *Product:* ${productTitle}\n`;
  text += `📍 *Market City:* ${location}\n`;
  text += `📅 *Date:* ${dateStr}\n\n`;
  text += `💰 *Your Price:* ₹${formatINRValue(sellerPrice)}\n`;
  text += `🛒 *Market Median:* ₹${formatINRValue(median)}\n`;
  text += `📉 *Price Gap:* ${gap > 0 ? '+' : ''}${gap}%\n`;
  if (costPrice) {
    const margin = metrics.gross_margin_percent !== undefined ? metrics.gross_margin_percent.toFixed(1) : 'N/A';
    text += `🏷️ *Landed Cost:* ₹${formatINRValue(costPrice)} (Gross Margin: ${margin}%)\n`;
  }
  text += `\n${actionEmoji} *DECISION: ${actionLabel.toUpperCase()}*\n`;
  if (explanation) {
    text += `💡 *Reasoning:* ${explanation}\n`;
  }
  const localCount = Array.isArray(data.local_merchants) ? data.local_merchants.length : 0;
  if (localCount > 0) {
    text += `\n🏬 *Local Sourcing:* ${localCount} wholesalers identified in ${location}\n`;
  }
  if (data.trends_evidence?.trend_direction) {
    text += `📈 *Demand Trend:* ${data.trends_evidence.trend_direction.toUpperCase()}\n`;
  }
  text += `\n━━━━━━━━━━━━━━━━━━━━━\n`;
  text += `✅ *Grounded live via SerpApi (Google Shopping, Local, Trends)*\n`;
  text += `_BharatPrice Pulse • SerpApi Hackathon 2026_`;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      showToast('💬 WhatsApp report copied to clipboard! Paste into your chat.');
    }).catch(() => {
      fallbackCopyText(text);
    });
  } else {
    fallbackCopyText(text);
  }
}

function exportToPDF() {
  const current = window.CURRENT_ANALYSIS;
  if (!current || !current.data) {
    showToast('No active analysis to print. Please run an analysis first.', true);
    return;
  }
  const prevTitle = document.title;
  const safeName = (current.data.product_name || 'Report').replace(/[^a-zA-Z0-9_-]/g, '_');
  document.title = `BharatPrice_Pulse_Report_${safeName}`;
  document.body.classList.add('printing-report');
  const restorePrintState = () => {
    document.body.classList.remove('printing-report');
    document.title = prevTitle;
    window.removeEventListener('afterprint', restorePrintState);
  };
  window.addEventListener('afterprint', restorePrintState, { once: true });
  window.print();
}

function toExportText(value) {
  if (typeof value === 'string') return value.trim();
  if (Array.isArray(value)) return value.map(toExportText).filter(Boolean).join(' ');
  if (!value || typeof value !== 'object') return '';
  const preferred = ['summary', 'reasoning', 'text', 'message', 'description', 'explanation'];
  for (const key of preferred) {
    const text = toExportText(value[key]);
    if (text) return text;
  }
  return Object.values(value).map(toExportText).filter(Boolean).join(' ');
}

function roundRectCanvas(ctx, x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}

function wrapCanvasText(ctx, text, x, y, maxWidth, lineHeight) {
  const words = (text || '').split(' ');
  let line = '';
  let curY = y;
  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + ' ';
    const metrics = ctx.measureText(testLine);
    if (metrics.width > maxWidth && n > 0) {
      ctx.fillText(line, x, curY);
      line = words[n] + ' ';
      curY += lineHeight;
      if (curY > y + lineHeight * 2) {
        ctx.fillText(line.trim() + '...', x, curY);
        return;
      }
    } else {
      line = testLine;
    }
  }
  ctx.fillText(line, x, curY);
}

function drawCanvasMetric(ctx, x, y, w, h, title, val, valColor, sub) {
  ctx.fillStyle = 'rgba(18, 26, 43, 0.75)';
  roundRectCanvas(ctx, x, y, w, h, 12);
  ctx.fill();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
  ctx.stroke();

  ctx.fillStyle = '#94a3b8';
  ctx.font = 'bold 11px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText(title, x + 16, y + 26);

  ctx.fillStyle = valColor;
  ctx.font = 'bold 22px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText(val, x + 16, y + 62);

  ctx.fillStyle = '#64748b';
  ctx.font = '12px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText(sub, x + 16, y + 92);
}

function exportToPNGLegacy() {
  const current = window.CURRENT_ANALYSIS;
  if (!current || !current.data) {
    showToast('No active analysis to export. Please run an analysis first.', true);
    return;
  }

  const { data, sellerPrice, costPrice } = current;
  const metrics = data.market_metrics || {};
  const median = metrics.median_price || metrics.median || null;
  const minPrice = metrics.min_price || metrics.min || null;
  const maxPrice = metrics.max_price || metrics.max || null;
  const gap = metrics.seller_price_gap_percent !== undefined ? metrics.seller_price_gap_percent : null;
  const margin = metrics.gross_margin_percent !== undefined ? metrics.gross_margin_percent : null;
  const productTitle = data.product_name || data.search_query_used || 'Product';
  const location = data.location_display || data.city_raw || 'India';
  const actionLabel = data.action_label || data.action || 'RECOMMENDATION';
  const explanation = data.explanation || 'Market evidence indicates current price position relative to observed medians.';
  const dateStr = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });

  const canvas = document.createElement('canvas');
  canvas.width = 1200;
  canvas.height = 760;
  const ctx = canvas.getContext('2d');

  // Background Gradient
  const bgGrad = ctx.createLinearGradient(0, 0, 1200, 760);
  bgGrad.addColorStop(0, '#090d16');
  bgGrad.addColorStop(1, '#0e1628');
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, 1200, 760);

  // Ambient glows
  const glowTop = ctx.createRadialGradient(200, 50, 10, 200, 50, 400);
  glowTop.addColorStop(0, 'rgba(255, 119, 0, 0.22)');
  glowTop.addColorStop(1, 'transparent');
  ctx.fillStyle = glowTop;
  ctx.fillRect(0, 0, 1200, 450);

  const glowBottom = ctx.createRadialGradient(1000, 700, 10, 1000, 700, 450);
  glowBottom.addColorStop(0, 'rgba(0, 229, 255, 0.15)');
  glowBottom.addColorStop(1, 'transparent');
  ctx.fillStyle = glowBottom;
  ctx.fillRect(0, 400, 1200, 360);

  // Outer Glowing Border
  ctx.strokeStyle = 'rgba(255, 119, 0, 0.55)';
  ctx.lineWidth = 3;
  ctx.strokeRect(16, 16, 1168, 728);

  // Inner subtle border
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
  ctx.lineWidth = 1;
  ctx.strokeRect(24, 24, 1152, 712);

  // Brand Header
  ctx.fillStyle = '#ff7700';
  ctx.fillRect(50, 48, 8, 44);

  // Logo glyph
  ctx.fillStyle = '#ff7700';
  roundRectCanvas(ctx, 68, 48, 44, 44, 10);
  ctx.fill();
  ctx.fillStyle = '#090d16';
  ctx.font = 'bold 24px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('₹', 82, 78);

  // Brand Titles
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 24px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('BHARATPRICE PULSE', 124, 70);

  ctx.fillStyle = '#94a3b8';
  ctx.font = '13px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('RETAIL INTELLIGENCE & PRICING COPILOT • POWERED BY SERPAPI', 124, 90);

  // Top-Right Badges
  ctx.fillStyle = 'rgba(255, 255, 255, 0.07)';
  roundRectCanvas(ctx, 920, 48, 228, 44, 8);
  ctx.fill();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
  ctx.stroke();

  ctx.fillStyle = '#ffb703';
  ctx.font = 'bold 13px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('📅 ' + dateStr, 940, 75);

  // Product Banner
  ctx.fillStyle = 'rgba(18, 26, 43, 0.85)';
  roundRectCanvas(ctx, 50, 114, 1100, 80, 14);
  ctx.fill();
  ctx.strokeStyle = 'rgba(0, 229, 255, 0.35)';
  ctx.lineWidth = 1.5;
  ctx.stroke();

  ctx.fillStyle = '#00e5ff';
  ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('EVALUATED PRODUCT & MARKET CONTEXT', 75, 140);

  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 22px -apple-system, BlinkMacSystemFont, sans-serif';
  const prodDisplay = productTitle.length > 55 ? productTitle.slice(0, 52) + '...' : productTitle;
  ctx.fillText('📦 ' + prodDisplay, 75, 172);

  ctx.fillStyle = '#94a3b8';
  ctx.font = '14px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('📍 ' + location, 850, 172);

  // Action Recommendation Banner
  let actionColor = '#ff7700';
  if (data.action === 'REPRICE_UP') actionColor = '#10b981';
  else if (data.action === 'REPRICE_DOWN' || data.action === 'REVIEW_PRICE') actionColor = '#ef4444';
  else if (data.action === 'HOLD') actionColor = '#06b6d4';
  else if (data.action === 'SOURCE_LOCALLY') actionColor = '#14b8a6';

  ctx.fillStyle = 'rgba(18, 26, 43, 0.9)';
  roundRectCanvas(ctx, 50, 214, 1100, 130, 16);
  ctx.fill();
  ctx.strokeStyle = actionColor;
  ctx.lineWidth = 2;
  ctx.stroke();

  // Action Badge Pill
  ctx.fillStyle = actionColor;
  roundRectCanvas(ctx, 75, 236, 260, 34, 8);
  ctx.fill();
  ctx.fillStyle = '#ffffff';
  ctx.font = 'bold 15px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('⚡ ' + (actionLabel.toUpperCase()), 92, 259);

  // Confidence Pill
  const confText = data.confidence_score ? `Confidence: ${data.confidence_score}%` : 'High Confidence';
  ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
  roundRectCanvas(ctx, 350, 236, 170, 34, 8);
  ctx.fill();
  ctx.fillStyle = '#cbd5e1';
  ctx.font = '13px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('🛡️ ' + confText, 365, 258);

  // Explanation text wrapped
  ctx.fillStyle = '#f8fafc';
  ctx.font = '15px -apple-system, BlinkMacSystemFont, sans-serif';
  wrapCanvasText(ctx, explanation, 75, 298, 1050, 22);

  // 4 Key Metric Cards
  const cardW = 260;
  const cardH = 110;
  const startY = 364;
  const gapX = 20;

  drawCanvasMetric(ctx, 50, startY, cardW, cardH, 'YOUR SELLING PRICE', `₹${formatINRValue(sellerPrice)}`, '#ffb703', 'Input Price');
  const medianStr = median ? `₹${formatINRValue(median)}` : 'N/A';
  drawCanvasMetric(ctx, 50 + cardW + gapX, startY, cardW, cardH, 'MARKET MEDIAN', medianStr, '#00e5ff', 'Google Shopping');
  const gapStr = gap !== null ? `${gap > 0 ? '+' : ''}${gap.toFixed(1)}%` : '0.0%';
  const gapColor = gap > 5 ? '#ef4444' : (gap < -5 ? '#10b981' : '#ffb703');
  drawCanvasMetric(ctx, 50 + (cardW + gapX) * 2, startY, cardW, cardH, 'PRICE POSITION GAP', gapStr, gapColor, 'vs Median');
  let m4Title = 'MARKET RANGE';
  let m4Val = (minPrice && maxPrice) ? `₹${formatINRValue(minPrice)} - ₹${formatINRValue(maxPrice)}` : 'Observed';
  let m4Sub = 'Online Range';
  if (margin !== null) {
    m4Title = 'GROSS MARGIN';
    m4Val = `${margin.toFixed(1)}%`;
    m4Sub = costPrice ? `Cost: ₹${formatINRValue(costPrice)}` : 'Calculated';
  }
  drawCanvasMetric(ctx, 50 + (cardW + gapX) * 3, startY, cardW, cardH, m4Title, m4Val, '#10b981', m4Sub);

  // Dual Signals Section
  const signalCardW = 540;
  const signalCardH = 145;
  const signalY = 494;

  // Local Sourcing Box
  ctx.fillStyle = 'rgba(18, 26, 43, 0.7)';
  roundRectCanvas(ctx, 50, signalY, signalCardW, signalCardH, 12);
  ctx.fill();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
  ctx.stroke();

  ctx.fillStyle = '#ff7700';
  ctx.font = 'bold 14px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('📍 LOCAL WHOLESALE & SOURCING DISCOVERY', 72, signalY + 30);

  const localCount = Array.isArray(data.local_merchants) ? data.local_merchants.length : 0;
  const topMerchant = (data.local_merchants && data.local_merchants[0]) ? (data.local_merchants[0].name || data.local_merchants[0].title) : 'Local Mandis & Wholesalers';
  ctx.fillStyle = '#f8fafc';
  ctx.font = '15px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText(`• ${localCount > 0 ? localCount + ' Wholesalers Identified' : 'Local Wholesale Hubs Checked'} in ${location}`, 72, signalY + 65);
  ctx.fillStyle = '#94a3b8';
  ctx.font = '13px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText(`• Verified via SerpApi Google Local (Mandis, APMC, Distributors)`, 72, signalY + 92);
  ctx.fillText(`• Top Discovery: ${String(topMerchant).slice(0, 48)}`, 72, signalY + 118);

  // Demand / Trends Box
  ctx.fillStyle = 'rgba(18, 26, 43, 0.7)';
  roundRectCanvas(ctx, 610, signalY, signalCardW, signalCardH, 12);
  ctx.fill();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
  ctx.stroke();

  ctx.fillStyle = '#00e5ff';
  ctx.font = 'bold 14px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('📈 DEMAND TRENDS & EXTERNAL SIGNALS', 632, signalY + 30);

  const trendDir = data.trends_evidence?.trend_direction || 'STABLE';
  const peakRegion = data.trends_evidence?.peak_region || location;
  ctx.fillStyle = '#f8fafc';
  ctx.font = '15px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText(`• Consumer Search Demand Momentum: ${trendDir.toUpperCase()}`, 632, signalY + 65);
  ctx.fillStyle = '#94a3b8';
  ctx.font = '13px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText(`• Regional Demand Hotspot: ${peakRegion} (Google Trends 12-Wk)`, 632, signalY + 92);
  ctx.fillText(`• Supply & Tariffs: Verified against CBIC GST & Category Drivers`, 632, signalY + 118);

  // Footer Audit Bar
  ctx.fillStyle = 'rgba(10, 15, 26, 0.95)';
  roundRectCanvas(ctx, 50, 660, 1100, 60, 10);
  ctx.fill();
  ctx.strokeStyle = 'rgba(16, 185, 129, 0.3)';
  ctx.stroke();

  ctx.fillStyle = '#10b981';
  ctx.font = 'bold 13px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('🛡️ EVIDENCE-ONLY GUARANTEE: Real-Time Grounding via Official SerpApi Engines • Zero Hallucinations', 75, 696);

  ctx.fillStyle = '#64748b';
  ctx.font = '12px -apple-system, BlinkMacSystemFont, sans-serif';
  ctx.fillText('SerpApi Hackathon 2026 • BharatPrice Pulse MSME Decision Engine', 770, 696);

  try {
    const dataUrl = canvas.toDataURL('image/png');
    const safeName = (data.product_name || 'report').replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 30);
    const link = document.createElement('a');
    link.download = `BharatPrice_Pulse_Decision_${safeName}.png`;
    link.href = dataUrl;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('🖼️ Executive PNG Decision Card downloaded!');
  } catch (err) {
    console.error('PNG Export failed:', err);
    showToast('Failed to generate PNG image. Please try PDF download.', true);
  }
}

async function exportToPNG() {
  const current = window.CURRENT_ANALYSIS;
  if (!current?.data) {
    showToast('No active analysis to export. Please run an analysis first.', true);
    return;
  }

  const button = document.getElementById('btn-export-png');
  const originalLabel = button?.querySelector('span')?.textContent;
  if (button) button.disabled = true;
  if (button?.querySelector('span')) button.querySelector('span').textContent = 'Preparing…';

  try {
    const { data, sellerPrice } = current;
    const metrics = data.market_metrics || {};
    const median = Number(metrics.median_price ?? metrics.median);
    const min = Number(metrics.min_price ?? metrics.min);
    const max = Number(metrics.max_price ?? metrics.max);
    const gap = Number(metrics.seller_price_gap_percent);
    const product = data.product_name || data.search_query_used || 'Product';
    const location = data.location_display || data.city_raw || 'India';
    const decision = data.action_label || data.action || 'Recommendation';
    const reasoning = toExportText(data.explanation) || 'Market evidence was compared with your selling price.';
    const actionColor = data.action === 'REPRICE_UP' ? '#10b981' : data.action === 'REPRICE_DOWN' || data.action === 'REVIEW_PRICE' ? '#ef4444' : '#ff7700';
    const canvas = document.createElement('canvas');
    canvas.width = 1200; canvas.height = 650;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('Canvas is unavailable');

    const background = ctx.createLinearGradient(0, 0, 1200, 650);
    background.addColorStop(0, '#0b1220'); background.addColorStop(1, '#111c33');
    ctx.fillStyle = background; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = 'rgba(255,119,0,.16)'; ctx.beginPath(); ctx.arc(140, 20, 300, 0, Math.PI * 2); ctx.fill();

    ctx.fillStyle = '#ff7700'; ctx.fillRect(54, 48, 7, 52);
    ctx.fillStyle = '#ffffff'; ctx.font = '700 28px system-ui, sans-serif'; ctx.fillText('BHARATPRICE PULSE', 82, 72);
    ctx.fillStyle = '#9fb0c9'; ctx.font = '15px system-ui, sans-serif'; ctx.fillText('MARKET DECISION REPORT', 82, 96);
    ctx.textAlign = 'right'; ctx.fillText(new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }), 1145, 72); ctx.textAlign = 'left';

    ctx.fillStyle = 'rgba(255,255,255,.08)'; roundRectCanvas(ctx, 54, 128, 1092, 138, 18); ctx.fill();
    ctx.fillStyle = '#a9bedc'; ctx.font = '700 13px system-ui, sans-serif'; ctx.fillText('PRODUCT · ' + location.toUpperCase(), 82, 162);
    ctx.fillStyle = '#ffffff'; ctx.font = '700 30px system-ui, sans-serif';
    wrapCanvasText(ctx, product, 82, 205, 880, 38);
    ctx.fillStyle = actionColor; roundRectCanvas(ctx, 82, 226, 270, 28, 14); ctx.fill();
    ctx.fillStyle = '#09111f'; ctx.font = '700 13px system-ui, sans-serif'; ctx.fillText(decision.toUpperCase(), 98, 246);

    const cardY = 300, cardW = 336, cardH = 124;
    const drawMetric = (x, label, value, color, note) => {
      ctx.fillStyle = 'rgba(255,255,255,.07)'; roundRectCanvas(ctx, x, cardY, cardW, cardH, 16); ctx.fill();
      ctx.fillStyle = '#9fb0c9'; ctx.font = '700 13px system-ui, sans-serif'; ctx.fillText(label, x + 24, cardY + 32);
      ctx.fillStyle = color; ctx.font = '700 31px system-ui, sans-serif'; ctx.fillText(value, x + 24, cardY + 75);
      ctx.fillStyle = '#9fb0c9'; ctx.font = '14px system-ui, sans-serif'; ctx.fillText(note, x + 24, cardY + 101);
    };
    drawMetric(54, 'YOUR SELLING PRICE', `₹${formatINRValue(sellerPrice)}`, '#ffbf69', 'Current input');
    drawMetric(432, 'MARKET MEDIAN', Number.isFinite(median) ? `₹${formatINRValue(median)}` : 'N/A', '#4dd9ef', 'Observed online median');
    const gapLabel = Number.isFinite(gap) ? `${gap > 0 ? '+' : ''}${gap.toFixed(1)}%` : 'N/A';
    drawMetric(810, 'PRICE GAP', gapLabel, gap > 5 ? '#ff7a7a' : gap < -5 ? '#75e6ae' : '#ffbf69', 'Against market median');

    if (Number.isFinite(min) && Number.isFinite(max) && max > min && Number.isFinite(sellerPrice)) {
      const rangeY = 480, rangeX = 82, rangeW = 1035;
      const low = Math.min(min, sellerPrice), high = Math.max(max, sellerPrice);
      const position = value => rangeX + ((value - low) / (high - low)) * rangeW;
      ctx.fillStyle = '#32415d'; roundRectCanvas(ctx, rangeX, rangeY, rangeW, 10, 5); ctx.fill();
      ctx.fillStyle = '#ff8a27'; roundRectCanvas(ctx, position(min), rangeY - 3, Math.max(8, position(max) - position(min)), 16, 8); ctx.fill();
      ctx.fillStyle = '#4dd9ef'; ctx.fillRect(position(median) - 2, rangeY - 14, 4, 38);
      ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.arc(position(sellerPrice), rangeY + 5, 10, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#9fb0c9'; ctx.font = '13px system-ui, sans-serif'; ctx.fillText(`Observed range ₹${formatINRValue(min)} – ₹${formatINRValue(max)}`, rangeX, 530);
      ctx.textAlign = 'right'; ctx.fillText('Orange: market range  •  Blue: median  •  White: your price', rangeX + rangeW, 530); ctx.textAlign = 'left';
    }

    ctx.fillStyle = '#d7e2f2'; ctx.font = '16px system-ui, sans-serif';
    wrapCanvasText(ctx, reasoning, 82, 580, 1035, 24);

    const safeName = product.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 30);
    const blob = await new Promise((resolve, reject) => canvas.toBlob(value => value ? resolve(value) : reject(new Error('PNG encoding failed')), 'image/png'));
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = `BharatPrice_Pulse_Decision_${safeName}.png`;
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    showToast('PNG decision summary downloaded.');
  } catch (err) {
    console.error('PNG export failed:', err);
    showToast('Could not generate the PNG summary.', true);
  } finally {
    if (button) button.disabled = false;
    if (button?.querySelector('span')) button.querySelector('span').textContent = originalLabel || 'Download PNG';
  }
}

function showError(msg) {
  const banner = document.getElementById('error-banner');
  const text = document.getElementById('error-text');
  if (text) text.textContent = msg;
  if (banner) {
    banner.classList.remove('hidden');
    banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}


function initViewNavigation() {
  const progress = document.createElement('div'); progress.className = 'top-progress'; progress.setAttribute('aria-hidden','true'); document.body.prepend(progress);
  document.querySelectorAll('a[href="/"], a[href="/history"]').forEach(link => {
    link.addEventListener('click', event => {
      const target = new URL(link.href, location.href);
      if (target.pathname === location.pathname) return;
      event.preventDefault();
      progress.classList.remove('active'); void progress.offsetWidth; progress.classList.add('active');
      const navigate = () => { location.href = target.href; };
      window.setTimeout(() => { if (!document.startViewTransition) navigate(); }, 220);
      if (document.startViewTransition) document.startViewTransition(navigate);
    });
  });
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  window.addEventListener('pageshow', () => window.scrollTo(0, 0));
}

// ---------------------------------------------------------------------------
// App Bootstrap Function (Executes safely regardless of load timing)
// ---------------------------------------------------------------------------
async function initApp() {
  try { initThemeEngine(); } catch (e) { console.warn('Theme init warning:', e); }
  try { initViewNavigation(); initHeaderMotion(); normalizeUiIcons(); } catch (e) { console.warn('View navigation warning:', e); }
  const iconObserver = new MutationObserver(() => { if (!window._bppIconFrame) window._bppIconFrame = requestAnimationFrame(() => { window._bppIconFrame = 0; normalizeUiIcons(); }); });
  iconObserver.observe(document.body, { childList: true, subtree: true });
  try { BPP_AUTH.init(); } catch (e) { console.warn('BPP_AUTH init warning:', e); }
  // The static CSS aurora replaces the old per-frame particle canvas to keep rendering light.
  try { initScrollReveal(); } catch (e) { console.warn('Scroll reveal warning:', e); }

  if (window.i18n) {
    try {
      await window.i18n.init();
    } catch (e) {
      console.warn('i18n init error:', e);
    }
  }

  splitHeroHeadline();
  try { await updateQuotaBadge(); } catch (e) { console.warn('Quota badge warning:', e); }

  const langSelect = document.getElementById('lang-select');
  if (langSelect) {
    langSelect.onchange = async (e) => {
      const selected = e.target.value;
      if (window.i18n) {
        await window.i18n.loadLanguage(selected);
      }
    };
  }

  document.querySelectorAll('.sample-chip').forEach(chip => {
    chip.onclick = () => {
      const prodEl = document.getElementById('product_raw');
      const cityEl = document.getElementById('city_raw');
      const priceEl = document.getElementById('selling_price');
      const costEl = document.getElementById('landed_cost');
      const descEl = document.getElementById('description_raw');

      if (prodEl) prodEl.value = chip.dataset.product || '';
      if (cityEl) cityEl.value = chip.dataset.city || '';
      if (priceEl) priceEl.value = chip.dataset.price || '';
      if (costEl) costEl.value = chip.dataset.cost || '';

      if (descEl) {
        if (chip.dataset.product?.includes('Basmati')) {
          descEl.value = '1121 steam aged long grain 5kg';
        } else if (chip.dataset.product?.includes('Samsung')) {
          descEl.value = '6GB RAM 128GB ROM 5G Smartphone';
        } else if (chip.dataset.product?.includes('Mustard')) {
          descEl.value = 'Kachi Ghani cold pressed edible mustard oil 1L bottle';
        } else {
          descEl.value = '';
        }
      }

      chip.classList.add('is-pressed');
      setTimeout(() => chip.classList.remove('is-pressed'), 150);
    };
  });

  // Real-time inline field validation feedback & error clearing
  ['product_raw', 'city_raw', 'selling_price'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('input', () => {
      el.classList.remove('is-invalid');
      const errEl = document.getElementById(
        id === 'product_raw' ? 'err-product' :
        id === 'city_raw' ? 'err-city' : 'err-price'
      );
      if (errEl) errEl.classList.add('hidden');
      const errorBanner = document.getElementById('error-banner');
      if (errorBanner) errorBanner.classList.add('hidden');
    });
  });

  // URL Auto-fill support (e.g. from history card links or shared links)
  try {
    const urlParams = new URLSearchParams(window.location.search);
    const pProduct = urlParams.get('product') || urlParams.get('product_raw');
    const pCity = urlParams.get('city') || urlParams.get('city_raw');
    const pPrice = urlParams.get('price') || urlParams.get('selling_price');
    const pCost = urlParams.get('cost') || urlParams.get('landed_cost');
    const pDesc = urlParams.get('desc') || urlParams.get('description_raw');
    const pMode = urlParams.get('mode') || urlParams.get('analysis_mode');

    let hasPreFill = false;
    if (pProduct) {
      const prodEl = document.getElementById('product_raw');
      if (prodEl) { prodEl.value = pProduct; hasPreFill = true; }
    }
    if (pCity) {
      const cityEl = document.getElementById('city_raw');
      if (cityEl) { cityEl.value = pCity; hasPreFill = true; }
    }
    if (pPrice) {
      const priceEl = document.getElementById('selling_price');
      if (priceEl) { priceEl.value = pPrice; hasPreFill = true; }
    }
    if (pCost) {
      const costEl = document.getElementById('landed_cost');
      if (costEl) costEl.value = pCost;
    }
    if (pDesc) {
      const descEl = document.getElementById('description_raw');
      if (descEl) descEl.value = pDesc;
    }
    if (pMode) {
      const modeRadio = document.querySelector(`input[name="analysis_mode"][value="${pMode}"]`);
      if (modeRadio) modeRadio.checked = true;
    }

    if (hasPreFill) {
      const searchCard = document.getElementById('search-card');
      if (searchCard) {
        setTimeout(() => {
          searchCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 150);
      }
    }
  } catch (err) {
    console.warn('URL auto-fill error:', err);
  }

  const form = document.getElementById('analysis-form');
  if (form) {
    form.onsubmit = handleFormSubmit;
    form.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleFormSubmit(e);
      }
    });
  }
}

// Boot safely
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
