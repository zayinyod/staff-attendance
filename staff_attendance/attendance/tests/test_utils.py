"""
ユーティリティクラスのユニットテスト。
DB 接続が不要なため SimpleTestCase を使用。
"""
from django.test import SimpleTestCase
from datetime import datetime, time
from util.id_generator import IDGenerator
from util.round_calc import RoundCalculate
from util.now import Now


class TestIDGenerator(SimpleTestCase):
    def test_length_is_six(self):
        self.assertEqual(len(IDGenerator.create_id()), 6)

    def test_returns_string(self):
        self.assertIsInstance(IDGenerator.create_id(), str)

    def test_randomness(self):
        """50 回生成してほぼ全てユニークであること（確率的テスト）"""
        ids = {IDGenerator.create_id() for _ in range(50)}
        self.assertGreater(len(ids), 45)

    def test_contains_digits_only(self):
        """要件の「6 桁」に従い数字のみで構成されること"""
        for _ in range(50):
            self.assertTrue(IDGenerator.create_id().isdecimal())


class TestRoundCalculate(SimpleTestCase):
    def setUp(self):
        self.calc = RoundCalculate()
        self._base = datetime(2024, 4, 1)

    def _dt(self, h, m, s=0):
        return self._base.replace(hour=h, minute=m, second=s)

    # --- truncate_to_minutes ---

    def test_truncate_removes_seconds(self):
        result = self.calc.truncate_to_minutes(self._dt(9, 7, 45))
        self.assertEqual(result, self._dt(9, 7, 0))

    def test_truncate_preserves_exact_minute(self):
        dt = self._dt(9, 0, 0)
        self.assertEqual(self.calc.truncate_to_minutes(dt), dt)

    # --- round_up_hours (15 分単位切り上げ) ---

    def test_round_up_on_boundary(self):
        """15 分境界はそのまま"""
        result = self.calc.round_up_hours(self._dt(9, 0, 0))
        self.assertEqual(result.hour, 9)
        self.assertEqual(result.minute, 0)

    def test_round_up_off_boundary(self):
        """9:07 → 9:15"""
        result = self.calc.round_up_hours(self._dt(9, 7, 0))
        self.assertEqual(result.hour, 9)
        self.assertEqual(result.minute, 15)

    def test_round_up_one_minute_past_boundary(self):
        """9:01 → 9:15"""
        result = self.calc.round_up_hours(self._dt(9, 1, 0))
        self.assertEqual(result.hour, 9)
        self.assertEqual(result.minute, 15)

    def test_round_up_preserves_date(self):
        dt = self._dt(9, 7, 0)
        self.assertEqual(self.calc.round_up_hours(dt).date(), dt.date())

    # --- round_down_hours (15 分単位切り捨て) ---

    def test_round_down_on_boundary(self):
        """18:00 はそのまま"""
        result = self.calc.round_down_hours(self._dt(18, 0, 0))
        self.assertEqual(result.hour, 18)
        self.assertEqual(result.minute, 0)

    def test_round_down_off_boundary(self):
        """17:57 → 17:45"""
        result = self.calc.round_down_hours(self._dt(17, 57, 0))
        self.assertEqual(result.hour, 17)
        self.assertEqual(result.minute, 45)

    def test_round_down_one_minute_before_boundary(self):
        """17:59 → 17:45"""
        result = self.calc.round_down_hours(self._dt(17, 59, 0))
        self.assertEqual(result.hour, 17)
        self.assertEqual(result.minute, 45)

    def test_round_down_preserves_date(self):
        dt = self._dt(17, 57, 0)
        self.assertEqual(self.calc.round_down_hours(dt).date(), dt.date())


class TestNow(SimpleTestCase):
    def test_date_str_format(self):
        """YYYY-MM-DD 形式"""
        self.assertEqual(Now.date_str(datetime(2024, 1, 15)), "2024-01-15")

    def test_date_str_zero_padding(self):
        """月日はゼロパディング"""
        self.assertEqual(Now.date_str(datetime(2024, 3, 5)), "2024-03-05")

    def test_time_str_format(self):
        """HH:MM 形式"""
        self.assertEqual(Now.time_str(time(9, 30)), "09:30")

    def test_time_str_zero_padding(self):
        """時分はゼロパディング"""
        self.assertEqual(Now.time_str(time(8, 5)), "08:05")
