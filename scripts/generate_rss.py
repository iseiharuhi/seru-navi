#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/articles.json (特集記事) と data/deals.json (セール商品) から、
サイトのRSSフィード (rss.xml) を生成するスクリプト。

■ 目的
  X(旧Twitter)アカウント(@serunavi0901)などへの自動投稿は、2026年時点で
  X公式APIの無料枠が廃止されているため、無料のRSS連携ツール(dlvr.it等)を
  経由する方式を採用している。このスクリプトはそのためのRSSフィードを
  生成するだけで、実際の投稿(RSS→X)は外部ツール側の設定で行う。

■ 重要: リンク先について
  セール商品の記事アイテムは、Amazon/楽天の商品ページに直接リンクさせると
  アフィリエイトタグ(tag=/scid=)が付与されないまま(js/config.jsのbuildAffiliateUrlは
  サイト上でのクリック時にのみ動作するため)収益機会を失ってしまう。
  そのため、必ず本サイトの該当カテゴリページ(例: pages/category-amazon.html)に
  リンクする。記事アイテムは記事ページに直接リンクする。

■ 実行タイミング
  .github/workflows/update-deals.yml から update_deals.py の直後に実行され、
  deals.json の更新(楽天自動取得)に追従してrss.xmlも自動更新される。
  記事(data/articles.json)を追加した際は、手動でこのスクリプトを実行して
  rss.xmlを再生成し、GitHubにアップロードする。

■ 件数について(無料ツールの投稿上限に関する注意)
  dlvr.itの無料プランは目安で「1日5投稿」までとされている。本フィードは
  新着記事・新着セール商品をすべて含めるため、楽天の自動取得で一度に
  多数の新着が出た場合、無料プランの上限を超えた分は数日に分散して
  投稿されることになる(仕様であり、エラーではない)。投稿頻度を絞りたい
  場合は、環境変数 RSS_MAX_DEAL_ITEMS で1回の生成に含めるセール商品の
  最大件数を調整できる。
"""

import json
import os
import html
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

JST = timezone(timedelta(hours=9))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_PATH = os.path.join(BASE_DIR, "data", "articles.json")
DEALS_PATH = os.path.join(BASE_DIR, "data", "deals.json")
RSS_PATH = os.path.join(BASE_DIR, "rss.xml")

SITE_URL = os.environ.get("SITE_URL", "https://seru-navi-deals.netlify.app").rstrip("/")
SITE_NAME = "セールナビ"
SITE_DESC = "Amazon・楽天市場・各種ASPのお得なセール情報とお買い物のコツをお届けします。"

# 1回のフィード生成に含めるセール商品の最大件数(無料の投稿連携ツールの
# 1日あたりの投稿上限に配慮した目安。既定20件)。記事は件数制限なし。
MAX_DEAL_ITEMS = int(os.environ.get("RSS_MAX_DEAL_ITEMS", "20"))

STORE_LABEL = {"amazon": "Amazon", "rakuten": "楽天", "asp": "サービス・その他"}
STORE_CATEGORY_PAGE = {
    "amazon": "pages/category-amazon.html",
    "rakuten": "pages/category-rakuten.html",
    "asp": "pages/category-asp.html",
}


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def date_to_rfc822(date_str):
    """'YYYY-MM-DD' 形式の文字列を RFC 822 (pubDate用) に変換。JST 09:00固定。"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=9, tzinfo=JST)
    except (ValueError, TypeError):
        dt = datetime.now(JST)
    return format_datetime(dt)


def article_to_item(article):
    link = f"{SITE_URL}/{article['url']}"
    title = f"【特集記事】{article['title']}"
    return {
        "guid": f"seru-navi-{article['id']}",
        "title": title,
        "link": link,
        "description": article.get("description", ""),
        "pubDate": date_to_rfc822(article.get("publishedAt")),
        "sort_key": (article.get("publishedAt", ""), article["id"]),
    }


def deal_to_item(deal):
    store = deal.get("store", "asp")
    store_label = STORE_LABEL.get(store, store)
    category_page = STORE_CATEGORY_PAGE.get(store, "pages/category-asp.html")
    link = f"{SITE_URL}/{category_page}"

    price = deal.get("salePrice")
    price_text = f" ¥{price}" if price else ""
    title = f"【{store_label}】{deal.get('title', '')}{price_text}"

    desc_parts = []
    if deal.get("saleName"):
        desc_parts.append(deal["saleName"])
    if price:
        desc_parts.append(f"価格: ¥{price}")
    if deal.get("pointRate"):
        desc_parts.append(f"ポイント{deal['pointRate']}倍")
    desc_parts.append("詳細・購入は本サイトのカテゴリページから確認できます。価格・在庫は変動します。")
    description = " / ".join(desc_parts)

    return {
        "guid": f"seru-navi-{deal['id']}",
        "title": title,
        "link": link,
        "description": description,
        "pubDate": date_to_rfc822(deal.get("publishedAt")),
        "sort_key": (deal.get("publishedAt", ""), deal["id"]),
    }


def escape(text):
    return html.escape(text or "", quote=False)


def build_rss(items):
    now_rfc822 = format_datetime(datetime.now(JST))
    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">')
    parts.append("<channel>")
    parts.append(f"<title>{escape(SITE_NAME)}</title>")
    parts.append(f"<link>{escape(SITE_URL + '/')}</link>")
    parts.append(f'<atom:link href="{escape(SITE_URL + "/rss.xml")}" rel="self" type="application/rss+xml"/>')
    parts.append(f"<description>{escape(SITE_DESC)}</description>")
    parts.append("<language>ja</language>")
    parts.append(f"<lastBuildDate>{now_rfc822}</lastBuildDate>")

    for item in items:
        parts.append("<item>")
        parts.append(f"<title>{escape(item['title'])}</title>")
        parts.append(f"<link>{escape(item['link'])}</link>")
        parts.append(f"<guid isPermaLink=\"false\">{escape(item['guid'])}</guid>")
        parts.append(f"<description>{escape(item['description'])}</description>")
        parts.append(f"<pubDate>{item['pubDate']}</pubDate>")
        parts.append("</item>")

    parts.append("</channel>")
    parts.append("</rss>")
    return "\n".join(parts) + "\n"


def main():
    articles = load_json(ARTICLES_PATH)
    deals = load_json(DEALS_PATH)

    article_items = [article_to_item(a) for a in articles]

    deal_items = [deal_to_item(d) for d in deals]
    deal_items.sort(key=lambda i: i["sort_key"], reverse=True)
    deal_items = deal_items[:MAX_DEAL_ITEMS]

    all_items = article_items + deal_items
    all_items.sort(key=lambda i: i["sort_key"], reverse=True)

    rss_xml = build_rss(all_items)
    with open(RSS_PATH, "w", encoding="utf-8") as f:
        f.write(rss_xml)

    print(f"[info] rss.xml を生成しました(記事{len(article_items)}件 + セール商品{len(deal_items)}件 = 計{len(all_items)}件)")


if __name__ == "__main__":
    main()
