/**
 * STARBUCKS CUSTOMER INTELLIGENCE PLATFORM — CLIENT APPLICATION
 * Awards-Grade Puture-Inspired Digital Studio Architecture
 * Enterprise SPA Controller handling state, charts, REST API integrations,
 * interactive simulations, and dynamic reports.
 */

// Global App State
const AppState = {
    currentTab: 'dashboard',
    theme: localStorage.getItem('sb_theme') || 'dark',
    charts: {},
    segments: [],
    sampleCustomers: {},
    selectedSegmentId: 0,
    tableState: {
        page: 1,
        perPage: 10,
        sortBy: 'money_spent',
        order: 'desc',
        search: ''
    }
};

// Global Chart.js styling for obsidian dark theme
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#8192a5';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.07)';
    Chart.defaults.font.family = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
}

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
    initTheme();
    initNavigation();
    setupEventListeners();

    // Puture-Inspired Interactive Cyber Studio Enhancements
    initPutureShell();
    initCustomCursor();
    initThreeSpaceStage();
    initHudSimulator();
    attachCardTiltListeners();

    // 1. Immediately load dashboard
    await loadDashboardData();
    attachCardTiltListeners();

    // 2. Fetch sample customer profiles from database
    await loadSampleCustomers();

    // 3. Pre-load all modules so user doesn't have to wait or do manual work
    loadSegmentationData();
    loadPoolsData();
    loadCampaignsData();
    loadInsightsData();

    // 4. Auto-execute initial AI Recommender, Simulator, and Customer 360
    executeInitialRecommender();
    runSimulation();
    loadCustomer360Profile('ae6f43089b674728a50b8727252d3305');
    compareTwoCustomers('ae6f43089b674728a50b8727252d3305', '8efe784d3d864d1294e5d6c71af22032');
});

/* ==========================================================================
   THEME & NAVIGATION
   ========================================================================== */

function initTheme() {
    document.documentElement.setAttribute('data-theme', AppState.theme);
    const toggleBtn = document.getElementById('themeToggleBtn');
    if (toggleBtn) {
        toggleBtn.innerHTML = AppState.theme === 'dark' ? '☀️' : '🌙';
    }
}

function toggleTheme() {
    AppState.theme = AppState.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('sb_theme', AppState.theme);
    initTheme();
    if (typeof Chart !== 'undefined') {
        Chart.defaults.color = AppState.theme === 'dark' ? '#8192a5' : '#64748b';
        Chart.defaults.borderColor = AppState.theme === 'dark' ? 'rgba(255, 255, 255, 0.07)' : 'rgba(0, 0, 0, 0.06)';
    }
    Object.values(AppState.charts).forEach(chart => {
        if (chart && typeof chart.update === 'function') {
            chart.update();
        }
    });
}

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
}

function switchTab(tabId) {
    if (!tabId || tabId === AppState.currentTab) return;

    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.getAttribute('data-tab') === tabId);
    });

    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.toggle('active', tab.id === `tab-${tabId}`);
    });

    AppState.currentTab = tabId;

    const headerTitle = document.getElementById('headerPageTitle');
    const headerSubtitle = document.getElementById('headerPageSubtitle');
    const titles = {
        'dashboard': { title: 'Executive Overview', desc: 'Real-time performance indicators and revenue concentration' },
        'segmentation': { title: 'Customer Segmentation & K-Means Clusters', desc: 'Behavioral clustering, PCA projections, and customer cohort tables' },
        'campaigns': { title: 'Promotional Campaign Analytics', desc: 'Conversion funnels, offer responsiveness, and channel effectiveness' },
        'recommender': { title: 'AI Personalized Offer Recommender', desc: 'Probabilistic conversion forecasting & rule-based offer matching' },
        'customer360': { title: 'Customer 360° Profile & Comparator', desc: 'Individual customer transaction timelines, journeys, and side-by-side analysis' },
        'simulator': { title: 'What-If Marketing Campaign Simulator', desc: 'Scenario modeling for budget, audience reach, conversions, and expected ROI' },
        'pools': { title: 'Customer Pools & Cohort Explorer', desc: 'Actionable cohort pools, demographic breakdowns, and correlation matrix' },
        'insights': { title: 'Smart Marketing Insights Engine', desc: 'Automated data-driven strategic findings and ROI optimization directives' }
    };

    if (titles[tabId] && headerTitle && headerSubtitle) {
        headerTitle.textContent = titles[tabId].title;
        headerSubtitle.textContent = titles[tabId].desc;
    }

    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.scrollTo({ top: 0, behavior: 'smooth' });
    }
    attachCardTiltListeners();
}

function setupEventListeners() {
    const themeBtn = document.getElementById('themeToggleBtn');
    if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.querySelector('.sidebar');
    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    const searchInput = document.getElementById('customerTableSearch');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                AppState.tableState.search = e.target.value;
                AppState.tableState.page = 1;
                loadSegmentCustomers();
            }, 300);
        });
    }

    const sortSelect = document.getElementById('customerTableSort');
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            AppState.tableState.sortBy = e.target.value;
            AppState.tableState.page = 1;
            loadSegmentCustomers();
        });
    }

    const recForm = document.getElementById('recommenderForm');
    if (recForm) {
        recForm.addEventListener('submit', handleRecommenderSubmit);
    }

    const custSearchInput = document.getElementById('existingCustomerSearch');
    if (custSearchInput) {
        let debounce;
        custSearchInput.addEventListener('input', (e) => {
            clearTimeout(debounce);
            const query = e.target.value.trim();
            if (query.length < 3) return;
            debounce = setTimeout(() => searchCustomersAutocomplete(query), 250);
        });
        custSearchInput.addEventListener('change', (e) => {
            const customerId = e.target.value.trim();
            if (customerId) pickExistingCustomerForRec(customerId);
        });
    }

    const c360Form = document.getElementById('customer360SearchForm');
    if (c360Form) {
        c360Form.addEventListener('submit', (e) => {
            e.preventDefault();
            const custId = document.getElementById('customer360SearchInput').value.trim();
            if (custId) loadCustomer360Profile(custId);
        });
    }

    const compareForm = document.getElementById('customerCompareForm');
    if (compareForm) {
        compareForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const id1 = document.getElementById('compareId1').value.trim();
            const id2 = document.getElementById('compareId2').value.trim();
            if (id1 && id2) compareTwoCustomers(id1, id2);
        });
    }

    const simForm = document.getElementById('simulatorForm');
    if (simForm) {
        simForm.addEventListener('input', debounceSimulation);
        simForm.addEventListener('submit', (e) => {
            e.preventDefault();
            runSimulation();
        });
    }

    const exportCsvBtn = document.getElementById('exportCsvBtn');
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', () => {
            window.location.href = `/api/export/customers/csv?segment=${AppState.selectedSegmentId}`;
        });
    }
}

/* ==========================================================================
   SAMPLE CUSTOMER PROFILES (1-CLICK QUICK LOAD)
   ========================================================================== */

