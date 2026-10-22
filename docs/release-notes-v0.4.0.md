# Separador Vocal 0.4.0

## Novedades

- Separa cinco pistas: voz principal, coros, batería, bajo e instrumental restante.
- Añade dos pasadas instrumentales MDX-Net especializadas, en batería y después bajo; descarga los pesos bajo demanda y comprueba SHA-256 antes de inferir.
- Conserva los resultados completados como pistas parciales si falla una pasada posterior.
- Presenta las cinco pistas en el mezclador con una paleta semántica, formas de onda sincronizadas, volumen, mute, solo, pitch y exportación.
- Actualiza el progreso a cuatro etapas, el instalador y la guía en español.

## Validación

- 18 pruebas automatizadas para sesión, publicación de cinco stems, recuperación parcial, mezclador en tiempo real, mute/solo/ganancia, rutas locales, FFmpeg y runtime nativo.
- Ejecución de integración en Windows con los cuatro modelos oficiales: cinco WAV estéreo de 44.1 kHz, 682,816 frames (15.483 s), alineados desde el mismo inicio.
- UI offscreen con fuente Segoe UI registrada: cinco carriles visibles a 1280×800; controles de volumen y mute conectados al mezclador.
- El smoke test empaquetado puede repetir la inferencia si los cuatro modelos están en caché.

La muestra `Anvil — Crypt Loop` es una composición sintetizada corta publicada bajo CC BY 4.0. La evaluación confirma formato y alineación; no prueba la calidad de separación en canciones acústicas ni en mezclas vocales reales. Los modelos pueden filtrar contenido entre pistas.

## Datos locales y licencias

Los modelos permanecen fuera del instalador y del repositorio; se descargan a la caché local tras confirmación. La procedencia y los hashes están en `src/vocal_splitter/infrastructure/separation/model_license_manifest.json`. Revisa `docs/third-party-notices.md` antes de redistribuir o usar comercialmente.
