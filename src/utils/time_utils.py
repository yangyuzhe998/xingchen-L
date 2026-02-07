"""
时间工具模块 (Time Utilities)
提供相对时间解析、时间格式化等功能
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import re


# 相对时间映射表 (中文 -> timedelta)
RELATIVE_TIME_MAPPING = {
    # 秒级
    "刚才": timedelta(minutes=5),
    "刚刚": timedelta(minutes=2),
    "方才": timedelta(minutes=10),
    
    # 分钟级
    "几分钟前": timedelta(minutes=5),
    "十分钟前": timedelta(minutes=10),
    "半小时前": timedelta(minutes=30),
    
    # 小时级
    "一小时前": timedelta(hours=1),
    "两小时前": timedelta(hours=2),
    "几小时前": timedelta(hours=3),
    "今早": timedelta(hours=8),
    "今天": timedelta(hours=0),
    
    # 天级
    "昨天": timedelta(days=1),
    "前天": timedelta(days=2),
    "前几天": timedelta(days=3),
    
    # 周级
    "上周": timedelta(weeks=1),
    "上上周": timedelta(weeks=2),
    "这周": timedelta(days=0),
    
    # 月级
    "上个月": timedelta(days=30),
    "上上个月": timedelta(days=60),
    "这个月": timedelta(days=0),
    
    # 年级
    "去年": timedelta(days=365),
    "前年": timedelta(days=730),
}


def parse_relative_time(text: str, reference: datetime = None) -> Optional[datetime]:
    """
    解析相对时间表达式
    
    :param text: 相对时间文本 (如 "昨天", "上周", "两小时前")
    :param reference: 参考时间点，默认为当前时间
    :return: 解析后的 datetime，如果无法解析返回 None
    
    示例:
        >>> parse_relative_time("昨天")
        datetime(2026, 2, 6, 22, 0, 0)  # 假设今天是 2026-02-07
    """
    if reference is None:
        reference = datetime.now()
    
    text = text.strip()
    
    # 1. 直接匹配映射表
    if text in RELATIVE_TIME_MAPPING:
        delta = RELATIVE_TIME_MAPPING[text]
        return reference - delta
    
    # 2. 模式匹配: "N天前", "N小时前", "N分钟前"
    patterns = [
        (r"(\d+)天前", lambda m: timedelta(days=int(m.group(1)))),
        (r"(\d+)小时前", lambda m: timedelta(hours=int(m.group(1)))),
        (r"(\d+)分钟前", lambda m: timedelta(minutes=int(m.group(1)))),
        (r"(\d+)周前", lambda m: timedelta(weeks=int(m.group(1)))),
        (r"(\d+)个月前", lambda m: timedelta(days=int(m.group(1)) * 30)),
    ]
    
    for pattern, delta_func in patterns:
        match = re.match(pattern, text)
        if match:
            delta = delta_func(match)
            return reference - delta
    
    # 3. 无法解析
    return None


def format_time_ago(timestamp: datetime, reference: datetime = None) -> str:
    """
    将 datetime 格式化为"多久前"的友好文本
    
    :param timestamp: 要格式化的时间
    :param reference: 参考时间点，默认为当前时间
    :return: 友好的时间文本
    
    示例:
        >>> format_time_ago(datetime.now() - timedelta(hours=2))
        "2小时前"
    """
    if reference is None:
        reference = datetime.now()
    
    delta = reference - timestamp
    seconds = int(delta.total_seconds())
    
    if seconds < 0:
        return "未来"
    
    # 秒级
    if seconds < 60:
        return "刚刚"
    
    # 分钟级
    if seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}分钟前"
    
    # 小时级
    if seconds < 86400:
        hours = seconds // 3600
        return f"{hours}小时前"
    
    # 天级
    days = seconds // 86400
    if days == 1:
        return "昨天"
    if days == 2:
        return "前天"
    if days < 7:
        return f"{days}天前"
    
    # 周级
    if days < 30:
        weeks = days // 7
        return f"{weeks}周前"
    
    # 月级
    if days < 365:
        months = days // 30
        return f"{months}个月前"
    
    # 年级
    years = days // 365
    return f"{years}年前"


def get_time_context(last_time: datetime = None) -> str:
    """
    生成时间上下文信息 (用于注入到 Prompt 中)
    
    :param last_time: 上次记录的时间
    :return: 格式化的时间上下文字符串
    """
    now = datetime.now()
    
    if last_time is None:
        last_time = now
    
    time_passed = format_time_ago(last_time, now)
    
    # 获取当前时间段
    hour = now.hour
    if 5 <= hour < 12:
        period = "上午"
    elif 12 <= hour < 14:
        period = "中午"
    elif 14 <= hour < 18:
        period = "下午"
    elif 18 <= hour < 22:
        period = "晚上"
    else:
        period = "深夜"
    
    context = (
        f"[时间感知]\n"
        f"- 当前时刻: {now.strftime('%Y-%m-%d %H:%M:%S')} ({period})\n"
        f"- 上次记录: {last_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- 距今: {time_passed}\n"
    )
    
    return context


def is_same_day(time1: datetime, time2: datetime) -> bool:
    """判断两个时间是否是同一天"""
    return time1.date() == time2.date()


def is_same_week(time1: datetime, time2: datetime) -> bool:
    """判断两个时间是否是同一周"""
    return time1.isocalendar()[1] == time2.isocalendar()[1] and time1.year == time2.year


def get_day_period(dt: datetime = None) -> str:
    """
    获取时间段名称
    :return: 上午/中午/下午/晚上/深夜
    """
    if dt is None:
        dt = datetime.now()
    
    hour = dt.hour
    if 5 <= hour < 12:
        return "上午"
    elif 12 <= hour < 14:
        return "中午"
    elif 14 <= hour < 18:
        return "下午"
    elif 18 <= hour < 22:
        return "晚上"
    else:
        return "深夜"
