#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天ウェブサービスAPIから商品情報を自動取得し、data/deals.json を更新するスクリプト。

このスクリプト自体はデータの取得と deals.json の書き換えだけを行います。
GitHubへのコミット・プッシュは .github/workflows/update-deals.yml (GitHub Actions) が行います。

■ 前提
- 楽天ウェブサービスでアプリIDを取得済みであること (https://webservice.rakuten.co.jp/)
- 環境変数 RAKUTEN_APP_ID が設定されていること(必須)
- 環境変数 RAKUTEN_AFFILIATE_ID が設定されていること(推奨。無いとアフィリエイトリンクになりません)

■ このスクリプトが「自動で追加/更新/削除」するのは、
  id が "auto-" から始まる商品だけです。手動で deals.json に追加したサンプル商品
  (id: "sample-xxx" など)は書き換えません。

■ 免責
  楽天APIのレスポンスには「セール前の価格」が含まれないため、割引率(◯%OFF)は表示しません。
  代わりに「ポイント倍率」を目安として表示します。実際のお得度は必ず商品ページでご確認ください。
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))

SEARCH_ENDPOINT = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601"
RANKING_ENDPOINT = "https://app.rakuten.co.jp/services/api/IchibaItem/Ranking/20220601"

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "deals.json")

# ---- 設定(環境変数で上書き可能) ----
APP_ID = os.environ.get("RAKUTEN_APP_ID", "").strip()
AFFILIATE_ID = os.environ.get("RAKUTEN_AFFILIATE_ID", "").strip()
# カンマ区切りで複数指定可。"0" は総合ランキング。
# 特定ジャンルのIDは楽天ジャンル検索APIや商品ページのURLから調べて追加してください。
GENRE_IDS = [g.strip() for g in os.environ.get("RAKUTEN_GENRE_IDS", "0").split(",") if g.strip()]
# ポイント倍率がこの値以上の商品を「お得」として拾う
MIN_POINT_RATE = float(os.environ.get("RAKUTEN_MIN_POINT_RATE", "5"))
# 自動取得ぶんとして保持する最大件数(増えすぎ防止)
MAX_AUTO_ITEMS = int(os.environ.get("RAKUTEN_MAX_AUTO_ITEMS", "40"))
# キーワード検索でポイント還元の高い商品を探すときの検索語
SEARCH_KEYWORDS = [k.strip() for k in os.environ.get("RAKUTEN_KEYWORDS", "アウトレット,セール,訳あり").split(",") if k.strip()]

REQUEST_INTERVAL_SEC = 1.1  # 楽天APIは1秒に1回までの制限があるため余裕を持たせる


def api_get(endpoint, params):
    query = urllib.parse.urlencode(params)
    url = f"{endpoint}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "deal-site-auto-updater/1.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        body = res.read().decode("utf-8")
    return json.loads(body)


def fetch_ranking(genre_id):
    params = {
        "applicationId": APP_ID,
        "format": "json",
        "genreId": genre_id,
        "page": 1,
    }
    if AFFILIATE_ID:
        params["affiliateId"] = AFFILIATE_ID
    try:
        data = api_get(RANKING_ENDPOINT, params)
    except Exception as e:
        print(f"[warn] ランキング取得失敗 genreId={genre_id}: {e}", file=sys.stderr)
        return []
    items = []
    for row in data.get("Items", []):
        item = row.get("Item", row)  # レスポンス形式の揺れに両対応
        items.append(item)
    return items


def fetch_by_keyword(keyword):
    params = {
        "applicationId": APP_ID,
        "format": "json",
        "keyword": keyword,
        "hits": 30,
        "sort": "-reviewCount",  # レビュー数が多い= ある程度売れている商品を優先
    }
    if AFFILIATE_ID:
        params["affiliateId"] = AFFILIATE_ID
    try:
        data = api_get(SEARCH_ENDPOINT, params)
    except Exception as e:
        print(f"[warn] キーワード検索失敗 keyword={keyword}: {e}", file=sys.stderr)
        return []
    items = []
    for row in data.get("Items", []):
        item = row.get("Item", row)
        items.append(item)
    return items


