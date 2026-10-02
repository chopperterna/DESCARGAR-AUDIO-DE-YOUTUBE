#!/usr/bin/env python3
"""Anonymous Audio: una interfaz visual y sencilla para Termux."""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import parse_qs, urlparse


APP_NAME = "ANONYMOUS AUDIO"
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "anonymous-audio"
CONFIG_FILE = CONFIG_DIR / "config.json"
SPINNERS = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
MASK = (
    "       .-=========-.       ",
    "      /   .     .   \\      ",
    "     |   (o)   (o)   |     ",
    "     |      .-.      |     ",
    "     |   .-'   '-.   |     ",
    "      \\  \\_____/  /      ",
    "       '._     _.'       ",
    "          '---'           ",
)


class Theme:
    enabled = sys.stdout.isatty() and "NO_COLOR" not in os.environ
    RESET = "\033[0m" if enabled else ""
    BOLD = "\033[1m" if enabled else ""
    DIM = "\033[2m" if enabled else ""
    CYAN = "\033[96m" if enabled else ""
    GREEN = "\033[92m" if enabled else ""
    PURPLE = "\033[95m" if enabled else ""
    YELLOW = "\033[93m" if enabled else ""
    RED = "\033[91m" if enabled else ""
    WHITE = "\033[97m" if enabled else ""
    BLUE = "\033[94m" if enabled else ""


def paint(text: str, color: str) -> str:
    return f"{color}{text}{Theme.RESET}"


def terminal_size() -> tuple[int, int]:
    size = shutil.get_terminal_size((72, 24))
    return max(38, min(76, size.columns - 2)), size.lines


def wipe() -> None:
    if Theme.enabled:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
    else:
        print("\n" * 2)


def center(text: str, width: int) -> str:
    return text.center(width)


def clipped(text: str, width: int) -> str:
    safe = " ".join(str(text).replace("\r", " ").replace("\n", " ").split())
    safe = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", safe)
    if len(safe) > width:
        return safe[: max(0, width - 1)] + "…"
    return safe


def box_line(text: str, width: int, color: str = Theme.CYAN) -> str:
    inner = width - 4
    content = clipped(text, inner)
    return paint("│ ", color) + content + " " * (inner - len(content)) + paint(" │", color)


def box_top(title: str, width: int) -> str:
    title = f" {title} "
    dashes = max(0, width - len(title) - 2)
    return paint("╭─" + title + "─" * dashes + "╮", Theme.CYAN)


def box_bottom(width: int) -> str:
    return paint("╰" + "─" * (width - 2) + "╯", Theme.CYAN)


def intro() -> None:
    width, _ = terminal_size()
    wipe()
    print("\n")
    for line in MASK:
        print(paint(center(line, width), Theme.CYAN + Theme.BOLD))
        time.sleep(0.045)
    print("\n" + paint(center("A N O N Y M O U S  //  A U D I O", width), Theme.WHITE + Theme.BOLD))
    print(paint(center("DESARROLLADO POR CHOPPER_TERNA", width), Theme.DIM))
    print(paint(center("TERMINAL DE DESCARGA · TERMUX", width), Theme.DIM))
    print("\n" + paint(center("[ INICIANDO SISTEMA ]", width), Theme.GREEN))
    for label in ("CARGANDO INTERFAZ", "PREPARANDO MOTOR DE AUDIO", "SISTEMA LISTO"):
        print(paint("  " + label, Theme.DIM if label != "SISTEMA LISTO" else Theme.GREEN))
        time.sleep(0.16)
    time.sleep(0.35)


def default_destination() -> Path:
    android_music = Path.home() / "storage" / "music"
    if android_music.is_dir():
        return android_music / "Anonymous Audio"
    return Path.home() / "Music" / "Anonymous Audio"


def load_destination() -> Path:
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        value = data.get("destination") if isinstance(data, dict) else None
        if isinstance(value, str) and value.strip():
            return Path(value).expanduser()
    except (OSError, ValueError, TypeError):
        pass
    return default_destination()


