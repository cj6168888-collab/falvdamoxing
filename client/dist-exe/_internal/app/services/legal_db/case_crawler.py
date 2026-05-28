"""
指导性案例 + 典型案例爬虫
从最高人民法院官网和各高院爬取指导性案例
"""
import os
import sys
import json
import uuid
import sqlite3
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.config import settings

CASES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "guiding_cases")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

GUIDING_CASE_SOURCES = [
    {
        "name": "最高法指导性案例",
        "base_url": "https://www.court.gov.cn",
        "list_url": "https://www.court.gov.cn/zixun-xiangqing-{page}.html",
        "search_keyword": "指导性案例",
    },
]


def get_db_path():
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path[2:])
    else:
        db_path = db_url
    if not os.path.exists(db_path):
        db_path = "legal_system.db"
    return db_path


def fetch_url(url: str, encoding: str = "utf-8") -> Optional[str]:
    """获取网页内容"""
    try:
        import httpx
        resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
        resp.encoding = encoding
        return resp.text
    except Exception as e:
        print(f"  [ERROR] 获取 {url} 失败: {e}")
        return None


def parse_guiding_case_page(html: str, source_url: str) -> Optional[Dict]:
    """解析指导性案例详情页"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.find("h1") or soup.find("title")
    title = title_el.get_text(strip=True) if title_el else ""

    content_el = soup.find("div", class_="TRS_Editor") or soup.find("div", class_="content") or soup.find("div", id="content")
    if not content_el:
        content_el = soup.find("article")

    full_text = content_el.get_text("\n", strip=True) if content_el else ""

    summary = ""
    keywords = []
    case_number = ""

    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if "关键词" in text:
            keywords_text = text.replace("关键词", "").replace("：", "").replace(":", "").strip()
            keywords = [k.strip() for k in re.split(r"[；;、]", keywords_text) if k.strip()]
        elif "裁判要点" in text or "指导要点" in text:
            summary = text

    if "指导案例" in title:
        match = re.search(r"指导案例(\d+)号", title)
        if match:
            case_number = f"指导案例{match.group(1)}号"

    court = ""
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if "法院" in text and "最高" in text:
            court = text

    return {
        "id": str(uuid.uuid4()),
        "case_number": case_number or title[:50],
        "title": title,
        "court": court or "最高人民法院",
        "case_type": _guess_case_type(title + full_text),
        "summary": summary,
        # 法律应用：保留完整文本内容
        "full_text": full_text,
        "keywords": keywords,
        "related_articles": [],
        "publish_date": "",
        "source": source_url,
    }


def _guess_case_type(text: str) -> str:
    if "民事" in text:
        return "civil"
    elif "刑事" in text:
        return "criminal"
    elif "行政" in text:
        return "administrative"
    elif "执行" in text:
        return "execution"
    elif "知识产权" in text or "商标" in text or "专利" in text:
        return "ip"
    elif "劳动" in text:
        return "labor"
    elif "合同" in text:
        return "contract"
    return "other"


def crawl_spc_guiding_cases(max_pages: int = 5) -> List[Dict]:
    """从最高人民法院官网爬取指导性案例列表"""
    cases = []
    print("\n  [SPC] 爬取最高法指导性案例...")

    try:
        import httpx
        search_url = "https://www.court.gov.cn/zixun-xiangqing.html"
        resp = httpx.get(
            "https://www.court.gov.cn/shenpan-xiangqing-111.html",
            headers=HEADERS, timeout=30, follow_redirects=True
        )

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")

        links = soup.find_all("a", href=True)
        case_links = []
        for link in links:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if "指导案例" in text:
                full_url = urljoin("https://www.court.gov.cn", href)
                case_links.append((text, full_url))

        print(f"  找到 {len(case_links)} 个指导性案例链接")

        for title, url in case_links[:50]:
            print(f"    获取: {title}")
            html = fetch_url(url)
            if html:
                case = parse_guiding_case_page(html, url)
                if case and case.get("full_text"):
                    cases.append(case)
            time.sleep(1)

    except Exception as e:
        print(f"  [ERROR] SPC 爬取失败: {e}")

    return cases


def crawl_from_builtin_data() -> List[Dict]:
    """
    使用内置的指导性案例 + 典型案例数据
    包含最高法已发布的全部指导性案例（200+）
    以及各地高院发布的典型案例
    """
    print("\n  [BUILTIN] 加载指导性案例 + 典型案例数据...")
    from app.services.legal_db.more_cases import get_all_cases
    return get_all_cases()

    builtin_cases = [
        {
            "case_number": "指导案例1号",
            "title": "上海中原物业顾问有限公司诉陶德华居间合同纠纷案",
            "court": "最高人民法院",
            "case_type": "contract",
            "summary": "房屋买卖居间合同中，买方利用居间方提供的房源信息但绕开该居间方与卖方直接签订合同的，构成违约。",
            "full_text": "上海中原物业顾问有限公司诉陶德华居间合同纠纷案。裁判要点：房屋买卖居间合同中，买方利用居间方提供的房源信息但绕开该居间方与卖方直接签订合同的，构成违约。关键词：民事 居间合同 房屋买卖 违约责任",
            "keywords": ["民事", "居间合同", "房屋买卖", "违约责任"],
            "related_articles": ["民法典第961条", "民法典第965条"],
            "publish_date": "2011-12-20",
            "source": "最高人民法院",
        },
        {
            "case_number": "指导案例2号",
            "title": "吴梅诉四川省眉山西城纸业有限公司买卖合同纠纷案",
            "court": "最高人民法院",
            "case_type": "contract",
            "summary": "民事案件二审期间，双方当事人达成和解协议后，一方不履行和解协议的，另一方可以申请执行一审生效判决。",
            "full_text": "吴梅诉四川省眉山西城纸业有限公司买卖合同纠纷案。裁判要点：民事案件二审期间，双方当事人达成和解协议后，一方不履行和解协议的，另一方可以申请执行一审生效判决。关键词：民事 买卖合同 二审和解 执行",
            "keywords": ["民事", "买卖合同", "二审和解", "执行"],
            "related_articles": ["民事诉讼法第237条"],
            "publish_date": "2011-12-20",
            "source": "最高人民法院",
        },
        {
            "case_number": "指导案例3号",
            "title": "潘玉梅、陈宁受贿案",
            "court": "最高人民法院",
            "case_type": "criminal",
            "summary": "国家工作人员利用职务便利为请托人谋取利益，以明显低于市场的价格向请托人购买房屋的，以受贿论处。",
            "full_text": "潘玉梅、陈宁受贿案。裁判要点：国家工作人员利用职务上的便利为请托人谋取利益，以明显低于市场的价格向请托人购买房屋等物品的，以受贿论处。受贿数额按照交易时当地市场价格与实际支付价格的差额计算。关键词：刑事 受贿 低价购房",
            "keywords": ["刑事", "受贿", "低价购房"],
            "related_articles": ["刑法第385条"],
            "publish_date": "2011-12-20",
            "source": "最高人民法院",
        },
        {
            "case_number": "指导案例4号",
            "title": "王志才故意杀人案",
            "court": "最高人民法院",
            "case_type": "criminal",
            "summary": "因恋爱、婚姻矛盾激化引发的故意杀人案件，被告人犯罪手段残忍但具有法定从轻处罚情节的，可以判处死刑缓期执行并限制减刑。",
            "full_text": "王志才故意杀人案。裁判要点：因恋爱、婚姻矛盾激化引发的故意杀人案件，被告人犯罪手段残忍，论罪应当判处死刑，但被告人具有坦白悔罪、积极赔偿等从轻处罚情节的，可以判处死刑缓期二年执行，同时决定限制减刑。关键词：刑事 故意杀人 死缓 限制减刑",
            "keywords": ["刑事", "故意杀人", "死缓", "限制减刑"],
            "related_articles": ["刑法第48条", "刑法第50条"],
            "publish_date": "2011-12-20",
            "source": "最高人民法院",
        },
        {
            "case_number": "指导案例5号",
            "title": "鲁潍（福建）盐业进出口有限公司苏州分公司诉江苏省苏州市盐务管理局盐业行政处罚案",
            "court": "最高人民法院",
            "case_type": "administrative",
            "summary": "地方政府规章违反行政法规设定行政许可的，人民法院在行政审判中不予适用。",
            "full_text": "鲁潍（福建）盐业进出口有限公司苏州分公司诉江苏省苏州市盐务管理局盐业行政处罚案。裁判要点：地方政府规章违反行政法规设定行政许可的，人民法院在行政审判中不予适用。关键词：行政 行政许可 规章 法律适用",
            "keywords": ["行政", "行政许可", "规章", "法律适用"],
            "related_articles": ["行政诉讼法第63条", "行政许可法第15条"],
            "publish_date": "2012-04-09",
            "source": "最高人民法院",
        },
        {
            "case_number": "指导案例6号",
            "title": "黄泽富、何伯琼、何熠诉四川省成都市金堂工商行政管理局行政处罚案",
            "court": "最高人民法院",
            "case_type": "administrative",
            "summary": "行政机关作出没收较大数额涉案财产的行政处罚决定时，未告知当事人有要求举行听证的权利或者未依法举行听证的，人民法院应当依法认定该行政处罚违反法定程序。",
            "full_text": "黄泽富、何伯琼、何熠诉四川省成都市金堂工商行政管理局行政处罚案。裁判要点：行政机关作出没收较大数额涉案财产的行政处罚决定时，未告知当事人有要求举行听证的权利或者未依法举行听证的，人民法院应当依法认定该行政处罚违反法定程序。关键词：行政 行政处罚 听证 程序违法",
            "keywords": ["行政", "行政处罚", "听证", "程序违法"],
            "related_articles": ["行政处罚法第42条"],
            "publish_date": "2012-04-09",
            "source": "最高人民法院",
        },
        {
            "case_number": "指导案例7号",
            "title": "牡丹江市宏阁建筑安装有限责任公司诉牡丹江市华隆房地产开发有限责任公司等建设工程合同纠纷案",
            "court": "最高人民法院",
            "case_type": "civil",
            "summary": "建设工程合同中，承包人主张工程价款优先受偿权的期限自建设工程竣工之日或合同约定的竣工之日起计算。",
            "full_text": "牡丹江市宏阁建筑安装有限责任公司诉牡丹江市华隆房地产开发有限责任公司等建设工程合同纠纷案。裁判要点：建设工程合同中，承包人主张工程价款优先受偿权的期限自建设工程竣工之日或合同约定的竣工之日起计算。关键词：民事 建设工程 优先受偿权",
            "keywords": ["民事", "建设工程", "优先受偿权"],
            "related_articles": ["民法典第807条"],
            "publish_date": "2012-09-18",
            "source": "最高人民法院",
        },
        {
            "case_number": "指导案例8号",
            "title": "林方清诉常熟市凯莱实业有限公司、戴小明公司解散纠纷案",
            "court": "最高人民法院",
            "case_type": "company",
            "summary": "公司法第一百八十三条将'公司经营管理发生严重困难'作为股东提起解散公司诉讼的条件之一。判断'公司经营管理是否发生严重困难'，应从公司组织机构的运行状态进行综合分析。",
            "full_text": "林方清诉常熟市凯莱实业有限公司、戴小明公司解散纠纷案。裁判要点：公司法第一百八十三条将'公司经营管理发生严重困难'作为股东提起解散公司诉讼的条件之一。判断'公司经营管理是否发生严重困难'，应从公司组织机构的运行状态进行综合分析。关键词：民事 公司解散 经营管理困难",
            "keywords": ["民事", "公司解散", "经营管理困难"],
            "related_articles": ["公司法第182条"],
            "publish_date": "2012-09-18",
            "source": "最高人民法院",
        },
        {
            "case_number": "指导案例9号",
            "title": "上海存亮贸易有限公司诉蒋志东、王卫明等买卖合同纠纷案",
            "court": "最高人民法院",
            "case_type": "company",
            "summary": "有限责任公司的股东、股份有限公司的董事和控股股东，应当依法在公司被吊销营业执照后履行清算义务，不能以其不是实际控制人或者未实际参加公司经营管理为由，免除清算义务。",
            "full_text": "上海存亮贸易有限公司诉蒋志东、王卫明等买卖合同纠纷案。裁判要点：有限责任公司的股东、股份有限公司的董事和控股股东，应当依法在公司被吊销营业执照后履行清算义务。关键词：民事 公司清算 股东责任",
            "keywords": ["民事", "公司清算", "股东责任"],
            "related_articles": ["公司法第183条"],
            "publish_date": "2012-09-18",
            "source": "最高人民法院",
        },
        {
            "case_number": "指导案例10号",
            "title": "李建军诉上海佳动力环保科技有限公司公司决议撤销纠纷案",
            "court": "最高人民法院",
            "case_type": "company",
            "summary": "人民法院在审理公司决议撤销纠纷案件中应当审查：会议召集程序、表决方式是否违反法律、行政法规或者公司章程，以及决议内容是否违反公司章程。",
            "full_text": "李建军诉上海佳动力环保科技有限公司公司决议撤销纠纷案。裁判要点：人民法院在审理公司决议撤销纠纷案件中应当审查会议召集程序、表决方式是否违反法律、行政法规或者公司章程，以及决议内容是否违反公司章程。关键词：民事 公司决议 撤销",
            "keywords": ["民事", "公司决议", "撤销"],
            "related_articles": ["公司法第22条"],
            "publish_date": "2012-09-18",
            "source": "最高人民法院",
        },
    ]

    cases = []
    for c in builtin_cases:
        cases.append({
            "id": str(uuid.uuid4()),
            **c,
        })

    print(f"  内置 {len(cases)} 个指导性案例")
    return cases


def insert_cases(db_path: str, cases: List[Dict]):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted = 0
    skipped = 0

    for case in cases:
        try:
            cursor.execute(
                "SELECT id FROM guiding_cases WHERE case_number = ?",
                (case["case_number"],)
            )
            if cursor.fetchone():
                cursor.execute(
                    """UPDATE guiding_cases SET title = ?, court = ?, case_type = ?,
                       summary = ?, full_text = ?, keywords = ?, related_articles = ?,
                       publish_date = ?, source = ?, updated_at = ?
                       WHERE case_number = ?""",
                    (case["title"], case["court"], case["case_type"],
                     case["summary"], case["full_text"],
                     json.dumps(case.get("keywords", []), ensure_ascii=False),
                     json.dumps(case.get("related_articles", []), ensure_ascii=False),
                     case.get("publish_date", ""), case.get("source", ""),
                     datetime.now().isoformat(), case["case_number"])
                )
                inserted += 1
            else:
                cursor.execute(
                    """INSERT INTO guiding_cases
                       (id, case_number, title, court, case_type, summary, full_text,
                        keywords, related_articles, publish_date, source, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (case["id"], case["case_number"], case["title"], case["court"],
                     case["case_type"], case["summary"], case["full_text"],
                     json.dumps(case.get("keywords", []), ensure_ascii=False),
                     json.dumps(case.get("related_articles", []), ensure_ascii=False),
                     case.get("publish_date", ""), case.get("source", ""),
                     datetime.now().isoformat(), datetime.now().isoformat())
                )
                inserted += 1
        except Exception as e:
            skipped += 1
            if skipped <= 3:
                print(f"  [ERROR] 插入失败 {case.get('case_number', '?')}: {e}")

    conn.commit()
    conn.close()
    return inserted, skipped


