/**
 * charts.js — BharatPrice Pulse
 * Pure CSS & SVG charts — Zero external libraries (No Chart.js, No D3).
 * Extremely lightweight, instant rendering, 100% offline reproducible.
 */

window.Charts = {

  /**
   * Horizontal visual bar showing where seller price sits relative to market distribution.
   */
  buildPriceRangeBar(min, q1, median, q3, max, sellerPrice) {
    if (!min || !max || min >= max) return '';

    // Calculate percentages on the scale [min, max] with a 10% visual padding
    const rangeSpan = (max - min) * 1.2 || 1;
    const baseMin = Math.max(0, min - (max - min) * 0.1);
    
    const toPercent = val => Math.min(100, Math.max(0, ((val - baseMin) / rangeSpan) * 100));

    const pMin = toPercent(min);
    const pQ1 = toPercent(q1 || min);
    const pMed = toPercent(median);
    const pQ3 = toPercent(q3 || max);
    const pMax = toPercent(max);
    const pSeller = toPercent(sellerPrice);

    return `
      <div class="price-range-widget">
        <div class="range-labels">
          <span>Min: ₹${min.toFixed(0)}</span>
          <span class="range-label-median">Median: ₹${median.toFixed(0)}</span>
          <span>Max: ₹${max.toFixed(0)}</span>
        </div>

        <div class="range-track-container">
          <!-- Full track -->
          <div class="range-track"></div>
          
          <!-- Middle 50% IQR band -->
          <div class="range-iqr-band" style="left: ${pQ1}%; width: ${Math.max(2, pQ3 - pQ1)}%;"></div>
          
          <!-- Median tick -->
          <div class="range-median-marker" style="left: ${pMed}%;" title="Market Median: ₹${median.toFixed(2)}"></div>

          <!-- Seller Price Indicator Pin -->
          <div class="range-seller-pin" style="left: ${pSeller}%;" title="Your Price: ₹${sellerPrice.toFixed(2)}">
            <span class="seller-pin-bubble">₹${sellerPrice.toFixed(0)} (You)</span>
            <div class="seller-pin-line"></div>
          </div>
        </div>

        <div class="range-legend">
          <span class="legend-iqr"><span class="iqr-swatch"></span> Middle 50% of Online Sellers</span>
          <span class="legend-seller"><span class="seller-swatch"></span> Your Current Price</span>
        </div>
      </div>
    `;
  },

  /**
   * SVG sparkline of Google Trends search interest over time.
   */
  buildTrendSparkline(points) {
    if (!points || points.length < 2) return '<p class="text-muted">Insufficient trend history.</p>';

    const width = 300;
    const height = 60;
    const maxVal = Math.max(...points.map(p => p.value), 100);
    const minVal = 0;

    const coords = points.map((p, i) => {
      const x = (i / (points.length - 1)) * (width - 10) + 5;
      const y = height - 5 - ((p.value - minVal) / (maxVal - minVal)) * (height - 15);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });

    const pathD = `M ${coords.join(' L ')}`;

    return `
      <div class="trend-sparkline-container">
        <svg viewBox="0 0 ${width} ${height}" class="trend-sparkline-svg">
          <path d="${pathD}" fill="none" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
          ${coords.map(c => `<circle cx="${c.split(',')[0]}" cy="${c.split(',')[1]}" r="2" fill="var(--color-accent)" />`).join('')}
        </svg>
        <div class="sparkline-labels">
          <small>${points[0].date || 'Earlier'}</small>
          <small>${points[points.length - 1].date || 'Recent'}</small>
        </div>
      </div>
    `;
  },

  /**
   * Horizontal bar breakdown of regional demand by Indian states.
   */
  buildRegionHeatBar(regions) {
    if (!regions || regions.length === 0) return '';

    const topRegions = regions.slice(0, 5);
    const maxVal = Math.max(...topRegions.map(r => r.max_value_index), 100);

    return `
      <div class="region-bars-container">
        ${topRegions.map(r => {
          const pct = Math.min(100, Math.max(5, (r.max_value_index / maxVal) * 100));
          return `
            <div class="region-bar-row">
              <span class="region-name">${r.location}</span>
              <div class="region-track">
                <div class="region-fill" style="width: ${pct}%;"></div>
              </div>
              <span class="region-val">${r.max_value_index}</span>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }
};
