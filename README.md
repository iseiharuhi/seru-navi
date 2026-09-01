# セールナビ(アフィリエイト向けセール情報サイト・雛形)

Amazon・楽天市場・各種ASPのセール情報をまとめる「セール情報サイト」の雛形です。
HTML/CSS/JSのみで作られた静的サイトなので、サーバー不要・無料ホスティングですぐ公開できます。

---

## 1. まずやること(公開前チェックリスト)

- [ ] `js/config.js` に自分のAmazonアソシエイトID・楽天アフィリエイトIDを入力する
- [ ] `data/deals.json` のサンプル商品を、実際にあなたが紹介したい商品・実在のアフィリエイトリンクに差し替える
- [ ] `pages/contact.html` の連絡先をあなたの実際のメールアドレスに差し替える
- [ ] `pages/privacy.html` / `pages/disclosure.html` の内容を確認し、必要に応じて調整する
- [ ] `robots.txt` / `sitemap.xml` の `https://example.com` を実際のドメインに置き換える
- [ ] 各記事に入っている商品・価格は**サンプルデータ**です。必ず公式ページで現在の価格・在庫・キャンペーン条件を確認してから公開してください

> ⚠️ 特に注意: Amazon・楽天のセール名や日程は変わります。記事内の「〇月開催」等の記述は、
> 公開直前に必ず公式サイトで最新の開催スケジュールを確認・更新してください。

---

## 2. フォルダ構成

```
deal-site/
├── index.html              トップページ
├── pages/
│   ├── category-amazon.html   Amazon特集
│   ├── category-rakuten.html  楽天特集
│   ├── category-asp.html      サービス・その他(ASP案件)
│   ├── article-*.html         記事ページ(サンプル2本)
│   ├── about.html             このサイトについて
│   ├── privacy.html           プライバシーポリシー
│   ├── disclosure.html        アフィリエイト広告表記(必須ページ)
│   └── contact.html           お問い合わせ
├── css/style.css           デザイン(1ファイルにまとめてあります)
├── js/
│   ├── config.js           ★アフィリエイトID設定はここ
│   └── main.js             セールカードの描画・絞り込み・並び替え
├── data/deals.json         ★セール商品データはここ(記事を増やさず商品追加が可能)
├── scripts/update_deals.py 楽天APIから商品を自動取得するスクリプト(§5参照)
├── .github/workflows/
│   └── update-deals.yml    30分毎にupdate_deals.pyを実行するGitHub Actions定義
├── robots.txt
└── sitemap.xml
```

---

## 3. 新しいセール情報を追加する方法(一番よく使う作業)

HTMLを編集する必要はありません。`data/deals.json` に以下の形式でオブジェクトを1つ追加するだけで、
トップページと該当カテゴリページの両方に自動で表示されます。

```json
{
  "id": "一意のID(自由に決めてOK)",
  "title": "商品名",
  "store": "amazon",            // "amazon" / "rakuten" / "asp"
  "category": "ガジェット",
  "emoji": "🎧",                // 画像がない場合のアイコン代わり
  "image": "",                  // 商品画像URLがあれば入力(任意)
  "originalPrice": 12800,
  "salePrice": 7480,
  "url": "https://www.amazon.co.jp/dp/XXXXXXXXXX",
  "saleName": "スマイルSALE",
  "saleEnd": "2026-09-03",      // 表示上の「残り〇日」計算に使用
  "isNew": true,
  "description": "商品説明(現在は表示に未使用、将来の拡張用)",
  "publishedAt": "2026-08-28"   // 新着順ソートに使用
}
```

Amazon商品のURLに `tag=` パラメータは**自動で付与される**ので、`config.js` にIDさえ設定しておけば
`deals.json` には素のAmazon商品URLを貼るだけでOKです。楽天・ASPはアフィリエイトツールで発行した
リンクをそのまま `url` に貼り付けてください。

---

## 4. 公開先(現在: Netlify)

本プロジェクトは **Netlify** で公開しています(公開URL: `https://seru-navi-deals.netlify.app/`)。
GitHub Pagesは公開URLに `https://ユーザー名.github.io/...` のようにGitHubアカウント名が出てしまうため、
それを避ける目的でNetlifyに移行しました(経緯はプロジェクトドキュメント参照)。

