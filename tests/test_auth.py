import json
import os
import tempfile
from unittest.mock import patch
import pytest
import bcrypt


@pytest.fixture
def temp_users_file(tmp_path):
    users_path = str(tmp_path / "users.json")
    with patch("auth.user_auth.USERS_PATH", users_path):
        yield users_path


class TestBcryptHashing:
    def test_register_and_verify(self, temp_users_file):
        from auth.user_auth import register_user, verify_user
        register_user("13800000001", "password123")
        assert verify_user("13800000001", "password123") is True

    def test_wrong_password_rejected(self, temp_users_file):
        from auth.user_auth import register_user, verify_user
        register_user("13800000002", "password123")
        assert verify_user("13800000002", "wrongpassword") is False

    def test_nonexistent_user(self, temp_users_file):
        from auth.user_auth import verify_user
        assert verify_user("99999999999", "password") is False

    def test_password_is_bcrypt_format(self, temp_users_file):
        from auth.user_auth import register_user, _load_users
        register_user("13800000003", "mypassword")
        users = _load_users()
        stored = users["13800000003"]["password"]
        assert stored.startswith("$2")

    def test_duplicate_registration_rejected(self, temp_users_file):
        from auth.user_auth import register_user
        assert register_user("13800000004", "pass1") is True
        assert register_user("13800000004", "pass2") is False


class TestLegacyMigration:
    def test_sha256_user_auto_migrates(self, temp_users_file):
        """Simulate a user with old SHA-256 hash, verify they can log in and hash gets upgraded."""
        import hashlib
        from auth.user_auth import verify_user, _load_users

        phone = "13800000099"
        password = "oldpassword"
        old_hash = hashlib.sha256(password.encode()).hexdigest()

        # Write a users.json with the old SHA-256 format
        with open(temp_users_file, "w") as f:
            json.dump({phone: {"password": old_hash}}, f)

        # Should still be able to verify
        assert verify_user(phone, password) is True

        # After successful login, the hash should be upgraded to bcrypt
        users = _load_users()
        assert users[phone]["password"].startswith("$2")

    def test_sha256_user_wrong_password(self, temp_users_file):
        """Old SHA-256 user with wrong password should be rejected."""
        import hashlib
        from auth.user_auth import verify_user

        phone = "13800000098"
        old_hash = hashlib.sha256("correctpassword".encode()).hexdigest()
        with open(temp_users_file, "w") as f:
            json.dump({phone: {"password": old_hash}}, f)

        assert verify_user(phone, "wrongpassword") is False


class TestPasswordReset:
    def test_reset_password(self, temp_users_file):
        from auth.user_auth import register_user, verify_user, reset_password
        register_user("13800000005", "oldpass")
        reset_password("13800000005", "newpass")
        assert verify_user("13800000005", "oldpass") is False
        assert verify_user("13800000005", "newpass") is True

    def test_reset_nonexistent_user(self, temp_users_file):
        from auth.user_auth import reset_password
        assert reset_password("99999999999", "newpass") is False
