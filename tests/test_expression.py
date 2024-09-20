import sys
import os
import unittest
import datetime
from pyinterval import Expression
from dateutil.relativedelta import relativedelta


class TestExpression(unittest.TestCase):
    def setUp(self):
        """Sets up a base datetime for use in tests."""
        self.base_dt = datetime.datetime(2024, 1, 1, 0, 0, 0)
        self.unit_types_descending = [
            "decade",
            "year",
            "quarter",
            "month",
            "week",
            "day",
            "hour",
            "minute",
            "second",
            "decisecond",
            "centisecond",
            "millisecond",
            "microsecond",
        ]

    def test_init_with_root_datetime(self):
        """Test the initialization of an Expression with a root datetime."""
        expr = Expression(self.base_dt)
        self.assertTrue(expr.is_root)
        self.assertEqual(expr.datetime, self.base_dt)

    def test_all_unit_types_descending(self):
        """Test if all unit types can be chained without errors."""
        root_part = Expression()
        # One level deep
        for i, unit in enumerate(self.unit_types_descending):
            scope_part = getattr(root_part, unit)
            # Two levels deep
            for j, _unit in enumerate(self.unit_types_descending[i + 1 :]):
                unit_part = getattr(scope_part, _unit)
                # Three levels deep
                for __unit in self.unit_types_descending[j + i + 2 :]:
                    getattr(unit_part[0], __unit)

    def test_root_datetime(self):
        """Test the initialization of an Expression without a root datetime."""
        exp = Expression()
        based_expr = Expression(self.base_dt)

        self.assertTrue(based_expr.is_root)
        self.assertEqual(based_expr.datetime, self.base_dt)
        self.assertIsNone(exp.datetime)

        # Lazily evaluate the day before the base datetime
        day_before = based_expr.day - based_expr.day.n(1)
        day_before_base = day_before(self.base_dt)

        expected_date = self.base_dt - datetime.timedelta(days=1)
        self.assertEqual(day_before_base, expected_date)

    def test_unit_type_recognition(self):
        """Test that each part of an expression chain is correctly identified for its role."""
        expr = Expression()

        self.assertTrue(expr.is_root)
        self.assertFalse(expr.is_scope)
        self.assertFalse(expr.is_unit)

        # Recognize units as scope after root, and then units themselves
        for i, unit in enumerate(self.unit_types_descending):
            scope_part = getattr(expr, unit)
            self.assertFalse(scope_part.is_root)
            self.assertTrue(scope_part.is_scope)
            self.assertFalse(scope_part.is_unit)

            # Assert that its parent is the root
            self.assertTrue(scope_part.parent.is_root)

            for _unit in self.unit_types_descending[i + 1 :]:
                unit_part = getattr(scope_part, _unit)
                self.assertFalse(unit_part.is_root)
                self.assertFalse(unit_part.is_scope)
                self.assertTrue(unit_part.is_unit)

                # Assert that its parent is the scope
                self.assertTrue(unit_part.parent.is_scope)

    def test_expression_indexing(self):
        """Test indexing of different units."""
        expr = Expression()

        # Test one level deep
        for n in range(0, 12):
            result_expr = expr.year.month[n]
            self.assertEqual(result_expr.index, n)

            # Test two levels deep
            for n in range(0, 6):
                _result_expr = result_expr.week[n]
                self.assertEqual(_result_expr.index, n)

    def test_lazy_validation(self):
        """Test lazily validating indexes and ensuring correct boundaries."""
        expr = Expression()

        for i, unit in enumerate(self.unit_types_descending):
            scope = getattr(expr, unit)
            for _unit in self.unit_types_descending[i + 1 :]:
                new_expr = getattr(scope, _unit)
                max_index = new_expr.get_max_index()
                try:
                    new_expr[max_index + 1]
                except ValueError:
                    pass
                else:
                    self.fail(
                        f"{unit} should not accept an index larger than {max_index}."
                    )

    def test_negative_indexing(self):
        """Test negative indexing for units like last day of the month or week."""
        expr = Expression()
        last_day_of_month = expr.month.day[-1]
        last_day_of_current_month = last_day_of_month(self.base_dt)

        expected_last_day = datetime.datetime(2024, 1, 31)
        self.assertEqual(last_day_of_current_month, expected_last_day)

        # Test leap year (Feb 29th)
        feb_2020 = datetime.datetime(2020, 2, 1)
        last_day_of_feb = expr.month.day[-1](feb_2020)
        self.assertEqual(last_day_of_feb, datetime.datetime(2020, 2, 29))

        # Test non-leap year (Feb 28th)
        feb_2019 = datetime.datetime(2019, 2, 1)
        last_day_of_feb_2019 = expr.month.day[-1](feb_2019)
        self.assertEqual(last_day_of_feb_2019, datetime.datetime(2019, 2, 28))

    def test_expression_addition_lazy_eval(self):
        """Test adding a relative delta to an Expression and ensuring lazy evaluation."""
        expr = Expression().year
        delta = relativedelta(years=2)
        new_expr = expr + delta

        expected_dt = datetime.datetime(2026, 1, 1)
        result_dt = new_expr(datetime.datetime(2024, 12, 25))

        self.assertEqual(result_dt, expected_dt)

    def test_expression_subtraction_lazy_eval(self):
        """Test subtracting a relative delta from an Expression."""
        expr = Expression()
        some_date = datetime.datetime(2024, 1, 1)

        two_years_before_expr = expr.year - expr.year.n(2)

        expected_dt = datetime.datetime(2022, 1, 1)
        result_dt = two_years_before_expr(some_date)

        self.assertEqual(result_dt, expected_dt)

    def test_evaluation_with_rollover(self):
        """Test evaluating an expression with rollover enabled."""
        expr = Expression().month.day[29]
        feb_date = datetime.datetime(2024, 2, 1)

        # Rollover allows going past valid days in February
        result_dt = expr(feb_date)
        expected_dt = datetime.datetime(2024, 3, 1)  # Rolls into March
        self.assertEqual(result_dt, expected_dt)

    def test_evaluation_without_rollover(self):
        """Test evaluating an expression without rollover."""
        expr = Expression(self.base_dt).month.day[30]
        feb_date = datetime.datetime(2024, 2, 1)

        # Without rollover, should raise an error for invalid day in February
        with self.assertRaises(IndexError):
            expr(feb_date, rollover=False)

    def test_yesterday(self):
        """Test that the day before a provided date is correctly evaluated."""
        expr = Expression()
        yesterday_expr = expr.day - expr.day.n(1)
        yesterday = yesterday_expr(self.base_dt)

        expected_date = self.base_dt - datetime.timedelta(days=1)
        self.assertEqual(yesterday, expected_date)

    def test_order_of_operations_complex_example(self):
        """Test a complex example with multiple operations and deltas."""
        expr = Expression()
        some_date = datetime.datetime(2024, 1, 1)

        # Create a holiday date chain
        holiday_expr = expr.year.month[-1].day[24].hour[7]
        holiday_date = holiday_expr(some_date)
        holiday_date_expectation = datetime.datetime(2024, 12, 25, 8)

        # Test date result after evaluation
        self.assertEqual(holiday_date, holiday_date_expectation)

        # Some date relative to that
        some_other_expr = holiday_expr + expr.day.n(1) - expr.month.n(1)
        some_other_date = some_other_expr(some_date)
        some_other_date_expectation = datetime.datetime(2024, 11, 26, 8)

        # Test adding more lazy evaluated operations
        self.assertEqual(some_other_date, some_other_date_expectation)

        # Check that holiday was not modified
        self.assertFalse(holiday_expr.operations_delta)
        self.assertTrue(some_other_expr.operations_delta)

        # Test more complex operations with finer granularity
        final_complex_expr = (
            (
                expr.year.month[1].day[27]  # Feb 28th, n year
                + expr.day.n(1)  # Feb 29th
                - expr.month.n(1)  # Jan 29th
            )
            .minute[5]
            .second[4]
            .decisecond[-2]
            .millisecond[5]
            .microsecond[-1]
        )

        final_complex_date = final_complex_expr(some_date)
        final_complex_date_expectation = datetime.datetime(2024, 1, 29, 0, 6, 5, 806999)
        self.assertEqual(final_complex_date, final_complex_date_expectation)


if __name__ == "__main__":
    unittest.main()
    # Add tests that make sure abstract time units correctly reset scope.
    # Add tests for rollover, operations_safe, and chaining negative indexes.
    # Add tests that try rollover=False while parent index is same, because "grand-parent" index incremented.
