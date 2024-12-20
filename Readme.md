# LoLCustomToolの使い方

このツールは、League of Legendsのカスタムゲームにおいて、プレイヤーのランク情報を考慮したチーム分けを自動的に行うツールです。

## 機能

+ プレイヤー名とランクの入力によるチーム分け
+ League of Legendsクライアントのロビーからプレイヤー情報を読み込み、チーム分け
+ チーム分け結果のコピー
+ 過去の試合結果の表示

## Windows用チーム分けツール

1. アプリケーションをダウンロードする
    [リリースページ](https://github.com/yamadalter/LOLCustomTool/releases/tag/v0.9.1)にアクセスし、lolteamsplit.zipという名前のアプリケーションの最新バージョンをダウンロードします.
2. 解凍してmain.exeを実行することで動作します
下記必要環境はwindowsツールを動かすうえでは必要ありません。

## リポジトリ必要環境

+ Python 3.7以上
+ PyQt6
+ requests
+ cassiopeia
+ lcu-driver
+ roleidentification

## インストール

1. 上記の必要環境をインストールします。
2. このリポジトリをクローンします。
3. pip install -r requirements.txt を実行して必要なライブラリをインストールします。

## 実行方法

1. python main.py を実行します。
2. メインウィンドウが表示されます。

## 使用例

### ロビーからのプレイヤー情報の読み込み

1. League of Legendsクライアントを起動し、カスタムゲームのロビーに入ります。
2. ツールの「ロビーから追加」ボタンをクリックします。
3. ロビー内のプレイヤー情報が自動的に読み込まれ、チーム分けに反映されます。

### チーム分け結果のコピー

1. 「結果コピー」ボタンをクリックすると、チーム分け結果がクリップボードにコピーされます。
2. コピーした結果は、チャットなどに貼り付けることができます。

### その他

+ プレイヤー情報は、JSONファイルとして保存・読み込みすることができます。
+ 許容ランク誤差を設定することで、チーム間のランク差を調整することができます。

## 注意

+ このツールは、League of LegendsのAPIを利用しています。APIの仕様変更などにより、ツールが正常に動作しなくなる可能性があります。
+ このツールは、非公式なツールです。利用によって発生したいかなる損害についても、作者は責任を負いません。