async function loadSampleCustomers() {
    try {
        const res = await fetch('/api/samples');
        const json = await res.json();
        if (json.status === 'success') {
            AppState.sampleCustomers = json.samples;
        }
    } catch (err) {
        console.error('Error fetching sample customers:', err);
    }
}

function loadSampleCustomer(clusterId) {
    const cust = AppState.sampleCustomers[clusterId];
    if (!cust) return;

    document.getElementById('recAge').value = cust.age;
    document.getElementById('recIncome').value = cust.income;
    document.getElementById('recGender').value = cust.gender || 'F';
    document.getElementById('recMoneySpent').value = cust.money_spent;
    document.getElementById('recTransactions').value = cust.num_transactions;
    document.getElementById('recReceived').value = cust.num_received;
    document.getElementById('recViewed').value = cust.num_viewed;
    document.getElementById('recCompleted').value = cust.num_completed;

    const searchInput = document.getElementById('existingCustomerSearch');
    if (searchInput) searchInput.value = cust.id;

    // Trigger recommendation automatically
    executeRecommenderForData({
        age: cust.age,
        income: cust.income,
        gender: cust.gender || 'F',
        money_spent: cust.money_spent,
        transactions: cust.num_transactions,
        received: cust.num_received,
        viewed: cust.num_viewed,
        completed: cust.num_completed
    });
}

function executeInitialRecommender() {
    executeRecommenderForData({
        age: 36,
        income: 71000,
        gender: 'F',
        money_spent: 1327.74,
        transactions: 16,
        received: 5,
        viewed: 3,
        completed: 3
    });
}

// Configure Chart.js global defaults for smooth rendering
if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.animation.duration = 900;
    Chart.defaults.animation.easing = 'easeOutQuart';
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
}

function animateValue(elementId, start, end, duration = 800, prefix = '', suffix = '', decimals = 0) {
    const el = document.getElementById(elementId);
    if (!el) return;
    
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        // easeOutExpo formula
        const easeProgress = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
        const current = start + (end - start) * easeProgress;
        
        el.textContent = `${prefix}${current.toLocaleString(undefined, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        })}${suffix}`;
        
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

/* ==========================================================================
   1. DASHBOARD OVERVIEW
   ========================================================================== */

async function loadDashboardData() {
    try {
        const res = await fetch('/api/dashboard/summary');
        const json = await res.json();
        if (json.status !== 'success') return;

        const kpis = json.kpis;
        animateValue('kpiTotalCustomers', 0, kpis.total_customers, 900);
        animateValue('kpiTotalRevenue', 0, kpis.total_revenue, 1000, '$');
        animateValue('kpiAvgSpend', 0, kpis.avg_spend_per_customer, 800, '$', '', 2);
        animateValue('kpiTotalTransactions', 0, kpis.total_transactions, 900);
        animateValue('kpiOverallViewRate', 0, kpis.overall_view_rate, 800, '', '%', 1);
        animateValue('kpiOverallCompletionRate', 0, kpis.overall_completion_rate, 800, '', '%', 1);

        renderRevenueDoughnut(json.segment_revenue_distribution);
        renderFunnelChart(kpis);

    } catch (err) {
        console.error('Error loading dashboard summary:', err);
    }
}

function renderRevenueDoughnut(dist) {
    const ctx = document.getElementById('chartRevenueDoughnut');
    if (!ctx) return;

    if (AppState.charts.revenueDoughnut) {
        AppState.charts.revenueDoughnut.destroy();
    }

    const labels = dist.map(d => d.name);
    const data = dist.map(d => d.revenue);
    const colors = dist.map(d => d.color);

    AppState.charts.revenueDoughnut = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: AppState.theme === 'dark' ? '#161b22' : '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const val = context.parsed;
                            return ` Revenue: $${val.toLocaleString()} (${dist[context.dataIndex].revenue_share}%)`;
                        }
                    }
                }
            },
            cutout: '65%'
        }
    });
}

function renderFunnelChart(kpis) {
    const ctx = document.getElementById('chartPromotionalFunnel');
    if (!ctx) return;

    if (AppState.charts.promotionalFunnel) {
        AppState.charts.promotionalFunnel.destroy();
    }

    AppState.charts.promotionalFunnel = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Offers Received', 'Offers Viewed', 'Offers Completed'],
            datasets: [{
                label: 'Event Volume',
                data: [kpis.total_offers_received, kpis.total_offers_viewed, kpis.total_offers_completed],
                backgroundColor: ['#155f45', '#00754a', '#238636'],
                borderRadius: 6
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        afterLabel: function (context) {
                            if (context.dataIndex === 1) return `View Rate: ${kpis.overall_view_rate}% of received`;
                            if (context.dataIndex === 2) return `Completion Rate: ${kpis.overall_completion_rate}% of viewed`;
                            return '';
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { display: false } }
            }
        }
    });
}

/* ==========================================================================
   2. CUSTOMER SEGMENTATION & ML EVALUATION
   ========================================================================== */

async function loadSegmentationData() {
    try {
        const [segRes, pcaRes, elbowRes] = await Promise.all([
            fetch('/api/segments'),
            fetch('/api/ml/pca'),
            fetch('/api/ml/elbow')
        ]);

        const segJson = await segRes.json();
        const pcaJson = await pcaRes.json();
        const elbowJson = await elbowRes.json();

        if (segJson.status === 'success') {
            AppState.segments = segJson.segments;
            renderSegmentCards(segJson.segments);
            loadSegmentCustomers();
            loadSegmentComparisonRadar();
        }

        if (pcaJson.status === 'success') {
            renderPcaScatterPlot(pcaJson.points);
        }

        if (elbowJson.status === 'success') {
            renderElbowSilhouetteChart(elbowJson);
        }

    } catch (err) {
        console.error('Error loading segmentation data:', err);
    }
}

