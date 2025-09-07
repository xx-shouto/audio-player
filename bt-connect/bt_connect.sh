#!/bin/bash
# Ubuntu Server用 Bluetoothイヤホン 接続スクリプト（パッケージ自動インストール・インタラクティブ接続付き）

if [ "$EUID" -ne 0 ]; then
  echo "このスクリプトはsudoで実行してください"
  exit 1
fi

# パッケージインストール
echo "必要なパッケージをインストール中..."
apt update
apt install -y bluetooth bluez bluez-tools pulseaudio pulseaudio-module-bluetooth fzf

# Bluetoothサービス起動
echo "Bluetoothサービスを起動..."
systemctl enable bluetooth
systemctl start bluetooth

# デバイススキャン
echo "Bluetoothデバイスをスキャンしています... (10秒)"
bluetoothctl <<EOF
power on
agent on
default-agent
scan on
EOF

sleep 10  # デバイス検出のため少し待機

# スキャンしたデバイス一覧取得
DEVICES=$(bluetoothctl devices | awk '{print $2 " " substr($0,index($0,$3))}')

if [ -z "$DEVICES" ]; then
  echo "デバイスが見つかりませんでした。終了します。"
  exit 1
fi

# fzfで選択
echo "接続したいデバイスを選択してください:"
SELECTED=$(echo "$DEVICES" | fzf --prompt="> " --height 10 --border)

if [ -z "$SELECTED" ]; then
  echo "デバイスが選択されませんでした。終了します。"
  exit 1
fi

DEVICE_MAC=$(echo "$SELECTED" | awk '{print $1}')
echo "選択したデバイス: $SELECTED"

read -p "このデバイスに接続しますか？ (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" ]]; then
  echo "接続を中止しました。"
  exit 0
fi

# ペアリング・接続
echo "ペアリング・接続中..."
bluetoothctl <<EOF
pair $DEVICE_MAC
trust $DEVICE_MAC
connect $DEVICE_MAC
exit
EOF

# PulseAudio再起動
echo "PulseAudioを再起動中..."
pulseaudio -k
pulseaudio --start

# A2DP設定
CARD_NAME=$(pactl list cards short | grep "$DEVICE_MAC" | awk '{print $2}')
if [ -n "$CARD_NAME" ]; then
  pactl set-card-profile "$CARD_NAME" a2dp_sink
  pactl set-default-sink "$CARD_NAME"
  echo "Bluetoothイヤホンに接続完了！"
else
  echo "カード情報が取得できませんでした。接続に失敗している可能性があります。"
fi
