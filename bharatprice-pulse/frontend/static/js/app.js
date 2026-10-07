/**
 * app.js — BharatPrice Pulse
 * Main browser controller: form handling, asynchronous fetch,
 * progress orchestration, and UI rendering.
 */

document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initialize i18n
  if (window.i18n) {
    await window.i18n.init();
  }

  // 2. Fetch initial quota telemetry
  updateQuotaBadge();

  // 3. Language Selector Change Listener
  const langSelect = document.getElementById('lang-select');
  if (langSelect) {
    langSelect.addEventListener('change', async (e) => {
      const selected = e.target.value;
      if (window.i18n) {
        await window.i18n.loadLanguage(selected);
      }
    });
  }

  // 4. Form Submission Listener
  const form = document.getElementById('analysis-form');
  if (form) {
    form.addEventListener('submit', handleFormSubmit);
  }
});

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
  const errorText = document.getElementById('error-text');
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
  const btnText = submitBtn.querySelector('.btn-text');
  const btnSpinner = submitBtn.querySelector('.btn-spinner');
  const progressSection = document.getElementById('progress-section');
  const resultsContainer = document.getElementById('results-container');

  submitBtn.disabled = true;
  btnSpinner.classList.remove('hidden');
  resultsContainer.classList.add('hidden');
  progressSection.classList.remove('hidden');

  // Simulated progress steps for friendly UX
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
    submitBtn.disabled = false;
    btnSpinner.classList.add('hidden');
    progressSection.classList.add('hidden');
  }
}

/**
 * Step-by-step progress animation in plain shopkeeper language.
 */
function runProgressAnimation() {
  const progressBar = document.getElementById('progress-bar');
  const progressMsg = document.getElementById('progress-message');

  const steps = [
    { pct: 20, msg: 'Checking online prices on Google Shopping…' },
    { pct: 45, msg: 'Finding nearby wholesalers and local sellers…' },
    { pct: 70, msg: 'Checking recent category news and market events…' },
    { pct: 90, msg: 'Analyzing consumer search interest and finalizing recommendation…' },
  ];

  let currentStep = 0;
  progressBar.style.width = '10%';
  progressMsg.textContent = steps[0].msg;

  return setInterval(() => {
    currentStep++;
    if (currentStep < steps.length) {
      progressBar.style.width = `${steps[currentStep].pct}%`;
      progressMsg.textContent = steps[currentStep].msg;
    }
  }, 1200);
}

/**
 * Populate all result cards using Components module.
 */
function renderAnalysisResults(data, sellerPrice, costPrice) {
  const container = document.getElementById('results-container');
  container.classList.remove('hidden');

  // 1. Primary Action Card
  const actionCard = document.getElementById('card-action');
  actionCard.innerHTML = Components.renderActionCard(
    data.action,
    data.action_label,
    data.explanation,
    data.fusion
  );

  // 2. Online Market Card
  const marketCard = document.getElementById('card-market');
  marketCard.innerHTML = Components.renderMarketCard(data.market_metrics, sellerPrice);

  // 3. Local Sourcing Card
  const localCard = document.getElementById('card-local');
  const merchants = (data.fusion && data.fusion.local_merchants_found > 0) ?
    (data.sources ? data.sources.filter(s => s.source_type === 'Local Discovery') : []) : [];
  localCard.innerHTML = Components.renderLocalCard(merchants, data.location_display);

  // 4. Consumer Demand Card
  const demandCard = document.getElementById('card-demand');
  // Reconstruct minimal trends display from explanation/fusion if present
  demandCard.innerHTML = Components.renderDemandCard(data.trends_evidence || null);

  // 5. External Signals Card
  const externalCard = document.getElementById('card-external');
  const newsSources = data.sources ? data.sources.filter(s => s.source_type === 'News Event') : [];
  externalCard.innerHTML = Components.renderExternalCard(newsSources, []);

  // 6. Seller Economics Card (if cost supplied)
  const econCard = document.getElementById('card-economics');
  if (costPrice && data.market_metrics) {
    econCard.innerHTML = Components.renderEconomicsCard(data.market_metrics, costPrice);
    econCard.classList.remove('hidden');
  } else {
    econCard.classList.add('hidden');
  }

  // 7. GST Reference Card
  const gstCard = document.getElementById('card-gst');
  if (data.gst_reference_display) {
    gstCard.innerHTML = Components.renderGSTCard(data.gst_reference_display);
    gstCard.classList.remove('hidden');
  } else {
    gstCard.classList.add('hidden');
  }

  // 8. Sources Provenance Card
  const sourcesCard = document.getElementById('card-sources');
  sourcesCard.innerHTML = Components.renderSourcesCard(
    data.sources,
    data.searches_consumed,
    data.searches_from_cache
  );

  // Scroll smoothly to results
  actionCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showError(msg) {
  const banner = document.getElementById('error-banner');
  const text = document.getElementById('error-text');
  text.textContent = msg;
  banner.classList.remove('hidden');
  banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
}