function renderSegmentCards(segments) {
    const container = document.getElementById('segmentCardsContainer');
    if (!container) return;

    container.innerHTML = '';
    segments.forEach(seg => {
        const isSelected = seg.id === AppState.selectedSegmentId;
        const card = document.createElement('div');
        card.className = `segment-card ${isSelected ? 'selected' : ''}`;
        card.setAttribute('data-id', seg.id);

        card.innerHTML = `
            <div class="segment-card-header">
                <span class="segment-badge" style="background-color: ${seg.badge_color}20; color: ${seg.badge_color};">
                    ${seg.tier}
                </span>
                <span style="font-size: 11px; font-weight: 700; color: var(--sb-text-muted);">
                    Cluster ${seg.id}
                </span>
            </div>
            <div class="segment-name">${seg.name}</div>
            <div class="segment-desc">${seg.description}</div>
            <div class="segment-stats-row">
                <div>
                    <div class="seg-stat-val">$${seg.avg_money_spent.toFixed(0)}</div>
                    <div class="seg-stat-lbl">Avg Spend</div>
                </div>
                <div>
                    <div class="seg-stat-val">${seg.count.toLocaleString()}</div>
                    <div class="seg-stat-lbl">Members (${seg.percentage}%)</div>
                </div>
                <div>
                    <div class="seg-stat-val">${seg.completion_rate}%</div>
                    <div class="seg-stat-lbl">Comp. Rate</div>
                </div>
            </div>
        `;

        card.addEventListener('click', () => {
            document.querySelectorAll('.segment-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            AppState.selectedSegmentId = seg.id;
            AppState.tableState.page = 1;
            loadSegmentCustomers();
            updateSelectedSegmentInspector(seg);
        });

        container.appendChild(card);
    });

    if (segments.length > 0) {
        updateSelectedSegmentInspector(segments[AppState.selectedSegmentId] || segments[0]);
    }
    attachCardTiltListeners();
}

function updateSelectedSegmentInspector(seg) {
    const titleEl = document.getElementById('inspectorSegmentTitle');
    const stratEl = document.getElementById('inspectorStrategyText');
    if (titleEl) titleEl.textContent = `${seg.name} (Cluster ${seg.id})`;
    if (stratEl) stratEl.textContent = seg.strategy;
}

async function loadSegmentCustomers() {
    try {
        const { page, perPage, sortBy, order, search } = AppState.tableState;
        const url = `/api/segments/${AppState.selectedSegmentId}/customers?page=${page}&per_page=${perPage}&sort_by=${sortBy}&order=${order}&search=${encodeURIComponent(search)}`;
        const res = await fetch(url);
        const json = await res.json();
        if (json.status !== 'success') return;

        renderCustomersTable(json.customers);
        renderPagination(json.pagination);
    } catch (err) {
        console.error('Error loading segment customers:', err);
    }
}

function renderCustomersTable(customers) {
    const tbody = document.getElementById('customerTableBody');
    if (!tbody) return;

    if (!customers || customers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 30px; color: var(--sb-text-muted);">No customer records match your filter criteria.</td></tr>`;
        return;
    }

    tbody.innerHTML = customers.map(c => `
        <tr>
            <td>
                <span style="font-family: monospace; font-size: 11px; font-weight: 600; color: var(--sb-green); cursor: pointer;" onclick="inspectCustomerDirectly('${c.id}')">
                    ${c.id.substring(0, 10)}...
                </span>
            </td>
            <td>${c.gender || '—'} / ${c.age} yrs</td>
            <td>$${c.income.toLocaleString()}</td>
            <td><strong>$${c.money_spent.toFixed(2)}</strong></td>
            <td>${c.num_transactions}</td>
            <td>
                <span class="badge" style="background: var(--badge-bg-green); color: var(--badge-text-green); font-size: 10.5px; padding: 2px 6px; border-radius: 4px;">
                    ${c.completion_rate}%
                </span>
            </td>
            <td>
                <button class="page-btn" onclick="inspectCustomerDirectly('${c.id}')" title="View Customer 360">🔍 View</button>
            </td>
        </tr>
    `).join('');
}

function renderPagination(p) {
    const footer = document.getElementById('customerTablePagination');
    if (!footer) return;

    footer.innerHTML = `
        <div>Showing page ${p.page} of ${p.total_pages} (${p.total_records.toLocaleString()} total members)</div>
        <div class="pagination-controls">
            <button class="page-btn" ${p.page <= 1 ? 'disabled' : ''} onclick="changeCustomerPage(${p.page - 1})">← Prev</button>
            <span style="padding: 4px 10px; font-weight: 600;">${p.page}</span>
            <button class="page-btn" ${p.page >= p.total_pages ? 'disabled' : ''} onclick="changeCustomerPage(${p.page + 1})">Next →</button>
        </div>
    `;
}

function changeCustomerPage(newPage) {
    AppState.tableState.page = newPage;
    loadSegmentCustomers();
}

function renderPcaScatterPlot(points) {
    const ctx = document.getElementById('chartPcaScatter');
    if (!ctx) return;

    if (AppState.charts.pcaScatter) {
        AppState.charts.pcaScatter.destroy();
    }

    const clustersData = {};
    points.forEach(p => {
        if (!clustersData[p.cluster]) {
            clustersData[p.cluster] = {
                label: p.segment_name,
                backgroundColor: p.color,
                data: []
            };
        }
        clustersData[p.cluster].data.push({ x: p.x, y: p.y, raw: p });
    });

    const datasets = Object.values(clustersData).map(c => ({
        label: c.label,
        data: c.data,
        backgroundColor: c.backgroundColor,
        pointRadius: 3.5,
        pointHoverRadius: 6
    }));

    AppState.charts.pcaScatter = new Chart(ctx, {
        type: 'scatter',
        data: { datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 10, font: { size: 10 } } },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            const raw = ctx.raw.raw;
                            return ` ${raw.segment_name} | Spend: $${raw.money_spent} | Income: $${raw.income.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: { title: { display: true, text: 'PCA Component 1 (Spending & Volume Dimension)' } },
                y: { title: { display: true, text: 'PCA Component 2 (Demographic & Income Dimension)' } }
            }
        }
    });
}

async function loadSegmentComparisonRadar() {
    try {
        const res = await fetch('/api/segments/comparison');
        const json = await res.json();
        if (json.status !== 'success') return;

        const ctx = document.getElementById('chartSegmentRadar');
        if (!ctx) return;

        if (AppState.charts.segmentRadar) {
            AppState.charts.segmentRadar.destroy();
        }

        const comp = json.comparison;
        const datasets = comp.map(seg => {
            const m = seg.metrics;
            return {
                label: seg.name,
                data: [
                    Math.min(100, (m.avg_money_spent / 600) * 100),
                    Math.min(100, (m.avg_transactions / 16) * 100),
                    Math.min(100, (m.avg_income / 90000) * 100),
                    m.completion_rate,
                    m.view_rate
                ],
                borderColor: seg.color,
                backgroundColor: `${seg.color}20`,
                pointBackgroundColor: seg.color,
                borderWidth: 2
            };
        });

        AppState.charts.segmentRadar = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Spend Intensity', 'Visit Frequency', 'Income Bracket', 'Completion %', 'View Rate %'],
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } }
                },
                scales: {
                    r: { min: 0, max: 100, ticks: { display: false } }
                }
            }
        });
    } catch (err) {
        console.error('Error loading radar comparison:', err);
    }
}

function renderElbowSilhouetteChart(elbowData) {
    const ctx = document.getElementById('chartElbowCurve');
    if (!ctx) return;

    if (AppState.charts.elbowCurve) {
        AppState.charts.elbowCurve.destroy();
    }

    AppState.charts.elbowCurve = new Chart(ctx, {
        type: 'line',
        data: {
            labels: elbowData.k_values.map(k => `k=${k}`),
            datasets: [
                {
                    label: 'Inertia (Sum of Squared Distances)',
                    data: elbowData.inertias,
                    borderColor: '#00754a',
                    backgroundColor: '#00754a',
                    yAxisID: 'y',
                    tension: 0.2
                },
                {
                    label: 'Silhouette Score',
                    data: elbowData.silhouette_scores,
                    borderColor: '#1f6feb',
                    backgroundColor: '#1f6feb',
                    yAxisID: 'y1',
                    borderDash: [5, 5],
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
                y: { type: 'linear', position: 'left', title: { display: true, text: 'Inertia' } },
                y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, title: { display: true, text: 'Silhouette' } }
            }
        }
    });
}

/* ==========================================================================
   3. PROMOTIONAL CAMPAIGN ANALYTICS
   ========================================================================== */

async function loadCampaignsData() {
    try {
        const [offersRes, byTypeRes, bySegRes] = await Promise.all([
            fetch('/api/campaigns/offers'),
            fetch('/api/campaigns/by-type'),
            fetch('/api/campaigns/by-segment')
        ]);

        const offersJson = await offersRes.json();
        const byTypeJson = await byTypeRes.json();
        const bySegJson = await bySegRes.json();

        if (offersJson.status === 'success') {
            renderCampaignOfferCards(offersJson.offers);
        }

        if (byTypeJson.status === 'success') {
            renderCampaignTypeBar(byTypeJson.by_type);
        }

        if (bySegJson.status === 'success') {
            renderSegmentResponseMatrix(bySegJson.matrix);
        }

    } catch (err) {
        console.error('Error loading campaigns data:', err);
    }
}

function renderCampaignOfferCards(offers) {
    const container = document.getElementById('campaignOffersGrid');
    if (!container) return;

    container.innerHTML = offers.map(o => `
        <div class="kpi-card" style="border-left: 4px solid var(--sb-green);">
            <div class="kpi-header">
                <span class="badge" style="background: var(--sb-light-green); color: var(--sb-dark-green); font-weight: 800; font-size: 11px; padding: 2px 8px; border-radius: 10px;">
                    ${o.offer_type.toUpperCase()}
                </span>
                <span style="font-size: 11px; color: var(--sb-text-muted);">
                    ${o.duration} Days
                </span>
            </div>
            <div style="font-size: 14px; font-weight: 700; margin: 6px 0;">
                Spend $${o.difficulty} → Get $${o.reward} Reward
            </div>
            <div style="font-size: 11.5px; color: var(--sb-text-muted); margin-bottom: 12px;">
                Channels: ${Array.isArray(o.channels) ? o.channels.join(', ') : o.channels}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; border-top: 1px solid var(--sb-border); padding-top: 10px;">
                <div>
                    <div style="font-size: 15px; font-weight: 800; color: var(--sb-text-main);">${o.view_rate}%</div>
                    <div style="font-size: 10px; color: var(--sb-text-muted); text-transform: uppercase;">View Rate</div>
                </div>
                <div>
                    <div style="font-size: 15px; font-weight: 800; color: var(--sb-green);">${o.completion_rate > 0 ? o.completion_rate + '%' : 'N/A (Info)'}</div>
                    <div style="font-size: 10px; color: var(--sb-text-muted); text-transform: uppercase;">Completion</div>
                </div>
            </div>
        </div>
    `).join('');
    attachCardTiltListeners();
}

function renderCampaignTypeBar(byType) {
    const ctx = document.getElementById('chartCampaignByType');
    if (!ctx) return;

    if (AppState.charts.campaignByType) {
        AppState.charts.campaignByType.destroy();
    }

    AppState.charts.campaignByType = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: byType.map(t => t.offer_type),
            datasets: [
                {
                    label: 'View Rate (%)',
                    data: byType.map(t => t.view_rate),
                    backgroundColor: '#1f6feb',
                    borderRadius: 4
                },
                {
                    label: 'Completion Rate (%)',
                    data: byType.map(t => t.completion_rate),
                    backgroundColor: '#00754a',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { max: 100 } }
        }
    });
}

function renderSegmentResponseMatrix(matrix) {
    const ctx = document.getElementById('chartSegmentMatrix');
    if (!ctx) return;

    if (AppState.charts.segmentMatrix) {
        AppState.charts.segmentMatrix.destroy();
    }

    AppState.charts.segmentMatrix = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: matrix.map(m => m.segment_name),
            datasets: [
                {
                    label: 'Discount Completion (%)',
                    data: matrix.map(m => m.discount_completion_rate),
                    backgroundColor: '#00754a',
                    borderRadius: 4
                },
                {
                    label: 'BOGO Completion (%)',
                    data: matrix.map(m => m.bogo_completion_rate),
                    backgroundColor: '#238636',
                    borderRadius: 4
                }
            ]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: { x: { max: 100 } }
        }
    });
}

/* ==========================================================================
   4. AI OFFER RECOMMENDER
   ========================================================================== */

async function handleRecommenderSubmit(e) {
    e.preventDefault();
    const payload = {
        age: parseFloat(document.getElementById('recAge').value),
        income: parseFloat(document.getElementById('recIncome').value),
        gender: document.getElementById('recGender').value,
        money_spent: parseFloat(document.getElementById('recMoneySpent').value),
        transactions: parseFloat(document.getElementById('recTransactions').value),
        received: parseFloat(document.getElementById('recReceived').value),
        viewed: parseFloat(document.getElementById('recViewed').value),
        completed: parseFloat(document.getElementById('recCompleted').value)
    };
    executeRecommenderForData(payload);
}

async function executeRecommenderForData(payload) {
    try {
        const res = await fetch('/api/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.status === 'success') {
            renderRecommendationResults(json.data);
        }
    } catch (err) {
        console.error('Error in recommendation:', err);
    }
}

async function searchCustomersAutocomplete(query) {
    try {
        const res = await fetch(`/api/customers/search?q=${encodeURIComponent(query)}`);
        const json = await res.json();
        const datalist = document.getElementById('customerSuggestionsList');
        if (!datalist) return;

        datalist.innerHTML = json.results.map(c => `
            <option value="${c.id}">Age: ${c.age}, Income: $${c.income.toLocaleString()}</option>
        `).join('');
    } catch (err) {
        console.error('Autocomplete error:', err);
    }
}

async function pickExistingCustomerForRec(customerId) {
    if (!customerId) return;
    try {
        const res = await fetch(`/api/recommend/customer/${customerId}`);
        const json = await res.json();
        if (json.status === 'success') {
            renderRecommendationResults(json.data);
        }
    } catch (err) {
        console.error('Error recommending for customer:', err);
    }
}

function renderRecommendationResults(data) {
    const resultsContainer = document.getElementById('recommendationOutputSection');
    if (!resultsContainer) return;

    const seg = data.assigned_segment;
    document.getElementById('recResultSegmentBadge').textContent = seg.tier;
    document.getElementById('recResultSegmentName').textContent = seg.name;
    document.getElementById('recResultSegmentDesc').textContent = seg.description;
    document.getElementById('recResultStrategy').textContent = seg.marketing_strategy;

    const cardsContainer = document.getElementById('recommendedOffersCardsGrid');
    cardsContainer.innerHTML = data.recommended_offers.map((offer, idx) => `
        <div class="offer-rec-card ${idx === 0 ? 'rank-1' : ''}">
            <div>
                <span class="rank-pill">${idx === 0 ? '★ Top Match' : `Rank #${idx + 1}`}</span>
                <div class="offer-type-tag">${offer.offer_type.toUpperCase()}</div>
                <div style="font-size: 16px; font-weight: 700; color: var(--sb-green); margin-bottom: 6px;">
                    Reward: $${offer.reward} (Spend $${offer.difficulty})
                </div>
                <div class="suitability-gauge">
                    <span style="font-size: 13px; font-weight: 800; color: var(--sb-green);">${offer.suitability_score}%</span>
                    <div class="gauge-bar">
                        <div class="gauge-fill" style="width: ${offer.suitability_score}%;"></div>
                    </div>
                </div>
                <p style="font-size: 12px; color: var(--sb-text-muted); line-height: 1.5; margin-bottom: 12px;">
                    ${offer.recommendation_reason}
                </p>
            </div>
            <div style="background: var(--sb-hover-bg); padding: 10px; border-radius: 6px; font-size: 11px;">
                <div>⚡ <strong>ML Predicted Conversion:</strong> ${offer.ml_completion_probability}%</div>
                <div>📊 <strong>Segment Benchmark:</strong> ${offer.historical_segment_completion_rate}%</div>
                <div>⏱️ <strong>Duration:</strong> ${offer.duration} Days</div>
            </div>
        </div>
    `).join('');
    attachCardTiltListeners();
}

/* ==========================================================================
   5. CUSTOMER 360 PROFILE & COMPARATOR
   ========================================================================== */

function inspectCustomerDirectly(customerId) {
    switchTab('customer360');
    const input = document.getElementById('customer360SearchInput');
    if (input) input.value = customerId;
    loadCustomer360Profile(customerId);
}

async function loadCustomer360Profile(customerId) {
    try {
        const res = await fetch(`/api/customer/${customerId}`);
        const json = await res.json();
        if (json.status !== 'success') return;

        const c = json.customer;
        document.getElementById('c360CustomerId').textContent = c.id;
        document.getElementById('c360Demographics').textContent = `${c.gender === 'F' ? 'Female' : 'Male'}, ${c.age} yrs | Member for ${c.membership_days} days`;
        document.getElementById('c360SegmentBadge').textContent = c.segment_name;
        document.getElementById('c360TotalSpend').textContent = `$${c.money_spent.toFixed(2)}`;
        document.getElementById('c360Transactions').textContent = c.num_transactions;
        document.getElementById('c360Income').textContent = `$${c.income.toLocaleString()}`;
        document.getElementById('c360CompletionRate').textContent = `${c.completion_rate}%`;

        renderCustomerTimelineChart(json.spending_timeline);

        const journeyContainer = document.getElementById('c360OfferJourney');
        journeyContainer.innerHTML = json.offer_history.map(oh => `
            <div class="journey-item">
                <div class="journey-time">T+${oh.received_time}h</div>
                <div style="flex: 1;">
                    <div style="font-weight: 700; font-size: 13px;">${oh.offer_type.toUpperCase()} ($${oh.reward} Reward / $${oh.difficulty} Difficulty)</div>
                    <div style="font-size: 11px; color: var(--sb-text-muted);">Channels: ${Array.isArray(oh.channels) ? oh.channels.join(', ') : oh.channels}</div>
                </div>
                <div>
                    <span class="badge" style="background: ${oh.was_completed ? 'var(--badge-bg-green)' : (oh.was_viewed ? 'var(--badge-bg-amber)' : 'var(--badge-bg-red)')}; font-size: 11px; padding: 4px 8px; border-radius: 4px;">
                        ${oh.was_completed ? '✓ Completed' : (oh.was_viewed ? '👁 Viewed Only' : '✉ Unopened')}
                    </span>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error('Error loading customer 360:', err);
    }
}

function renderCustomerTimelineChart(timeline) {
    const ctx = document.getElementById('chartCustomerTimeline');
    if (!ctx) return;

    if (AppState.charts.customerTimeline) {
        AppState.charts.customerTimeline.destroy();
    }

    AppState.charts.customerTimeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeline.map(t => `Hour ${t.hour}`),
            datasets: [{
                label: 'Spending ($)',
                data: timeline.map(t => t.amount),
                borderColor: '#00754a',
                backgroundColor: 'rgba(0, 117, 74, 0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Spend ($)' } }
            }
        }
    });
}

