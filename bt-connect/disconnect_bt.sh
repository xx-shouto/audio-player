#!/bin/bash
# Ubuntu Server用 Bluetoothイヤホン 接続解除スクリプト

if [ "$EUID" -ne 0 ]; then
  echo "このスクリプトはsudoで実行してください"
  exit 1
fi

# Bluetoothサービス確認
systemctl enable bluetooth
systemctl start bluetooth

# 接続中のデバイス一覧を取得
DEVICES=$(bluetoothctl devices Connected | awk '{print $2 " " substr($0,index($0,$3))}')

if [ -z "$DEVICES" ]; then
  echo "現在接続中のBluetoothデバイスはありません。"
  exit 0
fi

# fzfで選択
echo "切断したいデバイスを選択してください:"
SELECTED=$(echo "$DEVICES" | fzf --prompt="> " --height 10 --border)

if [ -z "$SELECTED" ]; then
  echo "デバイスが選択されませんでした。終了します。"
  exit 1
fi

DEVICE_MAC=$(echo "$SELECTED" | awk '{print $1}')
echo "選択したデバイス: $SELECTED"

read -p "このデバイスを切断しますか？ (y/n): " CONFIRM
if [[ "$CONFIRM" != "y" ]]; then
  echo "切断を中止しました。"
  exit 0
fi

# デバイス切断
echo "切断中..."
bluetoothctl <<EOF
disconnect $DEVICE_MAC
exit
EOF

# PulseAudio再起動
echo "PulseAudioを再起動中..."
pulseaudio -k
pulseaudio --start

echo "Bluetoothデバイス $DEVICE_MAC を切断しました。"
