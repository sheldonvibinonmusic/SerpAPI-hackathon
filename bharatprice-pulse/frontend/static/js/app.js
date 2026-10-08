/**
 * app.js — BharatPrice Pulse
 * Main browser controller: form handling, asynchronous fetch,
 * theme management, quick samples, progress orchestration, and UI rendering.
 */

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initialize Theme Engine (Dark/Light mode)
  initThemeEngine();

  // 2. Initialize i18n
  if (window.i18n) {
    await window.i18n.init();
  }

  // 3. Fetch initial quota telemetry
  updateQuotaBadge();

  // 4. Language Selector Change Listener
  const langSelect = document.getElementById('lang-select');
  if (langSelect) {
    langSelect.addEventListener('change', async (e) => {
      const selected = e.target.value;
      if (window.i18n) {
        await window.i18n.loadLanguage(selected);
      }
    });
  }

  // 5. Quick Sample Chips Click Handlers
  document.querySelectorAll('.sample-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const prodEl = document.getElementById('product_raw');
      const cityEl = document.getElementById('city_raw');
      const priceEl = document.getElementById('selling_price');
      const costEl = document.getElementById('landed_cost');
      if (prodEl) prodEl.value = chip.dataset.product || '';
      if (cityEl) cityEl.value = chip.dataset.city || '';
      if (priceEl) priceEl.value = chip.dataset.price || '';
      if (costEl) costEl.value = chip.dataset.cost || '';
      
      // Visual feedback
      chip.style.transform = 'scale(0.95)';
      setTimeout(() => { chip.style.transform = ''; }, 150);
    });
  });

  // 6. Form Submission Listener
  const form = document.getElementById('analysis-form');
  if (form) {
    form.addEventListener('submit', handleFormSubmit);
  }
});

/**
 * Dark/Light Mode Theme Engine with local preference memory
 */
function initThemeEngine() {
  const toggleBtn = document.getElementById('theme-toggle');
  const storedTheme = localStorage.getItem('bpp_theme') || 
    (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');

  document.documentElement.setAttribute('data-theme', storedTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('bpp_theme', newTheme);
    });
  }
}

/**
 * Update the live SerpApi quota badge in the top nav.
 */
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

/**
 * Handle form submission and run analysis pipeline.
 */
