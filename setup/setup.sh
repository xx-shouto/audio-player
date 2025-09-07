#!/bin/bash
set -e

# --- GitHubからクローン ---
REPO_URL="https://github.com/xx-shouto/audio-player/"
APP_DIR="$HOME/audio-player"

if [ ! -d "$APP_DIR" ]; then
    git clone "$REPO_URL" "$APP_DIR"
    echo "リポジトリを $APP_DIR にクローンしました"
else
    echo "既に $APP_DIR は存在します"
fi

cd "$APP_DIR"

# --- Python仮想環境作成 ---
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "仮想環境 'venv' を作成しました"
fi

source venv/bin/activate
pip install --upgrade pip

# requirements.txt がある場合
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# --- VLC/FFmpeg インストール ---
OS=$(uname)
if [ "$OS" == "Linux" ]; then
    sudo apt update
    sudo apt install -y vlc ffmpeg
elif [ "$OS" == "Darwin" ]; then
    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew が必要です: https://brew.sh/"
        exit 1
    fi
    brew install vlc ffmpeg
fi

# --- audio-player コマンド作成 ---
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

PLAYER_CMD="$BIN_DIR/audio-player"
cat > "$PLAYER_CMD" <<EOF
#!/bin/bash
source "$APP_DIR/venv/bin/activate"
python "$APP_DIR/main.py" "\$@"
EOF
chmod +x "$PLAYER_CMD"

# PATHに追加されていない場合は警告
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "注意: $BIN_DIR を PATH に追加してください"
    echo "例: export PATH=\$PATH:$BIN_DIR"
fi

echo "=== セットアップ完了 ==="
echo "ターミナルを再起動、または PATH を更新後に 'audio-player' コマンドが使用できます"

# --- Bluetooth接続確認 ---
read -p "Bluetooth接続しますか？ (y/n): " BT_CHOICE
if [[ "$BT_CHOICE" == "y" ]]; then
    echo "Bluetooth接続スクリプトを実行します..."
    sudo bash <<'BT_SCRIPT'
#!/bin/bash
# Ubuntu Server用 Bluetoothイヤホン 接続スクリプト

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

sleep 10

# デバイス一覧取得
DEVICES=$(bluetoothctl devices | awk '{print $2 " " substr($0,index($0,$3))}')
if [ -z "$DEVICES" ]; then
    echo "デバイスが見つかりませんでした。終了します。"
    exit 1
fi

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

CARD_NAME=$(pactl list cards short | grep "$DEVICE_MAC" | awk '{print $2}')
if [ -n "$CARD_NAME" ]; then
    pactl set-card-profile "$CARD_NAME" a2dp_sink
    pactl set-default-sink "$CARD_NAME"
    echo "Bluetoothイヤホンに接続完了！"
else
    echo "カード情報が取得できませんでした。接続に失敗している可能性があります。"
fi
BT_SCRIPT
fi

echo "すべて完了しました！"