async function compareTwoCustomers(id1, id2) {
    try {
        const res = await fetch(`/api/customer/compare?id1=${encodeURIComponent(id1)}&id2=${encodeURIComponent(id2)}`);
        const json = await res.json();
        if (json.status !== 'success') return;

        const c1 = json.customer_1;
        const c2 = json.customer_2;
        const container = document.getElementById('comparisonResultsGrid');
        container.style.display = 'grid';

        container.innerHTML = `
            <div class="kpi-card" style="border-top: 4px solid var(--sb-green);">
                <h3>Customer 1 (${c1.id.substring(0, 8)}...)</h3>
                <div style="margin: 10px 0;"><span class="segment-badge" style="background: ${c1.badge_color}20; color: ${c1.badge_color};">${c1.segment_name}</span></div>
                <div><strong>Spend:</strong> $${c1.money_spent.toFixed(2)}</div>
                <div><strong>Income:</strong> $${c1.income.toLocaleString()}</div>
                <div><strong>Transactions:</strong> ${c1.num_transactions}</div>
                <div><strong>Completions:</strong> ${c1.num_completed} (${c1.completion_rate}%)</div>
            </div>
            <div class="kpi-card" style="border-top: 4px solid #1f6feb;">
                <h3>Customer 2 (${c2.id.substring(0, 8)}...)</h3>
                <div style="margin: 10px 0;"><span class="segment-badge" style="background: ${c2.badge_color}20; color: ${c2.badge_color};">${c2.segment_name}</span></div>
                <div><strong>Spend:</strong> $${c2.money_spent.toFixed(2)}</div>
                <div><strong>Income:</strong> $${c2.income.toLocaleString()}</div>
                <div><strong>Transactions:</strong> ${c2.num_transactions}</div>
                <div><strong>Completions:</strong> ${c2.num_completed} (${c2.completion_rate}%)</div>
            </div>
        `;
        attachCardTiltListeners();
    } catch (err) {
        console.error('Comparison error:', err);
    }
}

