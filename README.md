# CALIDAD
1. Alta calidad de video, misma resolución y audio con la misma calidad:
- crf 18: Establece una alta calidad de video (valores más bajos indican mayor calidad).
- preset slow: Utiliza una configuración de codificación más lenta para mejorar la calidad.
- b:a 192k: Establece una tasa de bits de audio de 192 kbps.
``` bash
ffmpeg -i input.avi -c:v libx264 -crf 18 -preset slow -c:a aac -b:a 192k -strict experimental -movflags +faststart output_alta_calidad.mp4
```

2. Mediana calidad de video, menos resolución y audio con la misma calidad:
- crf 23: Establece una calidad de video intermedia.
- vf scale=640:-1: Redimensiona el video a una anchura de 640 píxeles, manteniendo la proporción original.
- b:a 192k: Establece una tasa de bits de audio de 192 kbps.
``` bash
ffmpeg -i input.avi -c:v libx264 -crf 23 -vf scale=640:-1 -c:a aac -b:a 192k -strict experimental -movflags +faststart output_mediana_calidad.mp4
```

3. Baja calidad de video, poca resolución y audio con media calidad:
- crf 28: Establece una baja calidad de video.
- vf scale=320:-1: Redimensiona el video a una anchura de 320 píxeles, manteniendo la proporción original.
- b:a 128k: Establece una tasa de bits de audio de 128 kbps.
``` bash
ffmpeg -i input.avi -c:v libx264 -crf 28 -vf scale=320:-1 -c:a aac -b:a 128k -strict experimental -movflags +faststart output_baja_calidad.mp4
```

# Tipo AUDIO
## Mono:
En este ejemplo, -ac 1 indica que deseas un canal de audio, lo que hace que el audio sea mono.
``` bash
ffmpeg -i input.avi -c:v libx264 -crf 23 -c:a aac -ac 1 -b:a 192k -strict experimental -movflags +faststart output_mono.mp4
```

## Stereo:
En este caso, -ac 2 especifica que deseas dos canales de audio, lo que hace que el audio sea stereo.
``` bash
ffmpeg -i input.avi -c:v libx264 -crf 23 -c:a aac -ac 2 -b:a 192k -strict experimental -movflags +faststart output_stereo.mp4
```


# Tipos de conversion
## Video a Video en Otro Formato:
En este ejemplo, el comando -c:v libx264 especifica que el video se codificará utilizando el códec H.264 (libx264). -c:a aac indica que el audio se codificará utilizando el códec AAC.
``` bash
ffmpeg -i input_video.avi -c:v libx264 -c:a aac -strict experimental -movflags +faststart output_video.mp4
```

## Video a Audio:
La opción -vn indica que no se debe incluir video en la salida. -acodec aac especifica que el audio se codificará utilizando el códec AAC.
``` bash
ffmpeg -i input_video.avi -vn -acodec aac -strict experimental output_audio.aac
```

## Audio a Audio en Otro Formato:
En este caso, simplemente especificas el códec de audio (-c:a aac) que deseas utilizar en el archivo de salida.
``` bash
ffmpeg -i input_audio.mp3 -c:a aac -strict experimental output_audio.aac
```


# Codecs
## Códecs de Video:
1. H.264 (libx264):
- Usos Comunes:
    Streaming en línea.
    Archivos de video de alta calidad.
    Videos para dispositivos móviles.
- Pros:
    Alta eficiencia de compresión.
    Amplia compatibilidad.
    Calidad visual aceptable.
- Contras:
    Algunas restricciones de patentes.
    No siempre proporciona la mejor calidad en comparación con códecs más recientes.
    Puede requerir más recursos de procesamiento.
- Comando FFmpeg Estándar:
``` bash
ffmpeg -i input.avi -c:v libx264 -crf 23 -c:a aac -strict experimental output.mp4
```
- Comando FFmpeg con Aceleración por Hardware (NVIDIA NVENC):
``` bash
ffmpeg -i input.avi -c:v h264_nvenc -b:v 5M -c:a aac -strict experimental output_nvenc.mp4
```

