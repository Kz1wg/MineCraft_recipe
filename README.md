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

## GitHub Pagesで公開する

1. GitHubで新しい **Public repository** を作成（例：`minecraft-recipe`）。
2. このZIPの中身を、フォルダごとではなくリポジトリ直下にアップロードする。
   - `index.html`
   - `manifest.webmanifest`\n- `sw.js`
   - `scripts/build_data.py`
   - `.github/workflows/build.yml`
   - `data/` フォルダ
3. リポジトリの **Settings → Pages → Build and deployment** で、Sourceを **GitHub Actions** にする。
4. **Actions** タブを開き、`Build recipe database` が完了するまで待つ。
5. 公開URLは `https://あなたのGitHubユーザー名.github.io/minecraft-recipe/` の形式。

初回はActionsがレシピデータを生成してから公開します。`data/recipes.json` が生成される前は「レシピデータ未生成」と表示されます。

## iPhoneのホーム画面に追加

1. iPhoneのSafariで公開URLを開く。初回表示後は、読み込んだレシピデータをキャッシュしてオフラインでも参照できるようにします。
2. 共有ボタンをタップ。
3. **ホーム画面に追加** を選択。
4. 追加したアイコンから図鑑を起動。

## 更新

GitHub Actionsは毎週月曜日に公式サンプルデータを取得し直します。手動更新したい場合は、Actions → Build recipe database → Run workflow を実行してください。

## データ出典

- Mojang Bedrock Samples: https://github.com/Mojang/bedrock-samples
- Microsoft Learn: https://learn.microsoft.com/minecraft/creator/documents/moreinfosources

MinecraftはMojang Studios / Microsoftの商標です。本ツールは非公式です。
