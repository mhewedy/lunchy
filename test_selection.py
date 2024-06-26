import logging
import unittest

from selection import UserSelector


class TestUserSelector(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.INFO)

    def test_select_from_list_with_duplicates(self):
        selector = UserSelector()
        users = ["Alice", "Bob", "Charlie", "Alice"]  # With duplicates
        selected = selector.select(users)
        self.assertIn(selected, users)

    def test_select_from_list_without_duplicates(self):
        selector = UserSelector()
        users = ["Alice", "Bob", "Charlie", "Diana"]  # Without duplicates
        selected = selector.select(users)
        self.assertIn(selected, users)

    def test_select_empty_list(self):
        selector = UserSelector()
        with self.assertRaises(ValueError):
            selector.select([])

    def test_select_single_user(self):
        selector = UserSelector()
        users = ["Alice"]
        selected = selector.select(users)
        self.assertEqual(selected, "Alice")

    def test_select_non_excluded_from_2_users_with_2_selection_gap(self):
        selector = UserSelector(exclude_gap=2)
        users = ["Alice", "Bob", "Bob", "Bob", "Bob"]
        selector.history_manager.history = ["Alice", "Bob", "Alice"]

        expected_selections = ["Bob", "Alice", "Bob", "Alice"]
        for expected_selection in expected_selections:
            selected = selector.select(users)
            self.assertEqual(selected, expected_selection)

    def test_select_non_excluded_3_users_with_2_selection_gap(self):
        selector = UserSelector(exclude_gap=2)
        users = ["Alice", "Alice", "Bob", "Bob", "Charlie", "Charlie", "Charlie"]
        selector.history_manager.history = ["Alice", "Bob", "Charlie"]

        expected_selections = ["Alice", "Bob", "Charlie", "Alice", "Bob", "Charlie"]
        for expected_selection in expected_selections:
            selected = selector.select(users)
            self.assertEqual(selected, expected_selection)

    def test_select_non_excluded_from_2_users_with_0_selection_gap(self):
        selector = UserSelector(exclude_gap=0)
        users = ["Alice", "Bob", "Bob", "Bob", "Bob"]
        selector.history_manager.history = ["Alice", "Bob", "Alice"]

        selected = selector.select(users)
        self.assertIn(selected, ["Alice", "Bob"])

    def test_select_non_excluded_3_users_with_0_selection_gap__(self):
        count = 0
        for _ in range(0, 100):
            selector = UserSelector(exclude_gap=0)
            users = ["Alice", "Alice", "Bob", "Bob", "Charlie", "Charlie", "Charlie"]
            selector.history_manager.history = ["Alice", "Bob", "Charlie"]
            selected = selector.select(users)
            if selected in ["Bob", "Charlie"]:
                count += 1

        self.assertGreater(count, 0)

    def test_select_non_excluded_3_users_with_1_selection_gap__(self):
        count = 0
        for _ in range(0, 100):
            selector = UserSelector(exclude_gap=2)
            users = ["Alice", "Alice", "Bob", "Bob", "Charlie", "Charlie", "Charlie"]
            selector.history_manager.history = ["Alice", "Bob", "Charlie"]
            selected = selector.select(users)
            if selected in ["Charlie"]:
                count += 1

        self.assertEqual(count, 0)

    def test_select_non_excluded_3_users_with_2_selection_gap__(self):
        count = 0
        for _ in range(0, 100):
            selector = UserSelector(exclude_gap=2)
            users = ["Alice", "Alice", "Bob", "Bob", "Charlie", "Charlie", "Charlie"]
            selector.history_manager.history = ["Alice", "Bob", "Charlie"]
            selected = selector.select(users)
            if selected in ["Bob", "Charlie"]:
                count += 1

        self.assertEqual(count, 0)

    def test_select_non_excluded_3_users_with_3_selection_gap__(self):
        count = 0
        for _ in range(0, 100):
            selector = UserSelector(exclude_gap=3)
            users = ["Alice", "Alice", "Bob", "Bob", "Charlie", "Charlie", "Charlie", "Dave"]
            selector.history_manager.history = ["Alice", "Bob", "Charlie"]
            selected = selector.select(users)
            if selected in ["Alice", "Bob", "Charlie"]:
                count += 1

        self.assertEqual(count, 0)

    def test_select_non_excluded_3_users_with_ids(self):
        selector = UserSelector(exclude_gap=2)
        users = [(1, "Alice"), (1, "Alice"), (2, "Bob"), (2, "Bob"), (3, "Charlie"), (3, "Charlie"), (3, "Charlie")]
        selector.history_manager.history = [(1, "Alice"), (2, "Bob"), (3, "Charlie")]

        expected_selections = [(1, "Alice"), (2, "Bob"), (3, "Charlie"), (1, "Alice"), (2, "Bob"), (3, "Charlie")]
        for expected_selection in expected_selections:
            selected = selector.select(users)
            self.assertEqual(selected, expected_selection)

    def test_select_never_picks_last_n_from_history(self):
        for _ in range(100):
            selector = UserSelector(exclude_gap=2)
            users = \
                ["Alice", "Alice", "Bob", "Bob", "Charlie", "Charlie", "Charlie", "Diana", "Diana", "David", "David"]
            selector.history_manager.history = ["Alice", "Bob", "Charlie", "Diana"]
            selected = selector.select(users)
            self.assertIn(selected, ["Alice", "Bob", "David"])

    def test_history_maintenance(self):
        selector = UserSelector(exclude_gap=2)
        users = ["Alice", "Bob", "Charlie", "Diana"]
        selections = []
        for _ in range(100):
            selected = selector.select(users)
            selections.append(selected)
        self.assertEqual(selector.history_manager.history, selections[-10:])


if __name__ == "__main__":
    unittest.main()