def run_crawler():
    print("=" * 60)
    print("指导性案例 + 典型案例爬虫")
    print("=" * 60)

    os.makedirs(CASES_DIR, exist_ok=True)

    all_cases = []

    print("\n--- 尝试在线爬取 ---")
    online_cases = crawl_spc_guiding_cases()
    all_cases.extend(online_cases)

    if len(all_cases) < 10:
        print("\n--- 在线数据不足，补充内置数据 ---")
        builtin_cases = crawl_from_builtin_data()
        existing_numbers = {c["case_number"] for c in all_cases}
        for c in builtin_cases:
            if c["case_number"] not in existing_numbers:
                all_cases.append(c)

    print(f"\n总计获取 {len(all_cases)} 个案例")

    db_path = get_db_path()
    print(f"写入数据库: {db_path}")

    inserted, skipped = insert_cases(db_path, all_cases)
    print(f"\n[RESULT] 插入/更新: {inserted}, 跳过: {skipped}")

    type_stats = {}
    for c in all_cases:
        t = c.get("case_type", "other")
        type_stats[t] = type_stats.get(t, 0) + 1

    print(f"\n[STATS] 案例类型分布:")
    for t, count in sorted(type_stats.items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")

    with open(os.path.join(CASES_DIR, "cases_summary.json"), "w", encoding="utf-8") as f:
        json.dump({
            "total": len(all_cases),
            "cases": [{"case_number": c["case_number"], "title": c["title"], "case_type": c["case_type"]} for c in all_cases],
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[SAVE] 摘要已保存到 {CASES_DIR}/cases_summary.json")


if __name__ == "__main__":
    run_crawler()
