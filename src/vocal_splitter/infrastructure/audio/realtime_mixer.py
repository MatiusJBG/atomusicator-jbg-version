"""Mezclador de baja latencia sobre buffers de audio ya preparados."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf


@dataclass(slots=True)
class MixerTrack:
    name: str
    samples: np.ndarray
    gain: float = 1.0
    muted: bool = False
    solo: bool = False


class RealtimeMixer:
    """Mezcla pistas alineadas en el callback; nunca lee archivos allí."""

    def __init__(self, tracks: list[MixerTrack], sample_rate: int) -> None:
        if not tracks:
            raise ValueError("El mezclador necesita al menos una pista")
        lengths = {len(track.samples) for track in tracks}
        channels = {track.samples.shape[1] for track in tracks}
        if len(lengths) != 1 or len(channels) != 1:
            raise ValueError("Las pistas deben estar alineadas y tener los mismos canales")
        self.tracks = tracks
        self.sample_rate = sample_rate
        self.channels = channels.pop()
        self.frame_count = lengths.pop()
        self.position = 0
        self._lock = threading.Lock()
        self._scratch = np.zeros((8192, self.channels), dtype=np.float32)
        self._stream = None

    @classmethod
    def from_files(cls, paths: list[tuple[str, Path]]) -> "RealtimeMixer":
        tracks: list[MixerTrack] = []
        rate: int | None = None
        for name, path in paths:
            samples, current_rate = sf.read(path, dtype="float32", always_2d=True)
            if rate is None:
                rate = current_rate
            if current_rate != rate:
                raise ValueError("Las pistas tienen frecuencias de muestreo distintas")
            tracks.append(MixerTrack(name, np.ascontiguousarray(samples)))
        if rate is None:
            raise ValueError("No hay pistas para cargar")
        return cls(tracks, rate)

    def set_controls(self, index: int, *, gain: float | None = None,
                     muted: bool | None = None, solo: bool | None = None) -> None:
        with self._lock:
            track = self.tracks[index]
            if gain is not None:
                track.gain = max(0.0, min(1.5, float(gain)))
            if muted is not None:
                track.muted = muted
            if solo is not None:
                track.solo = solo

    def seek(self, frame: int) -> None:
        with self._lock:
            self.position = max(0, min(int(frame), self.frame_count))

    def start(self) -> None:
        try:
            import sounddevice as sd
        except ImportError as error:
            raise RuntimeError("Instala el componente de reproducción: pip install -e '.[playback]'") from error
        if self._stream is None:
            self._stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="float32",
                callback=self._callback,
                blocksize=1024,
            )
        self._stream.start()

    def pause(self) -> None:
        if self._stream is not None and self._stream.active:
            self._stream.stop()

    def close(self) -> None:
        if self._stream is not None:
            self._stream.close()
            self._stream = None

    def _callback(self, outdata: np.ndarray, frames: int, _time: object, status: object) -> None:
        del status
        outdata.fill(0)
        with self._lock:
            start = self.position
            end = min(start + frames, self.frame_count)
            count = end - start
            if count <= 0:
                raise __import__("sounddevice").CallbackStop
            solo_active = any(track.solo for track in self.tracks)
            for track in self.tracks:
                if track.muted or (solo_active and not track.solo):
                    continue
                scratch = self._scratch[:count]
                np.multiply(track.samples[start:end], track.gain, out=scratch)
                np.add(outdata[:count], scratch, out=outdata[:count])
            # Guardamos margen de pico antes de entregar el bloque al dispositivo.
            peak = float(np.max(np.abs(outdata[:count])))
            if peak > 0.98:
                outdata[:count] *= 0.98 / peak
            self.position = end
        if count < frames:
            outdata[count:].fill(0)

