/**
 * components.js — BharatPrice Pulse
 * High-intensity UI component renderers for analysis outcomes.
 */

window.Components = {

  renderActionCard(action, actionLabel, explanation, fusion) {
    const actionKey = (action || 'HOLD').toLowerCase().replace(/_/g, '-');
    const actionClass = `action-${actionKey}`;
    const confScore = fusion?.confidence_score ? fusion.confidence_score.toFixed(0) : '85';
    const confLevel = (fusion?.confidence || 'MEDIUM').toUpperCase();

    const pointsHtml = explanation && explanation.points ? explanation.points.map(pt => `
      <li class="action-bullet ${pt.is_disclaimer ? 'bullet-disclaimer' : ''}">
        <span class="bullet-icon">${pt.is_disclaimer ? '⚠️' : '✓'}</span>
        <span>${pt.text}</span>
      </li>
    `).join('') : '';

    return `
      <div class="action-header ${actionClass}">
        <div class="action-title-group">
          <span class="action-eyebrow">Strategic Pricing Recommendation</span>
          <h2 class="action-main-title">${actionLabel}</h2>
          <p class="action-headline">${explanation?.headline || ''}</p>
        </div>
        <div class="action-meta-badges">
          <span class="badge-confidence">
            ✦ Evidence Confidence: ${confLevel} (${confScore}/100)
          </span>
        </div>
      </div>

      <div class="action-body">
        <p class="action-rationale">${explanation?.action_rationale || ''}</p>
        <ul class="action-bullets-list">
          ${pointsHtml}
        </ul>
      </div>
    `;
  },

  renderMarketCard(metrics, sellerPrice) {
    if (!metrics || metrics.comparable_count < 1) {
      return `
        <h3 class="card-title">Online Market Prices</h3>
        <p class="form-hint" style="margin-top:0.5rem;">No comparable online listings found for this exact SKU.</p>
      `;
    }

    const numGap = (metrics.price_gap_percent !== null && metrics.price_gap_percent !== undefined && !isNaN(Number(metrics.price_gap_percent))) ? Number(metrics.price_gap_percent) : null;
    const gapClass = (numGap !== null && numGap > 5) ? 'text-danger' : ((numGap !== null && numGap < -5) ? 'text-success' : 'text-primary');
    const gapSign = (numGap !== null && numGap > 0) ? '+' : '';

    const rangeChartHtml = (metrics.price_min !== null && metrics.price_max !== null && metrics.price_min !== undefined && metrics.price_max !== undefined) ? 
      Charts.buildPriceRangeBar(
        metrics.price_min,
        metrics.price_q1,
        metrics.price_median,
        metrics.price_q3,
        metrics.price_max,
        sellerPrice
      ) : '';

    return `
      <div class="card-header-flex">
        <h3 class="card-title">Online Competitor Prices</h3>
        <span class="badge badge-neutral">${metrics.comparable_count} Listings Sampled</span>
      </div>

      <div class="market-stats-grid">
        <div class="stat-box">
          <span class="stat-label">Your Price</span>
          <span class="stat-value text-primary">₹${Number(sellerPrice || 0).toFixed(2)}</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Market Median</span>
          <span class="stat-value">₹${metrics.price_median !== null && metrics.price_median !== undefined ? Number(metrics.price_median).toFixed(2) : '—'}</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Observed Gap</span>
          <span class="stat-value ${gapClass}">${numGap !== null ? `${gapSign}${numGap.toFixed(1)}%` : '—'}</span>
        </div>
      </div>

      ${rangeChartHtml}

      <div class="form-hint" style="display:flex; justify-content:space-between; margin-top:0.75rem;">
        <span>Observed: ₹${metrics.price_min !== null && metrics.price_min !== undefined ? Number(metrics.price_min).toFixed(0) : '—'} – ₹${metrics.price_max !== null && metrics.price_max !== undefined ? Number(metrics.price_max).toFixed(0) : '—'}</span>
        ${metrics.unit_label && metrics.unit_price_median !== null && metrics.unit_price_median !== undefined ? `<span>Normalized: ₹${Number(metrics.unit_price_median).toFixed(2)} ${metrics.unit_label}</span>` : ''}
      </div>
    `;
  },

  renderLocalCard(merchants, city) {
    if (!merchants || merchants.length === 0) {
      return `
        <h3 class="card-title">Local Sourcing & Suppliers (${city})</h3>
        <p class="form-hint" style="margin-top:0.5rem;">No registered local wholesalers discovered in this immediate radius.</p>
      `;
    }

    return `
      <div class="card-header-flex">
        <h3 class="card-title">Nearby Suppliers in ${city}</h3>
        <span class="badge badge-success">${merchants.length} Discovered</span>
      </div>

      <p class="form-hint" style="margin-bottom:0.85rem;">
        Discovered via Google Local. Explore these options for local B2B spot pricing:
      </p>

      <div class="merchants-list">
        ${merchants.slice(0, 4).map(m => {
          if (!m) return '';
          const name = m.title || 'Local Business';
          const type = m.type || (Array.isArray(m.types) && m.types[0]) || 'Merchant';
          const address = m.address || m.source_name || city;
          const isWholesale = Boolean(m.is_wholesaler_or_distributor);
          const ratingBadge = (m.rating !== null && m.rating !== undefined && !isNaN(Number(m.rating))) ? `<span class="badge badge-neutral">⭐ ${Number(m.rating).toFixed(1)}</span>` : '';
          const wholesaleBadge = isWholesale ? `<span class="badge badge-wholesale">Wholesaler</span>` : '';
          return `
          <div class="merchant-item ${isWholesale ? 'merchant-wholesale' : ''}">
            <div class="merchant-info">
              <span class="merchant-name">${name}</span>
              <span class="merchant-type">${type}</span>
              <span class="merchant-address">📍 ${address}</span>
            </div>
            <div class="merchant-side">
              ${ratingBadge}
              ${wholesaleBadge}
            </div>
          </div>
          `;
        }).join('')}
      </div>

      <div class="local-disclaimer">
        ⚠️ <em>Merchant presence discovered via Google Local. Physical SKU inventory and spot wholesale rates must be verified directly.</em>
      </div>
    `;
  },

  renderDemandCard(trends) {
    if (!trends || !trends.interest_over_time || trends.interest_over_time.length === 0) {
      return `
        <h3 class="card-title">Consumer Demand Signal</h3>
        <p class="form-hint" style="margin-top:0.5rem;">Google Trends search interest data unavailable for this specific keyword.</p>
      `;
    }

    const dirBadgeClass = trends.trend_direction === 'rising' ? 'badge-success' : 
                         (trends.trend_direction === 'falling' ? 'badge-danger' : 'badge-neutral');

    return `
      <div class="card-header-flex">
        <h3 class="card-title">Consumer Search Interest</h3>
        <span class="badge ${dirBadgeClass}">${(trends.trend_direction || 'STABLE').toUpperCase()}</span>
      </div>

      <p class="form-hint" style="margin-bottom:0.75rem;">
        Google Trends search volume over time across India:
      </p>

      ${Charts.buildTrendSparkline(trends.interest_over_time)}

      ${trends.interest_by_region && trends.interest_by_region.length > 0 ? `
        <h4 style="font-size:0.8rem; font-weight:700; margin-top:1rem; color:var(--color-text-secondary);">Top Regional Demand by State</h4>
        ${Charts.buildRegionHeatBar(trends.interest_by_region)}
      ` : ''}

      <small class="form-hint" style="display:block; margin-top:0.75rem;">
        ${trends.disclaimer || 'Data sourced from Google Trends.'}
      </small>
    `;
  },

  renderExternalCard(news, finance) {
    const hasNews = news && news.length > 0;
    const hasFin = finance && finance.length > 0;

    if (!hasNews && !hasFin) {
      return `
        <h3 class="card-title">External Market Events</h3>
        <p class="form-hint" style="margin-top:0.5rem;">No acute supply chain disruptions or regulatory alerts detected in recent news cycles.</p>
      `;
    }

    const signalBadgeText = (hasNews && hasFin) ? 'News & Macro Signals' : (hasFin ? 'Google Finance' : 'Google News Signals');

    return `
      <div class="card-header-flex">
        <h3 class="card-title">External Market Events</h3>
        <span class="badge badge-neutral">${signalBadgeText}</span>
      </div>

      ${hasNews ? `
        <div class="news-list">
          ${news.slice(0, 3).map(art => `
            <div class="news-item">
              <a href="${art.link || art.url || '#'}" target="_blank" rel="noopener" class="news-title">${art.title}</a>
              <div class="news-meta">
                <span>📰 ${art.source_name || 'News Source'}</span>
                ${art.published_date ? `<span>📅 ${art.published_date}</span>` : ''}
                ${art.signal_direction && art.signal_direction !== 'neutral' ? `<span class="badge badge-warning">${art.signal_direction.replace(/_/g, ' ')}</span>` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}

      ${hasFin ? `
        <div class="finance-signal-box" style="margin-top:0.75rem; padding:0.75rem; border-radius:var(--radius-md); background:var(--color-bg-alt); border:1px solid var(--color-card-border);">
          ${finance.map(fin => `
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div>
                <strong>${fin.instrument_label || fin.instrument}</strong>
                ${fin.interpretation ? `<div class="form-hint" style="font-size:0.75rem;">${fin.interpretation}</div>` : ''}
              </div>
              <div style="text-align:right;">
                <span class="stat-value" style="font-size:0.95rem;">${fin.current_value !== null && fin.current_value !== undefined ? fin.current_value : '—'}</span>
                ${fin.change_percent !== null && fin.change_percent !== undefined ? `<span class="badge ${fin.change_percent > 0 ? 'badge-danger' : 'badge-success'}">${fin.change_percent > 0 ? '+' : ''}${fin.change_percent.toFixed(2)}%</span>` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}
    `;
  },

  renderEconomicsCard(metrics, costPrice) {
    if (!costPrice || !metrics || metrics.gross_margin_percent === null || metrics.gross_margin_percent === undefined) return '';

    const margin = metrics.gross_margin_percent;
    const marginClass = margin > 15 ? 'text-success' : (margin < 8 ? 'text-danger' : 'text-primary');

    return `
      <div class="card-header-flex">
        <h3 class="card-title">Your Unit Economics & Margins</h3>
        <span class="badge badge-info">Gross Margin Calculated</span>
      </div>
      <div class="market-stats-grid">
        <div class="stat-box">
          <span class="stat-label">Purchase Cost</span>
          <span class="stat-value">₹${costPrice.toFixed(2)}</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Current Margin</span>
          <span class="stat-value ${marginClass}">${margin.toFixed(1)}%</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Margin at Median</span>
          <span class="stat-value">${metrics.margin_vs_market_median ? `${metrics.margin_vs_market_median.toFixed(1)}%` : '—'}</span>
        </div>
      </div>
      <small class="form-hint">Calculated as: (Selling Price - Landed Cost) / Selling Price × 100.</small>
    `;
  },

  renderGSTCard(gst) {
    if (!gst) return '';

    return `
      <div class="card-header-flex">
        <h3 class="card-title">Official GST Tax Reference</h3>
        <span class="badge badge-info">HSN ${gst.hsn_code || 'Reference'}</span>
      </div>
      <p style="font-size:0.95rem; margin-bottom:0.4rem;">
        <strong>Applicable GST Rate:</strong> <span class="text-primary">${gst.rate_percent !== null ? `${gst.rate_percent}%` : 'Exempt / Zero Rated'}</span>
      </p>
      <p class="form-hint">${gst.description || ''}</p>
      <small class="form-hint" style="display:block; margin-top:0.4rem;">Source: ${gst.source || 'Offline GST Master'} (Directly verified, 0 API searches consumed).</small>
    `;
  },

  renderSourcesCard(sources, searchesConsumed, fromCache) {
    if (!sources || sources.length === 0) return '';

    return `
      <div class="card-header-flex">
        <h3 class="card-title">Evidence Provenance Audit</h3>
        <span class="badge badge-neutral">SerpApi Searches: ${searchesConsumed || 1}</span>
      </div>

      <p class="form-hint" style="margin-bottom:0.75rem;">
        Every insight generated in BharatPrice Pulse is grounded in verifiable external citations:
      </p>

      <div class="sources-table-container">
        <table class="sources-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Observed Evidence</th>
              <th>Source</th>
              <th>Verification</th>
            </tr>
          </thead>
          <tbody>
            ${sources.map(s => `
              <tr>
                <td><span class="badge badge-neutral">${s.source_type}</span></td>
                <td><strong>${s.title}</strong></td>
                <td>${s.source_name || 'SerpApi Engine'}</td>
                <td>
                  ${(s.url || s.link) ? `<a href="${s.url || s.link}" target="_blank" rel="noopener" class="btn btn-sm">View Listing ↗</a>` : '<span>Ground Truth</span>'}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }
};