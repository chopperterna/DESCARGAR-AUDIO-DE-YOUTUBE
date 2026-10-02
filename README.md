# Anonymous Audio · Termux

Una aplicación de terminal visual para descargar audio individual de YouTube como MP3 desde Android con Termux. Tiene una pantalla de inicio animada, un menú guiado en español, indicador de progreso, selector de carpeta y conversión automática a 192 kbps.

**Desarrollador:** `chopper_terna`

## Instalación rápida

Instala [Termux](https://termux.dev/) y ejecuta estos comandos:

```bash
pkg install -y git
git clone https://github.com/chopperterna/anonymous-audio-termux.git
cd anonymous-audio-termux
bash install.sh
```

El instalador instala Python, FFmpeg y yt-dlp. Android puede pedir permiso para escribir en el almacenamiento compartido. Acepta el permiso para que las descargas aparezcan en la carpeta Música.

## Uso

Después de la instalación, inicia la aplicación cuando quieras con:

```bash
cd ~/anonymous-audio-termux
bash start.sh
```

Elige **Descargar una canción**, pega un enlace individual de YouTube o YouTube Music y espera a que termine la conversión. Por defecto, el audio se guarda en `~/storage/music/Anonymous Audio`. El menú permite cambiar esa carpeta y abrirla desde Android.

Para pegar un enlace en Termux, mantén pulsado dentro de la terminal y toca **Pegar**.

## Características

- Interfaz visual en español, con portada animada y máscara ASCII.
- Progreso de descarga con velocidad y tiempo estimado cuando YouTube los proporciona.
- Conversión automática a MP3 de 192 kbps y guardado de metadatos.
- Descargas individuales para evitar bajar listas completas por accidente.
- Configuración persistente de la carpeta de destino.
- Requiere Python, FFmpeg y yt-dlp; no usa servicios web intermediarios.

## Actualizar dependencias

```bash
pkg upgrade python ffmpeg yt-dlp
```

## Uso responsable

Descarga únicamente audio que tengas derecho a guardar. Respeta las condiciones de YouTube y los derechos de autor aplicables en tu país.

## Licencia

Este proyecto se distribuye bajo la licencia MIT. yt-dlp, FFmpeg y Termux son proyectos independientes con sus propias licencias.
