import unittest
from datetime import datetime
from decimal import Decimal

from app import calculate_earned, count_month_workdays, is_workday, validate_settings


class ValidateSettingsTests(unittest.TestCase):
    def test_valid_settings_are_normalized(self):
        settings = validate_settings(
            {
                "monthly_salary": "10000",
                "working_days": "22",
                "paid_hours": "8.0",
                "start_time": "09:00",
            }
        )
        self.assertEqual(settings["monthly_salary"], "10000")
        self.assertEqual(settings["paid_hours"], "8.0")

    def test_invalid_settings_are_rejected(self):
        invalid = [
            {"monthly_salary": "0", "paid_hours": "8", "start_time": "09:00"},
            {"monthly_salary": "10000", "paid_hours": "25", "start_time": "09:00"},
            {"monthly_salary": "10000", "paid_hours": "8", "start_time": "24:00"},
        ]
        for settings in invalid:
            with self.subTest(settings=settings), self.assertRaises((ValueError, ArithmeticError)):
                validate_settings(settings)


class CalculateEarnedTests(unittest.TestCase):
    def test_before_start_is_zero(self):
        result = calculate_earned("10000", "22", "8", "09:00", datetime(2026, 10, 9, 8, 59))
        self.assertEqual(result, Decimal("0.00"))

    def test_half_day_is_half_daily_pay_to_the_cent(self):
        result = calculate_earned("10000", "22", "8", "09:00", datetime(2026, 10, 9, 13, 0))
        self.assertEqual(result, Decimal("227.27"))

    def test_amount_is_capped_at_daily_pay(self):
        result = calculate_earned("10000", "22", "8", "09:00", datetime(2026, 10, 9, 18, 0))
        self.assertEqual(result, Decimal("454.55"))

    def test_rounds_to_cents(self):
        result = calculate_earned("10000", "22", "8", "09:00", datetime(2026, 10, 9, 9, 1))
        self.assertEqual(result, Decimal("0.95"))

    def test_non_workday_has_no_accrued_pay(self):
        result = calculate_earned(
            "10000", "18", "8", "09:00", datetime(2026, 10, 3, 12, 0), workday=False
        )
        self.assertEqual(result, Decimal("0.00"))


class ChinaWorkCalendarTests(unittest.TestCase):
    def test_2026_monthly_workday_counts_follow_official_schedule(self):
        expected = {
            1: 21,
            2: 16,
            3: 22,
            4: 21,
            5: 19,
            6: 21,
            7: 23,
            8: 21,
            9: 22,
            10: 18,
            11: 21,
            12: 23,
        }
        for month, days in expected.items():
            with self.subTest(month=month):
                self.assertEqual(count_month_workdays(2026, month), days)

    def test_holidays_and_makeup_days_override_weekday_rules(self):
        self.assertFalse(is_workday(datetime(2026, 10, 1).date()))
        self.assertTrue(is_workday(datetime(2026, 10, 10).date()))
        self.assertTrue(is_workday(datetime(2026, 9, 20).date()))
        self.assertFalse(is_workday(datetime(2026, 10, 11).date()))

    def test_unknown_year_falls_back_to_weekdays(self):
        self.assertEqual(count_month_workdays(2027, 1), 21)


if __name__ == "__main__":
    unittest.main()
