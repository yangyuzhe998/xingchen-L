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
    """
    if reference is None:
        reference = datetime.now()
    
    delta = reference - timestamp
    
    if delta < timedelta(minutes=1):
        return "刚刚"
    if delta < timedelta(hours=1):
        return f"{int(delta.total_seconds() / 60)}分钟前"
    if delta < timedelta(days=1):
        return f"{int(delta.total_seconds() / 3600)}小时前"
    if delta < timedelta(days=2):
        return "昨天"
    if delta < timedelta(days=7):
        return f"{delta.days}天前"
    if delta < timedelta(days=30):
        return f"{delta.days}天前"
    if delta < timedelta(days=365):
        return f"{int(delta.days / 30)}个月前"
    
    return f"{int(delta.days / 365)}年前"


def get_time_context(last_time: Optional[datetime] = None) -> str:
    """
    获取当前时间上下文描述，供 LLM 参考
    """
    now = datetime.now()
    period = get_day_period(now.hour)
    
    context = f"[时间感知] 当前时刻: {now.strftime('%Y-%m-%d %H:%M:%S')} ({period})"
    
    if last_time:
        ago = format_time_ago(last_time, now)
        context += f"\n上次记录: {last_time.strftime('%Y-%m-%d %H:%M:%S')} ({ago})"
        
    return context


def is_same_day(t1: datetime, t2: datetime) -> bool:
    """判断两个时间是否在同一天"""
    return t1.date() == t2.date()


def is_same_week(t1: datetime, t2: datetime) -> bool:
    """判断两个时间是否在同一周 (周一为第一天)"""
    # isocalendar() 返回 (year, week, weekday)
    iso1 = t1.isocalendar()
    iso2 = t2.isocalendar()
    return iso1[0] == iso2[0] and iso1[1] == iso2[1]


def get_day_period(hour: int) -> str:
    """根据小时获取时间段描述"""
    if 5 <= hour < 11:
        return "早晨"
    elif 11 <= hour < 13:
        return "中午"
    elif 13 <= hour < 18:
        return "下午"
    elif 18 <= hour < 23:
        return "晚上"
    else:
        return "深夜"
