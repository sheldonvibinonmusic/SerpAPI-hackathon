/**
 * components.js — BharatPrice Pulse
 * High-intensity UI component renderers for analysis outcomes.
 */

window.Components = {

  renderActionCard(action, actionLabel, explanation, fusion, searchQueryUsed) {
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

    const queryEnrichmentHtml = searchQueryUsed ? `
      <div class="search-enrichment-pill" title="SerpApi query enriched by AI Disambiguation Engine">
        <span>🔍 SerpApi Query:</span> <strong>${searchQueryUsed}</strong>
      </div>
    ` : '';

    return `
      <div class="action-header ${actionClass}">
        <div class="action-title-group">
          <span class="action-eyebrow">Strategic Pricing Recommendation</span>
          <h2 class="action-main-title">${actionLabel}</h2>
          <p class="action-headline">${explanation?.headline || ''}</p>
          ${queryEnrichmentHtml}
        </div>
        <div class="action-meta-badges">
          <span class="badge-confidence">
            <svg class="ui-icon-inline" viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 8 4v5c0 5-3.5 8-8 10-4.5-2-8-5-8-10V7zM9 12l2 2 4-4"/></svg>
            Evidence Confidence: ${confLevel} (${confScore}/100)
          </span>
          <div class="confidence-meter" role="img" aria-label="Evidence confidence ${confScore} out of 100"><span class="confidence-fill" style="--score:${Number(confScore)/100}"></span></div>
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
        <div class="card-empty-state"><span class="empty-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 5h16v14H4zM8 9h8M8 13h5"/></svg></span><h3 class="card-title">Online Competitor Prices</h3><p class="form-hint">No comparable online listings found for this exact item.</p></div>
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
          <span class="stat-value text-primary count-up" data-count-up="${Number(sellerPrice || 0)}" data-prefix="₹" data-decimals="2">₹${Number(sellerPrice || 0).toFixed(2)}</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Market Median</span>
          <span class="stat-value count-up" ${metrics.price_median !== null && metrics.price_median !== undefined ? `data-count-up="${Number(metrics.price_median)}" data-prefix="₹" data-decimals="2"` : ''}>₹${metrics.price_median !== null && metrics.price_median !== undefined ? Number(metrics.price_median).toFixed(2) : '—'}</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Observed Gap</span>
          <span class="stat-value ${gapClass} count-up" ${numGap !== null ? `data-count-up="${numGap}" data-suffix="%" data-decimals="1"` : ''}>${numGap !== null ? `${gapSign}${numGap.toFixed(1)}%` : '—'}</span>
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
        <div class="card-empty-state"><span class="empty-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M3 17h4l3-8 4 6 3-4h4"/></svg></span><h3 class="card-title">Consumer Demand Signal</h3><p class="form-hint">Search interest data is unavailable for this item. You can still compare prices and sourcing evidence.</p></div>
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
        <div class="card-empty-state"><span class="empty-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 4h16v16H4zM8 8h8M8 12h8M8 16h5"/></svg></span><h3 class="card-title">External Market Events</h3><p class="form-hint">No recent supply or regulatory alerts were found for this check.</p></div>
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
    const prices = sources.map(s => { const m = String(s.title || '').match(/₹\s?([\d,]+(?:\.\d+)?)/); return m ? Number(m[1].replace(/,/g,'')) : null; }).filter(Number.isFinite).sort((a,b)=>a-b);
    const medianPrice = prices.length ? prices[Math.floor(prices.length/2)] : null;
    const rows = sources.map((s, index) => {
      const url = s.url || s.link || '';
      const dateValue = s.retrieved_at || s.published_date || s.date || '';
      const date = dateValue ? new Date(dateValue) : null;
      const validDate = date && !Number.isNaN(date.getTime());
      const ageDays = validDate ? Math.max(0, Math.floor((Date.now() - date.getTime()) / 86400000)) : null;
      const older = ageDays !== null && ageDays > 365;
      const dateLabel = validDate ? date.toLocaleDateString(undefined, { day: '2-digit', month: 'short', year: 'numeric' }) : 'Date unavailable';
      const ageLabel = ageDays === null ? '' : (older ? 'Older' : ageDays === 0 ? 'Today' : ageDays < 30 ? `${ageDays}d ago` : `${Math.floor(ageDays / 30)}mo ago`);
      const domain = (() => { try { return url ? new URL(url).hostname.replace(/^www\./,'') : ''; } catch (_) { return ''; } })();
      const text = `${s.title || ''} ${s.source_name || ''}`;
      const priceMatch = text.match(/₹\s?([\d,]+(?:\.\d+)?)/);
      const price = priceMatch ? Number(priceMatch[1].replace(/,/g,'')) : null;
      const country = s.country || (/\.in$/i.test(domain) ? 'India' : '');
      const isOutlier = price !== null && medianPrice !== null && medianPrice > 0 && Math.abs(price - medianPrice) > medianPrice * .35;
      const type = String(s.source_type || 'Evidence');
      const kind = /shopping|listing/i.test(type) ? 'shopping' : /local|merchant/i.test(type) ? 'local' : /news/i.test(type) ? 'news' : 'other';
      return `<tr data-kind="${kind}" data-price="${price ?? ''}" data-type="${type.toLowerCase()}" data-source="${(s.source_name || domain || '').toLowerCase()}" data-index="${index}">
        <td><span class="badge badge-neutral">${type}</span></td>
        <td><strong>${s.title || 'Evidence item'}</strong>${isOutlier ? '<span class="outlier-tag">Outlier</span>' : ''}</td>
        <td><span>${s.source_name || 'SerpApi Engine'}</span>${domain ? `<small class="source-domain">${country ? country + ' · ' : ''}${domain}</small>` : ''}</td>
        <td><span class="evidence-date">${dateLabel}</span>${ageLabel ? `<span class="age-tag ${older ? 'age-older' : ''}">${ageLabel}</span>` : ''}</td>
        <td>${url ? `<a href="${url}" target="_blank" rel="noopener noreferrer" class="source-link-icon" aria-label="Open source: ${domain || s.title || 'evidence'}" title="Open source"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6m0-6-9 9"/><path d="M18 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6"/></svg></a>` : '<span class="form-hint">—</span>'}</td>
      </tr>`;
    }).join('');
    return `
      <div class="card-header-flex"><h3 class="card-title">Evidence Provenance Audit</h3><span class="badge badge-neutral">SerpApi Searches: ${searchesConsumed || 1}</span></div>
      <p class="form-hint evidence-intro">Every recommendation is grounded in verifiable source evidence.</p>
      <div class="evidence-controls" role="group" aria-label="Filter evidence">
        <div class="evidence-filters"><button type="button" class="filter-chip active" data-filter="all">All</button><button type="button" class="filter-chip" data-filter="shopping">Shopping</button><button type="button" class="filter-chip" data-filter="local">Local</button><button type="button" class="filter-chip" data-filter="news">News</button></div>
        <label class="sort-control">Sort <select class="evidence-sort" aria-label="Sort evidence"><option value="type">Type</option><option value="price">Price</option><option value="source">Source</option></select></label>
      </div>
      <div class="sources-table-container" tabindex="0" aria-label="Evidence table, scroll horizontally on small screens">
        <table class="sources-table"><thead><tr><th>Type</th><th>Observed Evidence</th><th>Source</th><th>Retrieved</th><th>Link</th></tr></thead><tbody>${rows}</tbody></table>
      </div>`;
  }
};