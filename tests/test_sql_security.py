import pytest
from agents.sql_agent import _validate_sql


class TestSqlValidation:
    def test_select_allowed(self):
        _validate_sql("SELECT product, quantity FROM sales")

    def test_select_with_where(self):
        _validate_sql("SELECT * FROM sales WHERE region = '华北'")

    def test_select_with_join(self):
        _validate_sql("SELECT a.product FROM sales a JOIN sales b ON a.product = b.product")

    def test_select_with_subquery(self):
        _validate_sql("SELECT * FROM sales WHERE quantity > (SELECT AVG(quantity) FROM sales)")

    def test_drop_rejected(self):
        with pytest.raises(ValueError, match="只允许 SELECT"):
            _validate_sql("DROP TABLE sales")

    def test_delete_rejected(self):
        with pytest.raises(ValueError, match="只允许 SELECT"):
            _validate_sql("DELETE FROM sales WHERE 1=1")

    def test_insert_rejected(self):
        with pytest.raises(ValueError, match="只允许 SELECT"):
            _validate_sql("INSERT INTO sales VALUES ('hack', 999, 999, 999, '华北', '2024-01')")

    def test_update_rejected(self):
        with pytest.raises(ValueError, match="只允许 SELECT"):
            _validate_sql("UPDATE sales SET quantity = 0")

    def test_attach_rejected(self):
        with pytest.raises(ValueError, match="只允许 SELECT"):
            _validate_sql("ATTACH DATABASE '/etc/passwd' AS p")

    def test_union_rejected(self):
        with pytest.raises(ValueError, match="禁止"):
            _validate_sql("SELECT * FROM sales UNION SELECT * FROM other")

    def test_pragma_rejected(self):
        with pytest.raises(ValueError, match="只允许 SELECT"):
            _validate_sql("PRAGMA table_info(sales)")

    def test_semicolon_harmless(self):
        _validate_sql("SELECT 1;")

    def test_case_insensitive(self):
        with pytest.raises(ValueError):
            _validate_sql("drop table sales")
