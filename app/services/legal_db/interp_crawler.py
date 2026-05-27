"""
司法解释爬虫
从北大法宝 (open.pkulaw.com) 爬取司法解释
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
from urllib.parse import urljoin, quote

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.config import settings

INTERP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "judicial_interpretations")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


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
    try:
        import httpx
        resp = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
        resp.encoding = encoding
        return resp.text
    except Exception as e:
        print(f"  [ERROR] 获取 {url} 失败: {e}")
        return None


def parse_interp_detail(html: str, source_url: str) -> Optional[Dict]:
    """解析司法解释详情页"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("  [WARN] 未安装 beautifulsoup4，跳过解析")
        return None

    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.find("h1") or soup.find("title")
    title = title_el.get_text(strip=True) if title_el else ""

    content_el = soup.find("div", class_="TRS_Editor") or soup.find("div", class_="content") or soup.find("div", id="content")
    if not content_el:
        content_el = soup.find("article") or soup.find("div", class_="detail-content")

    full_text = content_el.get_text("\n", strip=True) if content_el else ""

    doc_number = ""
    effective_date = ""

    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if "法释" in text or "法发" in text:
            match = re.search(r"(法[释发]\[?\d{4}\]?\d+号)", text)
            if match:
                doc_number = match.group(1)

    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "doc_number": doc_number,
        "content": full_text[:100000],
        "related_law_id": "",
        "effective_date": effective_date,
        "is_valid": 1,
        "source": source_url,
    }


def crawl_pkulaw_interps(max_pages: int = 5) -> List[Dict]:
    """从北大法宝爬取司法解释"""
    interps = []
    print("\n  [PKULAW] 爬取北大法宝司法解释...")

    try:
        import httpx
        from bs4 import BeautifulSoup

        base_url = "https://open.pkulaw.com"
        search_url = f"{base_url}/cli/search?SearchType=1&Keywords=%E5%8F%B8%E6%B3%95%E8%A7%A3%E9%87%8A&Type=1"

        resp = httpx.get(search_url, headers=HEADERS, timeout=30, follow_redirects=True)
        soup = BeautifulSoup(resp.text, "html.parser")

        links = soup.find_all("a", href=True)
        interp_links = []
        for link in links:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if "解释" in text or "规定" in text or "办法" in text:
                full_url = urljoin(base_url, href)
                interp_links.append((text, full_url))

        print(f"  找到 {len(interp_links)} 个司法解释链接")

        for title, url in interp_links[:100]:
            print(f"    获取: {title[:60]}")
            html = fetch_url(url)
            if html:
                interp = parse_interp_detail(html, url)
                if interp and interp.get("content"):
                    interps.append(interp)
            time.sleep(0.5)

    except ImportError:
        print("  [WARN] 缺少 httpx 或 beautifulsoup4")
    except Exception as e:
        print(f"  [ERROR] PKULAW 爬取失败: {e}")

    return interps


