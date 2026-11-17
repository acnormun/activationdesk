"""CORS origins come from settings: the default keeps localhost:3000 working."""

import unittest

from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, parse_origins
from app.main import app


class ParseOriginsTests(unittest.TestCase):
    def test_splits_on_commas(self) -> None:
        self.assertEqual(
            parse_origins("http://a:1, http://b:2"),
            ["http://a:1", "http://b:2"],
        )

    def test_drops_blank_entries(self) -> None:
        self.assertEqual(parse_origins(" http://a:1 ,,  "), ["http://a:1"])
        self.assertEqual(parse_origins(""), [])

    def test_settings_override(self) -> None:
        settings = Settings(_env_file=None, allowed_origins="http://host:4200")
        self.assertEqual(parse_origins(settings.allowed_origins), ["http://host:4200"])


class AppCorsTests(unittest.TestCase):
    def test_app_keeps_default_frontend_origin(self) -> None:
        cors_kwargs = next(
            middleware.kwargs
            for middleware in app.user_middleware
            if middleware.cls is CORSMiddleware
        )
        self.assertEqual(cors_kwargs["allow_origins"], ["http://localhost:3000"])


if __name__ == "__main__":
    unittest.main()
