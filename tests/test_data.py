import unittest
from pathlib import Path
from scripts.build_data_sql import rows


class SourceDataTests(unittest.TestCase):
    def test_source_counts(self):
        self.assertEqual(len(rows('Products')), 31)
        self.assertEqual(len(rows('Sizes')), 35)
        self.assertEqual(len(rows('Stock_Items')), 92)
        self.assertEqual(len(rows('Users')), 20)
        self.assertEqual(len(rows('Orders')), 30)

    def test_no_stock_is_lost(self):
        sql = (Path(__file__).resolve().parents[1] / 'db' / 'data.sql').read_text()
        self.assertEqual(sql.count('INSERT INTO stock_items '), 92)
        self.assertEqual(sql.count('INSERT INTO products '), 34)
        self.assertEqual(sql.count('INSERT INTO order_items '), 30)
        self.assertEqual(sql.count('INSERT INTO orders '), 10)

    def test_half_sizes_preserved(self):
        sql = (Path(__file__).resolve().parents[1] / 'db' / 'data.sql').read_text()
        self.assertIn('36.5', sql)


if __name__ == '__main__':
    unittest.main()
