# Seguimiento de implementación del producto

## `audio-workbench`

- [x] Mostrar las formas de onda de voz principal, coros y acompañamiento con cursor común.
- [x] Reproducir y pausar sincronizados; buscar al pulsar una forma de onda.
- [x] Mute, Solo y ganancia independientes; control de pico del bus durante reproducción.
- [x] Aplicar pitch de -12 a +12 semitonos en segundo plano con Rubber Band de FFmpeg y mantener los WAV originales.
- [x] Exportar copias WAV de los stems seleccionados a una carpeta elegida desde el mezclador, sin bloquear la UI.
- [x] Verificar con señal sintética 0, +2 y -2 semitonos, duración constante, callback de mezcla y UI PySide6 offscreen.

## Continuidad de separación

- [x] Mantener segmentación MDX del motor y configurar solapamiento 0.35 para la mezcla entre ventanas.
- [x] Registrar tamaño de segmento, solapamiento y lote en `session.json` a través de los parámetros del modelo.
- [x] Detectar FFmpeg en PATH o en WinGet Links y exponerlo también al proceso del motor.
- [ ] Validar escucha comparativa con canción con licencia permisiva; no declarar mejora auditiva hasta hacer esa escucha.

## Separación de cuatro stems y exportación

- [ ] Añadir voz, batería, bajo y otros cuando haya pesos con derechos revisados para el modo de distribución previsto.
- [ ] Añadir elección de formato y exportación de mezcla.
- [ ] Mantener el procesamiento de mezclas largas dentro de límites de memoria y verificar continuidad con audio real.

## Windows / GitHub

- [x] README en español con instalación, configuración, uso y solución de problemas.
- [x] `.gitignore` cubre entornos, resultados, modelos y archivos de audio generados.
- [x] Definición PyInstaller/Inno Setup que excluye audio, modelos y FFmpeg.
- [x] Construir el instalador v0.2.0 e iniciar el ejecutable empaquetado.
- [x] Recompilar el instalador v0.3.0 y arrancar el ejecutable empaquetado.
- [x] Integrar ramas de funcionalidad/documentación a `develop` y subirlo.
- [x] Adjuntar el instalador v0.2.0 a una GitHub Release.
- [x] Adjuntar el instalador v0.3.0 a la GitHub Release `v0.3.0`.

## Flujo Git

- [x] Crear ramas feature/chore desde `develop`, commits atómicos y fast-forward de vuelta a `develop`.
- [x] Mantener `main` sin modificaciones; el mantenedor integrará `develop` cuando lo decida.