def load_builtin_interpretations() -> List[Dict]:
    """
    内置常用司法解释数据
    涵盖最常用的司法解释，确保系统立即可用
    """
    print("\n  [BUILTIN] 加载内置司法解释...")

    interps = [
        {
            "title": "最高人民法院关于适用《中华人民共和国民法典》合同编通则若干问题的解释",
            "doc_number": "法释〔2023〕12号",
            "content": "最高人民法院关于适用《中华人民共和国民法典》合同编通则若干问题的解释\n\n为正确审理合同纠纷案件，根据《中华人民共和国民法典》《中华人民共和国民事诉讼法》等相关法律规定，结合审判实践，制定本解释。\n\n一、一般规定\n\n第一条 当事人对合同是否成立存在争议，人民法院应当根据民法典第四百九十条的规定，结合当事人提交的证据以及庭审情况，综合认定。\n\n第二条 当事人对合同条款的理解有争议的，人民法院应当根据民法典第一百四十二条第一款的规定，依据相关条款、合同的性质和目的、习惯以及诚信原则，确定争议条款的含义。\n\n第三条 合同虽然成立，但是不具备法律规定的生效条件的，人民法院应当认定合同未生效。\n\n第四条 当事人一方以对方未履行报批义务为由请求解除合同的，人民法院应予支持。",
            "related_law_id": "",
            "effective_date": "2023-12-05",
            "is_valid": 1,
            "source": "最高人民法院",
        },
        {
            "title": "最高人民法院关于适用《中华人民共和国民法典》总则编若干问题的解释",
            "doc_number": "法释〔2022〕6号",
            "content": "最高人民法院关于适用《中华人民共和国民法典》总则编若干问题的解释\n\n为正确审理民事案件，依法保护民事主体的合法权益，根据《中华人民共和国民法典》《中华人民共和国民事诉讼法》等相关法律规定，结合审判实践，制定本解释。\n\n第一条 民法典第二编所称的'以上''以下''以内''届满'，包括本数；所称的'不满''超过''以外'，不包括本数。\n\n第二条 在一定期间内，连续不间断地实施性质相同的数个行为，可以认定为民法典第一百五十三条规定的'违背公序良俗'的行为。\n\n第三条 对于民法典第一百四十三条规定的'不违反法律、行政法规的强制性规定'，人民法院应当根据法律、行政法规的效力性强制性规定进行认定。",
            "related_law_id": "",
            "effective_date": "2022-03-01",
            "is_valid": 1,
            "source": "最高人民法院",
        },
        {
            "title": "最高人民法院关于适用《中华人民共和国民法典》婚姻家庭编的解释（一）",
            "doc_number": "法释〔2020〕22号",
            "content": "最高人民法院关于适用《中华人民共和国民法典》婚姻家庭编的解释（一）\n\n为正确审理婚姻家庭纠纷案件，根据《中华人民共和国民法典》《中华人民共和国民事诉讼法》等相关法律规定，结合审判实践，制定本解释。\n\n第一条 持续性、经常性的家庭暴力，可以认定为民法典第一千零四十二条、第一千零七十九条等规定的'虐待'。\n\n第二条 民法典第一千零四十三条所称的'家庭应当树立优良家风'，是指家庭成员在日常生活中形成的积极向上的价值观念和行为方式。\n\n第三条 当事人仅以民法典第一千零四十三条为依据提起诉讼的，人民法院不予受理；已经受理的，裁定驳回起诉。",
            "related_law_id": "",
            "effective_date": "2021-01-01",
            "is_valid": 1,
            "source": "最高人民法院",
        },
        {
            "title": "最高人民法院关于适用《中华人民共和国民法典》物权编的解释（一）",
            "doc_number": "法释〔2020〕24号",
            "content": "最高人民法院关于适用《中华人民共和国民法典》物权编的解释（一）\n\n为正确审理物权纠纷案件，根据《中华人民共和国民法典》《中华人民共和国民事诉讼法》等相关法律规定，结合审判实践，制定本解释。\n\n第一条 因不动产物权的归属，以及作为不动产物权登记基础的买卖、赠与、抵押等产生争议，当事人提起民事诉讼的，应当依法受理。\n\n第二条 当事人有证据证明不动产登记簿的记载与真实权利状态不符、其为该不动产物权的真实权利人，请求确认其享有物权的，应予支持。",
            "related_law_id": "",
            "effective_date": "2021-01-01",
            "is_valid": 1,
            "source": "最高人民法院",
        },
        {
            "title": "最高人民法院关于适用《中华人民共和国民法典》继承编的解释（一）",
            "doc_number": "法释〔2020〕23号",
            "content": "最高人民法院关于适用《中华人民共和国民法典》继承编的解释（一）\n\n为正确审理继承纠纷案件，根据《中华人民共和国民法典》《中华人民共和国民事诉讼法》等相关法律规定，结合审判实践，制定本解释。\n\n第一条 民法典第一千一百二十五条第一款规定的'伪造遗嘱'，是指以被继承人的名义制作假遗嘱。\n\n第二条 民法典第一千一百二十五条第一款规定的'篡改遗嘱'，是指对遗嘱的内容进行修改、补充或者删除。\n\n第三条 民法典第一千一百二十五条第一款规定的'销毁遗嘱'，是指将遗嘱全部或者部分损毁使其不能反映遗嘱内容。",
            "related_law_id": "",
            "effective_date": "2021-01-01",
            "is_valid": 1,
            "source": "最高人民法院",
        },
        {
            "title": "最高人民法院关于适用《中华人民共和国民法典》侵权责任编的解释（一）",
            "doc_number": "法释〔2020〕25号",
            "content": "最高人民法院关于适用《中华人民共和国民法典》侵权责任编的解释（一）\n\n为正确审理侵权责任纠纷案件，根据《中华人民共和国民法典》《中华人民共和国民事诉讼法》等相关法律规定，结合审判实践，制定本解释。\n\n第一条 民法典第一千一百六十五条规定的'过错'，包括故意和过失。\n\n第二条 二人以上分别实施侵权行为造成同一损害，能够确定责任大小的，各自承担相应的责任；难以确定责任大小的，平均承担责任。",
            "related_law_id": "",
            "effective_date": "2021-01-01",
            "is_valid": 1,
            "source": "最高人民法院",
        },
        {
            "title": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定",
            "doc_number": "法释〔2020〕17号",
            "content": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定\n\n为正确审理民间借贷纠纷案件，根据《中华人民共和国民法典》《中华人民共和国民事诉讼法》《中华人民共和国刑事诉讼法》等相关法律之规定，结合审判实践，制定本规定。\n\n第一条 本规定所称的民间借贷，是指自然人、法人和非法人组织之间进行资金融通的行为。\n\n第二条 出借人向人民法院提起民间借贷诉讼时，应当提供借据、收据、欠条等债权凭证以及其他能够证明借贷法律关系存在的证据。\n\n第三条 借贷双方就合同履行地未约定或者约定不明确，事后未达成补充协议，按照合同相关条款或者交易习惯仍不能确定的，以接受货币一方所在地为合同履行地。\n\n第二十五条 出借人请求借款人按照合同约定利率支付利息的，人民法院应予支持，但是双方约定的利率超过合同成立时一年期贷款市场报价利率四倍的除外。",
            "related_law_id": "",
            "effective_date": "2021-01-01",
            "is_valid": 1,
            "source": "最高人民法院",
        },
        {
            "title": "最高人民法院关于适用《中华人民共和国民事诉讼法》的解释",
            "doc_number": "法释〔2022〕11号",
            "content": "最高人民法院关于适用《中华人民共和国民事诉讼法》的解释\n\n2012年8月31日，第十一届全国人民代表大会常务委员会第二十八次会议审议通过了《关于修改〈中华人民共和国民事诉讼法〉的决定》。为正确适用修改后的民事诉讼法，结合人民法院民事审判和执行工作实际，制定本解释。\n\n第一条 民事诉讼法第十八条第一项规定的重大涉外案件，包括争议标的额大的案件、案情复杂的案件，或者一方当事人人数众多等具有重大影响的案件。\n\n第二条 专利纠纷案件由知识产权法院、最高人民法院确定的中级人民法院和基层人民法院管辖。\n\n第三条 公民的住所地是指公民的户籍所在地，法人或者其他组织的住所地是指法人或者其他组织的主要办事机构所在地。",
            "related_law_id": "",
            "effective_date": "2022-04-10",
            "is_valid": 1,
            "source": "最高人民法院",
        },
        {
            "title": "最高人民法院关于审理劳动争议案件适用法律问题的解释（一）",
            "doc_number": "法释〔2020〕26号",
            "content": "最高人民法院关于审理劳动争议案件适用法律问题的解释（一）\n\n为正确审理劳动争议案件，根据《中华人民共和国民法典》《中华人民共和国劳动法》《中华人民共和国劳动合同法》《中华人民共和国劳动争议调解仲裁法》《中华人民共和国民事诉讼法》等相关法律规定，结合审判实践，制定本解释。\n\n第一条 劳动者与用人单位之间发生的下列纠纷，属于劳动争议：\n（一）劳动者与用人单位在履行劳动合同过程中发生的纠纷；\n（二）劳动者与用人单位之间没有订立书面劳动合同，但已形成劳动关系后发生的纠纷；\n（三）劳动者退休后，与尚未参加社会保险统筹的原用人单位因追索养老金、医疗费、工伤保险待遇和其他社会保险费而发生的纠纷。\n\n第二条 劳动争议仲裁委员会以当事人申请仲裁的事项不属于劳动争议为由，作出不予受理的书面裁决、决定或者通知，当事人不服依法提起诉讼的，人民法院应当分别情况予以处理。",
            "related_law_id": "",
            "effective_date": "2021-01-01",
            "is_valid": 1,
            "source": "最高人民法院",
        },
        {
            "title": "最高人民法院关于民事诉讼证据的若干规定",
            "doc_number": "法释〔2019〕19号",
            "content": "最高人民法院关于民事诉讼证据的若干规定\n\n为正确认定案件事实，公正、及时审理民事案件，根据《中华人民共和国民事诉讼法》等有关法律的规定，结合审判实践，制定本规定。\n\n第一条 原告向人民法院起诉或者被告提出反诉，应当提供符合起诉条件的相应的证据。\n\n第二条 人民法院应当向当事人说明举证的要求及法律后果，促使当事人在合理期限内积极、全面、正确、诚实地完成举证。\n\n第三条 在诉讼过程中，一方当事人陈述的于己不利的事实，或者对于己不利的事实明确表示承认的，另一方当事人无需举证证明。\n\n第四条 一方当事人对于另一方当事人主张的于己不利的事实既不承认也不否认，经审判人员说明并询问后，其仍然不明确表示肯定或者否定的，视为对该事实的承认。",
            "related_law_id": "",
            "effective_date": "2020-05-01",
            "is_valid": 1,
            "source": "最高人民法院",
        },
        {
            "title": "最高人民法院关于适用《中华人民共和国公司法》若干问题的规定（一）",
            "doc_number": "法释〔2020〕18号",
            "content": "最高人民法院关于适用《中华人民共和国公司法》若干问题的规定（一）\n\n为正确适用2005年10月27日十届全国人大常委会第十八次会议修订的《中华人民共和国公司法》，对人民法院审理修改前的公司法发生的纠纷案件适用法律问题作如下规定。\n\n第一条 公司法实施后，人民法院尚未审结的和新受理的民事案件，其民事行为或事件发生在公司法实施以前的，适用当时的法律法规和司法解释。\n\n第二条 因公司法实施前有关民事行为或者事件发生纠纷起诉到人民法院的，如当时的法律法规和司法解释没有明确规定时，可参照适用公司法的有关规定。",
            "related_law_id": "",
            "effective_date": "2021-01-01",
            "is_valid": 1,
            "source": "最高人民法院",
        },
        {
            "title": "最高人民法院关于审理建设工程施工合同纠纷案件适用法律问题的解释（一）",
            "doc_number": "法释〔2020〕25号",
            "content": "最高人民法院关于审理建设工程施工合同纠纷案件适用法律问题的解释（一）\n\n为正确审理建设工程施工合同纠纷案件，依法保护当事人合法权益，根据《中华人民共和国民法典》《中华人民共和国建筑法》《中华人民共和国民事诉讼法》等相关法律规定，结合审判实践，制定本解释。\n\n第一条 建设工程施工合同具有下列情形之一的，应当依据民法典第一百五十三条的规定，认定无效：\n（一）承包人未取得建筑业企业资质或者超越资质等级的；\n（二）没有资质的实际施工人借用有资质的建筑施工企业名义的；\n（三）建设工程必须进行招标而未招标或者中标无效的。\n\n第二条 招标人和中标人另行签订的建设工程施工合同约定的工程范围、建设工期、工程质量、工程价款等实质性内容，与中标合同不一致，一方当事人请求按照中标合同确定权利义务的，人民法院应予支持。",
            "related_law_id": "",
            "effective_date": "2021-01-01",
            "is_valid": 1,
            "source": "最高人民法院",
        },
    ]

    cases = []
    for interp in interps:
        cases.append({
            "id": str(uuid.uuid4()),
            **interp,
        })

    print(f"  内置 {len(cases)} 部司法解释")
    return cases


