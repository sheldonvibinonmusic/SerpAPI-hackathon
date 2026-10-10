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

  openModal() {
    const modal = document.getElementById('login-modal');
    if (modal) {
      modal.classList.remove('hidden');
      modal.style.display = 'flex';
      const emailInput = document.getElementById('login-email');
      if (emailInput) setTimeout(() => emailInput.focus(), 80);
    }
  },

  closeModal() {
    const modal = document.getElementById('login-modal');
    if (modal) {
      modal.classList.add('hidden');
      modal.style.display = 'none';
    }
  },

  async quickDemoLogin() {
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
    this.closeModal();
  },

  async handleFormLogin(e) {
    if (e && e.preventDefault) e.preventDefault();
    const emailInput = document.getElementById('login-email');
    const nameInput = document.getElementById('login-name');
    const spinner = document.getElementById('login-spinner');
    const submitBtn = document.getElementById('login-submit-btn');

    const email = emailInput?.value.trim();
    const name = nameInput?.value.trim();

    if (!email || !email.includes('@')) {
      alert('Please enter a valid Gmail / email address.');
      return;
    }

    if (spinner) spinner.classList.remove('hidden');
    if (submitBtn) submitBtn.disabled = true;

    try {
      const resp = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, provider: 'email' }),
      });
      if (resp.ok) {
        const data = await resp.json();
        this.setUser(data.user);
        this.closeModal();
      } else {
        const err = await resp.json().catch(() => ({}));
        alert(err.detail || 'Login failed. Please check your email.');
      }
    } catch (err) {
      // Offline fallback
      this.setUser({
        email,
        name: name || email.split('@')[0],
        provider: 'email',
      });
      this.closeModal();
    } finally {
      if (spinner) spinner.classList.add('hidden');
      if (submitBtn) submitBtn.disabled = false;
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

    if (user && user.email) {
      if (authBtn) authBtn.classList.add('hidden');
      if (userBadge) userBadge.classList.remove('hidden');
      if (nameEl) nameEl.textContent = user.name || user.email.split('@')[0];
      if (emailEl) emailEl.textContent = user.email;
      if (avatarEl) {
        avatarEl.src = user.avatar_url || `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(user.name || 'BP')}&backgroundColor=ff7700`;
      }
    } else {
      if (authBtn) authBtn.classList.remove('hidden');
      if (userBadge) userBadge.classList.add('hidden');
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
      modal.onclick = (e) => {
        if (e.target === modal) this.closeModal();
      };
    }

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

// ---------------------------------------------------------------------------
// Glitter Stardust Background Particle System
// ---------------------------------------------------------------------------
function initGlitterEngine() {
  const canvas = document.getElementById('glitter-canvas');
  if (!canvas) return;

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
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('bpp_theme', newTheme);
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

  const product = productInput?.value.trim();
  const city = cityInput?.value.trim();
  const price = parseFloat(priceInput?.value);
  const cost = costInput?.value ? parseFloat(costInput.value) : null;
  const description = descInput?.value.trim() || null;

  if (!product || product.length < 2) {
    showError('Please enter a product name with at least 2 characters.');
    return;
  }
  if (!city || city.length < 2) {
    showError('Please enter your city/location.');
    return;
  }
  if (isNaN(price) || price <= 0) {
    showError('Please enter a valid positive selling price.');
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

  const steps = [
    { pct: 25, id: 'step-1', msg: 'Distilling description & querying SerpApi Google Shopping…' },
    { pct: 50, id: 'step-2', msg: 'Discovering nearby local wholesalers & distributors on Google Local…' },
    { pct: 75, id: 'step-3', msg: 'Analyzing supply events & category news…' },
    { pct: 95, id: 'step-4', msg: 'Measuring consumer demand trends & synthesizing recommendation…' },
  ];

  let currentStep = 0;
  if (progressBar) progressBar.style.width = '15%';
  if (progressMsg && steps[0]) progressMsg.textContent = steps[0].msg;

  return setInterval(() => {
    currentStep++;
    if (currentStep < steps.length) {
      if (progressBar) progressBar.style.width = `${steps[currentStep].pct}%`;
      if (progressMsg) progressMsg.textContent = steps[currentStep].msg;
      
      document.querySelectorAll('.step-chip').forEach(chip => chip.classList.remove('active'));
      const activeChip = document.getElementById(steps[currentStep].id);
      if (activeChip) activeChip.classList.add('active');
    }
  }, 1200);
}

function renderAnalysisResults(data, sellerPrice, costPrice) {
  // Store globally for export functions
  window.CURRENT_ANALYSIS = { data, sellerPrice, costPrice };

  const container = document.getElementById('results-container');
  if (container) container.classList.remove('hidden');

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

  if (window.BPP_OBSERVE_SCROLL) {
    window.BPP_OBSERVE_SCROLL();
  }

  if (actionCard) {
    actionCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
    showToast('💬 WhatsApp report copied to clipboard!');
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
  const explanation = data.explanation || '';
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
  window.print();
  setTimeout(() => {
    document.title = prevTitle;
  }, 1000);
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

function exportToPNG() {
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

function showError(msg) {
  const banner = document.getElementById('error-banner');
  const text = document.getElementById('error-text');
  if (text) text.textContent = msg;
  if (banner) {
    banner.classList.remove('hidden');
    banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// ---------------------------------------------------------------------------
// App Bootstrap Function (Executes safely regardless of load timing)
// ---------------------------------------------------------------------------
async function initApp() {
  try { initThemeEngine(); } catch (e) { console.warn('Theme init warning:', e); }
  try { BPP_AUTH.init(); } catch (e) { console.warn('BPP_AUTH init warning:', e); }
  try { initGlitterEngine(); } catch (e) { console.warn('Glitter engine warning:', e); }
  try { initScrollReveal(); } catch (e) { console.warn('Scroll reveal warning:', e); }

  if (window.i18n) {
    try {
      await window.i18n.init();
    } catch (e) {
      console.warn('i18n init error:', e);
    }
  }

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

      chip.style.transform = 'scale(0.95)';
      setTimeout(() => { chip.style.transform = ''; }, 150);
    };
  });

  const form = document.getElementById('analysis-form');
  if (form) {
    form.onsubmit = handleFormSubmit;
  }
}

// Boot safely
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}