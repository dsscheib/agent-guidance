import unittest

from app.db import connect, migrate
from app.users import create_user, get_user


class UserTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")
        migrate(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_create_and_get(self):
        user_id = create_user(self.conn, "Ada", "2026-01-01T00:00:00Z")
        self.assertEqual(get_user(self.conn, user_id)["name"], "Ada")

    def test_migrate_is_idempotent(self):
        migrate(self.conn)
        versions = [row[0] for row in self.conn.execute("SELECT version FROM schema_migrations")]
        self.assertEqual(versions, ["0001_create_users"])


if __name__ == "__main__":
    unittest.main()
