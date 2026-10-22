# Plan de producto: cinco stems y renovación visual

## Objetivo

Extender Separador Vocal para producir exactamente cinco pistas sincronizadas:
voz principal, coros, batería, bajo e instrumental. Primero se completa y valida
el flujo de audio y su mezclador; después se renueva la presentación y el flujo
visual de la aplicación de escritorio.

La app seguirá trabajando localmente. La separación es un proceso de renderizado
que puede tardar; reproducción, mute, solo, volumen y pitch se conservan en el
mezclador local.

## Supuestos para revisar

1. Se conserva el proceso UVR existente para voz total/acompañamiento y para
   estimar voz principal/coros.
2. El acompañamiento pasa por el modelo especializado UVR/Kuielab de batería y
   luego el modelo especializado de bajo. La segunda salida de cada paso se usa
   como entrada del siguiente; el remanente final representa instrumental sin
   batería ni bajo (incluye otros instrumentos y cualquier fuga de separación).
   Esta composición en serie evita sumar residuos WAV con posibles clipping.
3. Pitch, reproducción sincronizada, mute, solo, volumen y exportación siguen
   disponibles sobre las cinco pistas.
4. Los stems finales tienen el mismo inicio, frecuencia de muestreo y canales
   entre sí, y conservan la duración de la sesión con tolerancia máxima de
   100 ms. La interfaz avisará que la separación de voz principal/coros es una
   estimación del modelo.
5. Las ramas de trabajo parten de `develop`, usan commits pequeños y llegan a
   `develop` mediante PR. El usuario mantiene el merge de `main`.

## Mapa de capacidades

| Capacidad | Responsabilidad | Depende de |
|---|---|---|
| `instrumental-separation` | Elegir y ejecutar el modelo que obtiene batería, bajo, otros y residuo vocal desde el acompañamiento UVR. | Separación vocal actual |
| `five-stem-session` | Representar, validar, guardar, reanudar y publicar de forma atómica los cinco stems finales. | `instrumental-separation` |
| `five-stem-mixer` | Mostrar cinco pistas alineadas y mantener reproducción, controles en tiempo real, pitch y exportación. | `five-stem-session` |
| `product-visual-refresh` | Renovar el sistema visual y los flujos de importación, separación y mezcla después de estabilizar las cinco pistas. | `five-stem-mixer` |
| `desktop-release-validation` | Validar permisos, rutas locales, modelos, empaquetado e instalador con el flujo completo. | Todas las capacidades |

Orden: revisión técnica/licencias → `instrumental-separation` →
`five-stem-session` → `five-stem-mixer` → `product-visual-refresh` →
`desktop-release-validation`.

## Fase 1 — Selección y prueba del separador instrumental (completada)

1. Se seleccionaron `kuielab_a_drums.onnx` y `kuielab_a_bass.onnx` del catálogo
   público de UVR, que publica una solicitud de atribución MIT para aplicaciones
   que integran sus modelos. MDX-Net publica su código bajo MIT. No se redistribuye
   ningún peso: la aplicación los descarga desde el host oficial y verifica su
   SHA-256 antes de inferencia.
2. Se verificó compatibilidad con Python 3.13, Windows, Torch y `audio-separator`
   0.47.0. Los modelos especializados requieren `segment_size=512` para usar la
   ruta ONNX del modelo; se mantiene `overlap=0.35`.
3. Se añadieron métodos separados para batería y bajo, sin acoplar la aplicación
   al paquete de inferencia.
4. Las salidas `Drums`, `No Drums`, `Bass` y `No Bass` se mapean por nombre. El
   remanente final es `No Bass` tras retirar batería; no se suman archivos
   potencialmente saturados.
5. Modelos en caché local, descarga autorizada por el usuario, comprobación de
   integridad y registro local de perfil, hash, parámetros y tiempo.

**Validación real:** `Anvil — Crypt Loop` de Oğuzhan Girgin, licencia CC BY 4.0,
15.483 s. El motor produjo cinco WAV estéreo de 44.1 kHz, cada uno de 15.483 s,
sin truncamiento en los bordes. Se comprobó que la UI carga cinco canales. Esta
referencia instrumental no valida la clasificación de voz principal/coros.

## Fase 2 — Publicar una sesión de cinco stems

1. Añadir los tipos de dominio necesarios (`DRUMS`, `BASS`) y definir que
   `INSTRUMENTAL` es el resto musical después de extraer ambos, incluido el
   residuo del modelo.
2. Ampliar la orquestación: UVR voz/acompañamiento → UVR voz principal/coros y
   separador instrumental de batería → bajo → remanente.
3. Actualizar el cálculo de espacio libre antes de crear temporales para tener
   en cuenta todas las salidas y buffers intermedios.
4. Validar nombres, decodificación, canales, sample rate, offsets, duración y
   frames. No mostrar éxito ni publicar una separación parcial como completa.
5. Publicar las cinco salidas juntas de forma atómica. Si una etapa falla,
   conservar resultados recuperables con estado parcial y explicar qué pistas
   faltan.
6. Actualizar el manifiesto local de sesión con nombres, tamaños, modelos,
   versiones, hashes y parámetros.

Nombres de producto y archivos: `Voz principal`, `Coros`, `Batería`, `Bajo` e
`Instrumental`; `voz_principal.wav`, `coros.wav`, `bateria.wav`, `bajo.wav` e
`instrumental.wav`.

## Fase 3 — Integrar las cinco pistas al mezclador

1. Añadir cinco carriles sincronizados con forma de onda y playhead común.
2. Cada carril conserva mute, solo y volumen en tiempo real. El control afecta
   solo esa pista y el playhead/seek sincroniza todas.
