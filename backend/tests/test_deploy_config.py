"""Deploy-facing config: psycopg 3 URL rewrite and cross-domain cookie flags."""

import unittest

from app.config import Settings

from .base import ApiTestCase


class DatabaseUrlTests(unittest.TestCase):
    def test_bare_postgres_url_gains_psycopg3_driver(self) -> None:
        settings = Settings(_env_file=None, database_url="postgresql://u:p@h:5432/db")
        self.assertEqual(settings.database_url, "postgresql+psycopg://u:p@h:5432/db")

    def test_explicit_driver_url_is_kept(self) -> None:
        settings = Settings(
            _env_file=None, database_url="postgresql+psycopg://u:p@h:5432/db"
        )
        self.assertEqual(settings.database_url, "postgresql+psycopg://u:p@h:5432/db")

    def test_sqlite_url_is_untouched(self) -> None:
        settings = Settings(_env_file=None, database_url="sqlite:///./dev.db")
        self.assertEqual(settings.database_url, "sqlite:///./dev.db")


class CookieSettingsTests(unittest.TestCase):
    def test_defaults_are_local_development_safe(self) -> None:
        settings = Settings(_env_file=None)
        self.assertEqual(settings.cookie_samesite, "lax")
        self.assertFalse(settings.cookie_secure)


class LoginCookieHeaderTests(ApiTestCase):
    def test_default_login_cookie_is_lax_without_secure(self) -> None:
        response = self.login("manager", "manager123")
        cookie_header = response.headers["set-cookie"]
        self.assertIn("SameSite=lax", cookie_header)
        self.assertNotIn("Secure", cookie_header)

    def test_cross_domain_login_cookie_is_none_and_secure(self) -> None:
        from app import auth

        original_samesite = auth.settings.cookie_samesite
        original_secure = auth.settings.cookie_secure
        auth.settings.cookie_samesite = "none"
        auth.settings.cookie_secure = True
        try:
            response = self.login("manager", "manager123")
            cookie_header = response.headers["set-cookie"]
            self.assertIn("SameSite=none", cookie_header)
            self.assertIn("Secure", cookie_header)
        finally:
            auth.settings.cookie_samesite = original_samesite
            auth.settings.cookie_secure = original_secure


if __name__ == "__main__":
    unittest.main()
