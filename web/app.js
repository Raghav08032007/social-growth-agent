'use strict';

const app = document.querySelector('#app');
const notice = document.querySelector('#status');
let state = null;
let busy = false;
const pendingFormKeys = new WeakMap();
const pendingRefundKeys = new Map();
const viewNames = { overview: 'Overview', content: 'Content studio', leads: 'Inbox & leads', revenue: 'Revenue', roadmap: 'Product roadmap' };
const phases = [
  ['Foundation', 4, 'Workspace shell, encrypted token vault, reliable jobs and cost monitoring.'],
  ['Create & publish', 34, 'Business onboarding, regional content, approval workflows and connected publishing.'],
  ['Leads & inbox', 13, 'Unified conversations, consent records, follow-ups and guarded messaging.'],
  ['The money loop', 21, 'Tracked links, post-to-sale attribution, storefront and WhatsApp controls.'],
  ['Launch readiness', 10, 'Subscriptions, spending limits, notifications and data rights.'],
  ['Engagement', 36, 'More platforms, branching automations, reputation and content checks.'],
  ['Growth tools', 37, 'Media production, competitor signals, social SEO and deeper analytics.'],
  ['Agents & creators', 20, 'Scoped specialist agents, offers, digital products and creator tools.'],
  ['Teams & agencies', 23, 'Client reviews, workspaces, roles, white-label reports and public APIs.'],
  ['Marketplace', 29, 'Creator discovery, brand campaigns, rights and provider-managed payouts.'],
  ['Ecosystem', 30, 'Guarded missions, native apps, communities and third-party agents.'],
];
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
const money = paise => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(Number(paise || 0) / 100);
const currentView = () => viewNames[location.hash.slice(1)] ? location.hash.slice(1) : 'overview';
const postById = id => state.posts.find(post => String(post.id) === String(id));
const shortCaption = id => {
  const post = postById(id);
  return post ? `${post.caption.slice(0, 42)}${post.caption.length > 42 ? '…' : ''}` : 'Unlinked post';
};
const today = () => new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata' });

async function request(path, data) {
  const response = await fetch(path, {
    method: data === undefined ? 'GET' : 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Workspace-ID': 'demo-a' },
    ...(data === undefined ? {} : { body: JSON.stringify(data) }),
  });
  let payload;
  try { payload = await response.json(); } catch { throw new Error('The local server returned an unreadable response.'); }
  if (!response.ok) throw new Error(payload.error?.message || `Request failed (${response.status}).`);
  return payload;
}

function showNotice(message, error = false) {
  notice.textContent = message;
  notice.className = error ? 'error' : '';
  notice.hidden = false;
}

async function refresh() {
  state = await request('/api/state');
  render();
  document.querySelector('#loading').hidden = true;
  app.hidden = false;
}

function heading(title, subtitle, action = '') {
  return `<section class="page-heading"><div><p class="eyebrow">YOUR BUSINESS, MOVING FORWARD</p><h1>${title}</h1><p class="subtitle">${subtitle}</p></div><div class="heading-actions">${action}</div></section>`;
}

function stats() {
  const data = state.dashboard;
  return `<div class="stat-grid">${[
    ['Attributed revenue', money(data.revenue_paise), '↗', 'Demo sales less refunds'],
    ['Leads captured', data.leads_count, '♧', 'People interested in your business'],
    ['Posts published', data.published_count, '▤', 'Simulated publishing only'],
    ['Sales recorded', data.sales_count, '◈', 'Demo payment records'],
  ].map(([label, value, icon, hint]) => `<article class="stat"><div class="stat-head">${label}<span class="stat-icon" aria-hidden="true">${icon}</span></div><div class="stat-value">${escapeHtml(value)}</div><div class="stat-foot">${hint}</div></article>`).join('')}</div>`;
}

function postCard(post) {
  const language = { en: 'English', ta: 'Tamil', hi: 'Hindi' }[post.language] || post.language;
  let action = '';
  if (post.status === 'draft') action = `<button class="btn small" data-action="approve" data-id="${escapeHtml(post.id)}">Approve draft <span>✓</span></button>`;
  if (post.status === 'approved') action = `<button class="btn btn-primary small" data-action="publish" data-id="${escapeHtml(post.id)}">Simulate publish <span>↗</span></button>`;
  if (post.status === 'published') action = `<a class="btn small" href="#leads">Capture a demo lead <span>↗</span></a>`;
  return `<article class="post-card"><div class="post-top"><span class="platform"><span class="platform-icon" aria-hidden="true">◎</span>${escapeHtml(post.platform)}</span><span class="pill ${escapeHtml(post.status)}">${escapeHtml(post.status)}</span></div><p class="post-caption">${escapeHtml(post.caption)}</p><p class="post-meta">${escapeHtml(language)} · Post #${escapeHtml(post.id)}</p><div class="post-actions">${action}</div></article>`;
}

