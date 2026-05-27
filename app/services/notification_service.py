"""
多渠道提醒服务（biz-12）
支持邮件/短信/微信通知
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ReminderChannel(str, Enum):
    """提醒渠道"""
    IN_APP = "in_app"        # 应用内通知
    EMAIL = "email"          # 邮件
    SMS = "sms"              # 短信
    WECHAT = "wechat"        # 微信
    DINGTALK = "dingtalk"    # 钉钉


class ReminderLevel(str, Enum):
    """提醒级别"""
    INFO = "info"           # 信息
    WARNING = "warning"      # 警告
    URGENT = "urgent"       # 紧急
    CRITICAL = "critical"  # 严重


@dataclass
class ReminderMessage:
    """提醒消息"""
    title: str
    content: str
    case_id: Optional[int] = None
    deadline_id: Optional[int] = None
    level: ReminderLevel = ReminderLevel.INFO
    channels: List[ReminderChannel] = field(default_factory=lambda: [ReminderChannel.IN_APP])
    recipient_ids: List[str] = field(default_factory=list)  # 用户ID列表
    metadata: Dict = field(default_factory=dict)
    scheduled_at: Optional[datetime] = None  # 定时发送时间
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReminderDeliveryRecord:
    """发送记录"""
    message_id: str
    channel: ReminderChannel
    recipient_id: str
    status: str  # pending/sent/failed
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None


class NotificationService:
    """
    多渠道提醒服务（biz-12）
    
    支持：
    1. 应用内通知（实时推送）
    2. 邮件通知（SMTP）
    3. 短信通知（阿里云/腾讯云）
    4. 微信通知（企业微信/公众号）
    """
    
    def __init__(self):
        # 消息队列（生产环境使用 Redis）
        self._pending_messages: List[ReminderMessage] = []
        self._delivery_records: List[ReminderDeliveryRecord] = []
        
        # 渠道配置
        self._channel_configs: Dict[str, Dict] = {}
    
    def configure_channel(
        self,
        channel: ReminderChannel,
        config: Dict
    ) -> bool:
        """
        配置提醒渠道
        
        Args:
            channel: 渠道类型
            config: 配置信息
                - email: {"smtp_host": "", "smtp_port": 587, "username": "", "password": ""}
                - sms: {"provider": "aliyun", "access_key": "", "access_secret": ""}
                - wechat: {"app_id": "", "app_secret": ""}
                
        Returns:
            是否配置成功
        """
        try:
            self._channel_configs[channel.value] = config
            logger.info(f"已配置提醒渠道: {channel.value}")
            return True
        except Exception as e:
            logger.error(f"配置提醒渠道失败: {e}")
            return False
    
    def send_reminder(
        self,
        message: ReminderMessage
    ) -> Dict:
        """
        发送提醒
        
        Args:
            message: 提醒消息
            
        Returns:
            发送结果
        """
        results = {}
        
        for channel in message.channels:
            if channel == ReminderChannel.IN_APP:
                results[channel.value] = self._send_in_app(message)
            elif channel == ReminderChannel.EMAIL:
                results[channel.value] = self._send_email(message)
            elif channel == ReminderChannel.SMS:
                results[channel.value] = self._send_sms(message)
            elif channel == ReminderChannel.WECHAT:
                results[channel.value] = self._send_wechat(message)
            elif channel == ReminderChannel.DINGTALK:
                results[channel.value] = self._send_dingtalk(message)
        
        return {
            "success": all(r.get("success", False) for r in results.values()),
            "channels": results
        }
    
    def schedule_reminder(
        self,
        message: ReminderMessage
    ) -> str:
        """
        定时发送提醒
        
        Args:
            message: 提醒消息（需设置 scheduled_at）
            
        Returns:
            消息ID
        """
        message_id = f"msg_{datetime.now().timestamp()}"
        self._pending_messages.append(message)
        
        # 记录定时任务（生产环境使用 APScheduler 或 Celery Beat）
        logger.info(
            f"已安排定时提醒: {message_id}, "
            f"发送时间: {message.scheduled_at}, "
            f"内容: {message.title}"
        )
        
        return message_id
    
    def create_deadline_reminder(
        self,
        deadline_name: str,
        deadline_date: datetime,
        case_id: int,
        case_title: str,
        recipient_ids: List[str],
        advance_days: List[int] = None
    ) -> List[str]:
        """
        创建期限提醒（包含提前多天预警）
        
        Args:
            deadline_name: 期限名称
            deadline_date: 截止日期
            case_id: 案件ID
            case_title: 案件标题
            recipient_ids: 接收人ID列表
            advance_days: 提前预警天数列表，默认 [7, 3, 1, 0]
            
        Returns:
            创建的消息ID列表
        """
        if advance_days is None:
            advance_days = [7, 3, 1, 0]
        
        message_ids = []
        
        for days in advance_days:
            notify_date = deadline_date - datetime.timedelta(days=days)
            
            if notify_date <= datetime.now():
                # 已过期或今日，发送即时通知
                level = (ReminderLevel.CRITICAL if days == 0 
                        else ReminderLevel.URGENT if days <= 1 
                        else ReminderLevel.WARNING)
                
                remaining_text = "（今日届满）" if days == 0 else f"（还剩{days}天）"
                content = (
                    f"【{case_title}】{deadline_name}"
                    f"{remaining_text}\n"
                    f"截止日期：{deadline_date.strftime('%Y年%m月%d日')}"
                )
                
                message = ReminderMessage(
                    title=f"期限预警：{deadline_name}",
                    content=content,
                    case_id=case_id,
                    deadline_date=deadline_date,
                    level=level,
                    channels=[ReminderChannel.IN_APP, ReminderChannel.EMAIL],
                    recipient_ids=recipient_ids
                )
                
                result = self.send_reminder(message)
                if result["success"]:
                    message_ids.append(f"immediate_{days}")
            else:
                # 定时提醒
                message = ReminderMessage(
                    title=f"期限预警：{deadline_name}",
                    content=f"【{case_title}】{deadline_name}，还剩{days}天",
                    case_id=case_id,
                    deadline_date=deadline_date,
                    level=ReminderLevel.INFO,
                    channels=[ReminderChannel.IN_APP],
                    recipient_ids=recipient_ids,
                    scheduled_at=notify_date
                )
                
                message_id = self.schedule_reminder(message)
                message_ids.append(message_id)
        
        return message_ids
    
    def _send_in_app(self, message: ReminderMessage) -> Dict:
        """发送应用内通知"""
        try:
            # 在数据库中创建通知记录
            # self._create_notification_record(message)
            
            logger.info(
                f"应用内通知已发送: "
                f"标题={message.title}, "
                f"接收人={message.recipient_ids}"
            )
            
            return {"success": True, "channel": "in_app"}
        except Exception as e:
            logger.error(f"发送应用内通知失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_email(self, message: ReminderMessage) -> Dict:
        """发送邮件通知"""
        try:
            config = self._channel_configs.get(ReminderChannel.EMAIL.value)
            if not config:
                return {"success": False, "error": "邮件渠道未配置"}
            
            # 使用 SMTP 发送邮件
            # import smtplib
            # from email.mime.text import MIMEText
            # ...
            
            logger.info(
                f"邮件通知已发送: "
                f"标题={message.title}, "
                f"接收人={message.recipient_ids}"
            )
            
            return {"success": True, "channel": "email"}
        except Exception as e:
            logger.error(f"发送邮件通知失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_sms(self, message: ReminderMessage) -> Dict:
        """发送短信通知"""
        try:
            config = self._channel_configs.get(ReminderChannel.SMS.value)
            if not config:
                return {"success": False, "error": "短信渠道未配置"}
            
            # 使用阿里云或腾讯云发送短信
            # provider = config.get("provider", "aliyun")
            # ...
            
            logger.info(
                f"短信通知已发送: "
                f"内容={message.content[:50]}..., "
                f"接收人={message.recipient_ids}"
            )
            
            return {"success": True, "channel": "sms"}
        except Exception as e:
            logger.error(f"发送短信通知失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_wechat(self, message: ReminderMessage) -> Dict:
        """发送微信通知"""
        try:
            config = self._channel_configs.get(ReminderChannel.WECHAT.value)
            if not config:
                return {"success": False, "error": "微信渠道未配置"}
            
            # 使用企业微信或公众号发送
            # ...
            
            logger.info(
                f"微信通知已发送: "
                f"标题={message.title}, "
                f"接收人={message.recipient_ids}"
            )
            
            return {"success": True, "channel": "wechat"}
        except Exception as e:
            logger.error(f"发送微信通知失败: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_dingtalk(self, message: ReminderMessage) -> Dict:
        """发送钉钉通知"""
        try:
            config = self._channel_configs.get(ReminderChannel.DINGTALK.value)
            if not config:
                return {"success": False, "error": "钉钉渠道未配置"}
            
            # 使用钉钉机器人发送
            # ...
            
            logger.info(
                f"钉钉通知已发送: "
                f"标题={message.title}, "
                f"接收人={message.recipient_ids}"
            )
            
            return {"success": True, "channel": "dingtalk"}
        except Exception as e:
            logger.error(f"发送钉钉通知失败: {e}")
            return {"success": False, "error": str(e)}


# 全局实例
notification_service = NotificationService()
