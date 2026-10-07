/**
 * components.js — BharatPrice Pulse
 * UI card and component renderers for analysis results.
 */

window.Components = {

  renderActionCard(action, actionLabel, explanation, fusion) {
    const actionClass = `action-${action.toLowerCase().replace(/_/g, '-')}`;
    const confClass = `conf-${fusion.confidence.toLowerCase()}`;

    const pointsHtml = explanation && explanation.points ? explanation.points.map(pt => `
      <li class="action-bullet ${pt.is_disclaimer ? 'bullet-disclaimer' : ''}">
        ${pt.is_disclaimer ? 'ℹ️' : '✓'} ${pt.text}
      </li>
    `).join('') : '';

    return `
      <div class="action-header ${actionClass}">
        <div class="action-title-group">
          <span class="action-eyebrow">Recommended Business Action</span>
          <h2 class="action-main-title">${actionLabel}</h2>
          <p class="action-headline">${explanation?.headline || ''}</p>
        </div>
        <div class="action-meta-badges">
          <span class="badge-confidence ${confClass}">
            Evidence Strength: ${fusion.confidence.toUpperCase()} (${fusion.confidence_score.toFixed(0)}/100)
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
        <p class="text-muted">No comparable online listings found.</p>
      `;
    }

    const gap = metrics.price_gap_percent;
    const gapClass = gap > 5 ? 'text-danger' : (gap < -5 ? 'text-success' : 'text-primary');
    const gapSign = gap > 0 ? '+' : '';

    const rangeChartHtml = metrics.price_min && metrics.price_max ? 
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
        <span class="badge badge-neutral">${metrics.comparable_count} Listings Compared</span>
      </div>

      <div class="market-stats-grid">
        <div class="stat-box">
          <span class="stat-label">Your Shelf Price</span>
          <span class="stat-value text-primary">₹${sellerPrice.toFixed(2)}</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Observed Median</span>
          <span class="stat-value">₹${metrics.price_median?.toFixed(2) || '—'}</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Price Gap</span>
          <span class="stat-value ${gapClass}">${gap !== null ? `${gapSign}${gap.toFixed(1)}%` : '—'}</span>
        </div>
      </div>

      ${rangeChartHtml}

      <div class="stat-subtext">
        <span>Observed Range: ₹${metrics.price_min?.toFixed(0)} – ₹${metrics.price_max?.toFixed(0)}</span>
        ${metrics.unit_label && metrics.unit_price_median ? `<span>Unit Median: ₹${metrics.unit_price_median.toFixed(2)} ${metrics.unit_label}</span>` : ''}
      </div>
    `;
  },

  renderLocalCard(merchants, city) {
    if (!merchants || merchants.length === 0) {
      return `
        <h3 class="card-title">Local Sourcing & Suppliers (${city})</h3>
        <p class="text-muted">No nearby merchants or wholesalers found in this location.</p>
      `;
    }

    const wholesalers = merchants.filter(m => m.is_wholesaler_or_distributor);

    return `
      <div class="card-header-flex">
        <h3 class="card-title">Nearby Suppliers in ${city}</h3>
        <span class="badge badge-success">${merchants.length} Discovered</span>
      </div>

      <p class="section-intro">
        Discovered on Google Local. Useful for exploring wholesale procurement alternatives:
      </p>

      <div class="merchants-list">
        ${merchants.slice(0, 4).map(m => `
          <div class="merchant-item ${m.is_wholesaler_or_distributor ? 'merchant-wholesale' : ''}">
            <div class="merchant-info">
              <strong class="merchant-name">${m.title}</strong>
              <span class="merchant-type">${m.type || m.types[0] || 'Merchant'}</span>
              <span class="merchant-address">📍 ${m.address || city}</span>
            </div>
            <div class="merchant-side">
              ${m.rating ? `<span class="merchant-rating">⭐ ${m.rating} <small>(${m.reviews || 0})</small></span>` : ''}
              ${m.is_wholesaler_or_distributor ? `<span class="badge badge-wholesale">Wholesaler</span>` : ''}
            </div>
          </div>
        `).join('')}
      </div>

      <div class="local-disclaimer">
        ⚠️ <em>Merchant presence discovered via Google Local. Physical SKU inventory and spot rates must be verified by calling or visiting.</em>
      </div>
    `;
  },

  renderDemandCard(trends) {
    if (!trends || !trends.interest_over_time || trends.interest_over_time.length === 0) {
      return `
        <h3 class="card-title">Consumer Demand Signal</h3>
        <p class="text-muted">Google Trends search-interest data unavailable for this item.</p>
      `;
    }

    const dirBadgeClass = trends.trend_direction === 'rising' ? 'badge-success' : 
                         (trends.trend_direction === 'falling' ? 'badge-danger' : 'badge-neutral');

    return `
      <div class="card-header-flex">
        <h3 class="card-title">Consumer Search Interest</h3>
        <span class="badge ${dirBadgeClass}">${(trends.trend_direction || 'STABLE').toUpperCase()}</span>
      </div>

      <p class="section-intro">
        Google Trends index across India over recent weeks:
      </p>

      ${Charts.buildTrendSparkline(trends.interest_over_time)}

      ${trends.interest_by_region && trends.interest_by_region.length > 0 ? `
        <h4 class="subheading">Top Regional Interest (States)</h4>
        ${Charts.buildRegionHeatBar(trends.interest_by_region)}
      ` : ''}

      <small class="text-muted" style="display:block; margin-top:0.75rem;">
        ${trends.disclaimer}
      </small>
    `;
  },

  renderExternalCard(news, finance) {
    const hasNews = news && news.length > 0;
    const hasFin = finance && finance.length > 0;

    if (!hasNews && !hasFin) {
      return `
        <h3 class="card-title">External Market Events</h3>
        <p class="text-muted">No major recent supply chain or regulatory disruptions detected.</p>
      `;
    }

    return `
      <div class="card-header-flex">
        <h3 class="card-title">External Market Events</h3>
        <span class="badge badge-neutral">Google News & Finance</span>
      </div>

      ${hasFin ? `
        <div class="finance-signals-box">
          ${finance.map(f => `
            <div class="finance-signal-row">
              <strong>${f.instrument_label}</strong>: 
              <span>${f.current_value?.toFixed(2) || '—'}</span>
              ${f.change_percent ? `<span class="${f.change_percent >= 0 ? 'text-danger' : 'text-success'}">(${f.change_percent > 0 ? '+' : ''}${f.change_percent.toFixed(2)}%)</span>` : ''}
              ${f.interpretation ? `<p class="finance-note">${f.interpretation}</p>` : ''}
            </div>
          `).join('')}
        </div>
      ` : ''}

      ${hasNews ? `
        <div class="news-list">
          ${news.slice(0, 3).map(art => `
            <div class="news-item">
              <a href="${art.link || '#'}" target="_blank" rel="noopener" class="news-title">${art.title}</a>
              <div class="news-meta">
                <span>📰 ${art.source_name || 'News'}</span>
                ${art.published_date ? `<span>📅 ${art.published_date}</span>` : ''}
                ${art.signal_direction && art.signal_direction !== 'neutral' ? `<span class="badge badge-sm badge-warning">${art.signal_direction.replace('_', ' ')}</span>` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}
    `;
  },

  renderEconomicsCard(metrics, costPrice) {
    if (!costPrice || !metrics || metrics.gross_margin_percent === null) return '';

    const margin = metrics.gross_margin_percent;
    const marginClass = margin > 15 ? 'text-success' : (margin < 8 ? 'text-danger' : 'text-primary');

    return `
      <h3 class="card-title">Your Unit Economics & Margins</h3>
      <div class="market-stats-grid">
        <div class="stat-box">
          <span class="stat-label">Your Purchase Cost</span>
          <span class="stat-value">₹${costPrice.toFixed(2)}</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Your Gross Margin</span>
          <span class="stat-value ${marginClass}">${margin.toFixed(1)}%</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Margin at Market Median</span>
          <span class="stat-value">${metrics.margin_vs_market_median ? `${metrics.margin_vs_market_median.toFixed(1)}%` : '—'}</span>
        </div>
      </div>
      <small class="text-muted">Calculated as: (Selling Price - Cost) / Selling Price × 100.</small>
    `;
  },

  renderGSTCard(gst) {
    if (!gst) return '';

    return `
      <div class="card-header-flex">
        <h3 class="card-title">Official GST Tax Reference</h3>
        <span class="badge badge-info">HSN ${gst.hsn_code || 'Reference'}</span>
      </div>
      <p>
        <strong>Applicable GST Rate:</strong> ${gst.rate_percent !== null ? `${gst.rate_percent}%` : 'Exempt / Zero'}
      </p>
      <p class="text-muted"><small>${gst.description}</small></p>
      <small class="text-muted">Source: ${gst.source} (Verified offline, 0 API calls).</small>
    `;
  },

  renderSourcesCard(sources, searchesConsumed, fromCache) {
    if (!sources || sources.length === 0) return '';

    return `
      <div class="card-header-flex">
        <h3 class="card-title">Evidence Provenance & Verification Audit</h3>
        <span class="badge badge-neutral">SerpApi Searches: ${searchesConsumed}</span>
      </div>

      <p class="section-intro">
        Every claim made in BharatPrice Pulse is grounded in observable external citations:
      </p>

      <div class="sources-table-container">
        <table class="sources-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Citation / Listing</th>
              <th>Source</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            ${sources.map(s => `
              <tr>
                <td><span class="badge badge-sm badge-neutral">${s.source_type}</span></td>
                <td><strong>${s.title}</strong></td>
                <td>${s.source_name || 'SerpApi'}</td>
                <td>
                  ${s.url ? `<a href="${s.url}" target="_blank" rel="noopener" class="btn btn-sm btn-outline">View Listing ↗</a>` : '<span>Local Entry</span>'}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }
};
