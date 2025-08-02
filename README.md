# Skill-Zero Analyzer

スキルゼロでも OK！オフ会参加者の分析を行う 2 段階システムです。

## 概要

このシステムは、オフ会参加者のデータを処理し、AI 分析を行うための 2 段階アプローチを採用しています：

1. **データ処理段階**: スプレッドシートデータとリベシティのプロフィール URL から自動的にプロフィール情報を収集・統合
2. **AI 分析段階**: 統合されたデータを基に AI 分析を実行

## システム構成

```
skill-zero/
├── data_processor.py          # データ処理スクリプト（URLからプロフィール自動収集）
├── ai_analyzer.py            # AI分析スクリプト
├── config.py                 # 設定管理クラス
├── utils.py                  # 共通ユーティリティクラス
├── test_utils.py             # ユーティリティテスト
├── data/
│   └── prompts.md            # AI分析用プロンプトテンプレート
├── output/                   # 出力ファイル
├── spreadsheet_data - form_answer.csv      # スプレッドシートデータ（プロフィールURL含む）
├── requirements.txt          # Python依存関係
└── Dockerfile               # Docker設定
```

## リファクタリング内容

### 改善点

1. **設定の集中管理**

   - `config.py`で全ての設定を一元管理
   - 環境変数による認証情報の管理

2. **共通ユーティリティの分離**

   - `utils.py`で共通機能を集約
   - ログ管理、ファイル操作、HTTP 操作、データ処理、バリデーション

3. **エラーハンドリングの強化**

   - より詳細なエラーメッセージ
   - 安全なファイル操作
   - リトライ機能付き HTTP リクエスト

4. **コードの重複削除**

   - 共通処理の統一
   - 型ヒントの追加
   - より明確なクラス設計

5. **テスト可能性の向上**
   - ユニットテストの追加
   - モック可能な設計

## 前提条件

- Docker がインストールされていること
- プロジェクトディレクトリに以下のファイルが存在すること：
  - `spreadsheet_data - form_answer.csv`（リベシティのプロフィール URL を含む）
  - `data/prompts.md`
- インターネット接続（プロフィール情報の自動収集のため）

## 使用方法

### 1. Docker イメージのビルド

```bash
docker build -t skill-zero-analyzer .
```

### 2. データ処理の実行

スプレッドシートデータとリベシティのプロフィール URL から自動的にプロフィール情報を収集・統合します：

```bash
docker run --rm -v ${PWD}:/app skill-zero-analyzer python data_processor.py
```

**実行結果**:

- `output/processed_data.json` が生成されます
- 分析対象の参加者データが統合されます
- リベシティのプロフィールページから自動的に情報を収集します

### 3. AI 分析の準備

統合されたデータから分析用プロンプトを生成します：

```bash
docker run --rm -v ${PWD}:/app skill-zero-analyzer python ai_analyzer.py
```

**実行結果**:

- `output/{参加者名}_analysis_prompt.txt` ファイルが生成されます
- 各参加者ごとに個別の分析プロンプトが作成されます

### 4. AI 分析の実行

生成されたプロンプトファイルを使用して Cursor の AI で分析を実行します：

1. `output/` フォルダ内の `{参加者名}_analysis_prompt.txt` ファイルを開く
2. ファイル内容を Cursor の AI に投げる
3. AI 分析結果を `{参加者名}さんのAI分析.md` として保存

## ファイル説明

### 入力ファイル

- **`spreadsheet_data - form_answer.csv`**: フォーム回答データ（リベシティのプロフィール URL を含む）
- **`data/prompts.md`**: AI 分析用のプロンプトテンプレート

### 出力ファイル

- **`output/processed_data.json`**: 統合された参加者データ
- **`output/{参加者名}_analysis_prompt.txt`**: 各参加者の分析用プロンプト
- **`output/{参加者名}さんのAI分析.md`**: AI 分析結果（手動で保存）

## 分析内容

