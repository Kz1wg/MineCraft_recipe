# マイクラ レシピ図鑑（Bedrock / iOS）

iPhoneのSafariで使うことを想定した、Minecraft Bedrock Edition向けレシピ検索Webアプリです。

## 収録データについて

このプロジェクトは、Mojangが公開している `Mojang/bedrock-samples` の `behavior_pack/recipes` をGitHub Actionsで取得し、`data/recipes.json` を生成します。レシピデータは週1回、自動的に再生成されます。

- 作業台の配置レシピ
- 不定形レシピ
- かまど・溶鉱炉・燻製器・焚き火などの加工レシピ
- 醸造レシピ
- 鍛冶台レシピ
- 石切台など、公式データに含まれる専用作業場所のレシピ

**注意：** これは「クラフト・加工レシピの図鑑」です。ゲーム内の全アイテム一覧ではありません。クラフトできず、ドロップ・取引・探索などでのみ入手するアイテムはレシピとしては載りません。アドオン独自レシピも含みません。公式サンプルのデータ構造や翻訳キーの変更により、変換スクリプトの調整が必要になる場合があります。

## 使い方

- **検索バーは常に画面上部に固定**されています。どれだけスクロールしていても、すぐ再検索できます。
- ひらがな・カタカナ・全角半角の違いは無視して検索します（例：「だいや」→「ダイヤモンド…」）。英語ID（`pickaxe` など）や、スペース区切りの複数キーワード（AND検索）も使えます。
- 検索結果は「**そのアイテムを作るレシピ**」を先に、「**材料などに使うレシピ**」を後にまとめて表示します。
- レシピをタップすると**下からシートが開きます**（ページはスクロールしません）。シートは ✕・背景タップ・下スワイプ・iPhoneの戻る操作で閉じられます。
- シート内の材料の「レシピ ›」をタップすると、その材料のレシピへ移動できます（「‹ 戻る」で元のレシピへ）。
- 検索語・カテゴリ・作業場所はURLの `#` 以降に保存され、再読み込みしても復元されます。

## 日本語名の仕組み

日本語名は次の順で解決します（`scripts/build_data.py`）。

1. `scripts/ja_overrides.json`（手動の上書き）
2. `resource_pack/texts/ja_JP.lang`
3. `scripts/ja_names.py`（旧形式の `data` 値つきID、ポーション、タグ、色・木材・道具の組み立てルール）
4. 上記すべてで見つからない場合のみ英語のまま表示

英語のまま表示されたIDは、ビルドのたびに `data/untranslated.txt`（公開URLの `/data/untranslated.txt`）と Actions のログに一覧が出力されます。`scripts/ja_overrides.json` に次のように書き足すと、次回ビルドから日本語になります。

```json
{
  "diamond_sword": "ダイヤモンドの剣",
  "#planks": "板材（各種）"
}
```

## iPhoneのホーム画面に追加
URL: https://kz1wg.github.io/MineCraft_recipe/
1. iPhoneのSafariで公開URLを開く。初回表示後は、読み込んだレシピデータをキャッシュしてオフラインでも参照できるようにします。
2. 共有ボタンをタップ。
3. **ホーム画面に追加** を選択。
4. 追加したアイコンから図鑑を起動。

アプリ（HTML）の更新は、通信できるときは常に最新版を取得し、オフラインのときだけキャッシュを使います。新しい版が見つかると一度だけ自動で再読み込みします。

## 更新

GitHub Actionsは毎週月曜日に公式サンプルデータを取得し直します。手動更新したい場合は、Actions → Build recipe database → Run workflow を実行してください。

## 開発メモ

- ローカル確認：`python -m http.server` で配信し、`data/recipes.json` を用意して開く（`BEDROCK_SOURCE=/path/to/bedrock-samples python scripts/build_data.py` でも生成可）。
- `scripts/ja_names.py` は辞書・ルール、`scripts/build_data.py` はレシピ解析、`index.html` は画面、`sw.js` はキャッシュ制御です。

## データ出典

- Mojang Bedrock Samples: https://github.com/Mojang/bedrock-samples
- Microsoft Learn: https://learn.microsoft.com/minecraft/creator/documents/moreinfosources

MinecraftはMojang Studios / Microsoftの商標です。本ツールは非公式です。
