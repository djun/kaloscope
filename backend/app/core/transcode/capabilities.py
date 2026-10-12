import asyncio
import contextlib
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

_CAPABILITY_TIMEOUT = 10.0
_RUNTIME_PROBE_TIMEOUT = 10.0
_RUNTIME_REAP_TIMEOUT = 1.0
_RUNTIME_STDERR_LIMIT = 2048
_LISTING_OPTIONS = {
    "encoders": "-encoders",
    "filters": "-filters",
    "hwaccels": "-hwaccels",
    "bsfs": "-bsfs",
    "muxers": "-muxers",
}

_CAPABILITY_CACHE: dict[tuple[str, str], "FFmpegCapabilities"] = {}
_HW_ENCODER_CACHE: set[tuple[str, str, str | None]] = set()
_HW_DECODE_CACHE: set[tuple[str, str, str | None, str, int, int, int]] = set()
_HW_TRANSFORM_CACHE: set[tuple[str, str, str | None, str, int, int, int, str]] = set()


@dataclass(frozen=True)
class FFmpegCapabilities:
    """Capabilities advertised by one FFmpeg executable and video encoder.

    Attributes:
        executable: Executable name or path, resolved absolutely when available.
        encoders: Advertised audio and video encoder names.
        filters: Advertised filter names.
        hwaccels: Advertised hardware acceleration methods.
        bsfs: Advertised encoded stream filter names.
        muxers: Advertised output container format names.
        encoder_options: Selected encoder's private option names.
    """

    executable: str
    encoders: frozenset[str]
    filters: frozenset[str]
    hwaccels: frozenset[str]
    bsfs: frozenset[str]
    muxers: frozenset[str]
    encoder_options: frozenset[str]

    def supports_encoder(self, name: str) -> bool:
        """Check whether FFmpeg lists the requested encoder.

        Args:
            name: FFmpeg encoder name.

        Returns:
            Whether the name appears in the capability list.
        """
        return name in self.encoders

    def supports_filter(self, name: str) -> bool:
        """Check whether FFmpeg lists the requested filter.

        Args:
            name: FFmpeg filter name.

        Returns:
            Whether the name appears in the capability list.
        """
        return name in self.filters

    def supports_hwaccel(self, name: str) -> bool:
        """Check whether FFmpeg lists the requested hardware acceleration method.

        Args:
            name: FFmpeg hardware acceleration method name.

        Returns:
            Whether the name appears in the capability list.
        """
        return name in self.hwaccels

    def supports_bsf(self, name: str) -> bool:
        """Check whether FFmpeg lists the requested encoded stream filter.

        Args:
            name: FFmpeg encoded stream filter name.

        Returns:
            Whether the name appears in the capability list.
        """
        return name in self.bsfs

    def supports_muxer(self, name: str) -> bool:
        """Check whether FFmpeg lists the requested output format.

        Args:
            name: FFmpeg output format name.

        Returns:
            Whether the name appears in the capability list.
        """
        return name in self.muxers

    def supports_encoder_option(self, name: str) -> bool:
        """Check whether FFmpeg lists the requested encoder option.

        Args:
            name: FFmpeg encoder option name.

        Returns:
            Whether the name appears in the capability list.
        """
        return name in self.encoder_options


def _parse_listing(kind: str, output: str) -> set[str]:
    """Extract supported names from FFmpeg command output.

    Args:
        kind: Capability group to parse.
        output: Combined command output.

    Returns:
        Advertised capability names.

    Raises:
        ValueError: If the capability group is unknown.
    """
    names: set[str] = set()
    for line in output.splitlines():
        parts = line.split()
        if kind == "encoders":
            if (
                len(parts) >= 2
                and len(parts[0]) == 6
                and parts[0][0] in "VAS"
                and set(parts[0][1:]) <= set(".FSXBD")
            ):
                names.add(parts[1])
        elif kind == "filters":
            match = re.match(r"^\s*[TSC.]{2,3}\s+(\w+)\s+", line)
            if match:
                names.add(match.group(1))
        elif kind == "muxers":
            if len(parts) >= 2 and "E" in parts[0] and set(parts[0]) <= set("DEd."):
                names.update(parts[1].split(","))
        elif kind in {"hwaccels", "bsfs"}:
            value = line.strip()
            if value and " " not in value and re.fullmatch(r"[\w,-]+", value):
                names.update(value.split(","))
        else:
            raise ValueError(f"Unsupported FFmpeg capability kind: {kind}")
    return names