NetlifyはこのGitHubリポジトリ(`main`ブランチ)と連携済みで、`git push` されるたびに自動でビルド・
再デプロイされます(Continuous Deployment)。つまり `scripts/update_deals.py` が15分毎に
`data/deals.json` を更新・pushすると、Netlify側も自動的に最新内容に更新されます。追加の作業は不要です。

独自ドメインを使いたくなった場合は、NetlifyのSite settings → Domain managementから設定できます。

---

## 5. 商品を自動で取得・投稿する(15分毎の自動更新)

`scripts/update_deals.py` と `.github/workflows/update-deals.yml` を使うと、楽天ウェブサービスAPIから
商品情報を自動取得し、GitHub Actionsが15分毎(毎時07分・22分・37分・52分)に `data/deals.json` を
更新・コミット・プッシュしてくれます。GitHub Pagesで公開している場合、そのままサイトにも自動反映されます。

実行時刻をあえて「0分・30分ちょうど」からずらしているのは、GitHub Actions側でその時刻の実行が
混み合いやすく遅延・間引きされやすいためです(詳しくは5-3参照)。

このツールが自動で追加・入れ替えするのは `id` が `auto-` から始まる商品だけです。手動で追加した
商品(`sample-xxx` など)は書き換えられません。

### 5-1. 楽天APIの利用登録(無料・審査なし)

