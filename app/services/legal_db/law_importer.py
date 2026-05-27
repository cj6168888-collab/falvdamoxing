"""
法条数据导入脚本
从 GitHub 开源数据源 (lawtext/laws, LawRefBook/Laws) 导入法条到本地数据库
"""
import os
import sys
import json
import uuid
import sqlite3
import subprocess
import shutil
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.config import settings

LAWS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "laws_source")
CLONED_REPOS = []

CATEGORY_MAP = {
    "民法典": "civil",
    "民事诉讼法": "civil_procedure",
    "刑事诉讼法": "criminal_procedure",
    "刑法": "criminal",
    "劳动法": "labor",
    "劳动合同法": "labor",
    "公司法": "company",
    "行政法": "administrative",
    "行政诉讼法": "administrative_litigation",
    "仲裁法": "arbitration",
    "劳动争议调解仲裁法": "labor",
    "宪法": "constitutional",
    "合同法": "civil",
    "物权法": "civil",
    "侵权责任法": "civil",
    "婚姻法": "civil",
    "继承法": "civil",
    "担保法": "civil",
    "商标法": "ip",
    "专利法": "ip",
    "著作权法": "ip",
    "环境保护法": "environmental",
    "消费者权益保护法": "consumer",
    "个人信息保护法": "data_protection",
    "网络安全法": "data_protection",
    "数据安全法": "data_protection",
    "反不正当竞争法": "commercial",
    "反垄断法": "commercial",
    "税法": "tax",
    "个人所得税法": "tax",
    "企业所得税法": "tax",
    "增值税法": "tax",
    "社会保险法": "social_insurance",
    "治安管理处罚法": "public_security",
    "道路交通安全法": "traffic",
    "未成年人保护法": "minors",
    "反家庭暴力法": "family",
    "老年人权益保障法": "elderly",
    "残疾人保障法": "disabled",
    "妇女权益保障法": "women",
    "土地管理法": "land",
    "城市房地产管理法": "real_estate",
    "农村土地承包法": "land",
    "建筑法": "construction",
    "招标投标法": "bidding",
    "保险法": "insurance",
    "证券法": "securities",
    "银行法": "banking",
    "票据法": "commercial",
    "海商法": "maritime",
    "破产法": "bankruptcy",
    "企业破产法": "bankruptcy",
    "人民调解法": "mediation",
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


def clone_repo(url, name):
    target = os.path.join(LAWS_DIR, name)
    if os.path.exists(os.path.join(target, ".git")):
        print(f"[SKIP] {name} 已存在，拉取最新代码...")
        subprocess.run(["git", "-C", target, "pull"], capture_output=True, timeout=60)
    else:
        print(f"[CLONE] 克隆 {name}...")
        os.makedirs(LAWS_DIR, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", url, target], capture_output=True, timeout=120)
    CLONED_REPOS.append(name)
    return target


def try_clone_repo(url, name, timeout_sec=30):
    """尝试克隆仓库，超时则返回 None"""
    target = os.path.join(LAWS_DIR, name)
    if os.path.exists(os.path.join(target, ".git")):
        print(f"[SKIP] {name} 已存在")
        CLONED_REPOS.append(name)
        return target
    try:
        print(f"[CLONE] 尝试克隆 {name} (超时 {timeout_sec}s)...")
        os.makedirs(LAWS_DIR, exist_ok=True)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, target],
            capture_output=True, timeout=timeout_sec
        )
        if result.returncode == 0:
            CLONED_REPOS.append(name)
            return target
        else:
            print(f"  [FAIL] 克隆失败: {result.stderr.decode('utf-8', errors='ignore')[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] 克隆 {name} 超时 ({timeout_sec}s)")
        return None
    except Exception as e:
        print(f"  [ERROR] 克隆 {name} 异常: {e}")
        return None


def guess_category(law_name):
    for keyword, category in CATEGORY_MAP.items():
        if keyword in law_name:
            return category
    return "other"


def parse_lawtext_json(filepath, law_name_from_path=None):
    """解析 lawtext/laws 格式的 JSON 文件"""
    articles = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return articles

    law_name = data.get("law_name", data.get("title", law_name_from_path or "未知法律"))

    chapters = data.get("chapters", [])
    if not chapters and "articles" in data:
        chapters = [{"chapter": "", "articles": data["articles"]}]

    for chapter in chapters:
        chapter_name = chapter.get("chapter", "")
        for article in chapter.get("articles", []):
            article_number = article.get("number", article.get("article_number", ""))
            content = article.get("content", article.get("text", ""))
            title = article.get("title", "")

            if not article_number or not content:
                continue

            articles.append({
                "id": str(uuid.uuid4()),
                "law_name": law_name,
                "article_number": article_number,
                "title": title,
                "content": content,
                "chapter": chapter_name,
                "category": guess_category(law_name),
                "effective_date": data.get("effective_date", ""),
                "is_valid": 1,
                "source": "lawtext/laws",
            })

    return articles


