"""
测试时间工具模块
"""
import pytest
from datetime import datetime, timedelta
from src.utils.time_utils import (
    parse_relative_time,
    format_time_ago,
    get_time_context,
    is_same_day,
    is_same_week,
    get_day_period
)


class TestParseRelativeTime:
    """测试相对时间解析"""
    
    def test_parse_yesterday(self):
        ref = datetime(2026, 2, 7, 22, 0, 0)
        result = parse_relative_time("昨天", ref)
        assert result.date() == datetime(2026, 2, 6).date()
    
    def test_parse_last_week(self):
        ref = datetime(2026, 2, 7, 22, 0, 0)
        result = parse_relative_time("上周", ref)
        expected = ref - timedelta(weeks=1)
        assert result.date() == expected.date()
    
    def test_parse_n_days_ago(self):
        ref = datetime(2026, 2, 7, 22, 0, 0)
        result = parse_relative_time("3天前", ref)
        expected = ref - timedelta(days=3)
        assert result.date() == expected.date()
    
    def test_parse_n_hours_ago(self):
        ref = datetime(2026, 2, 7, 22, 0, 0)
        result = parse_relative_time("5小时前", ref)
        expected = ref - timedelta(hours=5)
        assert result.hour == expected.hour
    
    def test_parse_unknown(self):
        result = parse_relative_time("不存在的时间表达")
        assert result is None


class TestFormatTimeAgo:
    """测试时间格式化"""
    
    def test_format_just_now(self):
        ref = datetime.now()
        timestamp = ref - timedelta(seconds=30)
        assert format_time_ago(timestamp, ref) == "刚刚"
    
    def test_format_minutes(self):
        ref = datetime.now()
        timestamp = ref - timedelta(minutes=15)
        assert format_time_ago(timestamp, ref) == "15分钟前"
    
    def test_format_hours(self):
        ref = datetime.now()
        timestamp = ref - timedelta(hours=3)
        assert format_time_ago(timestamp, ref) == "3小时前"
    
    def test_format_yesterday(self):
        ref = datetime.now()
        timestamp = ref - timedelta(days=1)
        assert format_time_ago(timestamp, ref) == "昨天"
    
    def test_format_days(self):
        ref = datetime.now()
        timestamp = ref - timedelta(days=5)
        assert format_time_ago(timestamp, ref) == "5天前"


class TestTimeContext:
    """测试时间上下文"""
    
    def test_get_time_context(self):
        last_time = datetime.now() - timedelta(hours=2)
        context = get_time_context(last_time)
        
        assert "[时间感知]" in context
        assert "当前时刻" in context
        assert "上次记录" in context


class TestHelperFunctions:
    """测试辅助函数"""
    
    def test_is_same_day(self):
        t1 = datetime(2026, 2, 7, 10, 0, 0)
        t2 = datetime(2026, 2, 7, 22, 0, 0)
        t3 = datetime(2026, 2, 8, 10, 0, 0)
        
        assert is_same_day(t1, t2) is True
        assert is_same_day(t1, t3) is False
    
    def test_is_same_week(self):
        t1 = datetime(2026, 2, 2)  # Monday
        t2 = datetime(2026, 2, 6)  # Friday
        t3 = datetime(2026, 2, 9)  # Next Monday
        
        assert is_same_week(t1, t2) is True
        assert is_same_week(t1, t3) is False
    
    def test_get_day_period_morning(self):
        assert get_day_period(datetime(2026, 2, 7, 9, 0, 0)) == "上午"
    
    def test_get_day_period_evening(self):
        assert get_day_period(datetime(2026, 2, 7, 20, 0, 0)) == "晚上"