def save_destination(path: Path) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps({"destination": str(path)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def draw_dashboard(destination: Path, notice: str = "") -> None:
    width, _ = terminal_size()
    inner = width - 4
    wipe()
    print("\n" + box_top("ANONYMOUS AUDIO  /  TERMUX", width))
    print(box_line("MÚSICA DE YOUTUBE · MP3 · CALIDAD 192 KBPS", width, Theme.WHITE))
    print(box_line("", width))
    print(box_line("DESTINO", width, Theme.DIM))
    print(box_line(str(destination), width, Theme.CYAN))
    print(box_line("", width))
    print(box_line(paint("1", Theme.GREEN + Theme.BOLD) + "  Descargar una canción", width))
    print(box_line(paint("2", Theme.GREEN + Theme.BOLD) + "  Elegir carpeta de destino", width))
    print(box_line(paint("3", Theme.GREEN + Theme.BOLD) + "  Abrir carpeta de música", width))
    print(box_line(paint("4", Theme.GREEN + Theme.BOLD) + "  Ayuda y uso", width))
    print(box_line(paint("0", Theme.YELLOW + Theme.BOLD) + "  Salir", width))
    if notice:
        print(box_line("", width))
        print(box_line(notice, width, Theme.GREEN))
    print(box_bottom(width))
    print("\n" + paint(center("Pega el enlace y deja que el sistema haga el resto.", inner), Theme.DIM))
    print(paint(center("BY CHOPPER_TERNA", inner), Theme.DIM))


def valid_youtube_url(raw: str) -> tuple[bool, str]:
    value = raw.strip()
    if not value:
        return False, "No recibí ningún enlace."
    if "://" not in value:
        value = "https://" + value
    try:
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower().rstrip(".")
    except ValueError:
        return False, "El enlace no tiene un formato válido."
    allowed_hosts = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be", "www.youtu.be"}
    if host not in allowed_hosts:
        return False, "Usa un enlace de YouTube o YouTube Music."
    if host.endswith("youtu.be"):
        has_video = bool(parsed.path.strip("/"))
    elif parsed.path == "/watch":
        has_video = bool(parse_qs(parsed.query).get("v"))
    else:
        has_video = bool(re.match(r"^/(shorts|live|embed)/[^/]+", parsed.path))
    if not has_video:
        return False, "Pega el enlace de una canción o video individual."
    return True, value


def progress_bar(percent: float | None, width: int, tick: int) -> str:
    width = max(10, width)
    if percent is None:
        position = tick % width
        fill = "░" * position + "█" + "░" * (width - position - 1)
        return paint(fill, Theme.PURPLE)
    filled = int(width * max(0, min(100, percent)) / 100)
    return paint("█" * filled, Theme.GREEN) + paint("░" * (width - filled), Theme.DIM)


def human_size(value: float | int | None) -> str:
    if not value:
        return "—"
    amount = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if amount < 1024 or unit == "GB":
            return f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{amount:.1f} GB"


def render_download(state: dict, destination: Path, tick: int) -> None:
    width, _ = terminal_size()
    inner = width - 4
    wipe()
    print("\n" + box_top("ANONYMOUS AUDIO  /  DESCARGA", width))
    print(box_line("", width))
    print(box_line(center(SPINNERS[tick % len(SPINNERS)] + "  CONEXIÓN ACTIVA  " + SPINNERS[(tick + 3) % len(SPINNERS)], inner), width, Theme.GREEN))
    print(box_line("", width))
    phase = state.get("phase", "connect")
    labels = {
        "connect": "Conectando con YouTube",
        "downloading": "Descargando audio",
        "processing": "Convirtiendo a MP3",
        "finished": "Finalizando archivo",
    }
    status = labels.get(phase, "Procesando descarga")
    print(box_line(paint(status.upper(), Theme.WHITE + Theme.BOLD), width))
    print(box_line("", width))
    pct = state.get("percent") if phase == "downloading" else None
    bar_width = max(10, min(34, inner - 4))
    bar = progress_bar(pct, bar_width, tick)
    if pct is None:
        progress = f"{bar}  {paint(SPINNERS[tick % len(SPINNERS)], Theme.PURPLE)}"
    else:
        progress = f"{bar}  {pct:5.1f}%"
    print(box_line(progress, width))
    print(box_line("", width))
    detail = f"{human_size(state.get('downloaded'))} / {human_size(state.get('total'))}"
    speed = human_size(state.get("speed")) + "/s" if state.get("speed") else ""
    eta = f"ETA {int(state['eta'])}s" if state.get("eta") is not None and phase == "downloading" else ""
    print(box_line("   ·   ".join(part for part in (detail, speed, eta) if part), width, Theme.DIM))
    print(box_line("", width))
    print(box_line("GUARDANDO EN", width, Theme.DIM))
    print(box_line(str(destination), width, Theme.CYAN))
    print(box_bottom(width))


def download_worker(url: str, destination: Path, events: queue.Queue) -> dict:
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("Falta yt-dlp. Ejecuta bash install.sh dentro de Termux.") from exc

    def on_progress(data: dict) -> None:
        status = data.get("status")
        if status == "downloading":
            downloaded = data.get("downloaded_bytes")
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            percent = (100 * downloaded / total) if downloaded is not None and total else None
            events.put({
                "phase": "downloading",
                "percent": percent,
                "downloaded": downloaded,
                "total": total,
                "speed": data.get("speed"),
                "eta": data.get("eta"),
            })
        elif status == "finished":
            events.put({"phase": "processing", "percent": 100.0})

    def on_postprocess(data: dict) -> None:
        if data.get("status") == "started":
            events.put({"phase": "processing", "percent": 100.0})
        elif data.get("status") == "finished":
            events.put({"phase": "finished", "percent": 100.0})

    destination.mkdir(parents=True, exist_ok=True)
    options = {
        "format": "bestaudio/best",
        "outtmpl": str(destination / "%(title).150B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [on_progress],
        "postprocessor_hooks": [on_postprocess],
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
            {"key": "FFmpegMetadata"},
        ],
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
    if not info:
        raise RuntimeError("YouTube no devolvió información de esta canción.")
    return info


def ask_enter() -> None:
    try:
        input("\nPulsa Enter para volver al menú…")
    except (EOFError, KeyboardInterrupt):
        pass


def download_flow(destination: Path) -> None:
    width, _ = terminal_size()
    wipe()
    print("\n" + paint(center("NUEVA DESCARGA", width), Theme.CYAN + Theme.BOLD))
    print("\nPega el enlace de una canción o video individual de YouTube.")
    print(paint("Consejo: mantén pulsado el terminal para pegar desde Android.", Theme.DIM))
    try:
        raw = input("\nEnlace › ")
    except (EOFError, KeyboardInterrupt):
        return
    ok, result = valid_youtube_url(raw)
    if not ok:
        print(paint("\n✕ " + result, Theme.RED))
        ask_enter()
        return

    events: queue.Queue = queue.Queue()
    state: dict = {"phase": "connect"}
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(download_worker, result, destination, events)
            tick = 0
            while not future.done():
                while True:
                    try:
                        state.update(events.get_nowait())
                    except queue.Empty:
                        break
                render_download(state, destination, tick)
                tick += 1
                time.sleep(0.12)
            while True:
                try:
                    state.update(events.get_nowait())
                except queue.Empty:
                    break
            info = future.result()
    except Exception as exc:  # yt-dlp reports network and media errors as exceptions.
        message = clipped(str(exc), max(30, width - 8))
        wipe()
        print("\n" + paint(center("DESCARGA NO COMPLETADA", width), Theme.RED + Theme.BOLD))
        print("\n" + message)
        print(paint("\nRevisa el enlace, tu conexión y vuelve a intentarlo.", Theme.DIM))
        ask_enter()
        return

    state["phase"] = "finished"
    state["percent"] = 100.0
    render_download(state, destination, 0)
    title = clipped(info.get("title") or "Canción descargada", max(20, width - 10))
    print("\n" + paint(center("✓ DESCARGA COMPLETADA", width), Theme.GREEN + Theme.BOLD))
    print(paint(center(title, width), Theme.WHITE))
    print(paint(center("Archivo MP3 listo en la carpeta indicada.", width), Theme.DIM))
    ask_enter()


def choose_destination(current: Path) -> Path:
    wipe()
    print("\n" + paint("CARPETA DE DESCARGA", Theme.CYAN + Theme.BOLD))
    print("\nActual: " + str(current))
    print("\nEscribe una ruta completa. Puedes usar ~/ para tu carpeta personal.")
    print("Pulsa Enter para conservar el destino actual.")
    try:
        raw = input("\nNueva ruta › ").strip()
    except (EOFError, KeyboardInterrupt):
        return current
    if not raw:
        return current
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    try:
        path.mkdir(parents=True, exist_ok=True)
        save_destination(path)
    except OSError as exc:
        print(paint(f"\nNo pude usar esa carpeta: {clipped(exc, 90)}", Theme.RED))
        ask_enter()
        return current
    print(paint("\n✓ Carpeta guardada.", Theme.GREEN))
    time.sleep(0.5)
    return path


def open_destination(destination: Path) -> None:
    try:
        destination.mkdir(parents=True, exist_ok=True)
        opener = shutil.which("termux-open")
        if opener:
            subprocess.Popen([opener, str(destination)])
        else:
            print("\nCarpeta: " + str(destination))
            ask_enter()
    except OSError as exc:
        print(paint(f"\nNo pude abrir la carpeta: {clipped(exc, 90)}", Theme.RED))
        ask_enter()


def show_help() -> None:
    wipe()
    width, _ = terminal_size()
    print("\n" + box_top("AYUDA RÁPIDA", width))
    for line in (
        "1. Elige Descargar una canción.",
        "2. Pega un enlace individual de YouTube.",
        "3. Espera la conversión; se guarda como MP3.",
        "",
        "La primera instalación solicita permiso de archivos",
        "para guardar en Música del almacenamiento Android.",
        "Puedes cambiar la carpeta desde el menú principal.",
        "",
        "Descarga solo contenido que tengas derecho a guardar",
        "y respeta las condiciones de la plataforma.",
    ):
        print(box_line(line, width, Theme.WHITE if line else Theme.CYAN))
    print(box_bottom(width))
    ask_enter()


def main() -> int:
    intro()
    destination = load_destination()
    notice = ""
    while True:
        draw_dashboard(destination, notice)
        notice = ""
        try:
            choice = input("\n  Selecciona una opción › ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nHasta pronto.")
            return 0
        if choice == "1":
            download_flow(destination)
        elif choice == "2":
            destination = choose_destination(destination)
            notice = "Carpeta de destino actualizada."
        elif choice == "3":
            open_destination(destination)
        elif choice == "4":
            show_help()
        elif choice == "0":
            print("\n" + paint("Conexión cerrada. Hasta pronto.", Theme.CYAN))
            return 0
        else:
            notice = "Opción no reconocida. Elige un número del menú."


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n\n" + paint("Operación cancelada.", Theme.YELLOW))
        raise SystemExit(130)
