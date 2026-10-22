"""Errores recuperables de lectura de audio."""


class AudioImportError(Exception):
    """Error base mostrado de forma recuperable durante la importación."""


class UnsupportedAudioFormatError(AudioImportError):
    """El contenedor o la extensión no están soportados."""


class InvalidAudioFileError(AudioImportError):
    """El archivo no contiene metadatos de audio válidos."""