/* ==========================================================================
   6. WHAT-IF MARKETING SIMULATOR
   ========================================================================== */

let simDebounceTimer;
function debounceSimulation() {
    clearTimeout(simDebounceTimer);
    simDebounceTimer = setTimeout(runSimulation, 300);
}

async function runSimulation() {
    const payload = {
        segment_id: parseInt(document.getElementById('simSegmentSelect').value),
        offer_type: document.getElementById('simOfferType').value,
        reward: parseFloat(document.getElementById('simRewardSlider').value),
        difficulty: parseFloat(document.getElementById('simDifficultySlider').value),
        duration: parseFloat(document.getElementById('simDurationSlider').value),
        audience_size: parseInt(document.getElementById('simAudienceSlider').value),
        budget: parseFloat(document.getElementById('simBudgetInput').value)
    };

    document.getElementById('simRewardVal').textContent = `$${payload.reward}`;
    document.getElementById('simDifficultyVal').textContent = `$${payload.difficulty}`;
    document.getElementById('simDurationVal').textContent = `${payload.duration}d`;
    document.getElementById('simAudienceVal').textContent = `${payload.audience_size.toLocaleString()}`;

    try {
        const res = await fetch('/api/simulator/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.status !== 'success') return;

        const s = json.simulation;
        document.getElementById('simResultViews').textContent = s.estimated_views.toLocaleString();
        document.getElementById('simResultCompletions').textContent = s.estimated_completions.toLocaleString();
        document.getElementById('simResultCost').textContent = `$${s.estimated_campaign_cost.toLocaleString()}`;
        document.getElementById('simResultRevenue').textContent = `$${s.estimated_gross_revenue.toLocaleString()}`;
        document.getElementById('simResultProfit').textContent = `$${s.estimated_net_profit.toLocaleString()}`;
        document.getElementById('simResultRoi').textContent = `${s.estimated_roi_percentage}%`;
        document.getElementById('simBudgetStatus').textContent = s.budget_check.status;

        // Render Financial Comparison Chart
        renderSimulationFinancialChart(s, payload.budget);

    } catch (err) {
        console.error('Simulation error:', err);
    }
}

function renderSimulationFinancialChart(s, budget) {
    const ctx = document.getElementById('chartSimulationFinancials');
    if (!ctx) return;

    if (AppState.charts.simFinancials) {
        AppState.charts.simFinancials.destroy();
    }

    AppState.charts.simFinancials = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Budget', 'Est. Cost', 'Gross Revenue', 'Net Profit'],
            datasets: [{
                label: 'Financial Outlook ($)',
                data: [budget, s.estimated_campaign_cost, s.estimated_gross_revenue, s.estimated_net_profit],
                backgroundColor: ['#6b7280', '#cf222e', '#1f6feb', '#00754a'],
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { title: { display: true, text: 'USD ($)' } }
            }
        }
    });
}

