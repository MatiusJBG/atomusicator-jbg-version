# Separador Vocal

Aplicación de escritorio local para importar audio y estimar pistas de voz principal, coros/residuo vocal y acompañamiento.

## Desarrollo en Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m vocal_splitter
```

La aplicación abre y permite importar audio con la instalación base. Para habilitar la separación CPU, instala el extra opcional:

```powershell
python -m pip install -e ".[separation-cpu]"
```

La separación también requiere FFmpeg instalado en el equipo y `ffmpeg.exe` disponible en `PATH`. Consulta [las opciones de descarga de FFmpeg](https://ffmpeg.org/download.html); Separador Vocal no empaqueta ese ejecutable.

La primera vez que se pulse **Separar voz y coros**, la aplicación solicitará confirmar la descarga de los dos modelos UVR aprobados (aprox. 120 MB). Se guardan en la caché local y se comprueban sus sumas SHA-256 antes de usarlos. La inferencia procesa el audio en el equipo; no se sube la canción.

La voz principal y el residuo de coros son estimaciones: los arreglos con voces dobladas, armonías cercanas o reverberación pueden filtrarse entre pistas.

## Atribuciones

Los modelos elegidos pertenecen al proyecto Ultimate Vocal Remover (UVR). UVR solicita que las aplicaciones de terceros que integren sus modelos respeten MIT y den crédito a UVR y a sus desarrolladores Anjok07 y aufr33. El motor opcional `python-audio-separator` está publicado bajo MIT por karaokenerds. Consulta [docs/third-party-notices.md](docs/third-party-notices.md).