async function handleFormSubmit(e) {
  e.preventDefault();

  const productInput = document.getElementById('product_raw');
  const cityInput = document.getElementById('city_raw');
  const priceInput = document.getElementById('selling_price');
  const costInput = document.getElementById('landed_cost');
  const modeRadios = document.getElementsByName('analysis_mode');

  const errorBanner = document.getElementById('error-banner');
  errorBanner.classList.add('hidden');

  // Basic Validation
  const product = productInput.value.trim();
  const city = cityInput.value.trim();
  const price = parseFloat(priceInput.value);
  const cost = costInput.value ? parseFloat(costInput.value) : null;

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

  const payload = {
    product_raw: product,
    city_raw: city,
    selling_price: price,
    landed_cost: cost,
    analysis_mode: selectedMode,
    ui_language: window.i18n ? window.i18n.currentLang : 'en',
  };

  // UI state: Loading
  const submitBtn = document.getElementById('submit-btn');
  const btnSpinner = submitBtn.querySelector('.btn-spinner');
  const progressSection = document.getElementById('progress-section');
  const resultsContainer = document.getElementById('results-container');

  submitBtn.disabled = true;
  if (btnSpinner) btnSpinner.classList.remove('hidden');
  resultsContainer.classList.add('hidden');
  progressSection.classList.remove('hidden');

  // Progressive steps animation
  const progressInterval = runProgressAnimation();

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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

/**
 * Step-by-step progress animation in plain shopkeeper language.
 */
function runProgressAnimation() {
  const progressBar = document.getElementById('progress-bar');
  const progressMsg = document.getElementById('progress-message');

  const steps = [
    { pct: 25, id: 'step-1', msg: 'Checking online prices on Google Shopping…' },
    { pct: 50, id: 'step-2', msg: 'Finding nearby wholesalers and local sellers…' },
    { pct: 75, id: 'step-3', msg: 'Checking recent category news and market events…' },
    { pct: 95, id: 'step-4', msg: 'Analyzing consumer search interest & finalizing recommendation…' },
  ];

  let currentStep = 0;
  if (progressBar) progressBar.style.width = '15%';
  if (progressMsg && steps[0]) progressMsg.textContent = steps[0].msg;

  return setInterval(() => {
    currentStep++;
    if (currentStep < steps.length) {
      if (progressBar) progressBar.style.width = `${steps[currentStep].pct}%`;
      if (progressMsg) progressMsg.textContent = steps[currentStep].msg;
      
      // Update step chip indicators
      document.querySelectorAll('.step-chip').forEach(chip => chip.classList.remove('active'));
      const activeChip = document.getElementById(steps[currentStep].id);
      if (activeChip) activeChip.classList.add('active');
    }
  }, 1200);
}

/**
 * Populate all result cards using Components module.
 */
function renderAnalysisResults(data, sellerPrice, costPrice) {
  const container = document.getElementById('results-container');
  if (container) container.classList.remove('hidden');

  // Dismiss progress bar immediately
  const progressSection = document.getElementById('progress-section');
  if (progressSection) {
    progressSection.classList.add('hidden');
    progressSection.style.display = 'none';
  }

  // Hide any previous error banner
  const errorBanner = document.getElementById('error-banner');
  if (errorBanner) errorBanner.classList.add('hidden');

  // 1. Primary Action Card
  const actionCard = document.getElementById('card-action');
  if (actionCard) {
    actionCard.innerHTML = Components.renderActionCard(
      data.action,
      data.action_label,
      data.explanation,
      data.fusion
    );
  }

  // 2. Online Market Card
  const marketCard = document.getElementById('card-market');
  if (marketCard) {
    marketCard.innerHTML = Components.renderMarketCard(data.market_metrics, sellerPrice);
  }

  // 3. Local Sourcing Card
  const localCard = document.getElementById('card-local');
  if (localCard) {
    const merchants = (Array.isArray(data.local_merchants) && data.local_merchants.length > 0)
      ? data.local_merchants
      : ((Array.isArray(data.sources)) ? data.sources.filter(s => s.source_type === 'Local Discovery') : []);
    localCard.innerHTML = Components.renderLocalCard(merchants, data.location_display || 'Your Area');
  }

  // 4. Consumer Demand Card
  const demandCard = document.getElementById('card-demand');
  if (demandCard) {
    demandCard.innerHTML = Components.renderDemandCard(data.trends_evidence || null);
  }

  // 5. External Signals Card
  const externalCard = document.getElementById('card-external');
  if (externalCard) {
    const newsList = (Array.isArray(data.news_articles) && data.news_articles.length > 0)
      ? data.news_articles
      : ((Array.isArray(data.sources)) ? data.sources.filter(s => s.source_type === 'News Event') : []);
    const finList = (Array.isArray(data.finance_signals) && data.finance_signals.length > 0)
      ? data.finance_signals
      : [];
    externalCard.innerHTML = Components.renderExternalCard(newsList, finList);
  }

  // 6. Seller Economics Card (if cost supplied)
  const econCard = document.getElementById('card-economics');
  if (econCard) {
    if (costPrice && data.market_metrics) {
      econCard.innerHTML = Components.renderEconomicsCard(data.market_metrics, costPrice);
      econCard.classList.remove('hidden');
    } else {
      econCard.classList.add('hidden');
    }
  }

  // 7. GST Reference Card
  const gstCard = document.getElementById('card-gst');
  if (gstCard) {
    if (data.gst_reference_display) {
      gstCard.innerHTML = Components.renderGSTCard(data.gst_reference_display);
      gstCard.classList.remove('hidden');
    } else {
      gstCard.classList.add('hidden');
    }
  }

  // 8. Sources Provenance Card
  const sourcesCard = document.getElementById('card-sources');
  if (sourcesCard) {
    sourcesCard.innerHTML = Components.renderSourcesCard(
      data.sources || [],
      data.searches_consumed,
      data.searches_from_cache
    );
  }

  // Smooth cinematic scroll to results
  if (actionCard) {
    actionCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
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