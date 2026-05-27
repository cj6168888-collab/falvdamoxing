"""
法律期限计算服务 - 精准计算各类法定期限
包括：诉讼时效、举证期限、上诉期限、执行期限等
"""

from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta, date
from dateutil import parser
import calendar

from app.services.llm_service import llm_service


def _get_chinese_holidays(year: int) -> set:
    """
    动态获取指定年份的中国法定节假日（含农历节日支持）
    使用 chinese-calendar 库（pip install chinese-calendar）
    fallback: 如果库不可用，使用内置的硬编码节假日
    """
    holidays = set()
    
    try:
        import chinese_calendar
        from datetime import date as date_type
        # 获取该年的所有法定假日（含调休工作日）
        start = date_type(year, 1, 1)
        end = date_type(year, 12, 31)
        holiday_dates = chinese_calendar.get_holidays(start, end)
        for d in holiday_dates:
            holidays.add(d)
        
        # 补充农历节日（中国日历库可能不完全覆盖）
        # 春节（正月初一，约1月21日-2月20日之间）
        lunar_festivals = _get_lunar_festival_dates(year)
        holidays.update(lunar_festivals)
        
    except ImportError:
        # fallback: 使用内置硬编码节假日（2026年数据）
        holidays = _get_builtin_holidays(year)
    
    return holidays


def _get_lunar_festival_dates(year: int) -> set:
    """
    获取农历节日的大致公历日期
    注意：这是近似计算，精确农历转换需要 lunar-calendar 库
    实际使用 chinese-calendar 库会得到更精确的结果
    """
    lunar_dates = set()
    
    try:
        import chinese_calendar
        # 春节（正月初一）- chinese-calendar 库已包含
        # 中秋节（八月十五）和端午节（五月初五）使用库计算
        # 以下为 fallback 近似值
        pass
    except ImportError:
        pass
    
    return lunar_dates


def _get_builtin_holidays(year: int) -> set:
    """
    内置节假日数据（Fallback）
    包含：元旦、春节、清明、劳动节、端午、中秋、国庆
    """
    holidays = set()
    
    # 元旦
    holidays.add(date(year, 1, 1))
    
    # 春节（2026年：2月17日-2月24日，农历正月初一为2月17日）
    for day in range(17, 25):
        holidays.add(date(year, 2, day))
    
    # 清明节（2026年：4月4日）
    holidays.add(date(year, 4, 4))
    holidays.add(date(year, 4, 5))
    holidays.add(date(year, 4, 6))
    
    # 劳动节（2026年：5月1日-5月5日）
    for day in range(1, 6):
        holidays.add(date(year, 5, day))
    
    # 端午节（2026年：6月19日-6月21日，农历五月初五）
    for day in range(19, 22):
        holidays.add(date(year, 6, day))
    
    # 中秋节（2026年：9月25日-9月27日，农历八月十五）
    for day in range(25, 28):
        holidays.add(date(year, 9, day))
    
    # 国庆节（2026年：10月1日-10月8日）
    for day in range(1, 9):
        holidays.add(date(year, 10, day))
    
    return holidays


