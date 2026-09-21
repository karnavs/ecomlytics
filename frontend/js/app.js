const API = "/api";

(function(){
 if(!localStorage.getItem("ecomlytics_user")) window.location.href="/login.html";
})();

const fmt = n => new Intl.NumberFormat("en-IN",{maximumFractionDigits:0}).format(n);
const money = n => "₹" + fmt(n);

async function api(path){
 const r=await fetch(API+path);
 if(!r.ok) throw new Error("API request failed: "+r.status);
 return r.json();
}

window.addEventListener("error", e => {
 const c=document.getElementById("content");
 if(c && !c.innerHTML.trim()) c.innerHTML='<div class="card"><div class="section-title">Unable to load analytics</div><p class="note">Make sure the FastAPI server is running and refresh this page.</p></div>';
});

function shell(active){
 document.querySelector(".app").innerHTML = `
 <aside class="sidebar">
 <div class="brand"><div class="brand-mark">E</div><div class="brand-name">Ecom<span>lytics</span></div></div>

  <div class="nav-label">Workspace</div>

  <nav class="nav">
   <a href="/index.html" class="${active==="overview"?"active":""}">
    <span class="ico">⌂</span>Overview
   </a>

   <a href="/pages/sales.html" class="${active==="sales"?"active":""}">
    <span class="ico">◈</span>Sales Analytics
   </a>

   <a href="/pages/products.html" class="${active==="products"?"active":""}">
    <span class="ico">▦</span>Product Intelligence
   </a>

   <a href="/pages/customers.html" class="${active==="customers"?"active":""}">
    <span class="ico">◉</span>Customer Intelligence
   </a>

   <a href="/pages/retention.html" class="${active==="retention"?"active":""}">
    <span class="ico">↗</span>Retention & Funnel
   </a>

   <a href="/pages/insights.html" class="${active==="insights"?"active":""}">
    <span class="ico">✦</span>Business Insights
   </a>
  </nav>

  <div class="nav-label">Platform</div>

  <nav class="nav">
   <a href="/pages/data-sources.html" class="${active==="data-sources"?"active":""}">
    <span class="ico">⇄</span>Data Sources
   </a>

   <a href="#">
    <span class="ico">⚙</span>Settings
   </a>
  </nav>

  <div class="sidebar-footer">
   <span class="status-dot"></span>Analytics engine online
   <br>

   <a href="#"
      onclick="localStorage.removeItem('ecomlytics_user');window.location.href='/login.html';return false;"
      style="display:inline-block;margin-top:8px;color:#aab6ce">
      Sign out
   </a>
  </div>

 </aside>

 <main class="main" id="content"></main>`;
}

function header(title,sub){
 return `
 <div class="top">
  <div class="title">
   <h1>${title}</h1>
   <p>${sub}</p>
  </div>

  <div class="top-right">
   <span class="badge" title="This workspace is showing the bundled demo dataset (data/*.csv), not a live connected data source.">
    <span class="status-dot"></span>Demo Data
   </span>

   <div class="profile">GY</div>
  </div>
 </div>`
}

function deltaHtml(m){
 if(!m || m.change_pct===null || m.change_pct===undefined){
  return `<div class="delta note">Not enough data for period comparison</div>`;
 }
 const up = m.change_pct >= 0;
 const arrow = up ? "▲" : "▼";
 const cls = up ? "delta up" : "delta down";
 return `<div class="${cls}">${arrow} ${Math.abs(m.change_pct)}% vs previous ${'30 days'}</div>`;
}

function productRows(products){
 return products.map(p=>`
 <tr>
  <td><b>${p.product_name}</b></td>
  <td>${p.category}</td>
  <td>${fmt(p.views)}</td>
  <td>${fmt(p.units_sold)}</td>
  <td>${money(p.revenue)}</td>
  <td>${p.conversion}%</td>
  <td>${p.rating}</td>
  <td>${p.return_rate}%</td>
 </tr>
 `).join("");
}