def parse_lawrefbook_json(filepath, law_name_from_path=None):
    """解析 LawRefBook/Laws 格式的 JSON 文件"""
    articles = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return articles

    law_name = data.get("name", data.get("law_name", data.get("title", law_name_from_path or "未知法律")))

    items = data.get("articles", data.get("items", data.get("laws", [])))

    for item in items:
        article_number = item.get("number", item.get("article_number", item.get("no", "")))
        content = item.get("content", item.get("text", ""))
        title = item.get("title", "")
        chapter = item.get("chapter", "")

        if not article_number or not content:
            continue

        articles.append({
            "id": str(uuid.uuid4()),
            "law_name": law_name,
            "article_number": article_number,
            "title": title,
            "content": content,
            "chapter": chapter,
            "category": guess_category(law_name),
            "effective_date": data.get("effective_date", data.get("date", "")),
            "is_valid": 1,
            "source": "LawRefBook/Laws",
        })

    return articles


def parse_txt_file(filepath, law_name_from_path=None):
    """解析纯文本格式的法条文件"""
    articles = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, "r", encoding="gbk") as f:
                content = f.read()
        except UnicodeDecodeError:
            return articles

    law_name = law_name_from_path or os.path.splitext(os.path.basename(filepath))[0]

    import re
    pattern = re.compile(r"第[一二三四五六七八九十百千\d]+[条之]?[一二三四五六七八九十\d]*\s*[^\n]*")

    lines = content.split("\n")
    current_article = None
    current_content = []
    current_chapter = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("第") and "章" in line and "条" not in line:
            current_chapter = line
            continue

        match = pattern.match(line)
        if match:
            if current_article and current_content:
                articles.append({
                    "id": str(uuid.uuid4()),
                    "law_name": law_name,
                    "article_number": current_article,
                    "title": "",
                    "content": "\n".join(current_content).strip(),
                    "chapter": current_chapter,
                    "category": guess_category(law_name),
                    "effective_date": "",
                    "is_valid": 1,
                    "source": "txt_parse",
                })
            current_article = match.group().strip().split("\n")[0]
            rest = line[len(match.group()):].strip()
            current_content = [rest] if rest else []
        elif current_article:
            current_content.append(line)

    if current_article and current_content:
        articles.append({
            "id": str(uuid.uuid4()),
            "law_name": law_name,
            "article_number": current_article,
            "title": "",
            "content": "\n".join(current_content).strip(),
            "chapter": current_chapter,
            "category": guess_category(law_name),
            "effective_date": "",
            "is_valid": 1,
            "source": "txt_parse",
        })

    return articles


def scan_and_parse_repo(repo_path, repo_name):
    """扫描仓库中的所有法条文件"""
    all_articles = []

    for root, dirs, files in os.walk(repo_path):
        if ".git" in root or "__pycache__" in root:
            continue

        for filename in files:
            filepath = os.path.join(root, filename)
            law_name = os.path.splitext(filename)[0]

            if filename.endswith(".json"):
                if repo_name == "lawtext":
                    articles = parse_lawtext_json(filepath, law_name)
                else:
                    articles = parse_lawrefbook_json(filepath, law_name)
                all_articles.extend(articles)

            elif filename.endswith(".txt"):
                articles = parse_txt_file(filepath, law_name)
                all_articles.extend(articles)

    return all_articles


def deduplicate_articles(articles):
    """去重：同一法律+同一条文号的只保留一条"""
    seen = {}
    deduped = []
    for article in articles:
        key = f"{article['law_name']}|{article['article_number']}"
        if key not in seen:
            seen[key] = True
            deduped.append(article)
    return deduped


