# ビルドおよび環境構築手順書（Build Instructions）

## 1. 前提条件・動作環境
- **Python バージョン**: Python 3.10 以上（推奨: Python 3.11）
- **対応OS**: Windows 10 / Windows 11（DirectX / WASAPI サポート）
- **主要依存ライブラリ**:
  - `PyQt6`（デスクトップGUIおよびQtMultimedia音声エンジン）
  - `numpy`（数値配列処理および波形ピーク計算）
  - `scipy`（音声信号処理、STFT、クロマフィルタ、Onset検出）
  - `send2trash`（Windows ごみ箱への安全なファイル移動）
  - `pytest` & `hypothesis`（自動テストおよびプロパティベーステスト）
- **必要ディスク容量**: 約250MB（仮想環境、パッケージ、ライブラリDB用）

---

## 2. 環境構築および起動手順

### ステップ 1: Python 仮想環境の作成と有効化
PowerShell または コマンドプロンプトで以下のコマンドを実行します。
```powershell
# 仮想環境 .venv を作成
python -m venv .venv

# PowerShell の場合:
.venv\Scripts\Activate.ps1

# コマンドプロンプトの場合:
.venv\Scripts\activate.bat
```

### ステップ 2: 依存パッケージのインストール
```powershell
pip install -r requirements.txt
```

### ステップ 3: アプリケーションの起動
```powershell
python src/main.py
```

### ステップ 4: スタンドアロン実行ファイル（.exe）へのビルド（オプション）
PyInstaller を使用して、Python がインストールされていない Windows PC でも動作する単一の exe ファイルを生成できます。
```powershell
# PyInstaller のインストール
pip install pyinstaller

# 単一 exe ファイルへのパッケージング
pyinstaller --noconsole --onefile --name "BandLabSoundManager" --add-data "src;src" src/main.py
```
ビルド完了後、`dist/BandLabSoundManager.exe` に実行ファイルが生成されます。

---

## 3. ビルド・起動成功の確認項目
- アプリケーションウィンドウが DAW 向けダークテーマで正常に起動すること。
- 初回起動時に、管理対象の標準フォルダ構成がカレントディレクトリ配下の `SoundLibrary/` に自動生成されること：
  - `SoundLibrary/Database/library.db`（SQLite データベース）
  - `SoundLibrary/Library/Loop/`（ループ音源格納ディレクトリ）
  - `SoundLibrary/Library/Oneshot/`（ワンショット音源格納ディレクトリ）
  - `SoundLibrary/Library/Other/`（未分類音源隔離ディレクトリ）
  - `SoundLibrary/Backups/`（データベーススナップショットバックアップ）

---

## 4. トラブルシューティング

### トラブル 1: `ImportError: DLL load failed while importing QtGui`
- **原因**: Windows 側に必要な Visual C++ 再頒布可能パッケージが不足している可能性があります。
- **対処法**: Microsoft 公式サイトより「Visual C++ 2015–2022 Redistributable (x64)」をダウンロードしてインストールしてください。

### トラブル 2: 音声再生時に音が出ない
- **原因**: Windows の既定のオーディオ出力デバイスが無効化されているか、他の DAW ソフトウェア（ASIO 排他モード等）がデバイスをロックしている可能性があります。
- **対処法**: Windows のサウンド設定で既定の出力デバイスを確認するか、排他モードを使用している DAW を一時停止してください。