/* ==========================================================================
   7. CUSTOMER POOLS & COHORT EXPLORER
   ========================================================================== */

async function loadPoolsData() {
    try {
        const [poolsRes, demoRes, corrRes] = await Promise.all([
            fetch('/api/explorer/pools'),
            fetch('/api/explorer/demographics'),
            fetch('/api/explorer/correlations')
        ]);

        const poolsJson = await poolsRes.json();
        const demoJson = await demoRes.json();
        const corrJson = await corrRes.json();

        if (poolsJson.status === 'success') {
            renderPoolCards(poolsJson.pools);
            renderPoolsComparisonChart(poolsJson.pools);
        }

        if (demoJson.status === 'success') {
            renderDemographicsCharts(demoJson);
        }

        if (corrJson.status === 'success') {
            renderCorrelationHeatmap(corrJson);
        }

    } catch (err) {
        console.error('Error loading pools data:', err);
    }
}

function renderPoolCards(pools) {
    const container = document.getElementById('customerPoolsGrid');
    if (!container) return;

    container.innerHTML = pools.map(p => `
        <div class="pool-card">
            <div class="pool-header">
                <div class="pool-name">${p.pool_name}</div>
                <span class="badge" style="background: var(--badge-bg-green); color: var(--badge-text-green); font-size: 11px; padding: 2px 6px; border-radius: 4px;">
                    ${p.count.toLocaleString()} members
                </span>
            </div>
            <div class="pool-criteria">Criteria: ${p.criteria}</div>
            <div class="pool-stat-grid">
                <div>
                    <div style="font-size: 16px; font-weight: 800; color: var(--sb-text-main);">$${p.total_spend.toLocaleString()}</div>
                    <div style="font-size: 10px; color: var(--sb-text-muted);">Total Spend</div>
                </div>
                <div>
                    <div style="font-size: 16px; font-weight: 800; color: var(--sb-green);">$${p.avg_income.toLocaleString()}</div>
                    <div style="font-size: 10px; color: var(--sb-text-muted);">Avg Income</div>
                </div>
            </div>
            <div style="font-size: 12px; color: var(--sb-text-muted);">
                🎯 <strong>Strategy:</strong> ${p.action}
            </div>
        </div>
    `).join('');
    attachCardTiltListeners();
}

function renderPoolsComparisonChart(pools) {
    const ctx = document.getElementById('chartPoolsComparison');
    if (!ctx) return;

    if (AppState.charts.poolsComp) {
        AppState.charts.poolsComp.destroy();
    }

    AppState.charts.poolsComp = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: pools.map(p => p.pool_name),
            datasets: [
                {
                    label: 'Pool Members',
                    data: pools.map(p => p.count),
                    backgroundColor: '#1f6feb',
                    yAxisID: 'y',
                    borderRadius: 4
                },
                {
                    label: 'Total Revenue ($)',
                    data: pools.map(p => p.total_spend),
                    backgroundColor: '#00754a',
                    yAxisID: 'y1',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { type: 'linear', position: 'left', title: { display: true, text: 'Members' } },
                y1: { type: 'linear', position: 'right', grid: { drawOnChartArea: false }, title: { display: true, text: 'Revenue ($)' } }
            }
        }
    });
}