3. Mantener pitch con duración constante y procesar las cinco pistas de forma
   coherente, evitando clipping y dejando margen de pico en la salida.
4. Exportar las cinco pistas con sus nombres y sample rate/canales declarados.
5. Verificar que se puedan alternar mute/solo y mover el volumen durante la
   reproducción sin detenerla; revisar las cinco salidas en el mezclador después
   de una separación real.

## Fase 4 — Renovar la experiencia y el aspecto visual

La renovación se hará después de cerrar la funcionalidad, con un lenguaje de
estación de audio: superficies de grafito verdoso, señales de color consistentes
para cada pista y una sola línea temporal compartida. Se conservará el carácter
de audio profesional sin copiar la interfaz o marca de Moises.

### Sistema visual propuesto

| Token | Color | Uso |
|---|---|---|
| Grafito | `#151D20` | Fondo general |
| Pizarra | `#202B2F` | Paneles de trabajo |
| Relieve | `#2B383B` | Controles elevados y estados activos |
| Marfil | `#F0EEE6` | Texto principal |
| Menta señal | `#55CFC0` | Acción primaria, progreso y selección |
| Coral de playhead | `#E98970` | Posición y alertas de transporte |

Colores semánticos de pista: voz principal menta (`#55CFC0`), coros lavanda
(`#A895E8`), batería ámbar (`#E5B35B`), bajo azul (`#75B9E4`) e `Instrumental`
gris verdoso (`#A7B9AE`). Se comprobará contraste y que cada pista siga
identificable sin depender solo del color. Tipografía Segoe UI para la interfaz,
con escala consistente: títulos 22–24 pt, etiquetas 14 pt y controles 12–14 pt.

### Flujo y distribución propuestos

- **Importación:** nombre y duración del archivo, acción primaria clara y área
  de arrastre; los formatos y ubicación local aparecen como ayuda secundaria.
- **Separación:** panel central que muestra la fase actual, una secuencia
  entendible de cuatro etapas y progreso honesto (porcentaje al descargar/validar;
  indicador indeterminado durante inferencia cuando no existe porcentaje real).
- **Mezclador:** cinco carriles legibles, una escala temporal común y transporte
  fijo abajo. Los faders, mute y solo quedan agrupados por carril; pitch y
  exportación se encuentran en el transporte. En ventanas pequeñas habrá scroll
  vertical de pistas sin romper la alineación horizontal.

```text
┌ Proyecto: canción.wav       Guardado local       Importar   Exportar ┐
│             regla temporal y playhead compartidos                   │
├ Voz principal ─ forma de onda ───────────── volumen  M  S ──────────┤
├ Coros         ─ forma de onda ───────────── volumen  M  S ──────────┤
├ Batería       ─ forma de onda ───────────── volumen  M  S ──────────┤
├ Bajo          ─ forma de onda ───────────── volumen  M  S ──────────┤
├ Instrumental  ─ forma de onda ───────────── volumen  M  S ──────────┤
└────────────── transporte / tiempo / pitch / exportación ────────────┘
```

Se revisarán estados vacíos, separando, cancelado, error y éxito; foco de
teclado, textos cortos, tamaños de controles y escalado a 1280×800 y 1920×1080.
El rediseño seguirá patrones propios de PySide6 y no incorporará dependencias de
UI sin necesidad.

## Fase 5 — Verificación y entrega

- Pruebas unitarias para mapeo, residuo instrumental, alineación, publicación
  atómica, recuperación ante fallos, mute/solo/gain y pitch.
- Prueba sintética con golpes y tonos en diferentes posiciones, silencios largos
  y transitorios al principio/final para detectar cortes o desplazamientos.
- Prueba de integración con el EXE y pesos verificados: producir exactamente
  cinco WAV legibles, duración dentro de 100 ms, frecuencia de muestreo y
  canales comunes entre pistas y picos sin clipping en la mezcla de escucha.
- Prueba auditiva con referencias de licencia compatible; registrar fuente,
  atribución y qué se escuchó. No usar ni redistribuir audio de usuarios.
- Construir ejecutable e instalador desde cero; validar rutas, permisos, caché
  local de modelos, GUI, primera descarga y reapertura del mezclador.
- Guardar evidencias de ejecución y hash del instalador; publicar una versión
  nueva y el instalador después de pasar el flujo completo.

## Riesgos y mitigaciones

- **Licencia o acceso del peso:** revisar y registrar cada peso antes de descarga;
  mantener el módulo bloqueado hasta completar esa revisión.
- **Clasificación imperfecta:** batería/bajo pueden filtrarse entre sí o hacia
  el resto. Medir con una colección pequeña autorizada y documentar límites;
  no prometer separación perfecta.
- **Duración/cortes:** comprobar frames y transitorios de borde en cada etapa;
  usar padding/overlap coherente y corregir solo mediante una regla registrada.
- **Clipping al consolidar:** mezclar residuos en float32, medir el pico y no
  normalizar stems automáticamente; mantener margen de reproducción.
- **Recursos:** medir CPU, memoria y duración antes de fijar requisitos; la
  interfaz permanece receptiva y permite cancelar de forma segura.
- **Empaquetado:** incluir extensiones nativas del modelo en PyInstaller y probar
  el EXE, el instalador y las carpetas bajo permisos de usuario estándar.

## Entregas y revisión

1. Revisión del plan y confirmación de la interpretación de las cinco pistas.
2. Especificación y tareas para el separador instrumental/licencias.
3. PR de separación y sesión de cinco stems hacia `develop`.
4. PR del mezclador de cinco pistas y pitch hacia `develop`.
5. Propuesta visual y luego PR del rediseño hacia `develop`.
6. Verificación de release, instalador y guía de actualización.

Cada PR se revisa con commits atómicos. No se integra directamente en `main`.
