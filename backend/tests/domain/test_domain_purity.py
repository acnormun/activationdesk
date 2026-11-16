"""Done-when guard: the domain layer stays framework- and database-free."""

import re
import unittest
from pathlib import Path

DOMAIN_DIR = Path(__file__).resolve().parents[2] / "app" / "domain"

FORBIDDEN_IMPORT = re.compile(
    r"^\s*(?:import|from)\s+(fastapi|sqlalchemy|pydantic|app|database)\b",
    re.MULTILINE,
)


class DomainPurityTests(unittest.TestCase):
    def test_domain_imports_standard_library_only(self):
        for path in sorted(DOMAIN_DIR.glob("*.py")):
            with self.subTest(file=path.name):
                source = path.read_text(encoding="utf-8")
                match = FORBIDDEN_IMPORT.search(source)
                if match is not None:
                    self.fail(
                        f"{path.name} imports '{match.group(1)}' - the "
                        "domain layer must be standard library only"
                    )


if __name__ == "__main__":
    unittest.main()