function renderDemographicsCharts(demo) {
    const ctxAge = document.getElementById('chartAgeDistribution');
    const ctxIncome = document.getElementById('chartIncomeDistribution');
    if (!ctxAge || !ctxIncome) return;

    if (AppState.charts.ageDist) AppState.charts.ageDist.destroy();
    if (AppState.charts.incomeDist) AppState.charts.incomeDist.destroy();

    AppState.charts.ageDist = new Chart(ctxAge, {
        type: 'bar',
        data: {
            labels: demo.age_distribution.map(d => d.bracket),
            datasets: [{
                label: 'Customers',
                data: demo.age_distribution.map(d => d.count),
                backgroundColor: '#00754a',
                borderRadius: 4
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });

    AppState.charts.incomeDist = new Chart(ctxIncome, {
        type: 'bar',
        data: {
            labels: demo.income_distribution.map(d => d.bracket),
            datasets: [{
                label: 'Customers',
                data: demo.income_distribution.map(d => d.count),
                backgroundColor: '#1f6feb',
                borderRadius: 4
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });
}

function renderCorrelationHeatmap(corr) {
    const tableEl = document.getElementById('correlationTable');
    if (!tableEl) return;

    const features = corr.features;
    let html = `<thead><tr><th>Feature</th>${features.map(f => `<th>${f}</th>`).join('')}</tr></thead><tbody>`;

    corr.correlation_matrix.forEach(row => {
        html += `<tr><td><strong>${row.feature}</strong></td>`;
        features.forEach(f => {
            const val = row[f];
            const intensity = Math.abs(val);
            const bgColor = val > 0 ? `rgba(0, 117, 74, ${intensity * 0.7})` : `rgba(207, 34, 46, ${intensity * 0.7})`;
            const textColor = intensity > 0.5 ? '#ffffff' : 'inherit';
            html += `<td style="background-color: ${bgColor}; color: ${textColor}; text-align: center; font-weight: 600;">${val}</td>`;
        });
        html += `</tr>`;
    });
    html += `</tbody>`;
    tableEl.innerHTML = html;
}

/* ==========================================================================
   8. SMART MARKETING INSIGHTS
   ========================================================================== */

async function loadInsightsData() {
    try {
        const res = await fetch('/api/insights');
        const json = await res.json();
        if (json.status !== 'success') return;

        const container = document.getElementById('insightsCardsContainer');
        if (!container) return;

        container.innerHTML = json.insights.map(i => `
            <div class="insight-card">
                <div>
                    <div class="insight-header">
                        <span class="badge" style="background: var(--sb-light-green); color: var(--sb-dark-green); font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 700;">
                            ${i.badge}
                        </span>
                        <span style="font-size: 11px; text-transform: uppercase; color: var(--sb-text-muted);">${i.category}</span>
                    </div>
                    <div class="insight-highlight">${i.stat_highlight}</div>
                    <div class="insight-title">${i.title}</div>
                    <div class="insight-desc">${i.description}</div>
                </div>
                <div class="insight-rec-box">
                    <strong>Actionable Directive:</strong> ${i.recommendation}
                </div>
            </div>
        `).join('');
        attachCardTiltListeners();
    } catch (err) {
        console.error('Error loading insights:', err);
    }
}

/* ==========================================================================
   9. PUTURE-INSPIRED INTERACTIVE CYBER-STUDIO MODULES
   ========================================================================== */

/**
 * Puture-Style Kinetic Entrance Shell
 * Staggers letter-by-letter reveal of "STARBUCKS INTELLIGENCE"
 * and dismisses on user interaction or timer.
 */
function initPutureShell() {
    const shell = document.getElementById('putureShell');
    const titleContainer = document.getElementById('shellTitle');
    if (!shell || !titleContainer) return;

    if (sessionStorage.getItem('sb_shell_seen') === 'true') {
        shell.style.display = 'none';
        return;
    }

    const titleText = "STARBUCKS INTELLIGENCE";
    titleContainer.innerHTML = titleText.split('').map((char, i) => {
        if (char === ' ') return '&nbsp;';
        return `<span class="shell-char" style="animation-delay: ${0.05 + i * 0.035}s">${char}</span>`;
    }).join('');

    let dismissed = false;
    function dismissShell() {
        if (dismissed) return;
        dismissed = true;
        shell.classList.add('dismissed');
        sessionStorage.setItem('sb_shell_seen', 'true');
        setTimeout(() => {
            if (shell.parentNode) shell.parentNode.removeChild(shell);
        }, 550);
    }

    ['click', 'keydown', 'wheel', 'touchstart', 'pointerdown'].forEach(evt => {
        window.addEventListener(evt, dismissShell, { once: true, passive: true });
    });

    setTimeout(dismissShell, 2100);
}

/**
 * Puture-Inspired 3D SpaceStage Engine (Three.js WebGL)
 * Creates an orbiting 3D particle halo ring, star dust field, and perspective cyber ground grid
 * with real-time camera tracking and smooth inertia damping.
 */
function initThreeSpaceStage() {
    const canvas = document.getElementById('ambientCanvas');
    if (!canvas) return;

    if (typeof THREE === 'undefined') {
        initAmbientCanvas();
        return;
    }

    try {
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x02040c, 0.018);

        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 1.8, 14);

        const renderer = new THREE.WebGLRenderer({
            canvas: canvas,
            alpha: true,
            antialias: true,
            powerPreference: 'high-performance'
        });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));

        // 1. 3D Rotating Particle Halo Ring (Puture Multi-Chromatic Spectrum)
        const haloGeometry = new THREE.BufferGeometry();
        const haloCount = 700;
        const haloPos = new Float32Array(haloCount * 3);
        const haloColors = new Float32Array(haloCount * 3);

        const ringRadius = 7.0;
        const tubeRadius = 1.7;

        // Rich Multi-Chromatic Cyber Palette: Royal Blue -> Violet -> Cyan -> Gold -> Emerald
        const palette = [
            [0.23, 0.51, 0.96], // Royal Blue #3b82f6
            [0.55, 0.36, 0.96], // Cyber Violet #8b5cf6
            [0.02, 0.71, 0.83], // Electric Cyan #06b6d4
            [0.96, 0.62, 0.04], // Solar Gold #f59e0b
            [0.06, 0.72, 0.51]  // Luxe Mint #10b981
        ];

        for (let i = 0; i < haloCount; i++) {
            const u = Math.random() * Math.PI * 2;
            const v = Math.random() * Math.PI * 2;
            const r = tubeRadius * (0.3 + 0.7 * Math.random());
            const x = (ringRadius + r * Math.cos(v)) * Math.cos(u);
            const y = (ringRadius + r * Math.cos(v)) * Math.sin(u) * 0.45;
            const z = r * Math.sin(v);

            haloPos[i * 3] = x;
            haloPos[i * 3 + 1] = y;
            haloPos[i * 3 + 2] = z;

            const c = palette[i % palette.length];
            haloColors[i * 3] = c[0] + (Math.random() - 0.5) * 0.08;
            haloColors[i * 3 + 1] = c[1] + (Math.random() - 0.5) * 0.08;
            haloColors[i * 3 + 2] = c[2] + (Math.random() - 0.5) * 0.08;
        }

        haloGeometry.setAttribute('position', new THREE.BufferAttribute(haloPos, 3));
        haloGeometry.setAttribute('color', new THREE.BufferAttribute(haloColors, 3));

        const haloMaterial = new THREE.PointsMaterial({
            size: 0.13,
            vertexColors: true,
            transparent: true,
            opacity: 0.88,
            blending: THREE.AdditiveBlending
        });

        const haloMesh = new THREE.Points(haloGeometry, haloMaterial);
        haloMesh.rotation.x = Math.PI * 0.38;
        haloMesh.position.set(0, 0, -2);
        scene.add(haloMesh);

        // 2. 3D Floating Cosmic Star Dust Field (Soft Celestial Starlight)
        const dustGeometry = new THREE.BufferGeometry();
        const dustCount = 350;
        const dustPos = new Float32Array(dustCount * 3);

        for (let i = 0; i < dustCount; i++) {
            dustPos[i * 3] = (Math.random() - 0.5) * 45;
            dustPos[i * 3 + 1] = (Math.random() - 0.5) * 35;
            dustPos[i * 3 + 2] = (Math.random() - 0.5) * 40;
        }

        dustGeometry.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
        const dustMaterial = new THREE.PointsMaterial({
            size: 0.075,
            color: 0x93c5fd, // Soft celestial blue-white
            transparent: true,
            opacity: 0.55,
            blending: THREE.AdditiveBlending
        });

        const dustMesh = new THREE.Points(dustGeometry, dustMaterial);
        scene.add(dustMesh);

        // 3. 3D Perspective Ground Matrix Grid (Cobalt & Obsidian Horizon)
        const gridHelper = new THREE.GridHelper(60, 30, 0x3b82f6, 0x1e293b);
        gridHelper.position.y = -6.5;
        gridHelper.material.opacity = 0.22;
        gridHelper.material.transparent = true;
        scene.add(gridHelper);

        // Resize handler
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        // Mouse interactive 3D camera damping
        let mouseX = 0, mouseY = 0;
        let targetX = 0, targetY = 0;
        window.addEventListener('mousemove', (e) => {
            mouseX = (e.clientX / window.innerWidth) * 2 - 1;
            mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
        });

        let clock = new THREE.Clock();

        function animateStage() {
            requestAnimationFrame(animateStage);

            const elapsed = clock.getElapsedTime();

            haloMesh.rotation.z = elapsed * 0.08;
            haloMesh.rotation.y = Math.sin(elapsed * 0.2) * 0.15;
            dustMesh.rotation.y = elapsed * 0.015;

            targetX += (mouseX * 1.8 - targetX) * 0.05;
            targetY += (mouseY * 1.2 - targetY) * 0.05;

            camera.position.x = targetX;
            camera.position.y = 1.8 + targetY;
            camera.lookAt(0, 0, -2);

            renderer.render(scene, camera);
        }
        animateStage();

    } catch (err) {
        console.warn('Three.js SpaceStage error, falling back to 2D canvas:', err);
        initAmbientCanvas();
    }
}

/**
 * Ambient Canvas Particle Galaxy (2D Fallback)
 * Renders floating emerald and cyan nodes with interactive proximity laser lines
 * connecting to neighboring particles and the mouse position.
 */
function initAmbientCanvas() {
    const canvas = document.getElementById('ambientCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    const particles = [];
    const count = Math.min(50, Math.max(25, Math.floor((width * height) / 25000)));
    const colors = ['rgba(0, 255, 136, ', 'rgba(0, 229, 255, ', 'rgba(0, 117, 74, '];

    for (let i = 0; i < count; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.45,
            vy: (Math.random() - 0.5) * 0.45,
            radius: Math.random() * 2 + 1,
            colorBase: colors[Math.floor(Math.random() * colors.length)],
            alpha: Math.random() * 0.45 + 0.25
        });
    }

    let mouseX = -1000, mouseY = -1000;
    window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    function renderCanvas() {
        ctx.clearRect(0, 0, width, height);

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0) p.x = width;
            else if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            else if (p.y > height) p.y = 0;

            // Connect lines between nearby particles
            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const dx = p.x - p2.x;
                const dy = p.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 110) {
                    const lineAlpha = (1 - dist / 110) * 0.22;
                    ctx.strokeStyle = `rgba(0, 255, 136, ${lineAlpha})`;
                    ctx.lineWidth = 0.8;
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            }

            // Connect line to mouse if nearby
            const mdx = p.x - mouseX;
            const mdy = p.y - mouseY;
            const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
            if (mDist < 135) {
                const mAlpha = (1 - mDist / 135) * 0.45;
                ctx.strokeStyle = `rgba(0, 255, 136, ${mAlpha})`;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.moveTo(p.x, p.y);
                ctx.lineTo(mouseX, mouseY);
                ctx.stroke();
            }

            // Draw glowing particle point
            ctx.fillStyle = p.colorBase + p.alpha + ')';
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fill();
        }

        requestAnimationFrame(renderCanvas);
    }
    renderCanvas();
}

