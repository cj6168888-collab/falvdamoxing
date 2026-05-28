"""
lawtext/laws 仓库 Markdown 格式法条解析器
格式: YAML frontmatter + Markdown body，条文用 **第一条** 标记
"""
import os
import re
import yaml
import uuid
from typing import List, Dict


def parse_lawtext_markdown(filepath: str) -> Dict:
    """解析单个 lawtext markdown 文件"""
    with open(filepath, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8', errors='replace')

    # Split frontmatter
    parts = text.split('---', 2)
    if len(parts) < 3:
        return None

    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        fm = {}

    body = parts[2].strip()

    # Extract law name from frontmatter or body
    law_name = fm.get('title', '')
    if not law_name:
        # Try first line of body
        first_line = body.split('\n')[0].strip().strip('*').strip()
        law_name = first_line[:100]

    effective_date = fm.get('effective_date', '')
    status = fm.get('status', '')
    category = _guess_category(law_name)

    # Parse articles from body
    articles = _extract_articles(body, law_name, category, effective_date)

    return {
        'law_name': law_name,
        'effective_date': effective_date,
        'status': status,
        'articles': articles,
    }


def _extract_articles(body: str, law_name: str, category: str, effective_date: str) -> List[Dict]:
    """从 markdown body 中提取条文"""
    articles = []

    # Pattern: **第一条** 或 **第1条** 或 - **第一条**
    pattern = re.compile(r'(?:[-*]\s*)?\*\*(第[一二三四五六七八九十百千\d]+[条之]?[一二三四五六七八九十\d]*)\*\*')

    # Split by article markers
    parts = pattern.split(body)

    if len(parts) < 3:
        # Try alternative: no bold markers, just text
        return _extract_articles_plain(body, law_name, category, effective_date)

    current_chapter = ''
    i = 1
    while i < len(parts) - 1:
        article_number = parts[i].strip()
        content_raw = parts[i + 1].strip()

        # Clean content
        content = _clean_markdown(content_raw)

        # Detect chapter headings
        if '章' in article_number and '条' not in article_number:
            current_chapter = article_number
            i += 2
            continue

        if not content:
            i += 2
            continue

        articles.append({
            'id': str(uuid.uuid4()),
            'law_name': law_name,
            'article_number': article_number,
            'title': '',
            'content': content,
            'chapter': current_chapter,
            'category': category,
            'effective_date': effective_date,
            'is_valid': 1,
            'source': 'lawtext/laws',
        })

        i += 2

    return articles


def _extract_articles_plain(body: str, law_name: str, category: str, effective_date: str) -> List[Dict]:
    """备用解析：无加粗标记的条文"""
    articles = []
    pattern = re.compile(r'(?:[-*]\s*)?(第[一二三四五六七八九十百千\d]+[条之]?[一二三四五六七八九十\d]*)')

    lines = body.split('\n')
    current_article = None
    current_content = []
    current_chapter = ''

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Chapter heading
        if line.startswith('##') and '章' in line:
            current_chapter = line.replace('#', '').replace('*', '').strip()
            continue

        match = pattern.match(line)
        if match:
            if current_article and current_content:
                articles.append({
                    'id': str(uuid.uuid4()),
                    'law_name': law_name,
                    'article_number': current_article,
                    'title': '',
                    'content': '\n'.join(current_content).strip(),
                    'chapter': current_chapter,
                    'category': category,
                    'effective_date': effective_date,
                    'is_valid': 1,
                    'source': 'lawtext/laws',
                })
            current_article = match.group(1)
            rest = line[match.end():].strip()
            current_content = [rest] if rest else []
        elif current_article:
            current_content.append(line)

    if current_article and current_content:
        articles.append({
            'id': str(uuid.uuid4()),
            'law_name': law_name,
            'article_number': current_article,
            'title': '',
            'content': '\n'.join(current_content).strip(),
            'chapter': current_chapter,
            'category': category,
            'effective_date': effective_date,
            'is_valid': 1,
            'source': 'lawtext/laws',
        })

    return articles


def _clean_markdown(text: str) -> str:
    """清理 markdown 格式，保留纯文本"""
    # Remove bold/italic markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # Remove heading markers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # Remove list markers
    text = re.sub(r'^[-*]\s+', '', text, flags=re.MULTILINE)
    # Remove extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


CATEGORY_MAP = {
    '民法典': 'civil', '宪法': 'constitutional', '刑法': 'criminal',
    '刑事诉讼法': 'criminal_procedure', '民事诉讼法': 'civil_procedure',
    '行政诉讼法': 'administrative_litigation', '行政': 'administrative',
    '劳动法': 'labor', '劳动合同法': 'labor', '公司法': 'company',
    '仲裁': 'arbitration', '合同': 'civil', '物权': 'civil',
    '侵权责任': 'civil', '婚姻': 'civil', '继承': 'civil',
    '知识产权': 'ip', '商标': 'ip', '专利': 'ip', '著作权': 'ip',
    '环境': 'environmental', '消费者权益': 'consumer',
    '个人信息': 'data_protection', '网络安全': 'data_protection',
    '数据安全': 'data_protection', '反不正当竞争': 'commercial',
    '反垄断': 'commercial', '税': 'tax', '保险': 'insurance',
    '证券': 'securities', '银行': 'banking', '破产': 'bankruptcy',
    '土地': 'land', '房地产': 'real_estate', '建筑': 'construction',
    '招标投标': 'bidding', '治安管理': 'public_security',
    '道路交通': 'traffic', '未成年人': 'minors', '妇女': 'women',
    '人民调解': 'mediation', '社会保险': 'social_insurance',
    '海商': 'maritime', '票据': 'commercial', '担保': 'civil',
}


def _guess_category(law_name: str) -> str:
    for keyword, category in CATEGORY_MAP.items():
        if keyword in law_name:
            return category
    return 'other'


def scan_lawtext_repo(repo_path: str) -> List[Dict]:
    """扫描整个 lawtext 仓库"""
    all_articles = []
    content_dir = os.path.join(repo_path, 'content')

    if not os.path.exists(content_dir):
        return all_articles

    # Categories to scan (skip en, about)
    skip_dirs = {'en', 'about', '.git', '.github'}

    for cat_name in os.listdir(content_dir):
        cat_dir = os.path.join(content_dir, cat_name)
        if not os.path.isdir(cat_dir) or cat_name in skip_dirs:
            continue

        md_files = [f for f in os.listdir(cat_dir) if f.endswith('.md') and not f.startswith('_')]
        print(f'  解析 {cat_name}: {len(md_files)} 个文件')

        for md_file in md_files:
            filepath = os.path.join(cat_dir, md_file)
            try:
                result = parse_lawtext_markdown(filepath)
                if result and result['articles']:
                    all_articles.extend(result['articles'])
            except Exception as e:
                pass  # Skip files that fail to parse

    return all_articles