async function overviewPage(){

 shell("overview");

 const o=await api("/overview");
 const p=await api("/products");
 const ins=await api("/insights");

 document.getElementById("content").innerHTML=

 header(
  "Overview",
  "A single view of revenue, products, customers and business health"
 )+

 `
 <div class="grid kpis">

  <div class="card kpi">
   <div class="label">Revenue</div>
   <div class="value">${money(o.revenue)}</div>
   ${deltaHtml(o.comparison && o.comparison.metrics && o.comparison.metrics.revenue)}
  </div>

  <div class="card kpi">
   <div class="label">Orders</div>
   <div class="value">${fmt(o.orders)}</div>
   ${deltaHtml(o.comparison && o.comparison.metrics && o.comparison.metrics.orders)}
  </div>

  <div class="card kpi">
   <div class="label">Average Order Value</div>
   <div class="value">${money(o.aov)}</div>
   ${deltaHtml(o.comparison && o.comparison.metrics && o.comparison.metrics.aov)}
  </div>

  <div class="card kpi">
   <div class="label">Repeat Purchase Rate</div>
   <div class="value">${o.repeat_rate}%</div>
   ${deltaHtml(o.comparison && o.comparison.metrics && o.comparison.metrics.repeat_rate)}
  </div>

 </div>

 <div class="grid two" style="margin-top:18px">

  <div class="card">
   <div class="section-title">Top Products by Revenue</div>

   <div class="table-wrap">

    <table class="table">

     <thead>
      <tr>
       <th>Product</th>
       <th>Category</th>
       <th>Revenue</th>
       <th>Conversion</th>
      </tr>
     </thead>

     <tbody>

      ${
       p
       .sort((a,b)=>b.revenue-a.revenue)
       .slice(0,5)
       .map(x=>`
        <tr>
         <td><b>${x.product_name}</b></td>
         <td>${x.category}</td>
         <td>${money(x.revenue)}</td>
         <td>${x.conversion}%</td>
        </tr>
       `)
       .join("")
      }

     </tbody>

    </table>

   </div>
  </div>

  <div class="card">

   <div class="section-title">What needs attention?</div>

   ${
    ins
    .slice(0,3)
    .map(i=>`
     <div class="insight ${i.priority.toLowerCase()}">
      <h3>${i.title}</h3>
      <p>${i.detail}</p>
     </div>
    `)
    .join("")
   }

  </div>

 </div>

 <div class="grid three" style="margin-top:18px">

  <div class="card">
   <div class="section-title">Catalog</div>
   <div class="value" style="font-size:25px;font-weight:800">
    ${o.products}
   </div>
   <p class="note">Products tracked across the store.</p>
  </div>

  <div class="card">
   <div class="section-title">Units Sold</div>
   <div class="value" style="font-size:25px;font-weight:800">
    ${fmt(o.units)}
   </div>
   <p class="note">Total units represented in the order dataset.</p>
  </div>

  <div class="card">
   <div class="section-title">Return Rate</div>
   <div class="value" style="font-size:25px;font-weight:800">
    ${o.return_rate}%
   </div>
   <p class="note">
    Use returns as a product-quality and expectation signal.
   </p>
  </div>

 </div>
 `;
}

async function salesPage(){

 shell("sales");

 const o=await api("/overview");

 const days=[
  42000,
  51000,
  47000,
  63000,
  59000,
  76000,
  82000,
  79000,
  91000,
  86000,
  103000,
  98000
 ];

 document.getElementById("content").innerHTML=

 header(
  "Sales Analytics",
  "Understand revenue movement, order volume and basket value"
 )+

 `
 <div class="grid kpis">

  <div class="card kpi">
   <div class="label">Revenue</div>
   <div class="value">${money(o.revenue)}</div>
   <div class="delta">Current dataset</div>
  </div>

  <div class="card kpi">
   <div class="label">Orders</div>
   <div class="value">${fmt(o.orders)}</div>
   <div class="delta">Completed + returned</div>
  </div>

  <div class="card kpi">
   <div class="label">AOV</div>
   <div class="value">${money(o.aov)}</div>
   <div class="delta">Revenue / orders</div>
  </div>

  <div class="card kpi">
   <div class="label">Units</div>
   <div class="value">${fmt(o.units)}</div>
   <div class="delta">Units sold</div>
  </div>

 </div>

 <div class="grid two" style="margin-top:18px">

  <div class="card">

   <div class="section-title">Revenue Trend</div>

   <div class="chart">

    ${
     days.map((v,i)=>`
      <div class="col">

       <div class="barv">
        <i style="height:${Math.round(v/1100)}px"></i>
       </div>

       <small>W${i+1}</small>

      </div>
     `).join("")
    }

   </div>

  </div>

  <div class="card">

   <div class="section-title">Sales Questions</div>

   <div class="insight">
    <h3>Revenue health</h3>
    <p>
     Track whether revenue growth is coming from more customers,
     higher AOV, or increased repeat purchases.
    </p>
   </div>

   <div class="insight">
    <h3>Basket behavior</h3>
    <p>
     AOV can reveal opportunities for bundles,
     cross-sells and threshold-based offers.
    </p>
   </div>

  </div>

 </div>

 <div class="card" style="margin-top:18px">

  <div class="section-title">Business interpretation</div>

  <p class="note">
   Sales Analytics connects revenue and order metrics so operators
   can move from “what happened?” to “what should we investigate?”
  </p>

 </div>
 `;
}

