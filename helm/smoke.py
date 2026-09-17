"""Manual, instrumentation-only single-agent llama.cpp smoke path."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from helm.adapters.base import RuntimeMetadata
from helm.adapters.llama_cpp import LlamaCppAdapter


def _model_file_sha256(path: Path | None) -> str | None:
    if path is None:
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8080")
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-file", type=Path)
    parser.add_argument("--quantization")
    parser.add_argument("--llama-cpp-commit")
    parser.add_argument("--backend", default="VULKAN")
    parser.add_argument("--device", default="Vulkan1")
    parser.add_argument("--gpu-layers", default="all")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output is not None and any("analytic" in part.casefold() for part in args.output.parts):
        raise ValueError("SMOKE_OUTPUT_MUST_NOT_BE_ANALYTIC")
    runtime_metadata = RuntimeMetadata(
        model=args.model,
        backend=args.backend,
        device=args.device,
        quantization=args.quantization,
        model_file=None if args.model_file is None else str(args.model_file),
        model_file_sha256=_model_file_sha256(args.model_file),
        llama_cpp_commit=args.llama_cpp_commit,
        gpu_layers=args.gpu_layers,
    )
    result = LlamaCppAdapter(
        endpoint=args.endpoint,
        model=args.model,
        runtime_metadata=runtime_metadata,
    ).generate_structured_response(
        [{"role": "user", "content": "Instrumentation-only verifier smoke request."}]
    )
    document = {
        "INSTRUMENTATION_ONLY": True,
        "ANALYTIC_USE": "FORBIDDEN",
        "instrumentation_only": True,
        "analytic_use": "FORBIDDEN",
        "role": "VERIFIER",
        "result": result.to_dict(),
    }
    rendered = json.dumps(document, indent=2, sort_keys=True)
    if args.output is None:
        print(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)


if __name__ == "__main__":
    main()
