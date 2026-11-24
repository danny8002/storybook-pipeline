#!/usr/bin/env python3
"""Generate one MP3 with a local VoiceStudio OpenAI-compatible endpoint."""

import argparse
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_BASE_URL = "http://127.0.0.1:3900"
MODEL_ID = "omnivoice"
MODEL_NAME = "OmniVoice (k2-fsa/OmniVoice, 600+ languages)"
VOICE = "default"
RESPONSE_FORMAT = "mp3"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate one VoiceStudio MP3 using OmniVoice."
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("VOICESTUDIO_BASE_URL", DEFAULT_BASE_URL),
        help="VoiceStudio base URL (default: %(default)s)",
    )
    parser.add_argument("--voice", default=VOICE, help="Selected VoiceStudio profile ID or default")
    text_group = parser.add_mutually_exclusive_group()
    text_group.add_argument("--text", help="Approved narration text")
    text_group.add_argument(
        "--text-file", help="UTF-8 file containing the approved narration text"
    )
    text_group.add_argument(
        "--stdin", action="store_true", help="Read approved narration text from stdin"
    )
    parser.add_argument("--out", help="Destination .mp3 path")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check that VoiceStudio offers OmniVoice without generating audio",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="HTTP timeout in seconds (default: %(default)s)",
    )
    args = parser.parse_args()
    if not args.check and not (args.text is not None or args.text_file or args.stdin):
        parser.error("--text, --text-file, or --stdin is required unless --check is used")
    if not args.check and not args.out:
        parser.error("--out is required unless --check is used")
    if args.out and os.path.splitext(args.out)[1].lower() != ".mp3":
        parser.error("--out must end in .mp3")
    return args


def endpoint_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/v1/audio/speech"


def models_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/v1/models"


def check_model(base_url: str, timeout: float) -> None:
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("base URL must be an absolute http(s) URL")
    request = urllib.request.Request(
        models_url(base_url), headers={"Accept": "application/json"}, method="GET"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            document = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            "VoiceStudio model check returned HTTP %s: %s"
            % (exc.code, detail or exc.reason)
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("VoiceStudio connection failed: %s" % exc.reason) from exc
    if not isinstance(document, dict) or not isinstance(document.get("data"), list):
        raise RuntimeError("VoiceStudio model check returned an invalid JSON response")
    model_ids = {
        item.get("id")
        for item in document["data"]
        if isinstance(item, dict)
    }
    if MODEL_ID not in model_ids:
        raise RuntimeError(
            "VoiceStudio does not currently offer model 'omnivoice'. "
            "Enable the k2-fsa/OmniVoice engine and restart VoiceStudio."
        )


def looks_like_mp3(data: bytes) -> bool:
    return (
        len(data) > 3
        and (data.startswith(b"ID3") or (data[0] == 0xFF and data[1] & 0xE0 == 0xE0))
    )


def synthesize(base_url: str, voice: str, text: str, timeout: float) -> bytes:
    payload = json.dumps(
        {
            "model": MODEL_ID,
            "voice": voice,
            "input": text,
            "response_format": RESPONSE_FORMAT,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint_url(base_url),
        data=payload,
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        message = "VoiceStudio HTTP %s: %s" % (exc.code, detail or exc.reason)
        raise RuntimeError(message) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("VoiceStudio connection failed: %s" % exc.reason) from exc


def write_atomic(path: str, data: bytes) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".voicestudio-", suffix=".mp3", dir=parent, delete=False
        ) as temp:
            temp.write(data)
            temp_path = temp.name
        os.replace(temp_path, path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def main() -> int:
    args = parse_args()
    if args.check:
        try:
            check_model(args.base_url, args.timeout)
        except (json.JSONDecodeError, KeyError, OSError, RuntimeError, ValueError) as exc:
            print("VoiceStudio unavailable at %s: %s" % (args.base_url, exc), file=sys.stderr)
            return 1
        print(
            json.dumps(
                {
                    "ready": True,
                    "endpoint": endpoint_url(args.base_url),
                    "model": MODEL_ID,
                    "model_name": MODEL_NAME,
                    "voice": args.voice,
                    "response_format": RESPONSE_FORMAT,
                }
            )
        )
        return 0

    try:
        if args.text is not None:
            text = args.text
        elif args.text_file:
            with open(args.text_file, "r", encoding="utf-8") as source:
                text = source.read()
        else:
            text = sys.stdin.read()
        if not text.strip():
            raise ValueError("Narration text cannot be empty")
        audio = synthesize(args.base_url, args.voice, text, args.timeout)
        if not audio:
            raise RuntimeError("VoiceStudio returned an empty response")
        if not looks_like_mp3(audio):
            raise RuntimeError(
                "VoiceStudio did not return MP3 bytes; check the model and response_format"
            )
        write_atomic(args.out, audio)
    except (OSError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "path": args.out,
                "bytes": len(audio),
                "model": MODEL_ID,
                "model_name": MODEL_NAME,
                "voice": args.voice,
                "response_format": RESPONSE_FORMAT,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