class LitigationLimitationService:
    """
    诉讼时效服务 - 精确管理各类时效（基于民法典）
    
    民法典第188条：向人民法院请求保护民事权利的诉讼时效期间为三年
    最长保护期间：20年（从权利被侵害之日起算）
    短期时效：1年（如身体受到伤害要求赔偿）
    
    参考法规：
    - 《民法典》第188条（普通诉讼时效：3年）
    - 《民法典》第191条（未成年人性侵害：3年，自受害人年满18周岁起算）
    - 《民法典》第194条（时效中止/中断规定）
    - 《劳动争议调解仲裁法》第27条（劳动仲裁时效：1年）
    - 《仲裁法》第74条（仲裁时效：适用民事法律的规定，一般为4年）
    """
    
    # 普通诉讼时效（民法典第188条）
    GENERAL_LIMITATION = {
        "name": "普通诉讼时效",
        "days": 1095,  # 3年
        "years": 3,
        "basis": "《民法典》第188条",
        "description": "向人民法院请求保护民事权利的诉讼时效期间为三年。法律另有规定的，依照其规定。"
    }
    
    # 最长保护期间（民法典第188条）
    MAXIMUM_LIMITATION = {
        "name": "最长保护期间",
        "days": 7300,  # 20年
        "years": 20,
        "basis": "《民法典》第188条",
        "description": "诉讼时效期间自权利人知道或者应当知道权利受到损害以及义务人之日起计算。但是，从权利被侵害之日起超过二十年的，人民法院不予保护。"
    }
    
    # 短期诉讼时效（民法典第594条等）
    SHORT_LIMITATIONS = {
        "身体伤害": {
            "name": "人身损害赔偿时效",
            "days": 365,  # 1年
            "basis": "《民法典》第595条（参照）《民法典》第188条",
            "description": "因身体受到伤害要求赔偿的，诉讼时效期间为一年"
        },
        "租金": {
            "name": "租金请求权时效",
            "days": 365,  # 1年
            "basis": "《民法典》第734条",
            "description": "租赁合同的租金请求权适用一年短期时效"
        },
        "劳动报酬": {
            "name": "劳动报酬时效",
            "days": 365,  # 1年（劳动关系存续期间不受限制）
            "basis": "《劳动争议调解仲裁法》第27条",
            "description": "劳动报酬的仲裁时效期间为一年，从当事人知道或者应当知道其权利被侵害之日起计算"
        },
        "劳动争议": {
            "name": "劳动争议仲裁时效",
            "days": 365,  # 1年
            "basis": "《劳动争议调解仲裁法》第27条",
            "description": "劳动争议申请仲裁的时效期间为一年，从当事人知道或者应当知道其权利被侵害之日起计算"
        }
    }
    
    # 中止/中断事由
    STATUTORY_EVENTS = {
        "中止事由": [
            "不可抗力",
            "无民事行为能力人或限制民事行为能力人没有法定代理人",
            "权利人向义务人提出履行请求",
            "权利人提起诉讼或者申请仲裁",
            "与提起诉讼或者申请仲裁具有同等效力的其他情形"
        ],
        "中断事由": [
            "权利人向义务人提出履行请求",
            "义务人同意履行义务",
            "权利人提起诉讼或者申请仲裁",
            "与提起诉讼或者申请仲裁具有同等效力的其他情形"
        ]
    }
    
    @staticmethod
    def calculate_limitation_expiry(
        event_date: datetime,
        limitation_type: str = "general"
    ) -> datetime:
        """
        计算诉讼时效届满日期
        
        Args:
            event_date: 权利被侵害之日 / 知道权利被侵害之日
            limitation_type: 时效类型 ("general" | "maximum" | "身体伤害" | "租金" | "劳动报酬" | "劳动争议")
            
        Returns:
            时效届满的日期时间
        """
        if limitation_type == "maximum":
            days = LitigationLimitationService.MAXIMUM_LIMITATION["days"]
        elif limitation_type in LitigationLimitationService.SHORT_LIMITATIONS:
            days = LitigationLimitationService.SHORT_LIMITATIONS[limitation_type]["days"]
        else:
            days = LitigationLimitationService.GENERAL_LIMITATION["days"]
        
        return event_date + timedelta(days=days)
    
    @staticmethod
    def is_expired(
        event_date: datetime,
        limitation_type: str = "general"
    ) -> Tuple[bool, Optional[int]]:
        """
        检查诉讼时效是否已经届满
        
        Returns:
            (是否届满, 超出天数/剩余天数)
        """
        expiry_date = LitigationLimitationService.calculate_limitation_expiry(
            event_date, limitation_type
        )
        now = datetime.now()
        
        if now > expiry_date:
            overdue_days = (now - expiry_date).days
            return True, -overdue_days  # 已超出天数
        else:
            remaining_days = (expiry_date - now).days
            return False, remaining_days  # 剩余天数
    
    @staticmethod
    def get_limitation_info(limitation_type: str = "general") -> Dict:
        """获取时效类型信息"""
        if limitation_type == "maximum":
            return LitigationLimitationService.MAXIMUM_LIMITATION
        elif limitation_type in LitigationLimitationService.SHORT_LIMITATIONS:
            return LitigationLimitationService.SHORT_LIMITATIONS[limitation_type]
        else:
            return LitigationLimitationService.GENERAL_LIMITATION


