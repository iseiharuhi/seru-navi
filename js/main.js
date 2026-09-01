/* =========================================================
   セールナビ - 共通スクリプト
   deals.json を読み込み、カードを描画/絞り込み/並び替えする
   ========================================================= */

const STORE_LABEL = { amazon: "Amazon", rakuten: "楽天", asp: "その他" };

// 「新着順」で表示する際の店舗の並び順(交互表示の基準)。
// Amazonの掲載日は手動更新のため楽天(15分毎に自動更新)より古くなりがちで、
// 単純な日付ソートだとAmazon商品が埋もれてしまう。
// そのため「新着順」は日付の完全なソートではなく、店舗ごとに新しい順へ並べたグループを
// この順番でラウンドロビン(交互)に混ぜて表示する。
const STORE_ORDER = ["amazon", "rakuten", "asp"];

/**
 * 店舗ごとにグループ化し、各グループ内は publishedAt の新しい順に並べたうえで、
 * STORE_ORDER の順に1件ずつ交互に取り出して結合する。
 * (例: Amazon→楽天→その他→Amazon→楽天...の順で、各店舗の在庫が尽きるまで続く)
 */
function interleaveByStore(list) {
  const groups = {};
  STORE_ORDER.forEach((s) => {
    groups[s] = [];
  });
  const extra = []; // STORE_ORDER に定義のない店舗が来た場合の保険

  list.forEach((d) => {
    if (groups[d.store]) {
      groups[d.store].push(d);
    } else {
      extra.push(d);
    }
  });

  const order = STORE_ORDER.filter((s) => groups[s].length);
  order.forEach((s) => {
    groups[s].sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));
  });
  extra.sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt));

  const result = [];
  let added = true;
  while (added) {
    added = false;
    order.forEach((s) => {
      if (groups[s].length) {
        result.push(groups[s].shift());
        added = true;
      }
    });
  }
  return result.concat(extra);
}

async function loadDeals() {
  // data/deals.json への相対パスはページの場所によって変わるため、
  // <body data-root="."> や data-root="..": のような形でルートを指定しておく
  const root = document.body.dataset.root || ".";
  const res = await fetch(`${root}/data/deals.json`);
  if (!res.ok) throw new Error("deals.json の読み込みに失敗しました");
  return res.json();
}

function discountPercent(deal) {
  if (!deal.originalPrice || !deal.salePrice) return null;
  return Math.round((1 - deal.salePrice / deal.originalPrice) * 100);
}

function formatYen(n) {
  if (n === null || n === undefined) return "";
  return "¥" + n.toLocaleString("ja-JP");
}

function daysLeft(dateStr) {
  const end = new Date(dateStr + "T23:59:59+09:00");
  const now = new Date();
  const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
  return diff;
}

function dealCardHTML(deal) {
  const pct = discountPercent(deal);
  const url = buildAffiliateUrl(deal.url, deal.store);
  const left = daysLeft(deal.saleEnd);
  const endLabel = left > 0 ? `残り${left}日` : "終了間近";

  const badge = pct
    ? `<span class="discount-badge">${pct}%OFF</span>`
    : deal.pointRate
      ? `<span class="discount-badge point">P${deal.pointRate}倍</span>`
      : "";
  const thumbInner = deal.image
    ? `<img src="${deal.image}" alt="" loading="lazy">`
    : `<span class="emoji">${deal.emoji || "🛍️"}</span>`;

  return `
  <article class="deal-card" data-store="${deal.store}" data-category="${deal.category}"
           data-published="${deal.publishedAt}" data-discount="${pct ?? 0}">
    <a class="deal-thumb" href="${url}" target="_blank" rel="nofollow sponsored noopener">
      <span class="store-tag ${deal.store}">${STORE_LABEL[deal.store]}</span>
      ${badge}
      ${thumbInner}
    </a>
    <div class="deal-body">
      <a class="deal-title" href="${url}" target="_blank" rel="nofollow sponsored noopener">${deal.title}</a>
      <div class="deal-price-row">
        ${deal.salePrice ? `<span class="deal-price">${formatYen(deal.salePrice)}</span>` : ""}
        ${deal.originalPrice ? `<span class="deal-price-orig">${formatYen(deal.originalPrice)}</span>` : ""}
      </div>
      <div class="deal-meta">
        <span>${deal.saleName || ""}</span>
        <span>${endLabel}</span>
      </div>
      <a class="deal-cta" href="${url}" target="_blank" rel="nofollow sponsored noopener">
        詳細を見る<span class="rel-note"></span>
      </a>
    </div>
  </article>`;
}

/**
 * grid: 描画先の要素
 * deals: 表示する配列
 */
function renderGrid(grid, deals) {
  if (!deals.length) {
    grid.innerHTML = `<div class="empty-state">該当するセール情報はまだありません。</div>`;
    return;
  }
  grid.innerHTML = deals.map(dealCardHTML).join("");
}

/**
 * フィルター/並び替えバーと連動してカードを描画する
 * options.storeFilter: "amazon" | "rakuten" | "asp" | null(=絞り込みバーで全店舗切替)
 */
async function initDealGrid(gridId, options = {}) {
  const grid = document.getElementById(gridId);
  if (!grid) return;

  let deals = await loadDeals();
  if (options.fixedStore) {
    deals = deals.filter((d) => d.store === options.fixedStore);
  }
  if (options.limit) {
    deals = interleaveByStore(deals.slice()).slice(0, options.limit);
  }

  let currentStore = "all";
  let currentSort = "new";

  function apply() {
    let list = deals.slice();
    if (currentStore !== "all") {
      list = list.filter((d) => d.store === currentStore);
    }
    if (currentSort === "new") {
      list = interleaveByStore(list);
    } else if (currentSort === "discount") {
      list.sort((a, b) => (discountPercent(b) || 0) - (discountPercent(a) || 0));
    } else if (currentSort === "ending") {
      list.sort((a, b) => daysLeft(a.saleEnd) - daysLeft(b.saleEnd));
    }
    renderGrid(grid, list);
  }

  const chips = document.querySelectorAll(`[data-filter-target="${gridId}"] .chip`);
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((c) => c.setAttribute("aria-pressed", "false"));
      chip.setAttribute("aria-pressed", "true");
      currentStore = chip.dataset.store;
      apply();
    });
  });

  const sortSelect = document.querySelector(`[data-sort-target="${gridId}"]`);
  if (sortSelect) {
    sortSelect.addEventListener("change", () => {
      currentSort = sortSelect.value;
      apply();
    });
  }

  apply();
}

/* ---------- モバイルナビ開閉 ---------- */
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".main-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => nav.classList.toggle("open"));
  }
});
