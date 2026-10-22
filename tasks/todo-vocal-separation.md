# Tareas: `vocal-separation`

## Estado de esta iteración

- [x] Implementación del dominio, puerto, adaptador, orquestación y UI de separación.
- [x] Validación manual de ejecución CPU en fragmento local de 30 s; produjo y registró tres pistas WAV de 30 s, estéreo, alineadas desde 0 s.
- [x] Compilación de fuentes Python y arranque/cierre de humo de la ventana PySide6.
- [ ] Escuchar y evaluar subjetivamente las tres salidas.
- [ ] Validar la separación de principal/coros con una referencia de varias voces con derechos compatibles con el uso previsto.
- [ ] Ejecutar cancelación/error recuperable desde la interfaz y verificar cierre durante un trabajo.

La referencia disponible para la ejecución manual es CC BY-NC-SA 4.0; sirve para validación local no comercial, no para validar una referencia comercialmente libre. Detalles en [docs/vocal-separation-validation.md](../docs/vocal-separation-validation.md).

## 1. Seleccionar perfiles de modelo y referencias autorizadas

- Revisar compatibilidad actual del adaptador, versiones soportadas de Python/Windows y requisitos de CPU/GPU.
- Elegir un perfil candidato para voz/instrumental y otro para voz/karaoke solo si la fuente, versión y licencia de cada peso se pueden identificar.
- Crear el manifiesto local con origen, licencia, atribución, versión, hash, estado de revisión y fecha de comprobación. No incorporar pesos al repositorio.
- Identificar muestras de validación con licencia y atribución registradas. Comprobar acceso a Sanidha; si no está disponible, registrar una alternativa permisiva. No usar MUSDB18 como si tuviera licencia uniforme.
- **Aceptación:** cada perfil habilitado tiene origen/licencia/versión y hash documentados; las referencias elegidas tienen procedencia verificable. Si no se logra verificar un peso o una pista, queda bloqueado y se registra la limitación.
- **Verificación manual:** inspeccionar el manifiesto y los términos del origen primario de cada elemento seleccionado antes de permitir su descarga o uso.

## 2. Definir el dominio y el contrato del motor

- Implementar `SeparationJob`, estados, avance, cancelación cooperativa y errores recuperables.
- Implementar `Stem` y `SeparationResult` con etiquetas propias para `LeadVocal`, `BackingVocals` e `Instrumental`, y metadatos de formato/duración/canales.
- Definir el protocolo `VocalSeparator` y perfiles de modelo independientes del paquete externo.
- **Aceptación:** el dominio no depende de PySide6 ni del adaptador; las salidas desconocidas o ambiguas se rechazan en vez de mapearse por posición.
- **Verificación manual:** revisar tipos y flujo de estados con una ejecución simulada del contrato, sin cargar pesos de licencia pendiente.
- **Archivos previstos:** `src/vocal_splitter/domain/separation_job.py`, `stem.py`, `separation_result.py`; `src/vocal_splitter/application/ports/vocal_separator.py`.

## 3. Implementar el adaptador para voz e instrumental

- Integrar `python-audio-separator` detrás del protocolo propio para ejecutar la primera etapa.
- Configurar directorio de caché local; informar sobre la descarga de pesos y su tamaño cuando aplique.
- Normalizar las rutas y nombres que devuelve el motor; capturar incompatibilidad, fallo de modelo, falta de memoria y cancelación.
- **Aceptación:** con un perfil aprobado, una mezcla de referencia produce voz total e instrumental decodificables; errores se convierten a fallos recuperables del dominio.
- **Verificación manual:** procesar un fragmento con licencia aprobada, confirmar la identificación de ambas salidas y escuchar la separación.
- **Archivos previstos:** `src/vocal_splitter/infrastructure/separation/audio_separator_engine.py`, `model_profile.py` y configuración del manifiesto.

## 4. Implementar la segunda pasada para voz principal y residuo vocal

