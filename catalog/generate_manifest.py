"""Generate the VS Code component catalog without importing YanglabPDK.

Run with the Numerical environment:
    python catalog/generate_manifest.py
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import warnings
from pathlib import Path
from typing import Any

try:
    from registry import COMPONENT_OVERRIDES
except ImportError:
    from .registry import COMPONENT_OVERRIDES


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path(__file__).with_name("components.json")
warnings.filterwarnings("ignore", category=SyntaxWarning)


def _source_segment(source: str, node: ast.AST | None) -> str | None:
    if node is None:
        return None
    return ast.get_source_segment(source, node)


def _literal_value(node: ast.AST | None, source: str) -> dict[str, Any]:
    if node is None:
        return {"kind": "required", "value": None, "source": None}
    text = _source_segment(source, node) or ""
    try:
        value = ast.literal_eval(node)
        if isinstance(value, (str, int, float, bool)) or value is None:
            return {"kind": "literal", "value": value, "source": text}
        if isinstance(value, (tuple, list)):
            return {"kind": "literal", "value": value, "source": text}
    except (ValueError, TypeError, SyntaxError):
        pass
    return {"kind": "expression", "value": None, "source": text}


def _is_gf_cell(decorator: ast.expr) -> bool:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    if isinstance(target, ast.Attribute):
        return target.attr == "cell"
    return isinstance(target, ast.Name) and target.id == "cell"


def _parameters(node: ast.FunctionDef, source: str) -> list[dict[str, Any]]:
    positional = [*node.args.posonlyargs, *node.args.args]
    defaults: list[ast.AST | None] = [None] * (len(positional) - len(node.args.defaults))
    defaults.extend(node.args.defaults)
    result = []
    for argument, default in zip(positional, defaults):
        if argument.arg in {"self", "cls"}:
            continue
        item = _literal_value(default, source)
        item.update(
            {
                "name": argument.arg,
                "annotation": _source_segment(source, argument.annotation),
                "keywordOnly": False,
            }
        )
        result.append(item)
    for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        item = _literal_value(default, source)
        item.update(
            {
                "name": argument.arg,
                "annotation": _source_segment(source, argument.annotation),
                "keywordOnly": True,
            }
        )
        result.append(item)
    return result


def _category(relative: Path) -> str:
    parts = relative.parts
    return parts[1] if len(parts) > 2 and parts[0] == "components" else "other"


def discover(package_root: Path = PACKAGE_ROOT) -> list[dict[str, Any]]:
    components_root = package_root / "components"
    records: list[dict[str, Any]] = []
    for path in sorted(components_root.rglob("*.py")):
        if path.name == "__init__.py" or "__pycache__" in path.parts:
            continue
        source = path.read_text(encoding="utf-8-sig")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            records.append(
                {
                    "id": f"error:{path.relative_to(package_root).as_posix()}",
                    "name": path.stem,
                    "title": path.stem,
                    "category": "scan-errors",
                    "status": "error",
                    "error": str(error),
                }
            )
            continue
        relative = path.relative_to(package_root).with_suffix("")
        module = ".".join(relative.parts)
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not any(_is_gf_cell(item) for item in node.decorator_list):
                continue
            key = f"{module}:{node.name}"
            thumbnail_name = f"{node.name}-{hashlib.sha1(key.encode()).hexdigest()[:8]}.png"
            override = COMPONENT_OVERRIDES.get(key, {})
            params = _parameters(node, source)
            recommended = override.get(
                "recommended",
                [p["name"] for p in params if p["kind"] == "required"]
                or [p["name"] for p in params[:4]],
            )
            doc = ast.get_docstring(node) or ""
            records.append(
                {
                    "id": key,
                    "name": node.name,
                    "title": override.get("title", node.name.replace("_", " ").title()),
                    "category": _category(relative),
                    "module": f"YanglabPDK.{module}",
                    "relativeModule": module,
                    "file": relative.with_suffix(".py").as_posix(),
                    "line": node.lineno,
                    "description": override.get("description", doc.split("\n\n", 1)[0]),
                    "docstring": doc,
                    "parameters": params,
                    "recommended": recommended,
                    "registered": key in COMPONENT_OVERRIDES,
                    "status": "registered" if key in COMPONENT_OVERRIDES else "discovered",
                    "previewParameters": override.get("previewParameters", {}),
                    "thumbnail": f"thumbnails/{thumbnail_name}",
                }
            )
    return sorted(records, key=lambda item: (not item.get("registered", False), item["category"], item["name"]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=PACKAGE_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    components = discover(args.package_root.resolve())
    payload = {
        "schemaVersion": 1,
        "package": "YanglabPDK",
        "componentCount": len([c for c in components if c.get("status") != "error"]),
        "registeredCount": len([c for c in components if c.get("registered")]),
        "components": components,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {payload['componentCount']} components to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
