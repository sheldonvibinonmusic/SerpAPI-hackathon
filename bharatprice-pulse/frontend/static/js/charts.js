/**
 * charts.js — BharatPrice Pulse
 * Pure CSS & SVG charts — Ultra-lightweight, reactive, zero external libraries.
 */

window.Charts = {

  /**
   * Horizontal visual bar showing where seller price sits relative to market distribution.
   */
  buildPriceRangeBar(min, q1, median, q3, max, sellerPrice) {
    if (!min || !max || min >= max) return '';

    const rangeSpan = (max - min) * 1.2 || 1;
    const baseMin = Math.max(0, min - (max - min) * 0.1);
    
    const toPercent = val => Math.min(98, Math.max(2, ((val - baseMin) / rangeSpan) * 100));

    const pQ1 = toPercent(q1 || min);
    const pMed = toPercent(median);
    const pQ3 = toPercent(q3 || max);
    const pSeller = toPercent(sellerPrice);

    return `
      <div class="price-range-widget">
        <div class="range-labels">
          <span>Min: ₹${min.toFixed(0)}</span>
          <span style="color: var(--color-text);">Median: ₹${median.toFixed(0)}</span>
          <span>Max: ₹${max.toFixed(0)}</span>
        </div>

        <div class="range-track-container">
          <!-- Full track -->
          <div class="range-track"></div>
          
          <!-- Middle 50% IQR band -->
          <div class="range-iqr-band" style="left: ${pQ1}%; width: ${Math.max(4, pQ3 - pQ1)}%;"></div>
          
          <!-- Median tick -->
          <div class="range-median-marker" style="left: ${pMed}%;" title="Market Median: ₹${median.toFixed(2)}"></div>

          <!-- Seller Price Indicator Pin -->
          <div class="range-seller-pin" style="left: ${pSeller}%;" title="Your Price: ₹${sellerPrice.toFixed(2)}">
            <span class="seller-pin-bubble">₹${sellerPrice.toFixed(0)} (You)</span>
            <div class="seller-pin-line"></div>
          </div>
        </div>

        <div class="range-legend">
          <span><span class="iqr-swatch"></span> Middle 50% Range</span>
          <span><span class="seller-swatch"></span> Your Shelf Price</span>
        </div>
      </div>
    `;
  },

  /**
   * SVG sparkline of Google Trends search interest over time.
   */
  buildTrendSparkline(points) {
    if (!points || !Array.isArray(points) || points.length < 2) return '<p class="form-hint">Insufficient trend history.</p>';

    const width = 320;
    const height = 65;
    const values = points.map(p => Number(p?.value) || 0);
    const maxVal = Math.max(...values, 100);
    const minVal = 0;

    const coords = points.map((p, i) => {
      const x = (i / (points.length - 1)) * (width - 20) + 10;
      const y = height - 10 - (((Number(p?.value) || 0) - minVal) / (maxVal - minVal)) * (height - 20);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });

    const pathD = `M ${coords.join(' L ')}`;

    return `
      <div class="trend-sparkline-container">
        <svg viewBox="0 0 ${width} ${height}" class="trend-sparkline-svg">
          <defs>
            <linearGradient id="trendGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="var(--saffron-primary)" />
              <stop offset="100%" stop-color="var(--emerald-success)" />
            </linearGradient>
          </defs>
          <path d="${pathD}" fill="none" stroke="url(#trendGrad)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
          ${coords.map(c => {
            const parts = String(c).split(',');
            return `<circle cx="${parts[0] || 0}" cy="${parts[1] || 0}" r="3" fill="var(--color-card)" stroke="var(--saffron-primary)" stroke-width="2" />`;
          }).join('')}
        </svg>
        <div class="sparkline-labels">
          <span>${points[0]?.date || 'Earlier'}</span>
          <span>${points[points.length - 1]?.date || 'Recent'}</span>
        </div>
      </div>
    `;
  },

  /**
   * Horizontal bar breakdown of regional demand by Indian states.
   */
  buildRegionHeatBar(regions) {
    if (!regions || !Array.isArray(regions) || regions.length === 0) return '';

    const topRegions = regions.slice(0, 5);
    const maxVal = Math.max(...topRegions.map(r => r.max_value_index || 0), 100);

    return `
      <div class="region-bars-container">
        ${topRegions.map(r => {
          const pct = Math.min(100, Math.max(6, ((r.max_value_index || 0) / maxVal) * 100));
          return `
            <div class="region-bar-row">
              <span class="region-name" title="${r.location}">${r.location}</span>
              <div class="region-track">
                <div class="region-fill" style="width: ${pct}%;"></div>
              </div>
              <span class="region-val">${r.max_value_index || 0}</span>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }
};