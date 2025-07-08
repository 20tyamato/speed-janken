# 瞬間じゃんけんゲーム

OpenGLとMediaPipeを使ったリアルタイム手認識じゃんけんゲームです。

## 特徴

- 3Dグラフィックスによる美しいビジュアル
- カメラを使ったリアルタイム手認識
- パーティクルエフェクト
- スコア管理

## 必要な環境

- Python 3.9+
- Webカメラ

## インストール

```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 使い方

```bash
export PYTHONPATH=$(pwd); python src/main.py
```

## 操作方法

- **SPACE** - ゲーム開始
- **R** - リセット
- **ESC** - 終了

## ゲームの流れ

1. スペースキーでゲーム開始
2. カウントダウン（3, 2, 1）
3. コンピューターの手が表示される
4. カメラに向かって手を出す（グー✊、パー✋、チョキ✌️）
5. 結果判定とエフェクト表示

## 手の認識

- **グー（Rock）**: 握りこぶし
- **パー（Paper）**: 開いた手
- **チョキ（Scissors）**: 人差し指と中指を立てる
s
