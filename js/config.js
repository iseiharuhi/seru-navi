/* =========================================================
   アフィリエイト設定ファイル
   ここに自分のアフィリエイトIDを入力するだけで、
   サイト全体のリンクに自動反映されます。
   ========================================================= */
window.SITE_CONFIG = {
  // サイト基本情報
  siteName: "セールナビ",
  siteUrl: "https://example.com", // ← 独自ドメインが決まったら書き換えてください

  // ---- Amazonアソシエイト ----
  // 例: "yourid-22" のような、Amazonアソシエイトの「トラッキングID」を入力
  amazonAssociateTag: "your-associate-id-22",

  // ---- 楽天アフィリエイト ----
  // 楽天アフィリエイトの「あなたのアフィリエイトID」を入力(未取得ならそのまま)
  rakutenAffiliateId: "YOUR_RAKUTEN_ID",

  // ---- A8.net など ASP ----
  // ASP案件は発行される専用リンクをそのまま deals.json の url に貼り付けてください
  // (このconfigでの自動変換は行いません)

  // Googleアナリティクス測定ID (任意。使わない場合は空文字のままでOK)
  gaId: "",
};

/**
 * 商品リンクにアフィリエイトIDを自動付与する
 * @param {string} url 商品ページURL
 * @param {string} store "amazon" | "rakuten" | "asp"
 */
function buildAffiliateUrl(url, store) {
  const cfg = window.SITE_CONFIG;
  try {
    const u = new URL(url);
    if (store === "amazon") {
      u.searchParams.set("tag", cfg.amazonAssociateTag);
      return u.toString();
    }
    if (store === "rakuten") {
      // 楽天アフィリエイトはリンク生成ツールで発行したURLをそのまま使うのが確実です。
      // 素のURLしかない場合の簡易対応として、パラメータ付与のみ行います。
      u.searchParams.set("scid", cfg.rakutenAffiliateId);
      return u.toString();
    }
    return url; // ASP等はそのまま
  } catch (e) {
    return url;
  }
}
