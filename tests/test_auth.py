import os
import pytest
import bcrypt

# Use a test database to avoid polluting production data
os.environ["MYSQL_DATABASE"] = "multi_agent_rag_test"

from db import get_conn, init_db


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create test database and tables, clean up after each test."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE DATABASE IF NOT EXISTS multi_agent_rag_test")
    finally:
        conn.close()

    init_db()

    yield

    # Clean up test data
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM user_documents")
            cur.execute("DELETE FROM chat_history")
            cur.execute("DELETE FROM user_settings")
            cur.execute("DELETE FROM users")
        conn.commit()
    finally:
        conn.close()


class TestBcryptHashing:
    def test_register_and_verify(self):
        from auth.user_auth import register_user, verify_user
        register_user("13800000001", "password123")
        assert verify_user("13800000001", "password123") is True

    def test_wrong_password_rejected(self):
        from auth.user_auth import register_user, verify_user
        register_user("13800000002", "password123")
        assert verify_user("13800000002", "wrongpassword") is False

    def test_nonexistent_user(self):
        from auth.user_auth import verify_user
        assert verify_user("99999999999", "password") is False

    def test_password_is_bcrypt_format(self):
        from auth.user_auth import register_user
        register_user("13800000003", "mypassword")
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT password_hash FROM users WHERE phone=%s", ("13800000003",))
                row = cur.fetchone()
                assert row["password_hash"].startswith("$2")
        finally:
            conn.close()

    def test_duplicate_registration_rejected(self):
        from auth.user_auth import register_user
        assert register_user("13800000004", "pass1") is True
        assert register_user("13800000004", "pass2") is False


class TestLegacyMigration:
    def test_sha256_user_auto_migrates(self):
        """Simulate a user with old SHA-256 hash, verify they can log in and hash gets upgraded."""
        import hashlib
        from auth.user_auth import verify_user

        phone = "13800000099"
        password = "oldpassword"
        old_hash = hashlib.sha256(password.encode()).hexdigest()

        # Insert user with old SHA-256 hash directly
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (phone, password_hash) VALUES (%s, %s)",
                    (phone, old_hash),
                )
            conn.commit()
        finally:
            conn.close()

        # Should still be able to verify
        assert verify_user(phone, password) is True

        # After successful login, the hash should be upgraded to bcrypt
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT password_hash FROM users WHERE phone=%s", (phone,))
                row = cur.fetchone()
                assert row["password_hash"].startswith("$2")
        finally:
            conn.close()

    def test_sha256_user_wrong_password(self):
        """Old SHA-256 user with wrong password should be rejected."""
        import hashlib
        from auth.user_auth import verify_user

        phone = "13800000098"
        old_hash = hashlib.sha256("correctpassword".encode()).hexdigest()

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (phone, password_hash) VALUES (%s, %s)",
                    (phone, old_hash),
                )
            conn.commit()
        finally:
            conn.close()

        assert verify_user(phone, "wrongpassword") is False


class TestPasswordReset:
    def test_reset_password(self):
        from auth.user_auth import register_user, verify_user, reset_password
        register_user("13800000005", "oldpass")
        reset_password("13800000005", "newpass")
        assert verify_user("13800000005", "oldpass") is False
        assert verify_user("13800000005", "newpass") is True

    def test_reset_nonexistent_user(self):
        from auth.user_auth import reset_password
        assert reset_password("99999999999", "newpass") is False