async function productsPage(){

 shell("products");

 const p=await api("/products");

 document.getElementById("content").innerHTML=

 header(
  "Product Intelligence",
  "Find winning products, weak conversion and product-level opportunities"
 )+

 `
 <div class="filters">

  <input
   id="search"
   class="input"
   placeholder="Search products..."
  >

  <select id="cat" class="select">

   <option value="">All categories</option>

   ${
    [...new Set(p.map(x=>x.category))]
    .map(c=>`<option>${c}</option>`)
    .join("")
   }

  </select>

 </div>

 <div class="card">

  <div class="section-title">Product Performance</div>

  <div class="table-wrap">

   <table class="table">

    <thead>

     <tr>
      <th>Product</th>
      <th>Category</th>
      <th>Views</th>
      <th>Units</th>
      <th>Revenue</th>
      <th>Conversion</th>
      <th>Rating</th>
      <th>Returns</th>
     </tr>

    </thead>

    <tbody id="productBody">
     ${productRows(p)}
    </tbody>

   </table>

  </div>

 </div>

 <div class="grid three" style="margin-top:18px">

  <div class="card">
   <div class="section-title">High Traffic / Low Conversion</div>
   <p class="note">
    Identify products attracting attention but failing to convert.
    This is a strong investigation signal.
   </p>
  </div>

  <div class="card">
   <div class="section-title">Margin Opportunities</div>
   <p class="note">
    Compare product revenue with cost to identify products
    contributing meaningful gross margin.
   </p>
  </div>

  <div class="card">
   <div class="section-title">Return Signals</div>
   <p class="note">
    High return rates can point to expectation, quality,
    sizing or fulfillment problems.
   </p>
  </div>

 </div>
 `;

 const render=()=>{

  let q=document
   .getElementById("search")
   .value
   .toLowerCase();

  let c=document
   .getElementById("cat")
   .value;

  document.getElementById("productBody").innerHTML=

   productRows(
    p.filter(x=>
     (!q || x.product_name.toLowerCase().includes(q)) &&
     (!c || x.category===c)
    )
   );
 };

 document.getElementById("search").oninput=render;
 document.getElementById("cat").onchange=render;
}

async function customersPage(){

 shell("customers");

 const d=await api("/customers/segments");

 const colors={
  "Champions":"good",
  "Loyal":"good",
  "Potential Loyalist":"",
  "At Risk":"danger",
  "Lost":"warn"
 };

 document.getElementById("content").innerHTML=

 header(
  "Customer Intelligence",
  "Segment customers by value, recency and relationship"
 )+

 `
 <div class="grid three">

  ${
   Object.entries(d.counts)
   .map(([k,v])=>`

    <div class="card">

     <div class="section-title">${k}</div>

     <div style="font-size:28px;font-weight:800">
      ${v}
     </div>

     <p class="note">
      Customers in this segment
     </p>

     <span class="pill ${colors[k]||""}">
      ${money(d.spend[k]||0)} spend
     </span>

    </div>

   `)
   .join("")
  }

 </div>

 <div class="card" style="margin-top:18px">

  <div class="section-title">Customer Portfolio</div>

  <div class="table-wrap">

   <table class="table">

    <thead>

     <tr>
      <th>Customer</th>
      <th>City</th>
      <th>Orders</th>
      <th>Total Spend</th>
      <th>Days Since Order</th>
      <th>Segment</th>
     </tr>

    </thead>

    <tbody>

     ${
      d.customers.map(c=>`

       <tr>

        <td><b>${c.customer_name}</b></td>

        <td>${c.city}</td>

        <td>${c.orders}</td>

        <td>${money(c.total_spend)}</td>

        <td>${c.last_order_days}</td>

        <td>
         <span class="pill ${colors[c.segment]||""}">
          ${c.segment}
         </span>
        </td>

       </tr>

      `).join("")
     }

    </tbody>

   </table>

  </div>

 </div>

 <div class="grid two" style="margin-top:18px">

  <div class="card">

   <div class="section-title">RFM-style thinking</div>

   <p class="note">
    Recency shows who is becoming inactive.
    Frequency shows loyalty.
    Monetary value shows customer contribution.
    Together they support targeted retention decisions.
   </p>

  </div>

  <div class="card">

   <div class="section-title">Customer value</div>

   <p class="note">
    Prioritize personalized engagement around Champions
    and reactivation campaigns for At Risk and Lost customers.
   </p>

  </div>

 </div>
 `;
}

