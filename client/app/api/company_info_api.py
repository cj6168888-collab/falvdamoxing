# -*- coding: utf-8 -*-
"""
企业信息查询API - 天眼查/企查查风格
通过公开API查询企业工商信息
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Optional, List
import httpx
import os
from app.services.runtime_config import get_config_value

router = APIRouter(prefix="/api/company-info", tags=["企业信息查询"])


def _company_info_base_url() -> str:
    return get_config_value("COMPANY_INFO_API_BASE_URL").rstrip("/")


def _company_info_api_key() -> str:
    return get_config_value("COMPANY_INFO_API_KEY")


def _company_info_timeout() -> float:
    return float(os.getenv("COMPANY_INFO_API_TIMEOUT", "15"))


def _ensure_company_provider_configured() -> None:
    if not _company_info_base_url() or not _company_info_api_key():
        raise HTTPException(
            status_code=503,
            detail="COMPANY_INFO_API_BASE_URL and COMPANY_INFO_API_KEY are not configured",
        )


def _auth_headers() -> dict[str, str]:
    api_key = _company_info_api_key()
    return {
        "Authorization": f"Bearer {api_key}",
        "X-API-Key": api_key,
        "Accept": "application/json",
    }


def _first_value(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _payload_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "items", "results", "list", "companies"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = _payload_items(value)
            if nested:
                return nested
    return [payload]


def _normalize_company_payload(payload: dict[str, Any], fallback_name: str) -> CompanyInfo:
    return CompanyInfo(
        name=str(_first_value(payload, "name", "company_name", "companyName", "entName") or fallback_name),
        unified_social_credit_code=_first_value(payload, "unified_social_credit_code", "credit_code", "creditCode", "uscc"),
        legal_representative=_first_value(payload, "legal_representative", "legalPerson", "legal_person", "representative"),
        registered_capital=_first_value(payload, "registered_capital", "registeredCapital", "regCapital"),
        paid_capital=_first_value(payload, "paid_capital", "paidCapital"),
        establishment_date=_first_value(payload, "establishment_date", "estiblishTime", "establishDate", "registration_date"),
        business_term=_first_value(payload, "business_term", "businessTerm", "term"),
        registration_authority=_first_value(payload, "registration_authority", "regInstitute", "authority"),
        company_type=_first_value(payload, "company_type", "companyType", "type"),
        industry=_first_value(payload, "industry", "industryName"),
        approval_date=_first_value(payload, "approval_date", "approvedTime", "approvalDate"),
        address=_first_value(payload, "address", "regLocation"),
        business_scope=_first_value(payload, "business_scope", "businessScope", "scope"),
        shareholders=_first_value(payload, "shareholders", "holders", "investors") or [],
        board_members=_first_value(payload, "board_members", "staff", "members") or [],
        changes=_first_value(payload, "changes", "changeRecords") or [],
        status=_first_value(payload, "status", "regStatus") or "unknown",
    )


async def _provider_get(path: str, params: dict[str, Any]) -> Any:
    _ensure_company_provider_configured()
    url = f"{_company_info_base_url()}/{path.lstrip('/')}"
    async with httpx.AsyncClient(timeout=_company_info_timeout()) as client:
        response = await client.get(url, params=params, headers=_auth_headers())
    if response.status_code in (401, 403):
        raise HTTPException(status_code=502, detail="Company info provider authentication failed")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Company not found")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Company info provider request failed")
    return response.json()


async def query_company_info(company_name: str) -> CompanyInfo:
    normalized_name = normalize_company_name(company_name)
    payload = await _provider_get("company", {"name": normalized_name})
    items = _payload_items(payload)
    if not items:
        raise HTTPException(status_code=404, detail="Company not found")
    return _normalize_company_payload(items[0], normalized_name)


async def search_company_provider(keyword: str) -> list[CompanyInfo]:
    payload = await _provider_get("search", {"keyword": keyword})
    items = _payload_items(payload)
    return [_normalize_company_payload(item, keyword) for item in items]


@router.get("/search")
async def search_companies_get(keyword: str):
    """
    搜索企业信息 (GET)
    支持按企业名称模糊搜索
    """
    try:
        return await search_company_provider(keyword)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

class CompanyInfo(BaseModel):
    """企业基本信息"""
    name: str  # 企业名称
    unified_social_credit_code: Optional[str] = None  # 统一社会信用代码
    legal_representative: Optional[str] = None  # 法定代表人
    registered_capital: Optional[str] = None  # 注册资本
    paid_capital: Optional[str] = None  # 实缴资本
    establishment_date: Optional[str] = None  # 成立日期
    business_term: Optional[str] = None  # 营业期限
    registration_authority: Optional[str] = None  # 登记机关
    company_type: Optional[str] = None  # 企业类型
    industry: Optional[str] = None  # 所属行业
    approval_date: Optional[str] = None  # 核准日期
    address: Optional[str] = None  # 企业地址
    business_scope: Optional[str] = None  # 经营范围
    shareholders: Optional[List[dict]] = None  # 股东信息
    board_members: Optional[List[dict]] = None  # 董监高信息
    changes: Optional[List[dict]] = None  # 变更记录
    status: Optional[str] = None  # 企业状态

class CompanySearchRequest(BaseModel):
    """企业搜索请求"""
    company_name: str  # 企业名称（支持模糊搜索）
    search_type: str = "name"  # 搜索类型: name=按名称, credit_code=按信用代码

class CompanyVerifyRequest(BaseModel):
    """企业信息验证请求"""
    company_name: str
    legal_representative: Optional[str] = None  # 用户提交的法代信息
    registered_capital: Optional[str] = None  # 用户提交的注册资本
    shareholders: Optional[List[str]] = None  # 用户提交的股东名单
    board_members: Optional[List[dict]] = None  # 用户提交的董监高名单

class CompanyVerifyResponse(BaseModel):
    """企业信息验证响应"""
    official_info: CompanyInfo  # 官方查询到的信息
    discrepancies: List[dict]  # 与用户提交不一致的项目
    warnings: List[str]  # 警告信息
    needs_confirmation: bool  # 是否需要用户确认


def extract_company_keywords(name: str) -> List[str]:
    """提取公司名称关键词"""
    # 移除常见后缀
    suffixes = ['有限公司', '有限责任公司', '股份有限公司', '集团有限公司',
                '有限公司北京', '分公司', '子公司', '全资子公司']
    keywords = [name]
    for suffix in suffixes:
        if name.endswith(suffix):
            keywords.append(name.replace(suffix, ''))
            break
    return keywords


def normalize_company_name(name: str) -> str:
    """标准化公司名称"""
    # 移除空格、全角转半角等
    name = name.strip()
    name = name.replace(' ', '')
    # 全角转半角
    name = name.replace('（', '(').replace('）', ')')
    return name


@router.post("/search", response_model=List[CompanyInfo])
async def search_companies(request: CompanySearchRequest):
    """
    搜索企业信息
    支持按企业名称模糊搜索
    """
    try:
        return await search_company_provider(request.company_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/{company_name}", response_model=CompanyInfo)
async def get_company_info(company_name: str):
    """
    获取企业详细信息
    通过企业名称查询工商信息
    """
    try:
        return await query_company_info(company_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/verify", response_model=CompanyVerifyResponse)
async def verify_company_info(request: CompanyVerifyRequest):
    """
    验证并纠错企业信息
    将联网查询的信息与用户提交的信息进行比对
    返回不一致的项目供用户确认
    """
    try:
        official_info = await query_company_info(request.company_name)

        discrepancies = []
        warnings = []

        # 比对法定代表人
        if request.legal_representative:
            if official_info.legal_representative and \
               official_info.legal_representative != "待查询" and \
               request.legal_representative != official_info.legal_representative:
                discrepancies.append({
                    "field": "legal_representative",
                    "field_name": "法定代表人",
                    "user_value": request.legal_representative,
                    "official_value": official_info.legal_representative,
                    "severity": "high",  # 高严重性
                    "reason": "法定代表人信息与工商登记不符，可能影响案件处理"
                })
                warnings.append(f"⚠️ 法定代表人信息不一致：您提交的是'{request.legal_representative}'，工商登记为'{official_info.legal_representative}'")

        # 比对注册资本
        if request.registered_capital:
            if official_info.registered_capital and \
               official_info.registered_capital != "待查询" and \
               request.registered_capital != official_info.registered_capital:
                discrepancies.append({
                    "field": "registered_capital",
                    "field_name": "注册资本",
                    "user_value": request.registered_capital,
                    "official_value": official_info.registered_capital,
                    "severity": "medium",  # 中等严重性
                    "reason": "注册资本信息与工商登记不符"
                })
                warnings.append(f"⚠️ 注册资本信息不一致：您提交的是'{request.registered_capital}'，工商登记为'{official_info.registered_capital}'")

        # 比对股东
        if request.shareholders:
            official_shareholders = official_info.shareholders or []
            if official_shareholders and any(s.get("name") != "待查询" for s in official_shareholders):
                user_set = set(s.strip() for s in request.shareholders)
                official_set = set(s.get("name", "") for s in official_shareholders if s.get("name") != "待查询")

                missing_shareholders = official_set - user_set
                if missing_shareholders:
                    discrepancies.append({
                        "field": "shareholders",
                        "field_name": "股东信息",
                        "user_value": list(user_set),
                        "official_value": list(official_set),
                        "missing_from_user": list(missing_shareholders),
                        "severity": "high",
                        "reason": "存在工商登记股东未在案件信息中体现"
                    })
                    warnings.append(f"⚠️ 股东信息不完整：工商登记显示以下股东可能未在案件中体现: {', '.join(missing_shareholders)}")

        # 比对董监高
        if request.board_members:
            official_board = official_info.board_members or []
            if official_board and any(b.get("name") != "待查询" for b in official_board):
                warnings.append(f"⚠️ 董监高信息可能与工商登记不符，建议核实")

        return CompanyVerifyResponse(
            official_info=official_info,
            discrepancies=discrepancies,
            warnings=warnings,
            needs_confirmation=len(discrepancies) > 0
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.get("/{company_name}/basic")
async def get_company_basic(company_name: str):
    """
    获取企业基础信息（简化版）
    用于快速比对
    """
    try:
        info = await query_company_info(company_name)
        return {
            "name": info.name,
            "unified_social_credit_code": info.unified_social_credit_code,
            "legal_representative": info.legal_representative,
            "registered_capital": info.registered_capital,
            "establishment_date": info.establishment_date,
            "status": info.status,
            "company_type": info.company_type
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{company_name}/shareholders")
async def get_company_shareholders(company_name: str):
    """
    获取企业股东信息
    """
    try:
        info = await query_company_info(company_name)
        return {
            "company_name": info.name,
            "shareholders": info.shareholders or []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{company_name}/board")
async def get_company_board(company_name: str):
    """
    获取企业董监高信息
    """
    try:
        info = await query_company_info(company_name)
        return {
            "company_name": info.name,
            "board_members": info.board_members or []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{company_name}/changes")
async def get_company_changes(company_name: str):
    """
    获取企业变更记录
    """
    try:
        info = await query_company_info(company_name)
        return {
            "company_name": info.name,
            "changes": info.changes or []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
