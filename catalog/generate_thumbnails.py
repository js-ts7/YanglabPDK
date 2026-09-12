"""Render static previews for every catalog component that builds by default."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PACKAGE_ROOT.parent
MANIFEST = Path(__file__).with_name("components.json")
DEFAULT_OUTPUT = PACKAGE_ROOT / "catalog_assets" / "thumbnails"


def placeholder(path: Path, title: str, reason: str) -> None:
    fig, ax = plt.subplots(figsize=(4.6, 2.8), dpi=120)
    fig.patch.set_facecolor("#171717")
    ax.set_facecolor("#171717")
    ax.axis("off")
    ax.text(0.5, 0.60, title, ha="center", va="center", color="#e8e8e8", fontsize=12, weight="bold", wrap=True)
    ax.text(0.5, 0.36, "Preview unavailable", ha="center", va="center", color="#aaaaaa", fontsize=9)
    ax.text(0.5, 0.20, reason[:110], ha="center", va="center", color="#777777", fontsize=6.5, wrap=True)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.08, facecolor=fig.get_facecolor())
    plt.close(fig)


def render(component_info: dict, output: Path) -> tuple[bool, str]:
    destination = output / Path(component_info["thumbnail"]).name
    required = [item["name"] for item in component_info.get("parameters", []) if item["kind"] == "required"]
    if required:
        reason = "Required parameters: " + ", ".join(required)
        placeholder(destination, component_info["title"], reason)
        return False, reason
    try:
        module = importlib.import_module(component_info["module"])
        factory = getattr(module, component_info["name"])
        component = factory(**component_info.get("previewParameters", {}))
        fig = component.plot(show_labels=False, show_ruler=False, return_fig=True)
        if fig is None:
            raise RuntimeError("component.plot did not return a figure")
        fig.set_size_inches(4.6, 2.8)
        fig.savefig(destination, dpi=120, bbox_inches="tight", pad_inches=0.04, facecolor=fig.get_facecolor())
        plt.close(fig)
        return True, ""
    except Exception as error:
        reason = f"{type(error).__name__}: {error}"
        placeholder(destination, component_info["title"], reason)
        return False, reason


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--registered-only", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(WORKSPACE_ROOT))
    if PACKAGE_ROOT.name != "YanglabPDK":
        spec = importlib.util.spec_from_file_location(
            "YanglabPDK",
            PACKAGE_ROOT / "__init__.py",
            submodule_search_locations=[str(PACKAGE_ROOT)],
        )
        package = importlib.util.module_from_spec(spec)
        sys.modules["YanglabPDK"] = package
        spec.loader.exec_module(package)
    warnings.filterwarnings("ignore", category=SyntaxWarning)
    args.output.mkdir(parents=True, exist_ok=True)
    payload = json.loads(args.manifest.read_text(encoding="utf-8"))
    selected = [item for item in payload["components"] if item.get("status") != "error"]
    if args.registered_only:
        selected = [item for item in selected if item.get("registered")]
    successes = 0
    failures = []
    for index, item in enumerate(selected, 1):
        print(f"[{index}/{len(selected)}] {item['name']}", flush=True)
        ok, reason = render(item, args.output)
        item["previewStatus"] = "ready" if ok else "unavailable"
        if ok:
            successes += 1
        else:
            item["previewError"] = reason
            failures.append(f"{item['id']}: {reason}")
    args.manifest.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    error_log = args.output.parent / "thumbnail-errors.txt"
    error_log.write_text("\n".join(failures) + ("\n" if failures else ""), encoding="utf-8")
    print(f"Rendered {successes}/{len(selected)} real previews; placeholders: {len(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