def insert_articles(db_path, articles):
    """批量插入法条到数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted = 0
    updated = 0
    skipped = 0

    for article in articles:
        try:
            cursor.execute(
                "SELECT id FROM legal_articles WHERE law_name = ? AND article_number = ?",
                (article["law_name"], article["article_number"])
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """UPDATE legal_articles SET content = ?, title = ?, chapter = ?,
                       category = ?, source = ?, updated_at = ?
                       WHERE law_name = ? AND article_number = ?""",
                    (article["content"], article["title"], article["chapter"],
                     article["category"], article["source"], datetime.now().isoformat(),
                     article["law_name"], article["article_number"])
                )
                updated += 1
            else:
                cursor.execute(
                    """INSERT INTO legal_articles
                       (id, law_name, article_number, title, content, chapter, category,
                        effective_date, is_valid, source, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (article["id"], article["law_name"], article["article_number"],
                     article["title"], article["content"], article["chapter"],
                     article["category"], article["effective_date"], article["is_valid"],
                     article["source"], datetime.now().isoformat(), datetime.now().isoformat())
                )
                inserted += 1
        except Exception as e:
            skipped += 1
            if skipped <= 3:
                print(f"  [ERROR] 插入失败: {article.get('law_name', '?')} {article.get('article_number', '?')}: {e}")

    conn.commit()
    conn.close()
    return inserted, updated, skipped


def load_builtin_laws():
    """加载内置法条数据（当 GitHub 不可用时）"""
    print("\n  [BUILTIN] 加载内置法条数据...")
    from app.services.legal_db.builtin_laws import ALL_BUILTIN_LAWS

    all_articles = []
    for law_data in ALL_BUILTIN_LAWS:
        law_name = law_data["law_name"]
        effective_date = law_data.get("effective_date", "")
        for chapter in law_data.get("chapters", []):
            chapter_name = chapter.get("chapter", "")
            for article in chapter.get("articles", []):
                all_articles.append({
                    "id": str(uuid.uuid4()),
                    "law_name": law_name,
                    "article_number": article["number"],
                    "title": article.get("title", ""),
                    "content": article["content"],
                    "chapter": chapter_name,
                    "category": law_data.get("category", "other"),
                    "effective_date": effective_date,
                    "is_valid": 1,
                    "source": "builtin",
                })

    print(f"  内置 {len(all_articles)} 条法条")
    return all_articles


def run_import():
    print("=" * 60)
    print("法条数据导入")
    print("=" * 60)

    all_articles = []

    # 优先尝试从 lawtext 仓库解析
    # __file__ = app/services/legal_db/law_importer.py → 3 levels up = project root
    current = os.path.dirname(os.path.abspath(__file__))
    for _ in range(3):
        current = os.path.dirname(current)
    project_root = current
    lawtext_path = os.path.join(project_root, "data", "laws_source", "lawtext")
    if os.path.exists(os.path.join(lawtext_path, "content")):
        print("\n--- 解析 lawtext 仓库 ---")
        try:
            from app.services.legal_db.lawtext_parser import scan_lawtext_repo
            articles = scan_lawtext_repo(lawtext_path)
            print(f"  解析到 {len(articles)} 条法条")
            all_articles.extend(articles)
        except Exception as e:
            print(f"  [ERROR] lawtext 解析失败: {e}")

    # 如果 lawtext 数据不足，尝试 GitHub 克隆
    if len(all_articles) < 100:
        repos = [
            ("https://github.com/qundao/law-book.git", "lawtext"),
            ("https://github.com/LawRefBook/Laws.git", "lawrefbook"),
        ]

        for url, name in repos:
            print(f"\n--- 处理 {name} ---")
            try:
                repo_path = try_clone_repo(url, name, timeout_sec=30)
                if repo_path:
                    articles = scan_and_parse_repo(repo_path, name)
                    print(f"  解析到 {len(articles)} 条法条")
                    all_articles.extend(articles)
                else:
                    print(f"  [SKIP] 跳过 {name}")
            except Exception as e:
                print(f"  [ERROR] {name} 处理失败: {e}")

    # 如果仍然没有数据，使用内置备选
    if not all_articles:
        print("\n[WARN] 未从任何源获取数据，使用内置法条数据")
        all_articles = load_builtin_laws()

    if not all_articles:
        print("\n[ERROR] 无任何法条数据")
        return

    print(f"\n总计解析到 {len(all_articles)} 条法条")

    deduped = deduplicate_articles(all_articles)
    print(f"去重后剩余 {len(deduped)} 条法条")

    db_path = get_db_path()
    print(f"\n写入数据库: {db_path}")

    inserted, updated, skipped = insert_articles(db_path, deduped)
    print(f"\n[RESULT] 新增: {inserted}, 更新: {updated}, 跳过: {skipped}")

    stats = {}
    for a in deduped:
        law = a["law_name"]
        stats[law] = stats.get(law, 0) + 1

    print(f"\n[STATS] 法律分布 (Top 20):")
    for law, count in sorted(stats.items(), key=lambda x: -x[1])[:20]:
        print(f"  {law}: {count} 条")


if __name__ == "__main__":
    run_import()
