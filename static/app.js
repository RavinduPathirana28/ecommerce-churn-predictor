document.addEventListener('DOMContentLoaded', () => {

  // =========================================================================
  // TAB NAVIGATION
  // =========================================================================
  const tabLinks = document.querySelectorAll('.tab-link');
  const tabPanes = document.querySelectorAll('.tab-pane');

  function switchTab(tabId) {
    tabLinks.forEach(link => {
      const isTarget = link.getAttribute('data-tab') === tabId;
      link.classList.toggle('active', isTarget);
      link.setAttribute('aria-selected', isTarget ? 'true' : 'false');
    });

    tabPanes.forEach(pane => {
      pane.classList.toggle('active', pane.id === tabId);
    });
  }

  tabLinks.forEach(link => {
    link.addEventListener('click', () => {
      const tabId = link.getAttribute('data-tab');
      switchTab(tabId);
    });
  });

  const footerSpecsLink = document.getElementById('footer-specs-link');
  if (footerSpecsLink) {
    footerSpecsLink.addEventListener('click', (e) => {
      e.preventDefault();
      switchTab('tab-benchmarks');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // =========================================================================
  // TOAST NOTIFICATIONS
  // =========================================================================
  const toast = document.getElementById('toast-notify');
  let toastTimeout = null;

  function showToast(message) {
    if (!toast) return;
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
      toast.hidden = true;
    }, 3200);
  }

  // =========================================================================
  // FORM ELEMENTS & CONTROLS
  // =========================================================================
  const form = document.getElementById('churn-form');
  const predictBtn = document.getElementById('predict-btn');
  const globalResetBtn = document.getElementById('global-reset-btn');
  const complainCheckbox = document.getElementById('Complain');
  const complaintAlertBox = document.getElementById('complaint-alert-box');
  const complaintText = document.getElementById('complaint-text');
  const complaintIcon = document.getElementById('complaint-icon');
  const tenureInsight = document.getElementById('tenure-insight');

  // Sliders config
  const sliders = [
    { id: 'Tenure', suffix: ' mo' },
    { id: 'NumberOfDeviceRegistered', suffix: '' },
    { id: 'NumberOfAddress', suffix: '' },
    { id: 'OrderCount', suffix: '' },
    { id: 'DaySinceLastOrder', suffix: ' d' },
    { id: 'CashbackAmount', prefix: '$', suffix: '' },
    { id: 'CouponUsed', suffix: '' },
    { id: 'WarehouseToHome', suffix: ' km' },
    { id: 'OrderAmountHikeFromlastYear', suffix: '%' },
    { id: 'HourSpendOnApp', suffix: ' h' }
  ];

  function updateSlider(item) {
    const el = document.getElementById(item.id);
    const valEl = document.getElementById(`${item.id}-val`);
    if (!el) return;

    const min = parseFloat(el.min) || 0;
    const max = parseFloat(el.max) || 100;
    const val = parseFloat(el.value) || 0;
    const pct = Math.max(0, Math.min(100, ((val - min) / (max - min)) * 100));

    el.style.setProperty('--pct', `${pct}%`);

    if (valEl) {
      const prefix = item.prefix || '';
      const suffix = item.suffix || '';
      valEl.textContent = `${prefix}${val}${suffix}`;
    }

    // Special tenure hint update
    if (item.id === 'Tenure' && tenureInsight) {
      if (val <= 3) {
        tenureInsight.innerHTML = '<span class="insight-bullet">🚨</span> Critical Hazard Period: First 3 months account for 68.9% of churn (41.9% attrition rate vs 5.6% after).';
        tenureInsight.style.borderColor = 'rgba(239, 68, 68, 0.4)';
        tenureInsight.style.color = '#fca5a5';
      } else if (val <= 12) {
        tenureInsight.innerHTML = '<span class="insight-bullet">⚡</span> Growth Period: Churn rate drops to 12.4% as adoption takes root.';
        tenureInsight.style.borderColor = 'rgba(245, 158, 11, 0.4)';
        tenureInsight.style.color = '#fbbf24';
      } else {
        tenureInsight.innerHTML = '<span class="insight-bullet">✅</span> Established Loyal Account: Retention stability is > 95% for accounts past 1 year.';
        tenureInsight.style.borderColor = 'rgba(16, 185, 129, 0.4)';
        tenureInsight.style.color = '#86efac';
      }
    }
  }

  // Attach slider listeners
  sliders.forEach(item => {
    const el = document.getElementById(item.id);
    if (el) {
      updateSlider(item);
      el.addEventListener('input', () => {
        updateSlider(item);
        debouncedPredict();
      });
    }
  });

  // Segmented Pill Buttons
  document.querySelectorAll('.pill-group').forEach(group => {
    const groupName = group.getAttribute('data-group');
    group.querySelectorAll('.pill-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        group.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        debouncedPredict();
      });
    });
  });

  function getPillValue(groupName) {
    const active = document.querySelector(`.pill-group[data-group="${groupName}"] .pill-btn.active`);
    return active ? active.getAttribute('data-val') : null;
  }

  function setPillValue(groupName, val) {
    const btn = document.querySelector(`.pill-group[data-group="${groupName}"] .pill-btn[data-val="${val}"]`);
    if (btn) {
      const group = btn.closest('.pill-group');
      if (group) {
        group.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      }
    }
  }

  // Star Rating Bar
  const starLabels = {
    '1': '1 • Very Dissatisfied',
    '2': '2 • Dissatisfied',
    '3': '3 • Neutral',
    '4': '4 • Satisfied',
    '5': '5 • Highly Satisfied'
  };

  const starGroup = document.querySelector('.star-rating[data-group="SatisfactionScore"]');
  const satValEl = document.getElementById('SatisfactionScore-val');

  if (starGroup) {
    starGroup.querySelectorAll('.star-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        starGroup.querySelectorAll('.star-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const val = btn.getAttribute('data-val');
        if (satValEl) satValEl.textContent = starLabels[val] || `${val} Stars`;
        debouncedPredict();
      });
    });
  }

  function getStarValue() {
    const active = document.querySelector('.star-rating[data-group="SatisfactionScore"] .star-btn.active');
    return active ? parseInt(active.getAttribute('data-val'), 10) : 3;
  }

  function setStarValue(val) {
    const btn = document.querySelector(`.star-rating[data-group="SatisfactionScore"] .star-btn[data-val="${val}"]`);
    if (btn && starGroup) {
      starGroup.querySelectorAll('.star-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      if (satValEl) satValEl.textContent = starLabels[val] || `${val} Stars`;
    }
  }

  // Complaint Toggle UI
  function updateComplaintUI(checked) {
    if (!complaintAlertBox) return;
    if (checked) {
      complaintAlertBox.classList.remove('resolved');
      if (complaintText) complaintText.textContent = 'Active Customer Complaint Filed';
      if (complaintIcon) complaintIcon.textContent = '⚠️';
    } else {
      complaintAlertBox.classList.add('resolved');
      if (complaintText) complaintText.textContent = 'No Active Complaints (Ticket Resolved)';
      if (complaintIcon) complaintIcon.textContent = '✅';
    }
  }

  if (complainCheckbox) {
    complainCheckbox.addEventListener('change', () => {
      updateComplaintUI(complainCheckbox.checked);
      debouncedPredict();
    });
  }

  // Select dropdowns
  document.querySelectorAll('#churn-form select').forEach(sel => {
    sel.addEventListener('change', () => {
      debouncedPredict();
    });
  });

  // Debounced auto-prediction
  let debounceTimer = null;
  function debouncedPredict() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      runPrediction(false);
    }, 100);
  }

  // =========================================================================
  // SPEEDOMETER & RESULTS RENDERING
  // =========================================================================
  const gaugeCircle = document.getElementById('gauge-circle');
  const gaugeNeedle = document.getElementById('gauge-needle');
  const gaugePercent = document.getElementById('gauge-percent');
  const riskBadge = document.getElementById('risk-badge');
  const predictionTitle = document.getElementById('prediction-title');
  const predictionSummary = document.getElementById('prediction-summary');
  const kpiOutcome = document.getElementById('kpi-outcome');
  const kpiDelta = document.getElementById('kpi-delta');
  const kpiSignals = document.getElementById('kpi-signals');
  const driversList = document.getElementById('drivers-list');
  const actionsList = document.getElementById('actions-list');
  const resultAvatar = document.getElementById('result-avatar');
  const resultName = document.getElementById('result-name');
  const resultMeta = document.getElementById('result-meta');

  const scaleBands = {
    low: document.getElementById('scale-low'),
    mod: document.getElementById('scale-mod'),
    high: document.getElementById('scale-high'),
    crit: document.getElementById('scale-crit')
  };

  function setGauge(percent) {
    const pct = Math.max(0, Math.min(100, percent));

    // SVG pathLength is 100; stroke starts at offset 100 (empty) to 0 (full)
    if (gaugeCircle) {
      if (pct <= 0.5) {
        gaugeCircle.style.opacity = '0';
        gaugeCircle.style.strokeDashoffset = '100';
      } else {
        gaugeCircle.style.opacity = '1';
        gaugeCircle.style.strokeDashoffset = Math.max(0, 100 - pct);
      }
    }

    // Needle rotates -90deg at 0% to +90deg at 100%
    if (gaugeNeedle) {
      const angle = -90 + (pct / 100) * 180;
      gaugeNeedle.style.transform = `rotate(${angle}deg)`;
    }

    // Risk scale tier highlight
    Object.values(scaleBands).forEach(b => b && b.classList.remove('on'));
    if (pct >= 70) {
      scaleBands.crit && scaleBands.crit.classList.add('on');
    } else if (pct >= 40) {
      scaleBands.high && scaleBands.high.classList.add('on');
    } else if (pct >= 20) {
      scaleBands.mod && scaleBands.mod.classList.add('on');
    } else {
      scaleBands.low && scaleBands.low.classList.add('on');
    }
  }

  function getFormData() {
    const payload = {};

    // Sliders
    sliders.forEach(s => {
      const el = document.getElementById(s.id);
      if (el) payload[s.id] = parseFloat(el.value);
    });

    // Pill controls
    payload.CityTier = parseInt(getPillValue('CityTier') || '1', 10);
    payload.MaritalStatus = getPillValue('MaritalStatus') || 'Single';
    payload.Gender = getPillValue('Gender') || 'Female';
    payload.PreferredLoginDevice = getPillValue('PreferredLoginDevice') || 'Mobile Phone';

    // Star score
    payload.SatisfactionScore = getStarValue();

    // Complain toggle
    payload.Complain = complainCheckbox && complainCheckbox.checked ? 1 : 0;

    // Dropdowns
    const payEl = document.getElementById('PreferredPaymentMode');
    payload.PreferredPaymentMode = payEl ? payEl.value : 'Debit Card';

    const catEl = document.getElementById('PreferedOrderCat');
    payload.PreferedOrderCat = catEl ? catEl.value : 'Mobile Phone';

    return payload;
  }

  function loadFormData(data) {
    // Sliders
    sliders.forEach(s => {
      if (data[s.id] !== undefined) {
        const el = document.getElementById(s.id);
        if (el) {
          el.value = data[s.id];
          updateSlider(s);
        }
      }
    });

    // Pills
    if (data.CityTier !== undefined) setPillValue('CityTier', data.CityTier);
    if (data.MaritalStatus !== undefined) setPillValue('MaritalStatus', data.MaritalStatus);
    if (data.Gender !== undefined) setPillValue('Gender', data.Gender);
    if (data.PreferredLoginDevice !== undefined) setPillValue('PreferredLoginDevice', data.PreferredLoginDevice);

    // Star score
    if (data.SatisfactionScore !== undefined) setStarValue(data.SatisfactionScore);

    // Complaint
    if (complainCheckbox && data.Complain !== undefined) {
      complainCheckbox.checked = parseInt(data.Complain, 10) === 1;
      updateComplaintUI(complainCheckbox.checked);
    }

    // Dropdowns
    if (data.PreferredPaymentMode !== undefined) {
      const el = document.getElementById('PreferredPaymentMode');
      if (el) el.value = data.PreferredPaymentMode;
    }
    if (data.PreferedOrderCat !== undefined) {
      const el = document.getElementById('PreferedOrderCat');
      if (el) el.value = data.PreferedOrderCat;
    }
  }

  async function runPrediction(isManual = false) {
    if (isManual && predictBtn) predictBtn.disabled = true;

    try {
      const payload = getFormData();
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        throw new Error(`HTTP error ${res.status}`);
      }

      const data = await res.json();
      renderResults(data);
    } catch (err) {
      console.warn('Prediction request failed:', err);
    } finally {
      if (isManual && predictBtn) predictBtn.disabled = false;
    }
  }

  function renderResults(data) {
    const pct = data.churn_percentage;
    const assessment = data.risk_assessment;
    const baseline = assessment.baseline_churn || 16.8;

    // Readout
    if (gaugePercent) gaugePercent.textContent = `${pct.toFixed(1)}%`;
    setGauge(pct);

    // Risk badge
    if (riskBadge) {
      let badgeCls = 'badge-safe';
      if (pct >= 70) badgeCls = 'badge-crit';
      else if (pct >= 40) badgeCls = 'badge-crit';
      else if (pct >= 20) badgeCls = 'badge-mod';
      riskBadge.className = `risk-badge ${badgeCls}`;
      riskBadge.textContent = assessment.risk_level;
    }

    // Headline & Diagnostic
    if (predictionTitle) {
      if (data.prediction === 1) {
        predictionTitle.textContent = `🚨 High Attrition Risk (${pct.toFixed(1)}%)`;
      } else {
        predictionTitle.textContent = `✅ Customer Retained (${(100 - pct).toFixed(1)}% Stability)`;
      }
    }
    if (predictionSummary) {
      predictionSummary.textContent = assessment.summary;
    }

    // KPI Tiles
    if (kpiOutcome) {
      kpiOutcome.textContent = data.prediction_label;
      kpiOutcome.className = data.prediction === 1 ? 'kpi-val text-crit' : 'kpi-val text-green';
    }
    if (kpiDelta) {
      const diff = pct - baseline;
      const sign = diff >= 0 ? '+' : '';
      kpiDelta.textContent = `${sign}${diff.toFixed(1)}%`;
      kpiDelta.className = diff > 0 ? 'kpi-val text-crit' : 'kpi-val text-green';
    }
    if (kpiSignals) {
      const count = (assessment.risk_factors && assessment.risk_factors.length) || 0;
      kpiSignals.textContent = count === 1 ? '1 Active' : `${count} Active`;
    }

    // Attributed Drivers List
    if (driversList) {
      if (assessment.risk_factors && assessment.risk_factors.length > 0) {
        driversList.innerHTML = assessment.risk_factors.map(rf => {
          const sevCls = `sev-${(rf.severity || 'low').toLowerCase()}`;
          const segRate = rf.segment_rate !== undefined ? `${rf.segment_rate.toFixed(1)}%` : '';
          const barWidth = rf.segment_rate ? Math.min(100, (rf.segment_rate / 60) * 100) : 30;
          const basePos = (baseline / 60) * 100;
          return `
            <div class="signal-row">
              <div class="signal-top">
                <span class="sev-badge ${sevCls}">${rf.severity}</span>
                <span class="signal-name">${rf.factor}</span>
                ${segRate ? `<span class="signal-rate">${segRate} churn</span>` : ''}
              </div>
              <div class="signal-desc">${rf.description}</div>
              ${segRate ? `
                <div class="signal-bar-track" title="Segment rate (${segRate}) vs platform avg (${baseline}%)">
                  <div class="signal-bar-fill" style="width: ${barWidth}%;"></div>
                  <div class="signal-bar-bench" style="left: ${basePos}%;"></div>
                </div>
              ` : ''}
            </div>
          `;
        }).join('');
      } else {
        driversList.innerHTML = `
          <div class="empty-state">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin: 0 auto 6px; display: block; color: var(--color-green);"><path d="M20 6L9 17l-5-5"/></svg>
            No active segment risk flags. Customer has established tenure and healthy account telemetry.
          </div>
        `;
      }
    }

    // Prescriptive Playbook Actions
    if (actionsList) {
      if (assessment.recommended_actions && assessment.recommended_actions.length > 0) {
        actionsList.innerHTML = assessment.recommended_actions.map(act => {
          const prioCls = `prio-${(act.priority || 'P3').toLowerCase()}`;
          return `
            <div class="action-row">
              <span class="action-priority ${prioCls}">${act.priority || 'P3'}</span>
              <div class="action-content">
                <div class="action-head">
                  <span class="action-title">${act.action}</span>
                  ${act.owner ? `<span class="action-owner">${act.owner}</span>` : ''}
                </div>
                <div class="action-detail">${act.detail}</div>
              </div>
            </div>
          `;
        }).join('');
      } else {
        actionsList.innerHTML = '<div class="empty-state">No targeted retention actions mandated.</div>';
      }
    }
  }

  // =========================================================================
  // PRESET PERSONA CHIPS & CUSTOMER SELECTION
  // =========================================================================
  const personaMeta = {
    new_churn_risk: { name: 'Account #9428', id: '#CUST-9428', tier: 'Tier 3 Regional', initials: '#94', color: 'av-red' },
    moderate_watch: { name: 'Account #8104', id: '#CUST-8104', tier: 'Tier 2 Urban', initials: '#81', color: 'av-amber' },
    loyal_vip: { name: 'Account #3051', id: '#CUST-3051', tier: 'Tier 1 Metro (VIP)', initials: '#30', color: 'av-green' }
  };

  let presetsCache = {};
  fetch('/api/presets')
    .then(r => r.json())
    .then(presets => {
      presets.forEach(p => { presetsCache[p.id] = p.data; });
    })
    .catch(e => console.warn('Could not fetch presets:', e));

  const personaBtns = document.querySelectorAll('.persona-btn[data-preset]');
  personaBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const presetId = btn.getAttribute('data-preset');
      document.querySelectorAll('.persona-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const meta = personaMeta[presetId];
      if (meta) {
        if (resultAvatar) {
          resultAvatar.textContent = meta.initials;
          resultAvatar.className = `avatar-lg ${meta.color}`;
        }
        if (resultName) resultName.textContent = meta.name;
        if (resultMeta) resultMeta.textContent = `Customer ID: ${meta.id} • ${meta.tier} (PII Masked)`;
      }

      const data = presetsCache[presetId];
      if (data) {
        loadFormData(data);
        runPrediction(true);
        showToast(`Loaded ${meta ? meta.name : 'Customer'} Profile`);
      }
    });
  });

  const customProfileBtn = document.getElementById('custom-profile-btn');
  if (customProfileBtn) {
    customProfileBtn.addEventListener('click', () => {
      document.querySelectorAll('.persona-btn').forEach(b => b.classList.remove('active'));
      customProfileBtn.classList.add('active');
      if (resultAvatar) {
        resultAvatar.textContent = '⚙️';
        resultAvatar.className = 'avatar-lg av-blue';
      }
      if (resultName) resultName.textContent = 'Custom Account';
      if (resultMeta) resultMeta.textContent = 'Manual Telemetry Simulation (No PII)';
      showToast('Custom simulation mode active');
    });
  }

  // =========================================================================
  // INTERACTIVE "WHAT-IF" SIMULATION INTERVENTIONS
  // =========================================================================
  const simResolveComplaint = document.getElementById('sim-resolve-complaint');
  if (simResolveComplaint) {
    simResolveComplaint.addEventListener('click', () => {
      if (complainCheckbox) {
        complainCheckbox.checked = false;
        updateComplaintUI(false);
      }
      runPrediction(true);
      showToast('Intervention: Closed active complaint ticket (-40% Risk Drop)');
    });
  }

  const simBoostCashback = document.getElementById('sim-boost-cashback');
  if (simBoostCashback) {
    simBoostCashback.addEventListener('click', () => {
      const cbEl = document.getElementById('CashbackAmount');
      if (cbEl) {
        cbEl.value = 220;
        updateSlider({ id: 'CashbackAmount', prefix: '$', suffix: '' });
      }
      runPrediction(true);
      showToast('Intervention: Upgraded customer cashback to $220');
    });
  }

  const simReachMilestone = document.getElementById('sim-reach-milestone');
  if (simReachMilestone) {
    simReachMilestone.addEventListener('click', () => {
      const tenEl = document.getElementById('Tenure');
      if (tenEl) {
        tenEl.value = 6;
        updateSlider({ id: 'Tenure', suffix: ' mo' });
      }
      runPrediction(true);
      showToast('Simulation: Customer reached 6-month loyalty milestone');
    });
  }

  // Reset Button
  if (globalResetBtn) {
    globalResetBtn.addEventListener('click', () => {
      document.querySelectorAll('.persona-btn').forEach(b => b.classList.remove('active'));
      if (customProfileBtn) customProfileBtn.classList.add('active');

      const defaults = {
        Tenure: 2,
        CityTier: 1,
        NumberOfDeviceRegistered: 3,
        NumberOfAddress: 2,
        OrderCount: 2,
        DaySinceLastOrder: 4,
        CashbackAmount: 160,
        CouponUsed: 1,
        OrderAmountHikeFromlastYear: 15,
        WarehouseToHome: 12,
        Complain: 0,
        SatisfactionScore: 3,
        HourSpendOnApp: 3,
        MaritalStatus: 'Married',
        Gender: 'Female',
        PreferredLoginDevice: 'Mobile Phone',
        PreferredPaymentMode: 'Debit Card',
        PreferedOrderCat: 'Mobile Phone'
      };

      loadFormData(defaults);
      if (resultAvatar) {
        resultAvatar.textContent = '⚙️';
        resultAvatar.className = 'avatar-lg av-blue';
      }
      if (resultName) resultName.textContent = 'Custom Account';
      if (resultMeta) resultMeta.textContent = 'Platform Baseline Averages (No PII)';

      runPrediction(true);
      showToast('All parameters reset to platform defaults');
    });
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      runPrediction(true);
    });
  }

  // =========================================================================
  // TAB 2: CUSTOMER DIRECTORY (LIVE COHORT EXPLORER)
  // =========================================================================
  const customerTableBody = document.getElementById('customer-table-body');
  const customerSearchInput = document.getElementById('customer-search-input');
  let customerDirectoryData = [];

  async function loadCustomerDirectory() {
    try {
      const res = await fetch('/api/customers');
      if (!res.ok) return;
      customerDirectoryData = await res.json();
      renderCustomerDirectory(customerDirectoryData);
    } catch (e) {
      console.warn('Could not load customer directory:', e);
    }
  }

  function renderCustomerDirectory(customers) {
    if (!customerTableBody) return;

    if (customers.length === 0) {
      customerTableBody.innerHTML = '<tr><td colspan="10" style="text-align:center; padding: 24px; color: var(--text-muted);">No customers found matching filter.</td></tr>';
      return;
    }

    customerTableBody.innerHTML = customers.map(c => {
      const barWidth = Math.min(100, Math.max(4, c.churn_risk));
      const barColor = c.churn_risk >= 70 ? 'var(--color-red)' : (c.churn_risk >= 20 ? 'var(--color-amber)' : 'var(--color-green)');

      return `
        <tr>
          <td>
            <div class="customer-cell">
              <span class="c-tbl-avatar ${c.avatar_color}">${c.avatar}</span>
              <div>
                <div class="c-tbl-name">${c.name}</div>
                <div class="c-tbl-account-ref">${c.account_ref || c.id}</div>
              </div>
            </div>
          </td>
          <td><span class="c-id-tag">${c.id}</span></td>
          <td>${c.segment}</td>
          <td><b>${c.tenure_months} mo</b></td>
          <td>${c.ltv}</td>
          <td>${c.orders} / mo</td>
          <td>${c.complaint === 1 ? '<span class="status-tag tag-champ">1 Open</span>' : '<span class="status-tag tag-good">None</span>'}</td>
          <td>
            <div class="risk-bar-cell">
              <span class="risk-pct-num" style="color: ${barColor}">${c.churn_risk.toFixed(1)}%</span>
              <div class="risk-mini-track">
                <div class="risk-mini-fill" style="width: ${barWidth}%; background: ${barColor};"></div>
              </div>
            </div>
          </td>
          <td><span class="risk-badge ${c.tier_badge}">${c.risk_tier}</span></td>
          <td>
            <button type="button" class="btn-table-action" data-cust-id="${c.id}">
              <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
              Assess &amp; Retain
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Attach row action listeners
    customerTableBody.querySelectorAll('.btn-table-action').forEach(btn => {
      btn.addEventListener('click', () => {
        const custId = btn.getAttribute('data-cust-id');
        const cust = customerDirectoryData.find(c => c.id === custId);
        if (!cust) return;

        // Switch to predictor tab
        switchTab('tab-predictor');

        // Update active profile
        if (resultAvatar) {
          resultAvatar.textContent = cust.avatar;
          resultAvatar.className = `avatar-lg ${cust.avatar_color}`;
        }
        if (resultName) resultName.textContent = cust.name;
        if (resultMeta) resultMeta.textContent = `Customer ID: ${cust.id} • ${cust.segment} (PII Masked)`;

        // Load data & run prediction
        loadFormData(cust.data);
        runPrediction(true);
        window.scrollTo({ top: 0, behavior: 'smooth' });
        showToast(`Loaded ${cust.name} into Retention Predictor`);
      });
    });
  }

  if (customerSearchInput) {
    customerSearchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = customerDirectoryData.filter(c => {
        return c.name.toLowerCase().includes(q) ||
               (c.account_ref && c.account_ref.toLowerCase().includes(q)) ||
               c.id.toLowerCase().includes(q) ||
               c.segment.toLowerCase().includes(q);
      });
      renderCustomerDirectory(filtered);
    });
  }

  // =========================================================================
  // TAB 3: FINANCIAL ROI SIMULATOR
  // =========================================================================
  const roiCustomerBase = document.getElementById('roi-customer-base');
  const roiBaselineChurn = document.getElementById('roi-baseline-churn');
  const roiCustomerLtv = document.getElementById('roi-customer-ltv');
  const roiSaveRate = document.getElementById('roi-save-rate');
  const roiCostPerSave = document.getElementById('roi-cost-per-save');

  const roiCustomerBaseVal = document.getElementById('roi-customer-base-val');
  const roiBaselineChurnVal = document.getElementById('roi-baseline-churn-val');
  const roiCustomerLtvVal = document.getElementById('roi-customer-ltv-val');
  const roiSaveRateVal = document.getElementById('roi-save-rate-val');
  const roiCostPerSaveVal = document.getElementById('roi-cost-per-save-val');

  const roiNetSavings = document.getElementById('roi-net-savings');
  const roiFlaggedCount = document.getElementById('roi-flagged-count');
  const roiSavedCount = document.getElementById('roi-saved-count');
  const roiGrossSavings = document.getElementById('roi-gross-savings');
  const roiCampaignCost = document.getElementById('roi-campaign-cost');
  const roiMultiplier = document.getElementById('roi-multiplier');

  function calculateRoi() {
    if (!roiCustomerBase) return;

    const base = parseFloat(roiCustomerBase.value) || 5630;
    const churnPct = parseFloat(roiBaselineChurn.value) || 16.8;
    const ltv = parseFloat(roiCustomerLtv.value) || 850;
    const saveRatePct = parseFloat(roiSaveRate.value) || 35;
    const costPerCustomer = parseFloat(roiCostPerSave.value) || 25;

    // Display updates
    if (roiCustomerBaseVal) roiCustomerBaseVal.textContent = base.toLocaleString();
    if (roiBaselineChurnVal) roiBaselineChurnVal.textContent = `${churnPct.toFixed(1)}%`;
    if (roiCustomerLtvVal) roiCustomerLtvVal.textContent = `$${ltv.toLocaleString()}`;
    if (roiSaveRateVal) roiSaveRateVal.textContent = `${saveRatePct}%`;
    if (roiCostPerSaveVal) roiCostPerSaveVal.textContent = `$${costPerCustomer}`;

    // Financial formulas
    const atRiskCustomers = Math.round(base * (churnPct / 100));
    const savedCustomers = Math.round(atRiskCustomers * (saveRatePct / 100));
    const grossSaved = savedCustomers * ltv;
    const campaignCost = atRiskCustomers * costPerCustomer;
    const netSaved = Math.max(0, grossSaved - campaignCost);
    const roiMult = campaignCost > 0 ? (netSaved / campaignCost) * 100 : 0;

    if (roiFlaggedCount) roiFlaggedCount.textContent = atRiskCustomers.toLocaleString();
    if (roiSavedCount) roiSavedCount.textContent = savedCustomers.toLocaleString();
    if (roiGrossSavings) roiGrossSavings.textContent = `$${grossSaved.toLocaleString()}`;
    if (roiCampaignCost) roiCampaignCost.textContent = `$${campaignCost.toLocaleString()}`;
    if (roiNetSavings) roiNetSavings.textContent = `$${netSaved.toLocaleString()}`;
    if (roiMultiplier) roiMultiplier.textContent = `${Math.round(roiMult).toLocaleString()}% (${(roiMult / 100).toFixed(1)}×)`;
  }

  [roiCustomerBase, roiBaselineChurn, roiCustomerLtv, roiSaveRate, roiCostPerSave].forEach(input => {
    if (input) {
      input.addEventListener('input', calculateRoi);
    }
  });

  // =========================================================================
  // TAB 4: ACADEMIC BENCHMARKS & FEATURE IMPORTANCE
  // =========================================================================
  const featureBarsList = document.getElementById('feature-bars-list');

  async function loadModelMetadata() {
    try {
      const res = await fetch('/api/metadata');
      if (!res.ok) return;
      const meta = await res.json();

      if (meta.feature_importances && featureBarsList) {
        const top10 = meta.feature_importances.slice(0, 10);
        const maxVal = top10[0][1] || 1;

        featureBarsList.innerHTML = top10.map(([name, val]) => {
          const widthPct = Math.max(3, (val / maxVal) * 100).toFixed(1);
          return `
            <div class="fi-row">
              <span class="fi-name" title="${name}">${name}</span>
              <div class="fi-track">
                <div class="fi-fill" style="width: ${widthPct}%;"></div>
              </div>
              <span class="fi-val">${(val * 100).toFixed(1)}%</span>
            </div>
          `;
        }).join('');
      }
    } catch (e) {
      console.warn('Could not load metadata:', e);
    }
  }

  // =========================================================================
  // INITIALIZATION ON PAGE LOAD
  // =========================================================================
  loadCustomerDirectory();
  loadModelMetadata();
  calculateRoi();
  runPrediction(false);

});
