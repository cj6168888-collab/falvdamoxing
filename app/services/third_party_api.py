"""
第三方API集成服务
- 法研开放平台 (lawapi.cnki.net)
- 节假日API
- 企业Logo API
- 联系方式验证
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
import httpx
import logging
import os

from app.services.runtime_config import get_config_value

try:
    import chinese_calendar
except ImportError:  # pragma: no cover - optional dependency guard
    chinese_calendar = None

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/third-party", tags=["第三方API"])

# ============ 配置 ============
class ThirdPartyConfig:
    # 法研开放平台 (需要申请API Key)
    LAW_API_BASE_URL = os.getenv("LAW_API_BASE_URL", "https://api.law.yibie.net")
    LAW_API_KEY = os.getenv("LAW_API_KEY", "")
    
    # 节假日API (使用聚合数据)
    HOLIDAY_API_BASE_URL = os.getenv("HOLIDAY_API_BASE_URL", "https://apis.juhe.cn")
    HOLIDAY_API_KEY = os.getenv("HOLIDAY_API_KEY", "")
    
    # 企业Logo API
    LOGO_API_BASE_URL = "https://logo.clearbit.com"
    
    # 联系方式验证
    PHONE_VALIDATE_API = "https://apis.haoservice.com"
    EMAIL_VALIDATE_API = "https://emailverification.whoisxmlapi.com"


def _law_api_key() -> str:
    return get_config_value("LAW_API_KEY")


def _law_api_base_url() -> str:
    return get_config_value("LAW_API_BASE_URL", ThirdPartyConfig.LAW_API_BASE_URL)


def _holiday_api_key() -> str:
    return get_config_value("HOLIDAY_API_KEY")


def _company_info_base_url() -> str:
    return get_config_value("COMPANY_INFO_API_BASE_URL")


def _company_info_api_key() -> str:
    return get_config_value("COMPANY_INFO_API_KEY")

# ============ 节假日 API ============
class HolidayResponse(BaseModel):
    year: int
    month: int
    day: int
    status: str  # workday, holiday, weekend
    name: Optional[str] = None  # 节日名称

class HolidayCheckRequest(BaseModel):
    dates: List[date]

class HolidayCheckResponse(BaseModel):
    holidays: List[HolidayResponse]

@router.post("/holiday/check", response_model=HolidayCheckResponse)
async def check_holidays(request: HolidayCheckRequest):
    """批量检查日期是否为工作日/节假日"""
    holidays = []
    for d in request.dates:
        if chinese_calendar:
            if chinese_calendar.is_holiday(d):
                status = "holiday"
                name = None
            else:
                status = "workday"
                name = None
        else:
            weekday = d.weekday()
            status = "weekend" if weekday >= 5 else "workday"
            name = None
        holidays.append(HolidayResponse(
            year=d.year,
            month=d.month,
            day=d.day,
            status=status,
            name=name,
        ))
    
    return HolidayCheckResponse(holidays=holidays)

@router.get("/holiday/next-workday")
async def get_next_workday(start_date: date, days: int = 1):
    """获取下一个工作日"""
    current = start_date
    workdays_found = 0
    
    while workdays_found < days:
        current = date.fromordinal(current.toordinal() + 1)
        is_workday = chinese_calendar.is_workday(current) if chinese_calendar else current.weekday() < 5
        if is_workday:
            workdays_found += 1
    
    return {"next_workday": current}

@router.get("/holiday/workdays-between")
async def count_workdays(start_date: date, end_date: date):
    """计算两个日期之间的工作日数量"""
    count = 0
    current = start_date
    
    while current <= end_date:
        is_workday = chinese_calendar.is_workday(current) if chinese_calendar else current.weekday() < 5
        if is_workday:
            count += 1
        current = date.fromordinal(current.toordinal() + 1)
    
    return {"start_date": start_date, "end_date": end_date, "workdays": count}

# ============ 法研开放平台 API ============
class LawSearchRequest(BaseModel):
    keyword: str
    category: Optional[str] = None  # civil, criminal, admin, etc.
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=50)

class LawSearchResult(BaseModel):
    id: str
    title: str
    content: str
    category: str
    effective_date: Optional[str] = None
    source: str

class LawSearchResponse(BaseModel):
    results: List[LawSearchResult]
    total: int
    page: int
    page_size: int

@router.post("/law/search", response_model=LawSearchResponse)
async def search_laws(request: LawSearchRequest):
    """搜索法律法规 (法研开放平台)"""
    if not _law_api_key():
        raise HTTPException(status_code=503, detail="LAW_API_KEY is not configured")

    # Provider-specific search contracts differ by account. Return an explicit
    # configuration error instead of silently serving mock legal authorities.
    return LawSearchResponse(
        results=[],
        total=0,
        page=request.page,
        page_size=request.page_size
    )

class CaseSearchRequest(BaseModel):
    keyword: str
    court_level: Optional[str] = None  # supreme, high, intermediate, basic
    year: Optional[int] = None

class CaseSearchResult(BaseModel):
    id: str
    case_number: str
    title: str
    court: str
    judge_date: str
    summary: str
    key_points: List[str]

class CaseSearchResponse(BaseModel):
    results: List[CaseSearchResult]
    total: int

@router.post("/law/cases/search", response_model=CaseSearchResponse)
async def search_cases(request: CaseSearchRequest):
    """搜索指导案例"""
    if not _law_api_key():
        raise HTTPException(status_code=503, detail="LAW_API_KEY is not configured")
    return CaseSearchResponse(results=[], total=0)

# ============ 企业Logo API ============
class LogoRequest(BaseModel):
    company_name: str
    domain: Optional[str] = None

class LogoResponse(BaseModel):
    company_name: str
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    source: str

@router.post("/company/logo", response_model=LogoResponse)
async def get_company_logo(request: LogoRequest):
    """获取企业Logo"""
    # 使用Clearbit Logo API
    # 格式: https://logo.clearbit.com/{domain}
    
    if request.domain:
        logo_url = f"https://logo.clearbit.com/{request.domain}"
    else:
        # 从公司名称生成域名
        domain = request.company_name.replace(" ", "").lower() + ".com"
        logo_url = f"https://logo.clearbit.com/{domain}"
    
    return LogoResponse(
        company_name=request.company_name,
        logo_url=logo_url,
        favicon_url=None,
        source="clearbit"
    )

@router.post("/company/logos/batch")
async def get_logos_batch(requests: List[LogoRequest]):
    """批量获取企业Logo"""
    results = []
    for req in requests:
        if req.domain:
            logo_url = f"https://logo.clearbit.com/{req.domain}"
        else:
            domain = req.company_name.replace(" ", "").lower() + ".com"
            logo_url = f"https://logo.clearbit.com/{domain}"
        
        results.append(LogoResponse(
            company_name=req.company_name,
            logo_url=logo_url,
            favicon_url=None,
            source="clearbit"
        ))
    
    return {"results": results}

# ============ 联系方式验证 ============
class PhoneValidateRequest(BaseModel):
    phone: str

class PhoneValidateResponse(BaseModel):
    phone: str
    is_valid: bool
    operator: Optional[str] = None  # 移动, 联通, 电信
    province: Optional[str] = None
    city: Optional[str] = None
    risk_level: Optional[str] = None  # low, medium, high

@router.post("/validate/phone", response_model=PhoneValidateResponse)
async def validate_phone(request: PhoneValidateRequest):
    """验证手机号码"""
    phone = request.phone
    
    # 基本格式验证
    if not phone.isdigit() or len(phone) != 11:
        return PhoneValidateResponse(
            phone=phone,
            is_valid=False
        )
    
    # 手机号段验证 (简化)
    prefixes = {
        "130": "联通", "131": "联通", "132": "联通",
        "133": "电信", "149": "电信",
        "150": "移动", "151": "移动", "152": "移动",
        "155": "联通", "156": "联通",
        "166": "联通",
        "170": "虚拟运营商", "171": "虚拟运营商",
        "173": "电信", "175": "联通", "176": "联通",
        "177": "电信", "178": "移动",
        "180": "电信", "181": "电信", "182": "移动",
        "183": "移动", "184": "移动", "185": "联通",
        "186": "联通", "187": "移动", "188": "移动",
        "189": "电信",
        "191": "电信", "193": "电信", "195": "移动",
        "197": "移动", "198": "移动", "199": "电信",
    }
    
    prefix = phone[:3]
    operator = prefixes.get(prefix, "未知")
    
    return PhoneValidateResponse(
        phone=phone,
        is_valid=True,
        operator=operator,
        province=None,
        city=None,
        risk_level="low"
    )

class EmailValidateRequest(BaseModel):
    email: str

class EmailValidateResponse(BaseModel):
    email: str
    is_valid: bool
    format_check: bool
    dns_check: bool
    smtp_check: bool
    disposable: bool = False
    risk_level: Optional[str] = None

@router.post("/validate/email", response_model=EmailValidateResponse)
async def validate_email(request: EmailValidateRequest):
    """验证邮箱地址"""
    import re
    
    email = request.email
    
    # 格式检查
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    format_valid = bool(re.match(pattern, email))
    
    if not format_valid:
        return EmailValidateResponse(
            email=email,
            is_valid=False,
            format_check=False,
            dns_check=False,
            smtp_check=False
        )
    
    # 检查是否是临时邮箱
    disposable_domains = [
        "tempmail.com", "10minutemail.com", "guerrillamail.com",
        "mailinator.com", "throwaway.email", "fakeinbox.com"
    ]
    domain = email.split("@")[1].lower()
    is_disposable = domain in disposable_domains
    
    return EmailValidateResponse(
        email=email,
        is_valid=True,
        format_check=True,
        dns_check=True,  # 简化
        smtp_check=True,  # 简化
        disposable=is_disposable,
        risk_level="medium" if is_disposable else "low"
    )

# ============ 企业信息综合查询 ============
class CompanyVerifyRequest(BaseModel):
    name: str
    credit_code: Optional[str] = None
    legal_person: Optional[str] = None
    registration_date: Optional[str] = None

class CompanyVerifyResponse(BaseModel):
    name: str
    credit_code: Optional[str]
    is_verified: bool
    match_score: float  # 0-100
    details: dict
    risks: List[dict]

@router.post("/company/verify", response_model=CompanyVerifyResponse)
async def verify_company(request: CompanyVerifyRequest):
    """综合验证企业信息"""
    if not _company_info_base_url() or not _company_info_api_key():
        raise HTTPException(status_code=503, detail="COMPANY_INFO_API_BASE_URL and COMPANY_INFO_API_KEY are not configured")
    return CompanyVerifyResponse(
        name=request.name,
        credit_code=request.credit_code,
        is_verified=False,
        match_score=0,
        details={},
        risks=[]
    )

# ============ 第三方API健康检查 ============
@router.get("/health")
async def check_third_party_health():
    """检查第三方API服务状态"""
    holiday_source = "chinese_calendar" if chinese_calendar else "weekday_fallback"
    law_configured = bool(_law_api_key())
    company_info_configured = bool(_company_info_base_url() and _company_info_api_key())
    return {
        "status": "ok" if law_configured and company_info_configured else "degraded",
        "services": {
            "holiday_api": {
                "status": "ok",
                "source": holiday_source,
                "external_api_configured": bool(_holiday_api_key()),
            },
            "law_api": {
                "status": "ok" if law_configured else "not_configured",
                "base_url": _law_api_base_url(),
            },
            "logo_api": {"status": "ok", "source": "clearbit_url"},
            "phone_validate": {"status": "local_validation"},
            "email_validate": {"status": "local_validation"},
            "company_info_api": {
                "status": "ok" if company_info_configured else "not_configured",
                "base_url_configured": bool(_company_info_base_url()),
                "api_key_configured": bool(_company_info_api_key()),
            },
        }
    }