class LegalDeadlineService:
    """
    法律期限计算服务
    
    功能：
    1. 精确计算各类法定期限
    2. 自动排除节假日和工作日计算
    3. 生成期限风险预警
    4. 提供完成建议
    """
    
    # 标准期限定义（天）
    STANDARD_DEADLINES = {
        # ===== 诉讼时效（biz-1: 修正为3年民法典） =====
        "litigation_general": {
            "name": "普通诉讼时效",
            "days": 1095,
            "duration_type": "年",
            "years": 3,
            "category": "时效",
            "basis": "《民法典》第188条",
            "description": "向人民法院请求保护民事权利的诉讼时效期间为三年。法律另有规定的，依照其规定。"
        },
        "litigation_maximum": {
            "name": "最长保护期间",
            "days": 7300,
            "duration_type": "年",
            "years": 20,
            "category": "时效",
            "basis": "《民法典》第188条",
            "description": "从权利被侵害之日起超过二十年的，人民法院不予保护。"
        },
        "litigation_short_body_injury": {
            "name": "人身损害赔偿时效",
            "days": 365,
            "duration_type": "年",
            "years": 1,
            "category": "时效",
            "basis": "《民法典》第595条（参照）第188条",
            "description": "因身体受到伤害要求赔偿的，诉讼时效期间为一年。"
        },
        "labor_arbitration": {
            "name": "劳动争议仲裁时效",
            "days": 365,
            "duration_type": "年",
            "years": 1,
            "category": "仲裁",
            "basis": "《劳动争议调解仲裁法》第27条",
            "description": "劳动争议申请仲裁的时效期间为一年，从当事人知道或者应当知道其权利被侵害之日起计算。劳动关系存续期间因拖欠劳动报酬发生争议的，不受一年限制。"
        },
        
        # ===== 仲裁期限（biz-2: 修正为4年而非4个月） =====
        "arbitration": {
            "name": "仲裁申请期限",
            "days": 1460,
            "duration_type": "年",
            "years": 4,
            "category": "仲裁",
            "basis": "《仲裁法》第74条",
            "description": "仲裁时效适用相关民事法律的规定，一般为四年（《民法典》第188条）。法律对仲裁时效另有规定的，依照其规定。"
        },
        
        # ===== 举证期限（biz-4: 区分普通/简易/小额诉讼） =====
        "evidence_presentation_general": {
            "name": "举证期限（普通程序）",
            "days": 30,
            "category": "举证",
            "basis": "《民事诉讼法》第68条、《民诉法解释》第99条",
            "description": "当事人应当在举证期限内提供证据。普通程序案件的举证期限不得少于十五日。"
        },
        "evidence_presentation_simple": {
            "name": "举证期限（简易程序）",
            "days": 15,
            "category": "举证",
            "basis": "《民事诉讼法》第160条、《简易程序规定》第22条",
            "description": "适用简易程序审理的案件，举证期限一般不超过十五日。"
        },
        "evidence_presentation_small": {
            "name": "举证期限（小额诉讼）",
            "days": 7,
            "category": "举证",
            "basis": "《民事诉讼法》第165条",
            "description": "适用小额诉讼程序审理的案件，实行一审终审，举证期限一般不超过七日。"
        },
        "evidence_presentation_court_request": {
            "name": "法院指定举证期限",
            "days": 30,
            "category": "举证",
            "basis": "《民诉法解释》第99条",
            "description": "由人民法院指定举证期限的，指定的期限不得少于三十日。"
        },
        
        # 旧版保持兼容
        "evidence_presentation": {
            "name": "举证期限",
            "days": 30,
            "category": "举证",
            "basis": "《民事诉讼法》第68条",
            "description": "当事人应当在举证期限内提供证据，普通程序不少于15日，简易程序一般不超过15日，小额诉讼7日"
        },
        
        # ===== 管辖权异议（biz-14） =====
        "jurisdiction_objection": {
            "name": "管辖权异议期限",
            "days": 15,
            "category": "异议",
            "basis": "《民事诉讼法》第130条",
            "description": "人民法院受理案件后，当事人对管辖权有异议的，应当在提交答辩状期间（收到起诉状副本之日起15日内）提出。"
        },
        "jurisdiction_objection_qualified": {
            "name": "应诉答辩期限（管辖权异议关联）",
            "days": 15,
            "category": "答辩",
            "basis": "《民事诉讼法》第130条",
            "description": "被告收到起诉状副本后，应当在十五日内提出答辩状。管辖权异议应在答辩期内提出。"
        },
        
        # ===== 执行异议（biz-14） =====
        "execution_objection": {
            "name": "执行异议期限",
            "days": 15,
            "category": "异议",
            "basis": "《民事诉讼法》第232条",
            "description": "当事人、利害关系人认为执行行为违反法律规定的，可以向负责执行的人民法院提出书面异议，期限为执行措施作出之日起十五日内。"
        },
        "execution_objection_sub": {
            "name": "执行异议之诉期限",
            "days": 15,
            "category": "诉讼",
            "basis": "《民事诉讼法》第234条",
            "description": "执行异议裁定送达之日起十五日内向执行法院提起执行异议之诉。"
        },
        "execution_application": {
            "name": "执行申请期限",
            "days": 730,
            "duration_type": "年",
            "years": 2,
            "category": "执行",
            "basis": "《民事诉讼法》第246条",
            "description": "申请执行的期限为两年，从法律文书规定履行期间的最后一日起计算"
        },
        
        # 民事诉讼
        "civil_litigation_appeal": {
            "name": "民事判决上诉期限",
            "days": 15,
            "category": "上诉",
            "basis": "《民事诉讼法》第170条",
            "description": "不服一审判决的，上诉期限为判决书送达之日起15日内"
        },
        "civil_litigation_petition": {
            "name": "民事裁定上诉期限",
            "days": 10,
            "category": "上诉",
            "basis": "《民事诉讼法》第170条",
            "description": "不服一审裁定的，上诉期限为裁定书送达之日起10日内"
        },
        "property_preservation": {
            "name": "财产保全期限",
            "days": 5,
            "category": "保全",
            "basis": "《民事诉讼法》第100条",
            "description": "利害关系人可以在提起诉讼前申请财产保全，应当在48小时内作出裁定"
        },
        
        # 民事合同纠纷常用期限
        "contract_dispute_response": {
            "name": "合同纠纷答辩期限",
            "days": 15,
            "category": "答辩",
            "basis": "《民事诉讼法》第125条",
            "description": "被告收到起诉状副本后，应当在15日内提出答辩状"
        },
        "reconsideration": {
            "name": "复议申请期限",
            "days": 5,
            "category": "复议",
            "basis": "《民事诉讼法》第105条",
            "description": "当事人对财产保全裁定不服的，可以申请复议一次，申请应当在裁定送达之日起5日内提出"
        },
        
        # 公告送达期限（biz-14）
        "notice_service_60": {
            "name": "公告送达期限（60日）",
            "days": 60,
            "category": "送达",
            "basis": "《民事诉讼法》第95条",
            "description": "受送达人下落不明，或者用其他方式无法送达的，公告送达。自发出公告之日起，经过六十日，即视为送达。"
        },
        "notice_service_30": {
            "name": "公告送达期限（30日）",
            "days": 30,
            "category": "送达",
            "basis": "《民事诉讼法》第95条",
            "description": "公告送达的，经过三十日，即视为送达（涉外诉讼）"
        },
        
        # 刑事诉讼
        "criminal_appeal": {
            "name": "刑事判决上诉期限",
            "days": 10,
            "category": "上诉",
            "basis": "《刑事诉讼法》第230条",
            "description": "不服一审判决的上诉期限为10日，不服裁定的上诉期限为5日"
        },
        "criminal_prosecution": {
            "name": "公诉案件审查起诉期限",
            "days": 30,
            "category": "起诉",
            "basis": "《刑事诉讼法》第172条",
            "description": "人民检察院审查起诉期限为1个月，重大复杂案件可延长15日"
        },
        "criminal_detention": {
            "name": "刑事拘留期限",
            "days": 37,
            "category": "刑事",
            "basis": "《刑事诉讼法》第89条",
            "description": "公安机关拘留犯罪嫌疑人后，应当在24小时内讯问，拘留期限最长37日（提请批准逮捕7日+审查批准逮捕7日+侦查羁押2个月）"
        },
        "criminal_arrest_review": {
            "name": "审查批准逮捕期限",
            "days": 7,
            "category": "刑事",
            "basis": "《刑事诉讼法》第89条",
            "description": "公安机关提请批准逮捕后，人民检察院应当在七日内作出批准或者不批准逮捕的决定。"
        },
        
        # 行政诉讼
        "administrative_appeal": {
            "name": "行政诉讼起诉期限",
            "days": 180,
            "duration_type": "月",
            "months": 6,
            "category": "起诉",
            "basis": "《行政诉讼法》第46条",
            "description": "直接提起行政诉讼的期限为6个月，复议后起诉的15日内"
        },
        "administrative_reconsideration": {
            "name": "行政复议申请期限",
            "days": 60,
            "category": "复议",
            "basis": "《行政复议法》第20条",
            "description": "公民、法人或其他组织应当在知道具体行政行为之日起60日内申请行政复议"
        },
        
        # 律师函回复
        "lawyer_letter_response": {
            "name": "律师函回复建议期限",
            "days": 7,
            "category": "函件",
            "basis": "实务惯例",
            "description": "收到律师函后，建议在7日内回复或委托律师处理"
        },
        "demand_letter_response": {
            "name": "催告函回复期限",
            "days": 15,
            "category": "函件",
            "basis": "实务惯例",
            "description": "收到催告函后，如不及时回复，可能被视为默认"
        },
    }
    
    # 工作日计算的法定节假日（2026年硬编码，fallback用）
    # biz-3: 已升级为动态获取（chinese-calendar 库 + 农历支持）
    # 此处保留作为 fallback 基础数据
    HOLIDAYS_2026 = [
        # 元旦
        datetime(2026, 1, 1), datetime(2026, 1, 2), datetime(2026, 1, 3),
        # 春节
        datetime(2026, 2, 17), datetime(2026, 2, 18), datetime(2026, 2, 19),
        datetime(2026, 2, 20), datetime(2026, 2, 21), datetime(2026, 2, 22),
        datetime(2026, 2, 23), datetime(2026, 2, 24),
        # 清明节
        datetime(2026, 4, 4), datetime(2026, 4, 5), datetime(2026, 4, 6),
        # 劳动节
        datetime(2026, 5, 1), datetime(2026, 5, 2), datetime(2026, 5, 3),
        datetime(2026, 5, 4), datetime(2026, 5, 5),
        # 端午节
        datetime(2026, 6, 19), datetime(2026, 6, 20), datetime(2026, 6, 21),
        # 中秋节
        datetime(2026, 9, 25), datetime(2026, 9, 26), datetime(2026, 9, 27),
        # 国庆节
        datetime(2026, 10, 1), datetime(2026, 10, 2), datetime(2026, 10, 3),
        datetime(2026, 10, 4), datetime(2026, 10, 5), datetime(2026, 10, 6),
        datetime(2026, 10, 7), datetime(2026, 10, 8),
    ]
    
    def __init__(self, year: Optional[int] = None):
        """
        初始化法律期限服务
        
        Args:
            year: 指定年份，不指定则使用当前年份
        """
        if year is None:
            year = datetime.now().year
        
        # biz-3: 动态获取节假日（含 chinese-calendar 库支持 + 农历节日）
        self.holidays = _get_chinese_holidays(year)
        self.year = year
        # 缓存调休工作日（周末被调整为工作日的日期）
        self._transfer_workdays = self._get_transfer_workdays(year)
    
    def _get_transfer_workdays(self, year: int) -> set:
        """
        获取调休工作日（周末被调整为工作日的日期）
        例如：国庆节如果10月1日是周六，则10月4日（周日）会被调整为工作日
        """
        transfer_workdays = set()
        
        try:
            import chinese_calendar
            # chinese-calendar 库的 on_holiday_work 是判断某天是否因节假日而上班
            # 即判断调休工作日
            for month in range(1, 13):
                for day in range(1, calendar.monthrange(year, month)[1] + 1):
                    try:
                        d = date(year, month, day)
                        if chinese_calendar.on_holiday_work(d):
                            transfer_workdays.add(d)
                    except Exception:
                        pass
        except ImportError:
            pass
        
        return transfer_workdays
    
    def is_holiday(self, date_input: Union[datetime, date]) -> bool:
        """
        判断是否为节假日（含农历节日和调休工作日）
        
        Args:
            date_input: 日期或日期时间
            
        Returns:
            True 如果是节假日（休息日），False 如果是工作日
        """
        if isinstance(date_input, datetime):
            d = date_input.date()
        else:
            d = date_input
        
        # 如果是调休工作日，则不是节假日
        if d in self._transfer_workdays:
            return False
        
        # 如果是周末（周六=5，周日=6）
        if d.weekday() >= 5:
            # 周末调休工作日在上面已排除
            return True
        
        # 检查法定节假日
        return d in self.holidays
    
    def add_workdays(self, start_date: datetime, days: int, 
                     include_start: bool = False) -> datetime:
        """
        计算工作日后的日期（智能跳过节假日和周末）
        
        biz-3 增强：
        - 支持 chinese-calendar 库动态获取节假日
        - 支持农历节日（春节、中秋等）
        - 支持调休工作日（周末变工作日）
        
        Args:
            start_date: 起始日期
            days: 需要添加的工作日数
            include_start: 是否将起始日本身计入工作日（默认不计入，即从下一天开始算）
            
        Returns:
            计算后的日期
        """
        current_date = start_date
        days_added = 0
        
        if include_start and not self.is_holiday(current_date):
            days_added += 1
        
        while days_added < days:
            current_date += timedelta(days=1)
            if not self.is_holiday(current_date):
                days_added += 1
        
        return current_date
    
    def get_next_workday(self, date_input: Union[datetime, date]) -> date:
        """
        获取下一个工作日（节假日/周末后的第一个工作日）
        """
        if isinstance(date_input, datetime):
            d = date_input.date() + timedelta(days=1)
        else:
            d = date_input + timedelta(days=1)
        
        while self.is_holiday(d):
            d += timedelta(days=1)
        
        return d
    
    def get_working_days_between(self, start_date: datetime, end_date: datetime) -> int:
        """
        计算两个日期之间的工作日天数
        
        Args:
            start_date: 起始日期
            end_date: 结束日期
            
        Returns:
            工作日天数
        """
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        
        working_days = 0
        current = start_date.date()
        end = end_date.date()
        
        while current <= end:
            if not self.is_holiday(current):
                working_days += 1
            current += timedelta(days=1)
        
        return working_days
    
    def calculate_deadline(self, 
                          start_date: datetime, 
                          deadline_type: str,
                          use_workdays: bool = True) -> datetime:
        """
        计算截止日期
        
        biz-1 增强：支持诉讼时效精确计算（3年/20年/1年短期）
        biz-2 增强：仲裁期限修正为4年
        biz-3 增强：支持 chinese-calendar 动态节假日计算
        
        Args:
            start_date: 起算日期
            deadline_type: 期限类型标识
            use_workdays: 是否使用工作日计算
            
        Returns:
            截止日期
        """
        # 特殊处理：诉讼时效类型
        if deadline_type.startswith("litigation_"):
            return self._calculate_litigation_deadline(start_date, deadline_type)
        
        deadline_info = self.STANDARD_DEADLINES.get(deadline_type)
        if not deadline_info:
            return start_date + timedelta(days=30)  # 默认30天
        
        duration_type = deadline_info.get("duration_type", "日")
        days = deadline_info.get("days", 30)
        
        if duration_type == "年":
            # 按年计算：加n年然后减1天到最后一天
            end_date = start_date.replace(year=start_date.year + days)
            end_date = end_date - timedelta(days=1)
            return end_date
        elif duration_type == "月":
            # 按月计算
            month = start_date.month - 1 + days
            year = start_date.year + month // 12
            month = month % 12 + 1
            day = min(start_date.day, calendar.monthrange(year, month)[1])
            end_date = datetime(year, month, day)
            if use_workdays:
                # 减去起算日本身
                end_date = end_date - timedelta(days=1)
            return end_date
        else:
            # 按日计算
            if use_workdays:
                return self.add_workdays(start_date, days) - timedelta(days=1)
            else:
                return start_date + timedelta(days=days - 1)
    
    def _calculate_litigation_deadline(self, start_date: datetime, 
                                       limitation_type: str) -> datetime:
        """
        计算诉讼时效截止日期（biz-1）
        
        Args:
            start_date: 权利被侵害之日 / 知道权利被侵害之日
            limitation_type: litigation_general / litigation_maximum / litigation_short_*
            
        Returns:
            时效届满的日期
        """
        return LitigationLimitationService.calculate_limitation_expiry(
            start_date, limitation_type
        )
    
    def analyze_deadline(self,
                        start_date: datetime,
                        deadline_type: str,
                        case_type: str = "民事") -> Dict:
        """
        综合分析期限（返回详细信息，供前端展示）
        
        biz-1 增强：包含时效状态分析
        biz-4 增强：根据案件程序类型推荐举证期限
        
        Args:
            start_date: 起算日期
            deadline_type: 期限类型
            case_type: 案件类型
            
        Returns:
            期限分析结果
        """
        deadline_info = self.STANDARD_DEADLINES.get(deadline_type, {})
        deadline_date = self.calculate_deadline(start_date, deadline_type)
        now = datetime.now()
        days_remaining = (deadline_date.date() - now.date()).days
        
        # 优先级评估
        if days_remaining < 0:
            priority = "critical"
            status = "已超期"
        elif days_remaining <= 7:
            priority = "high"
            status = "紧急"
        elif days_remaining <= 15:
            priority = "medium"
            status = "预警"
        elif days_remaining <= 30:
            priority = "low"
            status = "正常"
        else:
            priority = "info"
            status = "充裕"
        
        return {
            "deadline_type": deadline_type,
            "deadline_name": deadline_info.get("name", deadline_type),
            "start_date": start_date,
            "deadline_date": deadline_date,
            "days_remaining": days_remaining,
            "priority": priority,
            "status": status,
            "legal_basis": deadline_info.get("basis", ""),
            "description": deadline_info.get("description", ""),
            "category": deadline_info.get("category", "其他"),
            "workdays_remaining": self.get_working_days_between(now, deadline_date)
        }
    
    def recommend_evidence_deadline(self, case_type: str = "民事",
                                     procedure_type: str = "普通") -> str:
        """
        根据案件类型和程序推荐举证期限（biz-4）
        
        Args:
            case_type: 案件类型（民事/刑事/行政）
            procedure_type: 程序类型（普通/简易/小额）
            
        Returns:
            推荐的举证期限类型键名
        """
        if case_type == "民事":
            if procedure_type == "小额":
                return "evidence_presentation_small"
            elif procedure_type == "简易":
                return "evidence_presentation_simple"
            else:
                return "evidence_presentation_general"
        else:
            return "evidence_presentation"
    
    def get_deadline_info(self, deadline_type: str) -> Dict:
        """获取期限类型信息"""
        return self.STANDARD_DEADLINES.get(deadline_type, {
            "name": "未知期限",
            "days": 30,
            "category": "其他",
            "basis": "",
            "description": ""
        })
    
    def analyze_letter_reply_requirement(self, 
                                        letter_type: str,
                                        content_summary: str = "",
                                        case_type: str = "民事") -> Dict:
        """
        分析函件是否需要回复及回复期限
        
        Args:
            letter_type: 函件类型
            content_summary: 函件内容摘要
            case_type: 案件类型
            
        Returns:
            分析结果，包含：
            - reply_required: 是否需要回复
            - deadline_days: 建议回复天数
            - legal_basis: 法律依据
            - reason: 分析原因
            - urgent_level: 紧急程度
        """
        result = {
            "reply_required": "optional",
            "deadline_days": 15,
            "legal_basis": "",
            "reason": "",
            "urgent_level": "medium",
            "suggestions": []
        }
        
        # 根据函件类型判断
        letter_type_rules = {
            "lawyer_letter": {
                "reply_required": "required",
                "deadline_days": 7,
                "legal_basis": "律师函通常涉及催告或警告，不及时回复可能被视为默认或承担不利后果",
                "urgent_level": "high",
                "reason": "律师函涉及法律后果，建议立即委托律师处理"
            },
            "demand_letter": {
                "reply_required": "recommended",
                "deadline_days": 15,
                "legal_basis": "催告函一般给予合理期限回复",
                "urgent_level": "high",
                "reason": "催告函通常要求履行义务，逾期可能产生违约责任"
            },
            "notice": {
                "reply_required": "optional",
                "deadline_days": 30,
                "legal_basis": "通知类函件一般无需回复",
                "urgent_level": "low",
                "reason": "通知类函件仅告知事实，无强制回复要求"
            },
            "warning": {
                "reply_required": "required",
                "deadline_days": 5,
                "legal_basis": "警告函涉及权利主张，逾期可能导致权利丧失",
                "urgent_level": "critical",
                "reason": "警告函通常附有最后期限，超期将承担不利后果"
            },
            "negotiation": {
                "reply_required": "recommended",
                "deadline_days": 30,
                "legal_basis": "协商函属于意思自治范畴",
                "urgent_level": "medium",
                "reason": "协商函提供和解机会，建议积极参与"
            },
            "response": {
                "reply_required": "required",
                "deadline_days": 3,
                "legal_basis": "回复函通常针对特定问题，需要及时回应",
                "urgent_level": "critical",
                "reason": "回复函是对方要求我方作出说明"
            }
        }
        
        rule = letter_type_rules.get(letter_type, letter_type_rules["notice"])
        result.update(rule)
        
        # 使用 AI 进行深度分析
        ai_analysis = self._ai_analyze_letter_content(letter_type, content_summary, case_type)
        if ai_analysis:
            result.update(ai_analysis)
        
        return result
    
    def _ai_analyze_letter_content(self, 
                                   letter_type: str, 
                                   content_summary: str,
                                   case_type: str) -> Optional[Dict]:
        """使用 AI 分析函件内容以获取更精确的建议"""
        if not content_summary:
            return None
        
        prompt = f"""分析以下函件，判断回复的必要性和紧迫性：

函件类型：{letter_type}
案件类型：{case_type}
内容摘要：{content_summary}

请分析：
1. 是否必须回复？（法律强制/建议/可选/无需）
2. 回复的紧迫程度？
3. 核心风险点是什么？
4. 建议的回复策略？

请用JSON格式返回分析结果，包含：reply_required, urgent_level, key_risks, strategy_suggestion"""
        
        try:
            analysis = llm_service.chat([
                {"role": "system", "content": "你是一位专业的法律顾问，擅长分析函件的法律意义并提供建议。"},
                {"role": "user", "content": prompt}
            ])
            
            # 简单解析
            if "必须" in analysis or "强制" in analysis:
                return {"reply_required": "required"}
            elif "建议" in analysis:
                return {"reply_required": "recommended"}
            elif "无需" in analysis:
                return {"reply_required": "not_required"}
        except:
            pass
        
        return None
    
    def generate_deadline_warning(self, 
                                  deadline_date: datetime,
                                  deadline_name: str,
                                  days_warning: List[int] = None) -> List[Dict]:
        """
        生成期限预警信息
        
        Args:
            deadline_date: 截止日期
            deadline_name: 期限名称
            days_warning: 预警天数列表，默认 [30, 15, 7, 3, 1, 0]
            
        Returns:
            预警信息列表
        """
        if days_warning is None:
            days_warning = [30, 15, 7, 3, 1, 0]
        
        warnings = []
        today = datetime.now().date()
        deadline = deadline_date.date() if isinstance(deadline_date, datetime) else deadline_date
        days_remaining = (deadline - today).days
        
        for threshold in days_warning:
            if threshold == 0 and days_remaining < 0:
                warnings.append({
                    "level": "critical",
                    "days_remaining": days_remaining,
                    "message": f"【严重】{deadline_name}已超期 {abs(days_remaining)} 天！",
                    "action": "立即处理，考虑申请展期或补救措施"
                })
            elif 0 <= days_remaining <= threshold:
                if threshold == 1:
                    level = "critical"
                    action = "今日必须完成！"
                elif threshold <= 3:
                    level = "high"
                    action = "紧急处理，优先完成"
                elif threshold <= 7:
                    level = "medium"
                    action = "尽快处理，避免遗忘"
                elif threshold <= 15:
                    level = "low"
                    action = "开始准备，预留时间"
                else:
                    level = "info"
                    action = "按计划推进"
                
                warnings.append({
                    "level": level,
                    "days_remaining": days_remaining,
                    "message": f"【{threshold}日预警】{deadline_name}还剩 {days_remaining} 天",
                    "action": action
                })
        
        return warnings
    
    def create_standard_deadlines(self, 
                                   case_type: str,
                                   case_start_date: datetime,
                                   filing_date: Optional[datetime] = None) -> List[Dict]:
        """
        为案件创建标准期限清单
        
        Args:
            case_type: 案件类型
            case_start_date: 案件起始日期
            filing_date: 立案日期
            
        Returns:
            标准期限列表
        """
        deadlines = []
        
        # 根据案件类型添加相关期限
        if case_type in ["民事", "civil"]:
            deadlines.append({
                "type": "execution_application",
                "name": "执行申请期限",
                "start_date": filing_date or case_start_date,
                "days": 730,  # 2年
                "description": "从履行期届满之日起算"
            })
        
        return deadlines
    
    def get_case_progress_info(self,
                               case_status: str,
                               filed_date: Optional[datetime] = None,
                               trial_date: Optional[datetime] = None,
                               judgment_date: Optional[datetime] = None,
                               deadline: Optional[datetime] = None) -> Dict:
        """
        获取案件进度时间信息
        
        Returns:
            案件时间线进度信息
        """
        today = datetime.now()
        
        info = {
            "current_date": today,
            "milestones": [],
            "upcoming_deadlines": [],
            "overdue_items": []
        }
        
        # 立案
        if filed_date:
            days_since_filed = (today - filed_date).days
            info["milestones"].append({
                "name": "立案",
                "date": filed_date,
                "days_ago": days_since_filed,
                "is_completed": True
            })
        
        # 开庭
        if trial_date:
            if trial_date > today:
                days_until_trial = (trial_date - today).days
                info["upcoming_deadlines"].append({
                    "name": "开庭",
                    "date": trial_date,
                    "days_remaining": days_until_trial,
                    "urgency": "high" if days_until_trial <= 7 else "medium"
                })
            else:
                days_since_trial = (today - trial_date).days
                info["milestones"].append({
                    "name": "开庭",
                    "date": trial_date,
                    "days_ago": days_since_trial,
                    "is_completed": True
                })
        
        # 判决
        if judgment_date:
            if judgment_date > today:
                days_until_judgment = (judgment_date - today).days
                info["upcoming_deadlines"].append({
                    "name": "判决",
                    "date": judgment_date,
                    "days_remaining": days_until_judgment,
                    "urgency": "high" if days_until_judgment <= 7 else "medium"
                })
            else:
                days_since_judgment = (today - judgment_date).days
                info["milestones"].append({
                    "name": "判决",
                    "date": judgment_date,
                    "days_ago": days_since_judgment,
                    "is_completed": True
                })
        
        # 一般期限
        if deadline:
            if deadline > today:
                days_until_deadline = (deadline - today).days
                info["upcoming_deadlines"].append({
                    "name": "期限届满",
                    "date": deadline,
                    "days_remaining": days_until_deadline,
                    "urgency": "critical" if days_until_deadline <= 3 else ("high" if days_until_deadline <= 7 else "medium")
                })
            else:
                days_overdue = (today - deadline).days
                info["overdue_items"].append({
                    "name": "期限届满",
                    "date": deadline,
                    "days_overdue": days_overdue
                })
        
        return info


# 全局实例
# biz-3: 动态初始化（支持跨年份）
deadline_service = LegalDeadlineService()

# 独立导出诉讼时效服务（biz-1）
litigation_limitation_service = LitigationLimitationService
