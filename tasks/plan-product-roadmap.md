# Plan de implementación del producto

Las ramas feature parten de `develop`; commits pequeños y descriptivos se integran de vuelta a `develop`. `main` queda bajo control del mantenedor.

1. `audio-workbench`: reproducción sincronizada, forma de onda, Mute/Solo, fader por stem, pitch con tempo preservado y documentación. **Implementado.**
2. `vocal-separation`: configurar solapamiento del modelo MDX y mantener segmentación interna para reducir discontinuidades; dejar parámetros registrados. **Implementado.**
3. `four-stem-separation`: agregar batería, bajo y otros cuando se apruebe un modelo con derechos compatibles y se verifique la respuesta del motor. **Bloqueo de licencia de pesos.**
4. `export-library`: exportar copias WAV de los stems a una ubicación elegida desde el mezclador. **Implementado.**
5. `packaging`: instalador Windows que excluye audio, modelos y FFmpeg; guía reproducible y adjunto en GitHub Release. **v0.3.0 publicado.**
6. Revisar el diff, compilar/verificar a mano la aplicación, crear commits atómicos por rama, integrar cada rama en `develop` y subir la rama de integración. **Completado. `main` queda sin cambios.**
