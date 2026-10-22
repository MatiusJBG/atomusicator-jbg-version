"""Prepara dependencias verificadas; no genera la aplicación ni el instalador."""

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen


RUNTIME_FILES = ("bin/ffmpeg.exe", "bin/ffprobe.exe", "LICENSE", "README.txt")
MAX_MEMBER_BYTES = 512 * 1024 * 1024


def load_manifest(project_root: Path) -> dict:
    return json.loads((project_root / "packaging" / "ffmpeg-runtime.json").read_text(encoding="utf-8"))


def verify_sha256(path: Path, expected: str) -> None:
    with path.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if actual != expected:
        raise RuntimeError(f"SHA-256 incorrecto para {path.name}; no se usará ese archivo.")


def _tool_output(executable: Path, *arguments: str) -> str:
    result = subprocess.run(
        [str(executable), *arguments], capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False, timeout=30,
        env=dict(os.environ, PATH=""),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode != 0:
        raise RuntimeError(f"No se pudo ejecutar {executable.name}: {result.stderr.strip()}")
    return result.stdout


def validate_runtime(root: Path, manifest: dict, *, check_tools: bool = True) -> None:
    for name in RUNTIME_FILES:
        if not (root / name).is_file():
            raise RuntimeError(f"Runtime de audio incompleto: falta {name}. Ejecuta packaging/prepare_ffmpeg.py.")
    for name, expected in manifest["files"].items():
        verify_sha256(root / name, expected)
    if "GNU GENERAL PUBLIC LICENSE" not in (root / "LICENSE").read_text(encoding="utf-8"):
        raise RuntimeError("Falta el texto de licencia del runtime de audio.")
    if check_tools:
        for tool in ("ffmpeg", "ffprobe"):
            version = _tool_output(root / "bin" / f"{tool}.exe", "-version")
            if not version.startswith(f"{tool} version {manifest['version']}"):
                raise RuntimeError(f"La versión de {tool} no coincide con el manifiesto.")
        executable = root / "bin" / "ffmpeg.exe"
        if " rubberband " not in _tool_output(executable, "-hide_banner", "-filters"):
            raise RuntimeError("El runtime no incluye Rubber Band para cambiar tonalidad.")
        if " libmp3lame " not in _tool_output(executable, "-hide_banner", "-encoders"):
            raise RuntimeError("El runtime no incluye el codificador MP3 requerido.")


def extract_runtime(archive: Path, destination: Path, archive_root: str) -> None:
    # Select exact members: never extractall() or trust names supplied by a zip.
    with zipfile.ZipFile(archive) as zipped:
        for name in RUNTIME_FILES:
            member = zipped.getinfo(f"{archive_root}/{name}")
            if member.is_dir() or stat.S_ISLNK(member.external_attr >> 16) or member.file_size > MAX_MEMBER_BYTES:
                raise RuntimeError(f"Miembro de runtime inválido: {name}")
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipped.open(member) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)


def _download_archive(cache: Path, manifest: dict) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    archive = cache / (manifest["archive_root"] + ".zip")
    if archive.is_file():
        try:
            verify_sha256(archive, manifest["archive_sha256"])
            return archive
        except RuntimeError:
            pass  # Replace only this generated cache file, never accept it.
    temporary = archive.with_suffix(".zip.part")
    try:
        request = Request(manifest["archive_url"], headers={"User-Agent": "SeparadorVocal-build"})
        with urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            received = 0
            while chunk := response.read(1024 * 1024):
                received += len(chunk)
                if received > manifest["archive_size"]:
                    raise RuntimeError("La descarga excede el tamaño verificado.")
                output.write(chunk)
        if received != manifest["archive_size"]:
            raise RuntimeError("La descarga de dependencias quedó incompleta.")
        verify_sha256(temporary, manifest["archive_sha256"])
        temporary.replace(archive)
        return archive
    finally:
        temporary.unlink(missing_ok=True)


def prepare_runtime(project_root: Path, source_directory: Path | None = None) -> Path:
    project_root = project_root.resolve()
    manifest = load_manifest(project_root)
    build = project_root / "build"
    build.mkdir(parents=True, exist_ok=True)
    destination = build / "ffmpeg-runtime"
    if not destination.resolve().is_relative_to(build.resolve()):
        raise RuntimeError("La carpeta de dependencias debe permanecer dentro de build.")
    if source_directory is None and destination.is_dir():
        try:
            validate_runtime(destination, manifest)
            return destination
        except (RuntimeError, OSError, subprocess.SubprocessError):
            pass  # Repair from the verified archive instead of using a host install.
    with tempfile.TemporaryDirectory(prefix="ffmpeg-prepare-", dir=build) as temporary:
        staging = Path(temporary)
        if source_directory is not None:
            validate_runtime(source_directory, manifest)
            for name in RUNTIME_FILES:
                target = staging / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_directory / name, target)
        else:
            archive = _download_archive(build / "ffmpeg-downloads", manifest)
            extract_runtime(archive, staging, manifest["archive_root"])
        validate_runtime(staging, manifest)
        (staging / "runtime-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        for name in (*RUNTIME_FILES, "runtime-manifest.json"):
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.resolve().is_relative_to(build.resolve()):
                raise RuntimeError("Destino de dependencia fuera de build.")
            (staging / name).replace(target)
    return destination


def get_bundle_entries(project_root: Path) -> tuple[list, list]:
    root = project_root / "build" / "ffmpeg-runtime"
    validate_runtime(root, load_manifest(project_root))
    manifest_file = root / "runtime-manifest.json"
    if not manifest_file.is_file():
        raise RuntimeError("Falta el manifiesto de procedencia de FFmpeg.")
    if json.loads(manifest_file.read_text(encoding="utf-8")) != load_manifest(project_root):
        raise RuntimeError("El manifiesto preparado no coincide con la versión revisada.")
    binaries = [(str(root / name), "runtime/ffmpeg/bin") for name in RUNTIME_FILES[:2]]
    data = [(str(root / name), "runtime/ffmpeg") for name in (*RUNTIME_FILES[2:], "runtime-manifest.json")]
    return binaries, data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="Copia offline de la misma versión verificada")
    args = parser.parse_args()
    try:
        runtime = prepare_runtime(Path(__file__).resolve().parents[1], args.source_dir)
    except (OSError, RuntimeError, subprocess.SubprocessError, zipfile.BadZipFile, KeyError) as error:
        parser.exit(1, f"No se pudo preparar el runtime de audio: {error}\n")
    print(f"Runtime verificado: {runtime}. No se generó ningún paquete de la aplicación.")