def to_deal(item, category_label, sale_name):
    item_code = item.get("itemCode") or item.get("itemUrl", "")
    safe_id = "auto-" + "".join(c if c.isalnum() else "-" for c in item_code)[-60:]

    images = item.get("mediumImageUrls") or []
    image = ""
    if images:
        image = images[0].get("imageUrl", "") if isinstance(images[0], dict) else images[0]

    point_rate = item.get("pointRate")
    try:
        point_rate = int(point_rate) if point_rate is not None else None
    except (TypeError, ValueError):
        point_rate = None

    now = datetime.now(JST)
    return {
        "id": safe_id,
        "title": (item.get("itemName") or "")[:80],
        "store": "rakuten",
        "category": category_label,
        "emoji": "🛍️",
        "image": image,
        "originalPrice": None,  # 楽天APIからは「セール前価格」を取得できないため意図的に空にする
        "salePrice": item.get("itemPrice"),
        "pointRate": point_rate,
        "url": item.get("affiliateUrl") or item.get("itemUrl") or "",
        "saleName": sale_name,
        "saleEnd": (now + timedelta(days=3)).strftime("%Y-%m-%d"),  # 目安。実際の終了日ではない
        "isNew": True,
        "description": "楽天ウェブサービスAPIから自動取得した商品です。価格・在庫は変動するため商品ページでご確認ください。",
        "publishedAt": now.strftime("%Y-%m-%d"),
        "source": "rakuten-auto",
    }


def collect_candidates():
    candidates = {}

    for genre_id in GENRE_IDS:
        items = fetch_ranking(genre_id)
        time.sleep(REQUEST_INTERVAL_SEC)
        for item in items[:10]:
            deal = to_deal(item, "ランキング上位", "楽天ランキング")
            candidates[deal["id"]] = deal

    for keyword in SEARCH_KEYWORDS:
        items = fetch_by_keyword(keyword)
        time.sleep(REQUEST_INTERVAL_SEC)
        high_point_items = [
            i for i in items
            if _safe_point_rate(i) >= MIN_POINT_RATE
        ]
        high_point_items.sort(key=_safe_point_rate, reverse=True)
        for item in high_point_items[:8]:
            deal = to_deal(item, "高ポイント還元", f"「{keyword}」で検出")
            candidates[deal["id"]] = deal

    return list(candidates.values())


def _safe_point_rate(item):
    try:
        return float(item.get("pointRate") or 0)
    except (TypeError, ValueError):
        return 0.0


def load_existing():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def save(deals):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(deals, f, ensure_ascii=False, indent=2)
        f.write("\n")


def merge(existing, new_candidates):
    manual = [d for d in existing if not d.get("id", "").startswith("auto-")]
    previous_auto_ids = {d["id"] for d in existing if d.get("id", "").startswith("auto-")}

    # 新規取得ぶんを新着順(publishedAt)で先頭に、既存auto分の古いものは切り捨てる
    new_candidates.sort(key=lambda d: d.get("publishedAt", ""), reverse=True)
    trimmed_auto = new_candidates[:MAX_AUTO_ITEMS]

    added = sum(1 for d in trimmed_auto if d["id"] not in previous_auto_ids)
    print(f"[info] 自動取得: 候補{len(new_candidates)}件 → 採用{len(trimmed_auto)}件(新規{added}件)")

    return manual + trimmed_auto


def main():
    if not APP_ID:
        print("[error] 環境変数 RAKUTEN_APP_ID が設定されていません。処理を中止します。", file=sys.stderr)
        sys.exit(1)

    existing = load_existing()
    candidates = collect_candidates()

    if not candidates:
        print("[warn] 取得できた商品が0件でした。deals.jsonは変更しません。")
        return

    merged = merge(existing, candidates)
    save(merged)
    print(f"[info] deals.json を更新しました(合計 {len(merged)} 件)")


if __name__ == "__main__":
    main()