2. H.265 (libx265):
- Usos Comunes:
    Streaming de video de alta calidad.
    Archivos de video con restricciones de ancho de banda.
    Videos 4K y Ultra HD.
- Pros:
    Mayor eficiencia de compresión que H.264.
    Mejora la calidad visual a tasas de bits más bajas.
    Soporta resoluciones más altas.
- Contras:
    Mayor complejidad computacional.
    No es tan compatible como H.264.
    Puede requerir hardware más potente.
- Comando FFmpeg Estándar:
``` bash
ffmpeg -i input.avi -c:v libx265 -crf 28 -c:a aac -strict experimental output.mp4
```
- Comando FFmpeg con Aceleración por Hardware (NVIDIA NVENC):
``` bash
ffmpeg -i input.avi -c:v hevc_nvenc -b:v 3M -c:a aac -strict experimental output_nvenc.mp4
```

3. VP9 (libvpx-vp9):
- Usos Comunes:
    Transmisión de video en línea (YouTube).
    Archivos de video de alta calidad.
    Contenido web de código abierto.
- Pros:
    Eficiencia de compresión competitiva.
    Código abierto y libre de regalías.
    Soporte para videos 4K.
- Contras:
    Mayor complejidad computacional.
    No es tan compatible como H.264.
    Menos eficiente que H.265 en ciertos escenarios.
- Comando FFmpeg Estándar:
``` bash
ffmpeg -i input.avi -c:v libvpx-vp9 -b:v 1M -c:a libvorbis output.webm
```
- Comando FFmpeg con Aceleración por Hardware (No disponible para VP9):
La aceleración por hardware específica para VP9 puede variar y no siempre está disponible en todas las configuraciones.

## Códecs de Audio:
1. AAC:
- Usos Comunes:
    Streaming de audio en línea.
    Archivos de audio de alta calidad.
    Codificación de audio en video.
- Pros:
    Buena calidad de audio a tasas de bits moderadas.
    Amplia compatibilidad.
    Eficiencia de compresión.
- Contras:
    Restricciones de patentes.
    Calidad ligeramente inferior a códecs sin pérdida.
    No es adecuado para aplicaciones de alta fidelidad.
- Comando FFmpeg Estándar:
``` bash
ffmpeg -i input.wav -c:a aac -b:a 192k output.aac
```
- Comando FFmpeg con Aceleración por Hardware (No común para códecs de audio como AAC):
La aceleración por hardware específica para códecs de audio como AAC es menos común y depende del hardware y la configuración.

2. MP3 (libmp3lame):
- Usos Comunes:
    Reproducción de música en reproductores de audio.
    Streaming de audio.
    Archivos de audio con pérdida.
- Pros:
    Amplia compatibilidad.
    Tamaño de archivo relativamente pequeño.
    Eficiente en términos de compresión.
- Contras:
    Calidad de audio inferior a códecs sin pérdida.
    Menos eficiente que códecs más modernos.
    Algunas restricciones de patentes.
- Comando FFmpeg Estándar:
``` bash
ffmpeg -i input.wav -c:a libmp3lame -b:a 192k output.mp3
```
- Comando FFmpeg con Aceleración por Hardware (No común para códecs de audio como MP3):
Similar a AAC, la aceleración por hardware específica para códecs de audio como MP3 es menos común y depende del hardware y la configuración.

3. Opus:
- Usos Comunes:
    VoIP y videoconferencias.
    Transmisión de audio en tiempo real.
    Archivos de audio de alta calidad.
- Pros:
    Eficiencia de compresión y calidad de audio excelentes.
    Baja latencia.
    Código abierto y libre de regalías.
- Contras:
    Menor penetración en comparación con códecs más establecidos.
    Requiere más recursos de procesamiento para codificación.
    Puede no ser tan eficiente para música de alta fidelidad.
- Comando FFmpeg Estándar:
``` bash
ffmpeg -i input.wav -c:a libopus -b:a 96k output.opus
```
- Comando FFmpeg con Aceleración por Hardware (No común para códecs de audio como Opus):
Similar a AAC y MP3, la aceleración por hardware específica para códecs de audio como Opus es menos común y depende del hardware y la configuración.