import unittest
import sqlite3
import os
from datetime import date, timedelta, datetime

# Modules to be tested
import database_operations
import database_setup # Import the module itself
from database_setup import create_table

class TestDatabaseOperations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Store original DB_FILE paths and override for testing
        cls.original_ops_db_file = database_operations.DB_FILE
        cls.original_setup_db_file = database_setup.SETUP_DB_FILE # Store original from database_setup

        cls.test_db_file = "test_allergy_tracker.db"

        database_operations.DB_FILE = cls.test_db_file
        database_setup.SETUP_DB_FILE = cls.test_db_file # Override for database_setup

    @classmethod
    def tearDownClass(cls):
        # Restore original DB_FILE paths
        database_operations.DB_FILE = cls.original_ops_db_file
        database_setup.SETUP_DB_FILE = cls.original_setup_db_file # Restore for database_setup

    def setUp(self):
        # Ensure a clean database for each test method
        if os.path.exists(self.test_db_file): # self.test_db_file is defined in setUpClass
            os.remove(self.test_db_file)

        # Create the schema in the test database
        # create_table() will now use the overridden database_setup.SETUP_DB_FILE
        create_table()

        # Common test data
        self.extract1_data = {
            "name": "Test Pollen A", "batch_number": "TPA001", "expiry_date": (date.today() + timedelta(days=100)).isoformat(),
            "quantity_on_hand": 50, "storage_location": "Fridge 1", "supplier_details": "Supplier X",
            "date_received": date.today().isoformat(), "notes": "Test note A"
        }
        self.extract2_data = {
            "name": "Test Dander B", "batch_number": "TDB002", "expiry_date": (date.today() + timedelta(days=20)).isoformat(),
            "quantity_on_hand": 5, "storage_location": "Fridge 2", "supplier_details": "Supplier Y",
            "date_received": (date.today() - timedelta(days=10)).isoformat(), "notes": "Test note B"
        }

    def tearDown(self):
        # Clean up the test database file after each test
        if os.path.exists(self.test_db_file):
            os.remove(self.test_db_file)

    # --- Helper to convert Row objects to dictionaries for easier comparison ---
    def _row_to_dict(self, row):
        if row is None:
            return None
        return dict(zip(row.keys(), row))

    def _rows_to_dicts(self, rows):
        return [self._row_to_dict(row) for row in rows]

    # --- Test Methods for CRUD Operations ---
    def test_add_and_get_extract(self):
        # Add an extract
        added_id = database_operations.add_extract(**self.extract1_data)
        self.assertIsNotNone(added_id, "add_extract should return an ID.")
        self.assertIsInstance(added_id, int)

        # Retrieve it by ID
        retrieved_extract_row = database_operations.get_extract_by_id(added_id)
        self.assertIsNotNone(retrieved_extract_row, "get_extract_by_id should retrieve the added extract.")
        retrieved_extract = self._row_to_dict(retrieved_extract_row)

        # Assert data matches (excluding 'id' as it's auto-generated)
        for key, value in self.extract1_data.items():
            self.assertEqual(retrieved_extract[key], value, f"Mismatch for {key}")

        # Check get_all_extracts
        all_extracts = database_operations.get_all_extracts()
        self.assertEqual(len(all_extracts), 1)
        self.assertEqual(self._row_to_dict(all_extracts[0])['name'], self.extract1_data['name'])

    def test_update_extract(self):
        added_id = database_operations.add_extract(**self.extract1_data)

        update_data = {
            "name": "Updated Pollen Name",
            "quantity_on_hand": 75,
            "notes": "Updated note"
        }
        # Merge update_data with original data, keeping other fields same
        full_update_data = self.extract1_data.copy()
        full_update_data.update(update_data)

        success = database_operations.update_extract(added_id, **full_update_data)
        self.assertTrue(success, "update_extract should return True on success.")

        retrieved_extract = self._row_to_dict(database_operations.get_extract_by_id(added_id))
        self.assertEqual(retrieved_extract['name'], update_data['name'])
        self.assertEqual(retrieved_extract['quantity_on_hand'], update_data['quantity_on_hand'])
        self.assertEqual(retrieved_extract['notes'], update_data['notes'])
        self.assertEqual(retrieved_extract['batch_number'], self.extract1_data['batch_number']) # Check unchanged field

    def test_delete_extract(self):
        added_id = database_operations.add_extract(**self.extract1_data)
        self.assertIsNotNone(database_operations.get_extract_by_id(added_id))

        success = database_operations.delete_extract(added_id)
        self.assertTrue(success, "delete_extract should return True on success.")
        self.assertIsNone(database_operations.get_extract_by_id(added_id), "Extract should be None after deletion.")

        all_extracts = database_operations.get_all_extracts()
        self.assertEqual(len(all_extracts), 0, "No extracts should remain after deletion.")

    def test_get_extract_non_existent(self):
        retrieved_extract = database_operations.get_extract_by_id(9999) # Assuming 9999 does not exist
        self.assertIsNone(retrieved_extract, "Getting a non-existent extract should return None.")

    # --- Test Methods for Inventory Management Functions ---
    def test_update_stock_quantity(self):
        added_id = database_operations.add_extract(**self.extract1_data) # initial qty: 50

        # Test receiving stock
        success, new_qty = database_operations.update_stock_quantity(added_id, 25) # 50 + 25 = 75
        self.assertTrue(success)
        self.assertEqual(new_qty, 75)
        self.assertEqual(self._row_to_dict(database_operations.get_extract_by_id(added_id))['quantity_on_hand'], 75)

        # Test dispensing stock
        success, new_qty = database_operations.update_stock_quantity(added_id, -15) # 75 - 15 = 60
        self.assertTrue(success)
        self.assertEqual(new_qty, 60)
        self.assertEqual(self._row_to_dict(database_operations.get_extract_by_id(added_id))['quantity_on_hand'], 60)

        # Test dispensing more than available
        current_qty_before_fail = self._row_to_dict(database_operations.get_extract_by_id(added_id))['quantity_on_hand']
        success, qty_after_fail = database_operations.update_stock_quantity(added_id, -100) # Try to dispense 100 from 60
        self.assertFalse(success, "Should fail when dispensing more than available.")
        self.assertEqual(qty_after_fail, current_qty_before_fail, "Quantity should remain unchanged on failure.")
        self.assertEqual(self._row_to_dict(database_operations.get_extract_by_id(added_id))['quantity_on_hand'], current_qty_before_fail)

        # Test with non-existent ID
        success, qty = database_operations.update_stock_quantity(9999, 10)
        self.assertFalse(success)
        self.assertEqual(qty, 0) # Per function spec, current_quantity is 0 if ID not found for return

    def test_get_extracts_nearing_expiry(self):
        # Add test data for expiry
        today = date.today()
        database_operations.add_extract("ExpiredItem", "EXP01", (today - timedelta(days=10)).isoformat(), 10, "Loc", "Sup", today.isoformat(), "")
        id_exp_soon = database_operations.add_extract("ExpiringSoon", "EXP02", (today + timedelta(days=15)).isoformat(), 10, "Loc", "Sup", today.isoformat(), "") # Within 30 days
        id_exp_later = database_operations.add_extract("ExpiringLater", "EXP03", (today + timedelta(days=45)).isoformat(), 10, "Loc", "Sup", today.isoformat(), "") # Outside 30 days
        database_operations.add_extract("NoExpiryDate", "NULLEXP", None, 10, "Loc", "Sup", today.isoformat(), "")
        id_exp_edge = database_operations.add_extract("ExpiringEdge", "EXP04", (today + timedelta(days=30)).isoformat(), 10, "Loc", "Sup", today.isoformat(), "") # Exactly 30 days

        # Test with default threshold (30 days)
        nearing_expiry = self._rows_to_dicts(database_operations.get_extracts_nearing_expiry())
        self.assertEqual(len(nearing_expiry), 2) # ExpiringSoon, ExpiringEdge
        retrieved_ids = sorted([d['id'] for d in nearing_expiry])
        self.assertListEqual(retrieved_ids, sorted([id_exp_soon, id_exp_edge]))

        # Test with different threshold (e.g., 20 days)
        nearing_expiry_20 = self._rows_to_dicts(database_operations.get_extracts_nearing_expiry(days_threshold=20))
        self.assertEqual(len(nearing_expiry_20), 1)
        self.assertEqual(nearing_expiry_20[0]['id'], id_exp_soon)

        # Test with threshold that includes none of the future-dated ones
        nearing_expiry_5 = self._rows_to_dicts(database_operations.get_extracts_nearing_expiry(days_threshold=5))
        self.assertEqual(len(nearing_expiry_5), 0)

    def test_get_extracts_low_stock(self):
        # Add test data for stock levels
        id_low1 = database_operations.add_extract("LowStockItem1", "LS01", date.today().isoformat(), 5, "Loc", "Sup", date.today().isoformat(), "") # At/Below 10
        id_exact = database_operations.add_extract("ExactStockItem", "LS02", date.today().isoformat(), 10, "Loc", "Sup", date.today().isoformat(), "") # At/Below 10
        id_high = database_operations.add_extract("HighStockItem", "LS03", date.today().isoformat(), 25, "Loc", "Sup", date.today().isoformat(), "") # Above 10
        id_low2 = database_operations.add_extract("LowStockItem2", "LS04", date.today().isoformat(), 2, "Loc", "Sup", date.today().isoformat(), "") # At/Below 5

        # Test with default threshold (10 units)
        low_stock = self._rows_to_dicts(database_operations.get_extracts_low_stock())
        # Order by quantity_on_hand ASC
        self.assertEqual(len(low_stock), 3)
        retrieved_ids = [d['id'] for d in low_stock] # Already sorted by qty by the function
        self.assertListEqual(retrieved_ids, [id_low2, id_low1, id_exact])


        # Test with different threshold (e.g., 5 units)
        low_stock_5 = self._rows_to_dicts(database_operations.get_extracts_low_stock(quantity_threshold=5))
        self.assertEqual(len(low_stock_5), 2)
        retrieved_ids_5 = [d['id'] for d in low_stock_5]
        self.assertListEqual(retrieved_ids_5, [id_low2, id_low1])

        # Test with threshold that includes all items
        low_stock_30 = self._rows_to_dicts(database_operations.get_extracts_low_stock(quantity_threshold=30))
        self.assertEqual(len(low_stock_30), 4)


if __name__ == '__main__':
    unittest.main()