1. [楽天ウェブサービス](https://webservice.rakuten.co.jp/)に楽天会員でログインし、「アプリID発行」からアプリを新規登録する
2. 発行された **アプリID(applicationId)** を控える
3. 楽天アフィリエイトに登録済みなら、楽天アフィリエイトの管理画面で **アフィリエイトID** も控える
   (無くても動きますが、その場合はアフィリエイト報酬が発生するリンクになりません)

### 5-2. GitHubリポジトリの設定

1. リポジトリの **Settings → Actions → General → Workflow permissions** で
   「Read and write permissions」を選択して保存する(これがないと自動コミットに失敗します)
2. **Settings → Secrets and variables → Actions** を開き、以下を登録する

   | 種類 | 名前 | 値 |
   |------|------|----|
   | Secret | `RAKUTEN_APP_ID` | 手順5-1で取得したアプリID(必須) |
   | Secret | `RAKUTEN_ACCESS_KEY` | 手順5-1で取得したアクセスキー(必須。2026年のAPI移行で追加された) |
   | Secret | `RAKUTEN_AFFILIATE_ID` | 楽天アフィリエイトID(任意・推奨) |
   | Variable | `RAKUTEN_GENRE_IDS` | 取得したいジャンルIDをカンマ区切りで(任意。省略時は総合ランキング) |
   | Variable | `RAKUTEN_KEYWORDS` | 高ポイント還元商品を探す検索語(任意。省略時は「アウトレット,セール,訳あり」) |
   | Variable | `RAKUTEN_MIN_POINT_RATE` | この倍率以上のポイント還元商品だけ拾う(任意。省略時は5) |
   | Variable | `RAKUTEN_APP_REFERRER` | 楽天アプリ登録時の「参照先URL」と完全一致させる値(任意。省略時は `https://seru-navi-deals.netlify.app/`)。公開URLを変えたらここも変更すること |

   ※ Secretは「Secrets」タブ、Variableは「Variables」タブから登録します。

3. `scripts/update_deals.py` と `.github/workflows/update-deals.yml` をリポジトリにpushする
4. **Actions** タブを開き、「Update deals.json from Rakuten API」ワークフローの
   「Run workflow」ボタンを押して手動テスト実行し、正常終了するか確認する
5. 問題なければ、以降は15分毎(毎時07分・22分・37分・52分)に自動実行されます

### 5-3. 楽天アプリのタイプについて(重要)

楽天ウェブサービスでアプリを新規登録する際、「Webアプリケーション」と「API/バックエンドサービス」の
どちらかを選ぶ必要があります。本プロジェクトは **「Webアプリケーション」タイプ** で登録しています。

- 「API/バックエンドサービス」はIPアドレスでアクセス元を制限する方式です。GitHub Actionsの実行環境は
  毎回IPアドレスが変わるため、この方式は実質使えません。
- 「Webアプリケーション」タイプは、アプリ登録時に指定した「参照先URL」(本プロジェクトでは
  `https://seru-navi-deals.netlify.app/`)と一致する `Origin` / `Referer` ヘッダーを付けてリクエストする
  ことでアクセスできます。ヘッダーが無い、または登録したURLと一致しないと `403 Forbidden` になります。
  `scripts/update_deals.py` はこのヘッダーを自動で付与するようになっているので、通常は意識する必要は
  ありませんが、公開URL(独自ドメイン化など)を変更した場合は、
  1. 楽天ウェブサービスのアプリ管理画面で「参照先URL」を新しいURLに更新し、
  2. GitHub Repository Variablesの `RAKUTEN_APP_REFERRER` も同じ値に更新する
  必要があります。片方だけ更新すると再び403エラーになるので注意してください。

### 5-4. 知っておくべき制限事項

- GitHub Actionsの無料枠のスケジュール実行は「ちょうど15分毎」を厳密には保証しません。実運用では
  数分〜数十分遅れることが珍しくなく、特に毎時0分などキリのいい時刻は混雑しやすいとGitHub公式も
  認めています。そのため本ワークフローは07分・22分・37分・52分にずらして設定しています。
  また **60日間リポジトリへのpush等が無いと自動停止**する仕様があるため、その場合はActionsタブから
  手動で1回実行すると再開します。
- 楽天のランキングはデイリー更新が基本、価格も数日単位のセール・キャンペーンが中心のため、
  15分より短い間隔にしても実際に取得できる新しい情報はあまり増えません。「秒・分単位の値下がり」を
  検知したい場合は、そもそもデータの性質上リアルタイム取得には向いていません。
- 楽天APIは商品ごとの「セール前価格」を返さないため、割引率(◯%OFF)は表示されません。代わりに
  「ポイント倍率」を目安バッジとして表示する仕様にしています。
- Amazon商品の自動取得は今回のスクリプトには含めていません。Amazon PA-API(Product Advertising API)は
  申請から**60日間は成果実績なしで利用開始**できるので、Amazonアソシエイトの審査に通ったら
  申請だけ先に済ませておくのがおすすめです。PA-API連携が必要になったら、その時点で拡張します。
- 1台のPCを常時起動しておく必要はありません(GitHubのサーバー上で実行されます)。

---

## 6. WordPressに移行したくなったら

このサイトはHTML/CSSがシンプルなので、`css/style.css` のデザインはWordPressテーマの
カスタムCSSにほぼそのまま流用できます。記事(`pages/article-*.html`)の本文もコピペで
WordPressの投稿エディタに移せます。本格的に更新頻度を上げたい・複数人で運用したい場合は
WordPress化を検討してください(その際はあらためてご相談ください)。

---

## 7. 法律・規約まわりの注意点(必ず確認)

- **ステマ規制(景品表示法)**: 企業から商品提供やタイアップを受けて紹介する場合は、記事内に
  「PR」「広告」等の表記が必須です。単なるアフィリエイトリンクの掲載でも、業界の自主基準として
  「アフィリエイト広告を利用しています」という表記をヘッダー・フッターに常時表示する構成にしてあります。
- **Amazonアソシエイト規約(2026年改定)**: 有料広告(リスティング広告等)経由の購入は成果対象外になる、
  適格販売は購入から180日以内の出荷・支払い完了が必要、などの改定が入っています。
  出稿する場合は必ず最新の[運営規約](https://affiliate.amazon.co.jp/help/operating/agreement/)を確認してください。
- **楽天アフィリエイト**: ステマ規制対応の詳細は[楽天アフィリエイトのガイドライン](https://affiliate.rakuten.co.jp/guideline/stealth_marketing_regulation/)を参照してください。
- 本テンプレートの `disclosure.html` / `privacy.html` は一般的なひな形です。実際の運営形態に合わせて
  内容を見直してください(必要であれば専門家にご確認ください)。

---

## 8. 今後の拡張アイデア(「収益ソフト」プロジェクトとして)

- Amazonアソシエイトの審査に通ったら、PA-API連携を追加してAmazon商品も自動取得する
- 楽天API取得結果に「前回価格との比較」を持たせ、実際の値下がりを検知して割引率を表示する
- メール配信(セール開始通知)やLINE通知との連携
- アクセス解析(Google Analytics)を `config.js` の `gaId` に設定して導入
- 記事数が増えてきたら検索・タグ絞り込み機能を追加