def _parse_encoder_options(output: str) -> set[str]:
    """Read private option names from FFmpeg encoder help.

    Args:
        output: Encoder help output.

    Returns:
        Private encoder option names.
    """
    return set(re.findall(r"^\s+-([^\s]+)\s+", output, flags=re.MULTILINE))


async def _query_ffmpeg(executable: str, *args: str) -> str:
    """Run a bounded FFmpeg capability query.

    Args:
        executable: FFmpeg command name or path.
        *args: Capability query arguments.

    Returns:
        Combined standard output and error text.

    Raises:
        RuntimeError: If the query fails or times out.
    """
    proc = await asyncio.create_subprocess_exec(
        executable,
        "-hide_banner",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=_CAPABILITY_TIMEOUT
        )
    except TimeoutError as exc:
        if proc.returncode is None:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
        await proc.communicate()
        raise RuntimeError(
            f"FFmpeg capability discovery timed out for '{executable}'"
        ) from exc
    if proc.returncode != 0:
        detail = stderr.decode(errors="replace").strip()
        raise RuntimeError(
            f"FFmpeg capability discovery failed for '{executable}': "
            f"{detail or f'exit code {proc.returncode}'}"
        )
    return (stdout + stderr).decode(errors="replace")


async def _read_stderr_tail(stream: asyncio.StreamReader) -> bytes:
    """Drain standard error and retain only the bounded tail.

    Args:
        stream: Process standard error stream.

    Returns:
        Final error bytes within the configured limit.
    """
    tail = bytearray()
    while chunk := await stream.read(4096):
        tail.extend(chunk)
        if len(tail) > _RUNTIME_STDERR_LIMIT:
            del tail[:-_RUNTIME_STDERR_LIMIT]
    return bytes(tail)


async def _kill_and_reap_probe(proc: asyncio.subprocess.Process):
    """Stop the probe and wait briefly for process cleanup.

    Args:
        proc: Running probe process.
    """
    if proc.returncode is None:
        with contextlib.suppress(ProcessLookupError):
            proc.kill()
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(proc.wait(), timeout=_RUNTIME_REAP_TIMEOUT)


