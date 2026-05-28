"""
法律知识库统一执行入口
并行执行：法条导入 + 判例爬取 + 司法解释爬取 + 向量化
"""
import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def run_migration():
    print("\n" + "=" * 60)
    print("步骤 0: 创建法律知识库数据库表")
    print("=" * 60)
    from app.db.migrate_legal_knowledge import migrate_legal_knowledge_db
    migrate_legal_knowledge_db()


def run_law_import():
    print("\n" + "=" * 60)
    print("步骤 1: 法条数据导入")
    print("=" * 60)
    from app.services.legal_db.law_importer import run_import
    run_import()


def run_case_crawler():
    print("\n" + "=" * 60)
    print("步骤 2: 指导性案例爬取")
    print("=" * 60)
    from app.services.legal_db.case_crawler import run_crawler
    run_crawler()


def run_interp_crawler():
    print("\n" + "=" * 60)
    print("步骤 3: 司法解释爬取")
    print("=" * 60)
    from app.services.legal_db.interp_crawler import run_crawler
    run_crawler()


def run_vectorization():
    print("\n" + "=" * 60)
    print("步骤 4: 向量化入库")
    print("=" * 60)
    from app.services.legal_db.vectorizer import run_vectorization
    run_vectorization()


def run_all(parallel: bool = True):
    start_time = time.time()

    print("=" * 60)
    print("  法律知识库构建 - 全部并行推进")
    print("=" * 60)

    # 步骤 0: 必须先创建表
    run_migration()

    if parallel:
        # 并行执行数据导入和爬取
        print("\n" + "=" * 60)
        print("  并行执行: 法条导入 + 判例爬取 + 司法解释爬取")
        print("=" * 60)

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(run_law_import): "法条导入",
                executor.submit(run_case_crawler): "判例爬取",
                executor.submit(run_interp_crawler): "司法解释爬取",
            }

            for future in as_completed(futures):
                name = futures[future]
                try:
                    future.result()
                    print(f"\n[OK] {name} 完成")
                except Exception as e:
                    print(f"\n[ERROR] {name} 失败: {e}")
    else:
        run_law_import()
        run_case_crawler()
        run_interp_crawler()

    # 步骤 4: 向量化（必须在数据入库后执行）
    run_vectorization()

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"  全部完成！总耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="法律知识库构建工具")
    parser.add_argument("--step", choices=["migration", "law", "case", "interp", "vector", "all"],
                        default="all", help="执行指定步骤")
    parser.add_argument("--sequential", action="store_true", help="顺序执行（非并行）")

    args = parser.parse_args()

    steps = {
        "migration": run_migration,
        "law": run_law_import,
        "case": run_case_crawler,
        "interp": run_interp_crawler,
        "vector": run_vectorization,
        "all": lambda: run_all(parallel=not args.sequential),
    }

    steps[args.step]()