- Reprocesar el stem de voz total con el perfil Karaoke aprobado.
- Etiquetar la salida vocal destacada como voz principal estimada y el residual como coros/residuo vocal.
- Definir el estado parcial disponible si esta etapa falla: conservar únicamente voz total e instrumental como resultados de primera etapa, nunca etiquetarlos como lead/coros.
- **Aceptación:** salidas de segunda etapa se identifican de forma explícita; el error de esta etapa no publica stems finales engañosos.
- **Verificación manual:** escuchar voz principal y residuo por separado, anotando filtraciones/artifacts y si la referencia permite evaluar coros reales.
- **Archivos previstos:** extensión del adaptador, perfiles y mapeo tipado de resultados.

## 5. Orquestar el caso de uso y persistir resultados validados

- Implementar el caso de uso que recibe una sesión importada, comprueba capacidad/espacio, ejecuta las dos etapas y emite progreso.
- Escribir intermedios en `processing/` y salidas a nombres temporales; validar decodificación, canales, comienzo y duración antes de publicar `voz_principal.wav`, `coros.wav` y `acompanamiento.wav`.
- Registrar en `session.json` motor, versiones/perfiles/pesos, parámetros, tiempos, rutas y transformaciones de alineación.
- **Aceptación:** los tres WAV finales se publican únicamente tras completar y validar ambas etapas; la fuente original permanece sin cambios; un fallo conserva solo resultados parciales etiquetados correctamente.
- **Verificación manual:** inspeccionar sesión y archivos, comparar duración/inicio, y confirmar que una interrupción simulada no deja temporales presentados como finales.
- **Archivos previstos:** `src/vocal_splitter/application/separate_vocals.py` y ajustes a la persistencia de sesión.

## 6. Integrar el worker y los estados en la aplicación de escritorio

- Añadir acción de separación habilitada cuando exista una sesión importada.
- Ejecutar el caso de uso fuera del hilo UI y mostrar `Preparando`, descarga, ambas etapas, finalización, listo y error.
- Integrar cancelación cooperativa y retención del worker hasta su finalización, siguiendo el patrón de vida útil de `ImportWorker`.
- Mostrar rutas/resultados y una nota breve de que voz principal/coros son estimaciones sujetas a filtraciones.
- **Aceptación:** la ventana sigue respondiendo; errores y cancelación devuelven controles a un estado recuperable; los resultados parciales se distinguen claramente de los stems finales.
- **Verificación manual:** ejecutar un trabajo desde la ventana, observar transiciones, cancelar o provocar un error recuperable y cerrar la app al terminar.
- **Archivos previstos:** `src/vocal_splitter/ui/separation_worker.py`, `main_window.py` y mensajes de presentación.

## 7. Revisar el flujo completo con referencias permisivas

- Completar una ejecución voz/instrumental usando una pista con licencia identificada.
- Completar una prueba de voz principal/coros solo con una referencia de múltiples voces y derechos compatibles; si no hay una disponible, dejar ese punto explícitamente pendiente y no declarar que los coros reales fueron validados.
- Documentar referencia, atribución, versión, transformación, parámetros del motor y observaciones de escucha junto a la sesión o en `docs/`.
- **Aceptación:** las salidas están alineadas y reproducibles localmente, con procedencia trazable; las limitaciones de rendimiento/calidad quedan descritas sin afirmar aislamiento perfecto.
- **Verificación manual:** reimportar una referencia de licencia permisiva, comparar mezcla y stems al reproducirlos juntos y escuchar cada pista aislada.
- **Archivos previstos:** `docs/` y metadatos de la sesión.

## Orden y criterio de bloqueo

Ejecutar las tareas en orden. La Tarea 1 bloquea cualquier descarga/uso de pesos y cualquier validación con audio externo; las Tareas 2–6 pueden avanzar con contratos y datos simulados si no se encuentra a tiempo un peso o una pista con derechos verificables. La Tarea 7 solo declara validados los casos que efectivamente se hayan podido ejecutar con referencias autorizadas.
