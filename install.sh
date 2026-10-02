#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

if ! command -v pkg >/dev/null 2>&1; then
  printf '\nEste instalador debe ejecutarse dentro de Termux en Android.\n' >&2
  exit 1
fi

PROJECT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
printf '\n  ANONYMOUS AUDIO · INSTALADOR TERMUX\n'
printf '  Instalando Python, FFmpeg y yt-dlp…\n\n'
pkg install -y python ffmpeg yt-dlp

if command -v termux-setup-storage >/dev/null 2>&1; then
  printf '\nAndroid puede solicitar permiso para guardar música en el almacenamiento compartido.\n'
  termux-setup-storage
fi

if [ -d "$HOME/storage/music" ]; then
  mkdir -p "$HOME/storage/music/Anonymous Audio"
fi

printf '\n  Instalación lista. Abriendo la aplicación…\n\n'
exec python "$PROJECT_DIR/app.py"