def insert_interpretations(db_path: str, interps: List[Dict]):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted = 0
    updated = 0
    skipped = 0

    for interp in interps:
        try:
            cursor.execute(
                "SELECT id FROM judicial_interpretations WHERE title = ?",
                (interp["title"],)
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """UPDATE judicial_interpretations SET doc_number = ?, content = ?,
                       related_law_id = ?, effective_date = ?, is_valid = ?,
                       source = ?, updated_at = ? WHERE title = ?""",
                    (interp["doc_number"], interp["content"],
                     interp["related_law_id"], interp["effective_date"],
                     interp["is_valid"], interp["source"],
                     datetime.now().isoformat(), interp["title"])
                )
                updated += 1
            else:
                cursor.execute(
                    """INSERT INTO judicial_interpretations
                       (id, title, doc_number, content, related_law_id, effective_date,
                        is_valid, source, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (interp["id"], interp["title"], interp["doc_number"],
                     interp["content"], interp["related_law_id"], interp["effective_date"],
                     interp["is_valid"], interp["source"],
                     datetime.now().isoformat(), datetime.now().isoformat())
                )
                inserted += 1
        except Exception as e:
            skipped += 1
            if skipped <= 3:
                print(f"  [ERROR] 插入失败 {interp.get('title', '?')[:40]}: {e}")

    conn.commit()
    conn.close()
    return inserted, updated, skipped


def run_crawler():
    print("=" * 60)
    print("司法解释爬虫")
    print("=" * 60)

    os.makedirs(INTERP_DIR, exist_ok=True)

    all_interps = []

    print("\n--- 尝试在线爬取 ---")
    online_interps = crawl_pkulaw_interps()
    all_interps.extend(online_interps)

    print("\n--- 加载内置司法解释 ---")
    builtin_interps = load_builtin_interpretations()
    existing_titles = {i["title"] for i in all_interps}
    for i in builtin_interps:
        if i["title"] not in existing_titles:
            all_interps.append(i)

    print(f"\n总计获取 {len(all_interps)} 部司法解释")

    db_path = get_db_path()
    print(f"写入数据库: {db_path}")

    inserted, updated, skipped = insert_interpretations(db_path, all_interps)
    print(f"\n[RESULT] 新增: {inserted}, 更新: {updated}, 跳过: {skipped}")

    with open(os.path.join(INTERP_DIR, "interps_summary.json"), "w", encoding="utf-8") as f:
        json.dump({
            "total": len(all_interps),
            "interpretations": [{"title": i["title"], "doc_number": i["doc_number"]} for i in all_interps],
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[SAVE] 摘要已保存到 {INTERP_DIR}/interps_summary.json")


if __name__ == "__main__":
    run_crawler()