AI 分析では以下の観点から参加者を分析します：

### プロフィール分析

- **実績・経験の分析**: やってきたこと、人から頼まれやすいこと
- **能力・特性の分析**: 得意なこと、好きなこと、苦手じゃないこと
- **改善・成長領域**: 苦手そうなこと

### オフ会情報に基づくキャリア提案

- **副業・スキル活用の可能性**: 具体的な副業提案、スキル開発ロードマップ
- **オフ会参加の戦略的価値**: マッチングポイント、参加メリット
- **リスク管理・注意点**: 気をつけるべき点、無理のない始め方

## トラブルシューティング

### よくある問題

1. **Docker イメージのビルドエラー**

   ```bash
   # キャッシュをクリアして再ビルド
   docker build --no-cache -t skill-zero-analyzer .
   ```

2. **ファイルが見つからないエラー**

   - 必要な入力ファイルが存在することを確認
   - ファイルパスが正しいことを確認

3. **権限エラー**
   ```bash
   # ファイルの権限を確認
   ls -la
   ```

### ログの確認

```bash
# コンテナのログを確認
docker logs <container_id>
```

## 開発者向け情報

### 依存関係

- Python 3.8+
- pandas
- requests
- beautifulsoup4
- python-dotenv

### 開発環境のセットアップ

```bash
# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
```

### テスト実行

```bash
# ユーティリティテスト
python -m unittest test_utils.py -v

# データ処理のテスト
python data_processor.py

# AI分析のテスト
python ai_analyzer.py
```

### 設定のカスタマイズ

`config.py`で以下の設定を変更できます：

- ログレベル
- ファイルパス
- HTTP タイムアウト
- リトライ回数
- プロフィール抽出設定

## ライセンス

このプロジェクトは内部使用を目的としています。

## 更新履歴

- v2.1: リファクタリング完了（設定集中管理、共通ユーティリティ分離、エラーハンドリング強化）
- v2.0: 2 段階システムに変更（データ処理 + AI 分析）
- v1.0: 統合システム（非推奨）

---

**注意**: このシステムは個人情報を含むため、適切なセキュリティ対策を講じてください。

仕様変更に基づいて、Python スクリプトを 2 段階に分けて作り直しました。

## ① データ作成スクリプトの作成

## ②AI 分析スクリプトの作成

Read file: data/prompts.md

## 使用方法の説明

新しい 2 段階システムが完成しました：

### ① データ処理スクリプト（data_processor.py）

```bash
# Dockerコンテナで実行
docker run --rm -v ${PWD}:/app skill-zero-analyzer python data_processor.py
```

**機能**:

- `spreadsheet_data - form_answer.csv`からデータを読み取り
- リベシティのプロフィール URL から自動的にプロフィール情報を収集
- フォームデータとプロフィールデータを統合
- `output/processed_data.json`として保存

### ②AI 分析スクリプト（ai_analyzer.py）

```bash
# Dockerコンテナで実行
docker run --rm -v ${PWD}:/app skill-zero-analyzer python ai_analyzer.py
```

**機能**:

- `processed_data.json`からデータを読み取り
- `prompts.md`のプロンプトを使用
- 各参加者の分析用プロンプトを`output/`フォルダに生成
- 生成されたプロンプトを Cursor の AI に投げて分析実行

### 実行手順

1. **データ処理**:

   ```bash
   docker run --rm -v ${PWD}:/app skill-zero-analyzer python data_processor.py
   ```

2. **AI 分析準備**:

   ```bash
   docker run --rm -v ${PWD}:/app skill-zero-analyzer python ai_analyzer.py
   ```

3. **Cursor で AI 分析**:
   - `output/`フォルダに生成された`{名前}_analysis_prompt.txt`ファイルを開く
   - ファイル内容を Cursor の AI に投げる
   - AI 分析結果を`{名前}さんのAI分析.md`として保存

これで、データ処理と AI 分析が分離され、より柔軟で管理しやすいシステムになりました！