function empty(title, text) {
  return `<div class="empty"><strong>${title}</strong>${text}</div>`;
}

function overview() {
  const posts = state.posts.slice(0, 3);
  const earnings = state.posts.slice(0, 7).map(post => ({ id: post.id, amount: state.sales.filter(sale => sale.post_id === post.id && sale.status !== 'refunded').reduce((sum, sale) => sum + sale.amount_paise, 0) }));
  const max = Math.max(...earnings.map(item => item.amount), 100);
  const chart = earnings.length ? `<div class="chart" role="img" aria-label="Recorded demo revenue by post">${earnings.map(item => `<div class="chart-col"><span class="chart-value">${money(item.amount)}</span><div class="chart-bar" style="height:${Math.max(2, (item.amount / max) * 120)}px"></div></div>`).join('')}</div><div class="chart-labels">${earnings.map(item => `<span>Post #${escapeHtml(item.id)}</span>`).join('')}</div>` : empty('Your story starts here', 'Publish a demo post and record a sale to see your results.');
  const audit = state.audit.slice(0, 4);
  return `${heading('Small steps. <span class="serif">Real momentum.</span>', 'Welcome back, Raghav. Let’s turn your next post into your next opportunity.', `<span class="date-chip">▦ &nbsp; ${today()}</span><a class="btn btn-primary" href="#content">＋ Create a post</a>`)}${stats()}
    <section class="hero-card"><div class="orb" aria-hidden="true">✳</div><div><h2>Your next good idea starts here.</h2><p>Write a post, give it your approval, then follow the journey from interest to a recorded sale.</p></div><a class="btn" href="#content">Open content studio <span>↗</span></a></section>
    <div class="two-col section-space"><section class="card card-pad"><div class="card-heading"><div><h2>The bigger picture</h2><p>Attributed revenue by post · demo workspace</p></div><span class="pill">RECORDED DATA</span></div>${chart}<p class="chart-note">Tracking shows recorded attribution. It does not prove a post caused a sale.</p></section>
    <section class="card card-pad"><div class="card-heading"><div><h2>From post to possibility</h2><p>Your approval stays at the center.</p></div></div>${[['Create something worth sharing', 'Write in English, Tamil or Hindi.'], ['Make it yours. Then approve.', 'Publish actions wait for your approval.'], ['Follow the money', 'Connect a lead and sale to the source post.']].map(([title, description], index) => `<a class="flow-step" href="#${['content', 'content', 'revenue'][index]}"><span class="step-num">0${index + 1}</span><div><strong>${title}</strong><p>${description}</p></div><span class="arrow">↗</span></a>`).join('')}</section></div>
    <div class="section-title"><div><h2>A little closer to your next win</h2><p>Your most recent content, ready for the next step.</p></div><a class="text-link" href="#content">View all content ↗</a></div><div class="post-grid">${posts.length ? posts.map(postCard).join('') : `<div class="wide">${empty('Make your first move', 'Create a draft to explore the approval and publishing flow.')}</div>`}</div>
    <section class="card card-pad section-space"><div class="card-heading"><div><h2>A clear trail of every action</h2><p>Accountability, built into the workflow.</p></div><span class="pill">DEMO AUDIT LOG</span></div>${audit.length ? audit.map(item => `<div class="activity-row"><span class="activity-dot"></span><div><strong>${escapeHtml(item.action || item.event || item.type || 'Workspace action')}</strong><small>${escapeHtml(item.entity_type || '')} ${escapeHtml(item.entity_id || '')}</small></div><time>${escapeHtml(item.created_at || item.timestamp || '')}</time></div>`).join('') : empty('Everything starts with your approval', 'Your actions will appear here as you explore.')}</section>`;
}

function content() {
  return `${heading('A space for <span class="serif">your next idea.</span>', 'Create a draft, review it, and explore a simulated publishing workflow.')}
    <div class="split-form"><form class="card form-card" data-form="post"><h2>Make something worth sharing</h2><p>Write your own content. AI generation and live social publishing are planned integrations.</p><label for="caption">Your post</label><textarea id="caption" name="caption" required maxlength="2200" placeholder="A new season, a fresh look. Tell your customers what’s happening…"></textarea><div class="hint">Drafts stay private until you approve them.</div><div class="form-row"><div><label for="platform">Platform</label><select id="platform" name="platform"><option value="instagram">Instagram</option><option value="facebook">Facebook</option></select></div><div><label for="language">Language</label><select id="language" name="language"><option value="en">English</option><option value="ta">Tamil</option><option value="hi">Hindi</option></select></div></div><button class="btn btn-primary" type="submit">Save draft <span>＋</span></button></form><section><div class="list-heading"><h2>Your content collection</h2><span class="count">${state.posts.length} posts</span></div><div class="stack">${state.posts.length ? state.posts.map(postCard).join('') : empty('Every good story begins with a draft', 'Write your first post in the studio.')}</div></section></div>`;
}

