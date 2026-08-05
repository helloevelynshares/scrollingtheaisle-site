"""Container-style import smoke for the hosted AisleCheck API.

Mirrors Render/Uvicorn startup: import the FastAPI app with only repo paths
on sys.path (no reliance on untracked local tooling such as holdout_labeler).
"""

from __future__ import annotations

import ast
import importlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class TestAisleCheckApiContainerImport(unittest.TestCase):
    def test_schema_does_not_import_holdout_labeler(self) -> None:
        schema_path = SCRIPTS / "shopper_query" / "schema.py"
        tree = ast.parse(schema_path.read_text(encoding="utf-8"))
        holdout_imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "holdout_labeler" or alias.name.startswith(
                        "holdout_labeler."
                    ):
                        holdout_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "holdout_labeler" or node.module.startswith(
                    "holdout_labeler."
                ):
                    holdout_imports.append(node.module)
        self.assertEqual(
            holdout_imports,
            [],
            "shopper_query.schema must not depend on holdout_labeler "
            "(that package is local-only and missing from Docker/Render)",
        )

    def test_offer_vocab_is_importable_without_holdout(self) -> None:
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        # Ensure a previously loaded holdout_labeler does not mask the check.
        sys.modules.pop("holdout_labeler", None)
        sys.modules.pop("holdout_labeler.paths", None)
        vocab = importlib.import_module("shopper_query.offer_vocab")
        self.assertIn("simple_sale", vocab.PROMOTION_TYPES)
        self.assertIn("each", vocab.PRICE_BASIS_VALUES)
        schema = importlib.import_module("shopper_query.schema")
        self.assertEqual(schema.PROMOTION_TYPES, vocab.PROMOTION_TYPES)
        self.assertEqual(schema.PRICE_BASIS_VALUES, vocab.PRICE_BASIS_VALUES)

    def test_app_import_ok(self) -> None:
        if str(SCRIPTS) not in sys.path:
            sys.path.insert(0, str(SCRIPTS))
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        try:
            from services.aislecheck_api.app import app
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest(f"fastapi not installed: {exc}") from exc
        self.assertIsNotNone(app)
        print("import ok")


if __name__ == "__main__":
    unittest.main()