async def _run_ffmpeg_probe(executable: str, args: list[str]) -> tuple[bool, str]:
    """Run a bounded probe without creating output files.

    Args:
        executable: FFmpeg command name or path.
        args: Probe arguments.

    Returns:
        Success flag and error detail.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            executable,
            "-hide_banner",
            "-loglevel",
            "error",
            *args,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as exc:
        return False, str(exc)
    assert proc.stderr is not None
    try:
        _, stderr = await asyncio.wait_for(
            asyncio.gather(proc.wait(), _read_stderr_tail(proc.stderr)),
            timeout=_RUNTIME_PROBE_TIMEOUT,
        )
    except TimeoutError:
        await _kill_and_reap_probe(proc)
        return False, f"timed out after {_RUNTIME_PROBE_TIMEOUT:.1f} seconds"
    except BaseException:
        await _kill_and_reap_probe(proc)
        raise
    detail = stderr.decode(errors="replace").strip()
    return proc.returncode == 0, detail


def _resolved_executable(executable: str) -> str:
    """Resolve a command path when the executable is available.

    Args:
        executable: Command name or path.

    Returns:
        Absolute path, or the original value if resolution fails.
    """
    resolved = shutil.which(executable)
    if resolved:
        return str(Path(resolved).resolve())
    return executable


async def require_hardware_encoder(
    executable: str,
    strategy: str,
    encoder: str,
    device: str | None,
    args: list[str],
):
    """Require one hardware encoder and device combination to encode a frame.

    Args:
        executable: The FFmpeg executable name or path.
        strategy: Hardware strategy identifier.
        encoder: Selected FFmpeg video encoder.
        device: Selected hardware device identifier.
        args: One-frame encoder probe arguments.

    Raises:
        RuntimeError: If the encoder probe cannot produce one frame.
    """
    executable = _resolved_executable(executable)
    key = (executable, strategy, device)
    if key in _HW_ENCODER_CACHE:
        return
    success, detail = await _run_ffmpeg_probe(executable, args)
    if not success:
        suffix = f": {detail}" if detail else ""
        raise RuntimeError(
            f"Hardware encoder '{encoder}' is unavailable for {strategy} "
            f"on device '{device or 'default'}'{suffix}"
        )
    _HW_ENCODER_CACHE.add(key)


def _decode_cache_key(
    executable: str,
    strategy: str,
    device: str | None,
    media_path: str,
    stream_index: int,
) -> tuple[str, str, str | None, str, int, int, int] | None:
    """Include source size and modification time in the probe key.

    Args:
        executable: Resolved FFmpeg path.
        strategy: Hardware strategy name.
        device: Selected device, or `None` for the default device.
        media_path: Source file path.
        stream_index: Video stream index.

    Returns:
        Cache key, or `None` if the source cannot be inspected.
    """
    path = Path(media_path).resolve()
    try:
        stat = path.stat()
    except OSError:
        return None
    return (
        executable,
        strategy,
        device,
        str(path),
        stat.st_size,
        stat.st_mtime_ns,
        stream_index,
    )


async def probe_hardware_decode(
    executable: str,
    strategy: str,
    device: str | None,
    media_path: str,
    stream_index: int,
    args: list[str],
) -> bool:
    """Probe source hardware decoding and cache successful file states.

    Args:
        executable: The FFmpeg executable name or path.
        strategy: Hardware strategy identifier.
        device: Selected hardware device identifier.
        media_path: Source media path.
        stream_index: Selected video stream index.
        args: One-frame decode probe arguments.

    Returns:
        Whether the source frame decoded and downloaded successfully.
    """
    executable = _resolved_executable(executable)
    key = _decode_cache_key(
        executable,
        strategy,
        device,
        media_path,
        stream_index,
    )
    if key is not None and key in _HW_DECODE_CACHE:
        return True
    success, _ = await _run_ffmpeg_probe(executable, args)
    if success and key is not None:
        _HW_DECODE_CACHE.add(key)
    return success


async def probe_hardware_transform(
    executable: str,
    strategy: str,
    device: str | None,
    media_path: str,
    stream_index: int,
    signature: str,
    args: list[str],
) -> bool:
    """Probe a source hardware-filter graph and cache successful file states.

    Args:
        executable: The FFmpeg executable name or path.
        strategy: Hardware strategy identifier.
        device: Selected hardware device identifier.
        media_path: Source media path.
        stream_index: Selected video stream index.
        signature: Hardware filter graph string used in cache keys.
        args: One-frame transform probe arguments.

    Returns:
        Whether the source frame completed every requested hardware transform.
    """
    executable = _resolved_executable(executable)
    decode_key = _decode_cache_key(
        executable,
        strategy,
        device,
        media_path,
        stream_index,
    )
    key = (*decode_key, signature) if decode_key is not None else None
    if key is not None and key in _HW_TRANSFORM_CACHE:
        return True
    success, _ = await _run_ffmpeg_probe(executable, args)
    if success and key is not None:
        _HW_TRANSFORM_CACHE.add(key)
    return success


async def load_ffmpeg_capabilities(executable: str, encoder: str) -> FFmpegCapabilities:
    """Discover and cache FFmpeg capabilities for the selected video encoder.

    Args:
        executable: The FFmpeg executable name or path.
        encoder: Selected video encoder name.

    Returns:
        Cached or newly discovered capability snapshot.

    Raises:
        OSError: If the FFmpeg process cannot be started.
        RuntimeError: If an FFmpeg capability query fails or times out.
    """
    executable = _resolved_executable(executable)
    key = (executable, encoder)
    cached = _CAPABILITY_CACHE.get(key)
    if cached is not None:
        return cached

    kinds = tuple(_LISTING_OPTIONS)
    outputs = await asyncio.gather(
        *(_query_ffmpeg(executable, _LISTING_OPTIONS[kind]) for kind in kinds)
    )
    listings = {
        kind: frozenset(_parse_listing(kind, output))
        for kind, output in zip(kinds, outputs, strict=True)
    }

    encoder_options: frozenset[str] = frozenset()
    # private option help is only valid for encoders present in this build
    if encoder in listings["encoders"]:
        help_output = await _query_ffmpeg(executable, "-h", f"encoder={encoder}")
        encoder_options = frozenset(_parse_encoder_options(help_output))

    capabilities = FFmpegCapabilities(
        executable=executable,
        encoders=listings["encoders"],
        filters=listings["filters"],
        hwaccels=listings["hwaccels"],
        bsfs=listings["bsfs"],
        muxers=listings["muxers"],
        encoder_options=encoder_options,
    )
    _CAPABILITY_CACHE[key] = capabilities
    return capabilities


def _clear_caches():
    """Clear cached capability snapshots, primarily for configuration changes."""
    _CAPABILITY_CACHE.clear()
    _HW_ENCODER_CACHE.clear()
    _HW_DECODE_CACHE.clear()
    _HW_TRANSFORM_CACHE.clear()
