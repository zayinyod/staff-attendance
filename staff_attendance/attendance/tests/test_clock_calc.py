"""
打刻計算ロジック (ClockCalculate) のビジネスロジックテスト。

ClockRepository のクラスレベル DB クエリ問題を修正済みのため、
通常どおりトップレベルでインポートできる。
各テストでは ClockRepository をモック化して計算ロジックのみを検証する。
"""
from django.test import TestCase
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from staff_attendance.clock.usecases.clock_calc import ClockCalculate


class TestClockCalculate(TestCase):

    def setUp(self):
        """各テスト前にリポジトリをモック化してクリーンな状態にする"""
        self._original_repo = ClockCalculate.clock_repository
        self.mock_repo = MagicMock()
        ClockCalculate.clock_repository = self.mock_repo

    def tearDown(self):
        """テスト後にリポジトリを元に戻して後続テストへの影響を防ぐ"""
        ClockCalculate.clock_repository = self._original_repo

    # ------------------------------------------------------------------ helpers

    def _make_record(self, date_str, time_str, break_time=Decimal("1.00")):
        """打刻レコードを模倣する MagicMock を生成する"""
        record = MagicMock()
        record.date_stamp = datetime.strptime(date_str, "%Y-%m-%d").date()
        record.time_stamp = datetime.strptime(time_str, "%H:%M").time()
        record.break_time = break_time
        return record

    def _set_clocks(self, in_time=None, out_time=None,
                    break_time=Decimal("1.00"), date_str="2024-04-01"):
        in_clock = self._make_record(date_str, in_time, break_time) if in_time else None
        out_clock = self._make_record(date_str, out_time, break_time) if out_time else None
        self.mock_repo.get_clock.return_value = {
            "in_clock": in_clock,
            "out_clock": out_clock,
        }

    # -------------------------------------------------------- get_base_datetime

    def test_base_datetime_no_records(self):
        """打刻レコードなし → in/out が None で返ること"""
        self._set_clocks()
        result = ClockCalculate.get_base_datetime(None, date(2024, 4, 1))
        self.assertIsNone(result["in_datetime"])
        self.assertIsNone(result["out_datetime"])

    def test_base_datetime_only_in(self):
        """打刻 IN のみ → in/out が None で返ること"""
        self._set_clocks(in_time="09:00")
        result = ClockCalculate.get_base_datetime(None, date(2024, 4, 1))
        self.assertIsNone(result["in_datetime"])
        self.assertIsNone(result["out_datetime"])

    def test_base_datetime_normal(self):
        """通常の IN/OUT → 正しい datetime が返ること"""
        self._set_clocks(in_time="09:00", out_time="18:00")
        result = ClockCalculate.get_base_datetime(None, date(2024, 4, 1))
        self.assertEqual(result["in_datetime"].hour, 9)
        self.assertEqual(result["in_datetime"].minute, 0)
        self.assertEqual(result["out_datetime"].hour, 18)
        self.assertEqual(result["out_datetime"].minute, 0)

    def test_base_datetime_midnight_crossing(self):
        """退勤が翌日にまたぐ場合、out_datetime が in_datetime より後になること"""
        self._set_clocks(in_time="22:00", out_time="02:00")
        result = ClockCalculate.get_base_datetime(None, date(2024, 4, 1))
        self.assertGreater(result["out_datetime"], result["in_datetime"])

    # ------------------------------------------------------- calculate_work_time

    def test_work_time_no_records(self):
        """打刻なし → 0.0"""
        base = {"in_datetime": None, "out_datetime": None, "break_time": timedelta(0)}
        self.assertEqual(ClockCalculate.calculate_work_time(base), 0.0)

    def test_work_time_standard_day(self):
        """09:00-18:00、休憩 1h → 8.0h（境界上なので丸めなし）"""
        base = {
            "in_datetime": datetime(2024, 4, 1, 9, 0),
            "out_datetime": datetime(2024, 4, 1, 18, 0),
            "break_time": timedelta(hours=1),
        }
        self.assertAlmostEqual(ClockCalculate.calculate_work_time(base), 8.0, places=2)

    def test_work_time_with_rounding(self):
        """09:07-17:57、休憩 1h → round_up(09:07)=09:15、round_down(17:57)=17:45 → 7.5h"""
        base = {
            "in_datetime": datetime(2024, 4, 1, 9, 7),
            "out_datetime": datetime(2024, 4, 1, 17, 57),
            "break_time": timedelta(hours=1),
        }
        self.assertAlmostEqual(ClockCalculate.calculate_work_time(base), 7.5, places=2)

    def test_work_time_exact_scheduled_hours(self):
        """09:00-17:45、休憩 1h → 所定 7.75h"""
        base = {
            "in_datetime": datetime(2024, 4, 1, 9, 0),
            "out_datetime": datetime(2024, 4, 1, 17, 45),
            "break_time": timedelta(hours=1),
        }
        self.assertAlmostEqual(ClockCalculate.calculate_work_time(base), 7.75, places=2)

    # ------------------------------------------------------ calculate_night_work

    def test_night_work_none(self):
        """22:00 前に退勤 → 深夜労働 0h"""
        start = datetime(2024, 4, 1, 9, 0)
        end = datetime(2024, 4, 1, 21, 0)
        self.assertEqual(ClockCalculate.calculate_night_work(start, end), 0.0)

    def test_night_work_partial(self):
        """22:00-23:00 の 1h 深夜労働"""
        start = datetime(2024, 4, 1, 9, 0)
        end = datetime(2024, 4, 1, 23, 0)
        self.assertAlmostEqual(
            ClockCalculate.calculate_night_work(start, end), 1.0, places=2
        )

    def test_night_work_full(self):
        """22:00-05:00 の 7h 全深夜労働"""
        start = datetime(2024, 4, 1, 22, 0)
        end = datetime(2024, 4, 2, 5, 0)
        self.assertAlmostEqual(
            ClockCalculate.calculate_night_work(start, end), 7.0, places=2
        )

    def test_night_work_capped_at_night_end(self):
        """05:00 以降も勤務していても深夜時間は 7h を超えないこと"""
        start = datetime(2024, 4, 1, 22, 0)
        end = datetime(2024, 4, 2, 8, 0)
        self.assertAlmostEqual(
            ClockCalculate.calculate_night_work(start, end), 7.0, places=2
        )

    # ----------------------------------------------------------- daily_summary

    def test_daily_summary_no_records(self):
        """打刻なし → 全項目 0.0"""
        self._set_clocks()
        result = ClockCalculate.daily_summary(None, date(2024, 4, 1))
        self.assertEqual(result["work_duration"], 0.0)
        self.assertEqual(result["night_work"], 0.0)
        self.assertEqual(result["overtime_duration"], 0.0)
        self.assertEqual(result["break_time"], 0.0)

    def test_daily_summary_with_overtime(self):
        """7.75h 超の場合、残業時間が計算されること"""
        self._set_clocks(in_time="09:00", out_time="19:00")
        result = ClockCalculate.daily_summary(None, date(2024, 4, 1))
        self.assertGreater(result["work_duration"], 7.75)
        self.assertGreater(result["overtime_duration"], 0.0)

    def test_daily_summary_no_overtime(self):
        """7.75h 以下の場合、残業なし"""
        self._set_clocks(in_time="09:00", out_time="16:45")
        result = ClockCalculate.daily_summary(None, date(2024, 4, 1))
        self.assertEqual(result["overtime_duration"], 0.0)

    def test_daily_summary_punch_times_are_strings(self):
        """punch_in / punch_out が HH:MM 形式の文字列で返ること"""
        self._set_clocks(in_time="09:00", out_time="18:00")
        result = ClockCalculate.daily_summary(None, date(2024, 4, 1))
        self.assertIsInstance(result["punch_in"], str)
        self.assertIsInstance(result["punch_out"], str)
        self.assertRegex(result["punch_in"], r"^\d{2}:\d{2}$")

    # --------------------------------------------------------- monthly_summary

    def test_monthly_summary_single_working_day(self):
        """1 日分だけ打刻がある月の合計が日次勤務時間と一致すること"""
        day1_in = self._make_record("2024-04-01", "09:00")
        day1_out = self._make_record("2024-04-01", "18:00")

        def get_clock_side_effect(user, d):
            if d == date(2024, 4, 1):
                return {"in_clock": day1_in, "out_clock": day1_out}
            return {"in_clock": None, "out_clock": None}

        self.mock_repo.get_clock.side_effect = get_clock_side_effect

        result = ClockCalculate.monthly_summary(None, 2024, 4)
        self.assertAlmostEqual(result["total_work_time"], 8.0, places=2)

    def test_monthly_summary_no_records(self):
        """打刻ゼロの月 → 全合計 0.0"""
        self.mock_repo.get_clock.return_value = {"in_clock": None, "out_clock": None}
        result = ClockCalculate.monthly_summary(None, 2024, 4)
        self.assertEqual(result["total_work_time"], 0.0)
        self.assertEqual(result["total_overtime"], 0.0)

    def test_monthly_summary_includes_all_keys(self):
        """月次集計が必要なキーを全て含むこと"""
        self.mock_repo.get_clock.return_value = {"in_clock": None, "out_clock": None}
        result = ClockCalculate.monthly_summary(None, 2024, 4)
        for key in ("total_work_time", "total_night_work", "total_break_time", "total_overtime"):
            self.assertIn(key, result)