function postOptions(publishedOnly = false) {
  return state.posts.filter(post => !publishedOnly || post.status === 'published').map(post => `<option value="${escapeHtml(post.id)}">#${escapeHtml(post.id)} · ${escapeHtml(post.caption.slice(0, 42))}</option>`).join('');
}

function leads() {
  return `${heading('Every conversation, <span class="serif">a possibility.</span>', 'Record demo leads and keep a clear connection to the content that brought them here.')}
    <div class="split-form"><form class="card form-card" data-form="lead"><h2>Meet your next customer</h2><p>Simulate a lead captured from a post. Live inbox, messages and WhatsApp are planned.</p><label for="name">Customer name</label><input id="name" name="name" required maxlength="100" placeholder="e.g. Priya Sharma"><label for="phone">Phone (optional)</label><input id="phone" name="phone" type="tel" maxlength="32" placeholder="e.g. +91 98765 43210"><label for="source-post">Source post (optional)</label><select id="source-post" name="post_id"><option value="">No source recorded</option>${postOptions()}</select><div class="hint">Use fictional contact details in this local demo.</div><button class="btn btn-primary" type="submit">Add demo lead <span>＋</span></button></form><section><div class="list-heading"><h2>People showing interest</h2><span class="count">${state.leads.length} leads</span></div><div class="stack">${state.leads.length ? [...state.leads].reverse().map(lead => `<article class="list-row"><span class="contact-avatar">${escapeHtml(lead.name.split(' ').map(part => part[0]).join('').slice(0, 2).toUpperCase())}</span><div><h3>${escapeHtml(lead.name)}</h3><p>${escapeHtml(lead.phone || 'No phone recorded')}<br>${lead.post_id ? escapeHtml(shortCaption(lead.post_id)) : 'No source post'}</p></div><span class="pill">${escapeHtml(lead.stage)}</span></article>`).join('') : empty('Your next customer is out there', 'Add a fictional lead to explore the post-to-sale journey.')}</div></section></div>`;
}

function revenue() {
  const publishedPosts = state.posts.filter(post => post.status === 'published');
  return `${heading('See where <span class="serif">growth happens.</span>', 'A transparent ledger of recorded demo sales and refunds. No live money moves.')}${stats()}
    <div class="split-form"><form class="card form-card" data-form="sale"><h2>Connect a sale to a post</h2><p>Use a simulated sale to follow the full attribution journey.</p><label for="sale-post">Published source post</label><select id="sale-post" name="post_id" required><option value="">Choose a published post</option>${postOptions(true)}</select><label for="sale-lead">Customer (optional)</label><select id="sale-lead" name="lead_id"><option value="">No linked customer</option>${state.leads.map(lead => `<option value="${escapeHtml(lead.id)}">${escapeHtml(lead.name)}</option>`).join('')}</select><label for="amount">Sale amount (₹)</label><input id="amount" name="amount" type="number" required min="0.01" max="1000000" step="0.01" placeholder="e.g. 1499"><div class="hint">${publishedPosts.length ? 'Refunding a sale adds a reversal to the ledger.' : 'Approve and simulate publishing a post in Content studio first.'}</div><button class="btn btn-primary" type="submit" ${publishedPosts.length ? '' : 'disabled'}>Record demo sale <span>↗</span></button></form><section><div class="list-heading"><h2>Your sales ledger</h2><span class="count">${state.sales.length} records</span></div>${state.sales.length ? `<div class="card table-scroll"><table><thead><tr><th>Source post</th><th>Amount</th><th>Status</th><th>Action</th></tr></thead><tbody>${state.sales.map(sale => `<tr><td>${escapeHtml(shortCaption(sale.post_id))}<br><span class="muted">Sale #${escapeHtml(sale.id)}</span></td><td class="amount">${money(sale.amount_paise)}</td><td><span class="pill ${sale.status === 'refunded' ? 'refunded' : 'published'}">${escapeHtml(sale.status)}</span></td><td>${sale.status !== 'refunded' ? `<button class="btn btn-danger small" data-action="refund" data-id="${escapeHtml(sale.id)}">Demo refund</button>` : '<span class="muted">Reversal recorded</span>'}</td></tr>`).join('')}</tbody></table></div>` : empty('Your results belong here', 'Record a demo sale to see it reflected in your dashboard.')}
    <div class="card card-pad section-space"><h3>Attribution with context</h3><p class="hint">These records link a sale to a chosen post. In production, verified payment webhooks, tracked links and consented customer interactions will provide evidence. A recorded link alone does not establish that the post caused the purchase.</p></div></section></div>`;
}