async function retentionPage(){

 shell("retention");

 const f=await api("/funnel");

 document.getElementById("content").innerHTML=

 header(
  "Retention & Funnel",
  "Understand where customers drop and how retention changes over time"
 )+

 `
 <div class="grid two">

  <div class="card">

   <div class="section-title">Purchase Funnel</div>

   ${
    f.stages.map((s,i)=>`

     <div class="funnel-row">

      <div class="funnel-head">
       <span>${s.name}</span>
       <b>${fmt(s.value)}</b>
      </div>

      <div class="bar">
       <i style="width:${Math.max(
        8,
        s.value/f.stages[0].value*100
       )}%"></i>
      </div>

      <p class="note">
       ${
        i
        ? ((s.value/f.stages[i-1].value)*100).toFixed(1)
          +"% of previous stage"
        : "Entry volume"
       }
      </p>

     </div>

    `).join("")
   }

  </div>

  <div class="card">

   <div class="section-title">Funnel Diagnosis</div>

   <div class="insight high">

    <h3>Largest opportunity</h3>

    <p>
     Compare each stage's conversion.
     A sharp drop can indicate pricing, UX, trust,
     stock or checkout friction.
    </p>

   </div>

   <div class="insight">

    <h3>Retention lens</h3>

    <p>
     Connect funnel behavior with repeat purchase segments
     to distinguish acquisition problems from loyalty problems.
    </p>

   </div>

  </div>

 </div>

 <div class="grid three" style="margin-top:18px">

  <div class="card">

   <div class="section-title">Week 1 Retention</div>

   <div style="font-size:27px;font-weight:800">
    42%
   </div>

   <p class="note">
    Illustrative cohort view.
   </p>

  </div>

  <div class="card">

   <div class="section-title">Week 4 Retention</div>

   <div style="font-size:27px;font-weight:800">
    27%
   </div>

   <p class="note">
    Illustrative cohort view.
   </p>

  </div>

  <div class="card">

   <div class="section-title">Repeat Purchase</div>

   <div style="font-size:27px;font-weight:800">
    80%
   </div>

   <p class="note">
    Dataset-based customer repeat signal.
   </p>

  </div>

 </div>
 `;
}

async function insightsPage(){

 shell("insights");

 const ins=await api("/insights");

 document.getElementById("content").innerHTML=

 header(
  "Business Insights",
  "Turn metrics into clear investigation points and recommended actions"
 )+

 `
 <div class="grid two">

  ${
   ins.map(i=>`

    <div class="card">

     <span class="pill ${
      i.priority==="High"
      ?"danger"
      :"warn"
     }">
      ${i.priority} priority
     </span>

     <div class="insight ${i.priority.toLowerCase()}">

      <h3>${i.title}</h3>

      <p>${i.detail}</p>

      <p>
       <b>Recommended action:</b>
       ${i.action}
      </p>

     </div>

    </div>

   `).join("")
  }

 </div>

 <div class="card" style="margin-top:18px">

  <div class="section-title">Decision workflow</div>

  <div class="grid three">

   <div>
    <b>1. Measure</b>
    <p class="note">
     Track the business KPI.
    </p>
   </div>

   <div>
    <b>2. Explain</b>
    <p class="note">
     Find the product, customer or funnel pattern behind it.
    </p>
   </div>

   <div>
    <b>3. Decide</b>
    <p class="note">
     Prioritize an action or investigation using evidence.
    </p>
   </div>

  </div>

 </div>
 `;
}

const GA_STATUS_MESSAGES = {
 connected: ["ok", "Google Analytics connected."],
 denied: ["warn", "Google Analytics connection was cancelled."],
 invalid_state: ["warn", "That connection link expired or was already used — try connecting again."],
 missing_code: ["warn", "Google didn't return an authorization code — try again."],
 token_exchange_failed: ["warn", "Google rejected the token exchange — check your client credentials."],
};

