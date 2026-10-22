# Plan de implementación del producto

Las ramas feature parten de `develop`; commits pequeños y descriptivos se integran de vuelta a `develop`. `main` queda bajo control del mantenedor.

1. `audio-workbench`: reproducción sincronizada, forma de onda, Mute/Solo, fader por stem, pitch con tempo preservado y documentación. **Implementado.**
2. `vocal-separation`: configurar solapamiento del modelo MDX y mantener segmentación interna para reducir discontinuidades; dejar parámetros registrados. **Implementado.**
3. `four-stem-separation`: agregar batería, bajo y otros cuando se apruebe un modelo con derechos compatibles y se verifique la respuesta del motor. **Bloqueo de licencia de pesos.**
4. `export-library`: interfaz de exportación de stems y mezcla con formato, profundidad y ubicación configurables. **Pendiente.**
5. `packaging`: instalador Windows que excluye audio, modelos y FFmpeg; guía reproducible y adjunto en GitHub Release. **Compilación en curso.**
6. Revisar el diff, compilar/verificar a mano la aplicación, crear commits atómicos por rama, integrar cada rama en `develop` y subir la rama de integración. Nunca integrar `develop` en `main`.
