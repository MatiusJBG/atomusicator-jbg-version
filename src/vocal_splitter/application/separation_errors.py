"""Fallos operativos de separación que la interfaz puede explicar."""


class SeparationError(Exception):
    code = "separation_error"
    user_message = "No se pudo completar la separación. Revisa el audio y vuelve a intentarlo."


class SeparationCancelledError(SeparationError):
    code = "cancelled"
    user_message = "La separación se canceló. Los archivos originales siguen intactos."


class SeparationEngineUnavailableError(SeparationError):
    code = "engine_unavailable"
    user_message = (
        'Falta el motor local de separación. Instálalo con '
        'python -m pip install -e ".[separation-cpu]" y vuelve a intentarlo. '
        "También necesitas instalar FFmpeg y dejar ffmpeg.exe disponible en PATH."
    )


class SeparationFfmpegUnavailableError(SeparationError):
    code = "ffmpeg_unavailable"
    user_message = (
        "No se encontró FFmpeg. Instala una compilación de FFmpeg y agrega "
        "su carpeta a PATH; la aplicación no incluye ese binario."
    )


class SeparationModelDownloadError(SeparationError):
    code = "model_download_failed"
    user_message = "No se pudo descargar el modelo. Comprueba la conexión e inténtalo de nuevo."


class SeparationModelIntegrityError(SeparationError):
    code = "model_integrity_failed"
    user_message = (
        "El archivo del modelo no coincide con la suma verificada. "
        "No se usó para procesar el audio."
    )


class SeparationModelProfileError(SeparationError):
    code = "model_profile_invalid"
    user_message = "El perfil de modelo no pasó la revisión de procedencia y licencia."


class SeparationOutputError(SeparationError):
    code = "invalid_output"
    user_message = "El motor no produjo todas las pistas de audio esperadas."


class SeparationStorageError(SeparationError):
    code = "storage_error"
    user_message = "No hay espacio o permisos suficientes para guardar los resultados."

    def __init__(self, user_message: str | None = None) -> None:
        if user_message is not None:
            self.user_message = user_message
        super().__init__(self.user_message)


class PartialSeparationError(SeparationError):
    code = "second_stage_failed"

    def __init__(self, message: str, result) -> None:
        super().__init__(message)
        self.partial_result = result