/**
 * Custom Magnetic Cursor & Glowing Trailing Ring
 * Provides instant zero-latency dot tracking with a smoothly lagging/elastic ring.
 * Expands on hover over interactive buttons, cards, and links.
 */
function initCustomCursor() {
    const dot = document.getElementById('cursorDot');
    const ring = document.getElementById('cursorRing');
    if (!dot || !ring) return;

    // Detect touch device
    if (window.matchMedia('(pointer: coarse)').matches) return;

    let mouseX = -100, mouseY = -100;
    let ringX = -100, ringY = -100;

    window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        dot.style.transform = `translate3d(${mouseX}px, ${mouseY}px, 0) translate(-50%, -50%)`;
        dot.style.opacity = '1';
        ring.style.opacity = '1';
    }, { passive: true });

    document.addEventListener('mouseleave', () => {
        dot.style.opacity = '0';
        ring.style.opacity = '0';
    });

    function loopCursor() {
        ringX += (mouseX - ringX) * 0.26;
        ringY += (mouseY - ringY) * 0.26;
        ring.style.transform = `translate3d(${ringX}px, ${ringY}px, 0) translate(-50%, -50%)`;
        requestAnimationFrame(loopCursor);
    }
    loopCursor();

    const interactiveSelector = 'a, button, input, select, .nav-item, .tilt-card, .kpi-card, .chart-card, .segment-card, .pool-card, .insight-card, .offer-rec-card, .brand-logo-badge, .layer-legend-item, .layer-slot';
    document.addEventListener('mouseover', (e) => {
        if (e.target.closest(interactiveSelector)) {
            document.body.classList.add('cursor-hover');
        }
    });
    document.addEventListener('mouseout', (e) => {
        if (e.target.closest(interactiveSelector)) {
            document.body.classList.remove('cursor-hover');
        }
    });
}

/**
 * 3D Perspective Tilt & Specular Dynamic Spotlight Glare
 * Jitter-free calculation with requestAnimationFrame batching and CSS transition bypass while moving.
 */
function attachCardTiltListeners() {
    const cardSelector = '.tilt-card, .kpi-card, .chart-card, .segment-card, .pool-card, .insight-card, .offer-rec-card, .sim-results-card';
    const cards = document.querySelectorAll(cardSelector);

    cards.forEach(card => {
        if (card.dataset.tiltAttached === 'true') return;
        card.dataset.tiltAttached = 'true';
        card.classList.add('tilt-card');

        // Add 4 corner crosshairs if missing
        if (!card.querySelector('.cyber-corner')) {
            const tl = document.createElement('span'); tl.className = 'cyber-corner top-left';
            const tr = document.createElement('span'); tr.className = 'cyber-corner top-right';
            const bl = document.createElement('span'); bl.className = 'cyber-corner bottom-left';
            const br = document.createElement('span'); br.className = 'cyber-corner bottom-right';
            card.appendChild(tl); card.appendChild(tr); card.appendChild(bl); card.appendChild(br);
        }

        let rafId = null;

        card.addEventListener('mouseenter', () => {
            card.classList.add('is-tilting');
        });

        card.addEventListener('mousemove', (e) => {
            if (rafId) cancelAnimationFrame(rafId);
            rafId = requestAnimationFrame(() => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const pctX = x / rect.width;
                const pctY = y / rect.height;

                const rotateX = ((0.5 - pctY) * 9).toFixed(2);
                const rotateY = ((pctX - 0.5) * 9).toFixed(2);

                card.style.setProperty('--mouse-x', `${x}px`);
                card.style.setProperty('--mouse-y', `${y}px`);
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.015, 1.015, 1.015)`;
            });
        }, { passive: true });

        card.addEventListener('mouseleave', () => {
            if (rafId) cancelAnimationFrame(rafId);
            card.classList.remove('is-tilting');
            card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
        });
    });
}

/**
 * Live Tech HUD Metric Jitter Simulator
 * Simulates ultra-fast live microsecond network/DB roundtrip pings.
 */
function initHudSimulator() {
    const hudLatency = document.getElementById('hudLatency');
    if (!hudLatency) return;
    setInterval(() => {
        const ms = (1.2 + Math.random() * 1.2).toFixed(1);
        hudLatency.textContent = `${ms}ms`;
    }, 2400);
}
