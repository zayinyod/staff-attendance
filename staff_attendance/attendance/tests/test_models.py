"""
Django モデルの制約・str 表現テスト。
repository や usecase は import せず、モデルを直接操作する。
"""
from django.test import TestCase
from django.db import IntegrityError
from attendance.models import User, Department, Clock, CodeMaster


class BaseModelTestCase(TestCase):
    """テスト共通のコードマスター・部署データを準備する基底クラス"""

    @classmethod
    def setUpTestData(cls):
        cls.dept = Department.objects.create(name="Engineering")
        # コードマスターはマイグレーション 0016 で投入済みのものを参照する
        cls.clock_in = CodeMaster.objects.get(code_type="clock", code="0")
        cls.clock_out = CodeMaster.objects.get(code_type="clock", code="1")
        cls.location_office = CodeMaster.objects.get(code_type="location", code="0")
        cls.location_telework = CodeMaster.objects.get(code_type="location", code="1")


class TestDepartmentModel(BaseModelTestCase):
    def test_str(self):
        dept = Department.objects.create(name="HR")
        self.assertEqual(str(dept), f"[{dept.id}] HR")


class TestCodeMasterModel(BaseModelTestCase):
    def test_str(self):
        self.assertEqual(str(self.clock_in), "[clock: 0] In")

    def test_unique_together_violation(self):
        """code_type + code の重複は IntegrityError になること"""
        with self.assertRaises(IntegrityError):
            CodeMaster.objects.create(
                code_type="clock", code="0", description="Duplicate"
            )

    def test_different_code_type_same_code_allowed(self):
        """code_type が異なれば同じ code を登録できること"""
        CodeMaster.objects.create(
            code_type="other_type", code="0", description="Other"
        )
        self.assertTrue(
            CodeMaster.objects.filter(code_type="other_type", code="0").exists()
        )


class TestUserModel(BaseModelTestCase):
    def test_user_creation(self):
        user = User.objects.create_user(
            user_id="A00001",
            username="alice",
            password="SecurePass1!",
            department=self.dept,
        )
        self.assertEqual(user.user_id, "A00001")
        self.assertEqual(user.username, "alice")
        self.assertEqual(user.department, self.dept)

    def test_user_str(self):
        user = User.objects.create_user(
            user_id="B00001",
            username="bob",
            password="SecurePass1!",
        )
        self.assertEqual(str(user), "[B00001] bob")

    def test_user_id_is_primary_key(self):
        user = User.objects.create_user(
            user_id="C00001",
            username="carol",
            password="SecurePass1!",
        )
        self.assertEqual(user.pk, "C00001")

    def test_department_set_null_on_delete(self):
        """部署削除時にユーザーの department が NULL になること"""
        dept = Department.objects.create(name="Temp")
        user = User.objects.create_user(
            user_id="D00001",
            username="dave",
            password="SecurePass1!",
            department=dept,
        )
        dept.delete()
        user.refresh_from_db()
        self.assertIsNone(user.department)


class TestClockModel(BaseModelTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user(
            user_id="U00001",
            username="clockuser",
            password="SecurePass1!",
        )

    def test_clock_creation(self):
        clock = Clock.objects.create(
            user=self.user,
            date_stamp="2024-01-15",
            time_stamp="09:00:00",
            clock=self.clock_in,
            break_time="1.00",
            location=self.location_office,
        )
        self.assertEqual(clock.user, self.user)
        self.assertEqual(clock.clock.description, "In")

    def test_clock_str(self):
        clock = Clock.objects.create(
            user=self.user,
            date_stamp="2024-01-15",
            time_stamp="09:00:00",
            clock=self.clock_in,
            location=self.location_office,
        )
        self.assertIn("2024-01-15", str(clock))
        self.assertIn("clockuser", str(clock))

    def test_unique_together_prevents_duplicate(self):
        """同一ユーザー・日付・打刻種別の重複は IntegrityError になること"""
        Clock.objects.create(
            user=self.user,
            date_stamp="2024-01-15",
            time_stamp="09:00:00",
            clock=self.clock_in,
            location=self.location_office,
        )
        with self.assertRaises(IntegrityError):
            Clock.objects.create(
                user=self.user,
                date_stamp="2024-01-15",
                time_stamp="10:00:00",
                clock=self.clock_in,
                location=self.location_office,
            )

    def test_in_and_out_on_same_date_allowed(self):
        """同一日に IN と OUT をそれぞれ 1 件登録できること"""
        Clock.objects.create(
            user=self.user,
            date_stamp="2024-01-16",
            time_stamp="09:00:00",
            clock=self.clock_in,
            location=self.location_office,
        )
        Clock.objects.create(
            user=self.user,
            date_stamp="2024-01-16",
            time_stamp="18:00:00",
            clock=self.clock_out,
            location=self.location_office,
        )
        count = Clock.objects.filter(user=self.user, date_stamp="2024-01-16").count()
        self.assertEqual(count, 2)

    def test_cascade_delete_with_user(self):
        """ユーザー削除時に打刻レコードも削除されること"""
        user = User.objects.create_user(
            user_id="X00001", username="xuser", password="SecurePass1!"
        )
        Clock.objects.create(
            user=user,
            date_stamp="2024-01-15",
            time_stamp="09:00:00",
            clock=self.clock_in,
            location=self.location_office,
        )
        user.delete()
        self.assertFalse(Clock.objects.filter(date_stamp="2024-01-15").exists())