async function dataSourcesPage(){

 shell("data-sources");

 const params = new URLSearchParams(window.location.search);
 const gaStatus = params.get("ga_status");
 if(gaStatus){
  // Strip the query param so a refresh doesn't re-show the toast.
  window.history.replaceState({}, "", window.location.pathname);
 }

 const res = await api("/data-sources");
 const sources = res.sources;

 const stateBadge = s => {
  const map = {
   connected: ["Connected","ok"],
   disconnected: ["Not connected","warn"],
   not_configured: ["Configuration required","warn"],
   needs_attention: ["Needs attention","warn"],
   syncing: ["Syncing","info"],
  };
  const [label, cls] = map[s] || [s, "warn"];
  return `<span class="source-state ${cls}">${label}</span>`;
 };

 const toast = gaStatus && GA_STATUS_MESSAGES[gaStatus]
  ? `<div class="note-banner ${GA_STATUS_MESSAGES[gaStatus][0]}">${GA_STATUS_MESSAGES[gaStatus][1]}</div>`
  : "";

 document.getElementById("content").innerHTML =

 header(
  "Data Sources",
  "Connect and manage where your analytics data comes from"
 ) +

 toast +

 `<div class="grid two" style="margin-top:18px">` +

 sources.map(s => `
  <div class="card">
   <div class="section-title">${s.name}</div>
   ${stateBadge(s.state)}
   <p class="note" style="margin-top:8px">${s.message || ""}</p>
   ${s.property_id ? `<p class="note">Property: ${s.property_id}</p>` : ""}
   <p class="note">Last synced: ${s.last_synced ? new Date(s.last_synced).toLocaleString() : "Never"}</p>
   ${s.id === "google_analytics" && s.state !== "connected" && s.state !== "needs_attention"
     ? `<button class="btn" id="connect-ga">Connect Google Analytics</button>` : ""}
   ${s.id === "google_analytics" && (s.state === "connected" || s.state === "needs_attention")
     ? `<button class="btn secondary" id="disconnect-ga">Disconnect</button>` : ""}
   ${s.id === "google_analytics" && s.state === "connected"
     ? `<div id="ga-preview" class="note" style="margin-top:10px">Loading live metrics…</div>` : ""}
  </div>
 `).join("") +

 `</div>`;

 const connectBtn = document.getElementById("connect-ga");
 if(connectBtn){
  connectBtn.onclick = async () => {
   try {
    const r = await fetch(API + "/data-sources/google/connect", {method:"POST"});
    const data = await r.json();
    if(!r.ok){
     alert(data.detail || "Google Analytics is not configured on this server yet.");
     return;
    }
    window.location.href = data.authorization_url;
   } catch(e){
    alert("Could not start the Google Analytics connection.");
   }
  };
 }

 const disconnectBtn = document.getElementById("disconnect-ga");
 if(disconnectBtn){
  disconnectBtn.onclick = async () => {
   if(!confirm("Disconnect Google Analytics? You'll need to reauthorize to reconnect.")) return;
   try {
    await fetch(API + "/data-sources/google_analytics", {method:"DELETE"});
    dataSourcesPage();
   } catch(e){
    alert("Could not disconnect Google Analytics.");
   }
  };
 }

 const preview = document.getElementById("ga-preview");
 if(preview){
  try {
   const r = await fetch(API + "/analytics/ga4-overview");
   const data = await r.json();
   if(data.success){
    const m = data.data;
    const show = v => (v===null || v===undefined) ? "N/A" : fmt(v);
    preview.innerHTML =
     `Last ${data.meta.date_range.start} → ${data.meta.date_range.end}: ` +
     `${show(m.activeUsers)} users · ${show(m.sessions)} sessions`;
   } else {
    preview.innerHTML = `<span class="delta note">${data.error.message}</span>`;
   }
  } catch(e){
   preview.innerHTML = `<span class="delta note">Couldn't load live metrics.</span>`;
  }
 }
}

const page=document.body.dataset.page;

if(page==="overview") overviewPage();

if(page==="data-sources") dataSourcesPage();

if(page==="sales") salesPage();

if(page==="products") productsPage();

if(page==="customers") customersPage();

if(page==="retention") retentionPage();

if(page==="insights") insightsPage();