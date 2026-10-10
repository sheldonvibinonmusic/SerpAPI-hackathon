/**
 * charts.js — BharatPrice Pulse
 * Pure CSS & SVG charts — Ultra-lightweight, reactive, zero external libraries.
 */

window.Charts = {

  /**
   * Horizontal visual bar showing where seller price sits relative to market distribution.
   */
  buildPriceRangeBar(min, q1, median, q3, max, sellerPrice) {
    const values = [min, q1, median, q3, max, sellerPrice].map(Number);
    if (!Number.isFinite(values[0]) || !Number.isFinite(values[2]) || !Number.isFinite(values[4]) || values[4] < values[0]) return '';
    const [lo, firstQ, med, thirdQ, hi, you] = values;
    const span = Math.max(hi - lo, Math.abs(hi) * 0.04, 1);
    const padding = span * 0.12;
    const domainMin = Math.max(0, lo - padding);
    const domainMax = hi + padding;
    const pct = value => Math.min(100, Math.max(0, ((value - domainMin) / (domainMax - domainMin)) * 100));
    const pMin = pct(lo), pQ1 = pct(Number.isFinite(firstQ) ? firstQ : lo);
    const pMed = pct(med), pQ3 = pct(Number.isFinite(thirdQ) ? thirdQ : hi);
    const pMax = pct(hi), pYou = pct(Number.isFinite(you) ? you : lo);
    return `
      <div class="price-range-widget" role="img" aria-label="Online prices range from ₹${lo.toFixed(0)} to ₹${hi.toFixed(0)}; median ₹${med.toFixed(0)}; your price ₹${Number.isFinite(you) ? you.toFixed(0) : 'not provided'}">
        <div class="range-plot">
          <div class="range-axis-labels" aria-hidden="true">
            <span style="left:${pMin}%">Min<br>₹${lo.toFixed(0)}</span>
            <span style="left:${pMed}%">Median<br>₹${med.toFixed(0)}</span>
            <span style="left:${pMax}%">Max<br>₹${hi.toFixed(0)}</span>
          </div>
          <div class="range-track-container">
            <div class="range-track"></div>
            <div class="range-whisker" style="left:${pMin}%;width:${Math.max(0,pMax-pMin)}%"></div>
            <div class="range-iqr-band" style="--band-start:${pQ1}%;--band-size:${Math.max(1,pQ3-pQ1)}%;left:${pQ1}%;width:${Math.max(1,pQ3-pQ1)}%"></div>
            <div class="range-median-marker" style="left:${pMed}%"></div>
            ${Number.isFinite(you) ? `<div class="range-seller-pin ${pYou < pMin ? 'pin-left' : pYou > pMax ? 'pin-right' : ''}" style="--you-position:${pYou}%;left:${pYou}%"><span class="seller-pin-bubble">You · ₹${you.toFixed(0)}</span><span class="seller-pin-line"></span></div>` : ''}
          </div>
        </div>
        <div class="range-legend"><span><i class="iqr-swatch"></i>Middle 50% of prices</span><span><i class="seller-swatch"></i>Your price</span></div>
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