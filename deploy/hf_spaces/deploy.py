"""Create and upload the private Jeeves and WaterSheep Hugging Face Spaces."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
TARGETS = {
    "jeeves": ("decisions-jeeves", REPO_ROOT / "deploy" / "hf_spaces" / "jeeves"),
    "watersheep": ("decisions-watersheep", REPO_ROOT / "deploy" / "hf_spaces" / "watersheep"),
}
IGNORE_PATTERNS = (
    "__pycache__",
    "**/__pycache__/**",
    "*.pyc",
    "**/*.pyc",
)
HARDWARE_HELP = "Open the Space › Settings › Hardware and choose ZeroGPU."


def hf_space_url(owner: str, name: str) -> str:
    """Return the lowercase Space URL using APCCS's shared naming rule."""
    def part(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")

    owner_part = part(owner)
    name_part = part(name)
    if not owner_part or not name_part:
        raise ValueError("Hugging Face owner and Space name must contain letters or digits")
    return f"https://{owner_part}-{name_part}.hf.space"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deploy the private APCCS decision Spaces.")
    parser.add_argument(
        "--which",
        choices=("both", "jeeves", "watersheep"),
        default="both",
        help="which Space to create or update (default: both)",
    )
    return parser


def _selected_targets(which: str) -> tuple[str, ...]:
    if which == "both":
        return ("jeeves", "watersheep")
    return (which,)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("HF_TOKEN is missing. Set it in the environment, then run the deployer again.", file=sys.stderr)
        return 2

    try:
        from huggingface_hub import HfApi, SpaceHardware

        api = HfApi(token=token)
        owner = api.whoami()["name"]
        for target in _selected_targets(args.which):
            name, source_folder = TARGETS[target]
            repo_id = f"{owner}/{name}"
            api.create_repo(
                repo_id,
                repo_type="space",
                space_sdk="gradio",
                private=True,
                exist_ok=True,
            )
            api.upload_folder(
                repo_id=repo_id,
                folder_path=str(source_folder),
                repo_type="space",
                ignore_patterns=list(IGNORE_PATTERNS),
            )
            try:
                api.request_space_hardware(repo_id, SpaceHardware.ZERO_A10G)
            except Exception:
                print(HARDWARE_HELP)
            print(hf_space_url(owner, name))
    except Exception:
        print(
            "Hugging Face deployment failed. Check the account, token permissions, and Space access.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