function roadmap() {
  return `${heading('A clear plan. <span class="serif">Room to grow.</span>', 'The full product catalogue, organized into phases with explicit acceptance gates.')}
    <div class="roadmap-intro"><span class="roadmap-number">257</span><div><h2>Planned features. One focused starting point.</h2><p>This reference demo explores one local workflow. Every production phase below remains planned. Live integrations, authentication, billing and production security are not implemented here.</p></div></div>
    <div class="phase-grid">${phases.map(([name, count, description], index) => `<article class="card phase"><div class="phase-head"><span class="phase-id">PHASE ${String(index).padStart(2, '0')}</span><span class="pill">Planned</span></div><h3>${name}</h3><p>${description}</p><div class="phase-foot">${count} planned features · Acceptance gate required</div></article>`).join('')}</div>`;
}

function render() {
  const view = currentView();
  document.querySelector('#crumb').textContent = viewNames[view];
  document.title = `${viewNames[view]} · Social Growth Agent Demo`;
  document.querySelectorAll('nav a').forEach(link => {
    const active = link.dataset.view === view;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
    link.setAttribute('aria-label', viewNames[link.dataset.view]);
  });
  app.innerHTML = ({ overview, content, leads, revenue, roadmap })[view]();
}

async function mutate(path, payload, success) {
  if (busy) return false;
  busy = true;
  const controls = [...app.querySelectorAll('button')];
  controls.forEach(button => { button.disabled = true; });
  try {
    await request(path, payload);
    await refresh();
    showNotice(success);
    return true;
  } catch (error) {
    showNotice(error.message, true);
    controls.forEach(button => { button.disabled = false; });
    return false;
  } finally { busy = false; }
}

app.addEventListener('submit', async event => {
  const form = event.target.closest('[data-form]');
  if (!form) return;
  event.preventDefault();
  if (!form.reportValidity()) return;
  const values = Object.fromEntries(new FormData(form));
  if (form.dataset.form === 'post') {
    if (!values.caption.trim()) { showNotice('Write a little content before saving your draft.', true); return; }
    mutate('/api/posts', { caption: values.caption.trim(), platform: values.platform, language: values.language }, 'Draft saved. It is ready for your review and approval.');
  }
  if (form.dataset.form === 'lead') {
    if (!values.name.trim()) { showNotice('Add a name for your demo lead.', true); return; }
    const payload = { name: values.name.trim(), phone: values.phone.trim() };
    if (values.post_id) payload.post_id = Number(values.post_id);
    mutate('/api/leads', payload, 'Demo lead recorded. No message was sent.');
  }
  if (form.dataset.form === 'sale') {
    const amount = Math.round(Number(values.amount) * 100);
    if (!Number.isSafeInteger(amount) || amount <= 0) { showNotice('Enter a valid sale amount greater than zero.', true); return; }
    const requestShape = JSON.stringify({ post_id: values.post_id, lead_id: values.lead_id, amount });
    const previous = pendingFormKeys.get(form);
    const key = previous?.shape === requestShape ? previous.key : crypto.randomUUID();
    pendingFormKeys.set(form, { shape: requestShape, key });
    const payload = { post_id: Number(values.post_id), amount_paise: amount, idempotency_key: key };
    if (values.lead_id) payload.lead_id = Number(values.lead_id);
    if (await mutate('/api/sales', payload, 'Demo sale recorded and attributed. No real payment was taken.')) pendingFormKeys.delete(form);
  }
});

app.addEventListener('click', async event => {
  const button = event.target.closest('[data-action]');
  if (!button) return;
  const id = encodeURIComponent(button.dataset.id);
  if (button.dataset.action === 'approve') mutate(`/api/posts/${id}/approve`, {}, 'Draft approved. You can now simulate publishing.');
  if (button.dataset.action === 'publish') mutate(`/api/posts/${id}/publish`, {}, 'Demo post marked published. Nothing was sent to a social network.');
  if (button.dataset.action === 'refund') {
    if (!pendingRefundKeys.has(id)) pendingRefundKeys.set(id, crypto.randomUUID());
    if (await mutate(`/api/sales/${id}/refund`, { idempotency_key: pendingRefundKeys.get(id) }, 'Demo refund recorded. The ledger includes a reversal; no real money moved.')) pendingRefundKeys.delete(id);
  }
});

window.addEventListener('hashchange', () => {
  notice.hidden = true;
  if (state) render();
  window.scrollTo({ top: 0, behavior: 'auto' });
});

refresh().catch(error => {
  document.querySelector('#loading').hidden = true;
  showNotice(`Cannot load the local demo. Start the Python backend, then reload this page. ${error.message}`, true);
});

