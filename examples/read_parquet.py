#!/usr/bin/env python3
"""
read_parquet.py — 通用 Parquet 文件读取/查看工具

用法:
    python3 read_parquet.py <parquet文件路径> [选项]

选项:
    -n, --rows N       预览前 N 行数据 (默认 5)
    -c, --columns      只打印列名与类型, 不打印数据
    --column NAME      只查看指定某一列的前 N 行
    --stats            对数值列打印 describe() 统计
    --full             打印完整表格 (不折叠列/行, 谨慎用于大文件)

示例:
    python3 read_parquet.py cube_stacking_merged/data/chunk-000/file-000.parquet
    python3 read_parquet.py cube_stacking_merged/data/chunk-000/file-000.parquet -n 10
    python3 read_parquet.py cube_stacking_merged/meta/tasks.parquet --column task
"""
import argparse
import os
import sys

try:
    import pandas as pd
    import pyarrow.parquet as pq
except ImportError:
    sys.exit("缺少依赖, 请先安装:  pip install pyarrow pandas")


def human_size(num_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


def read_parquet(path: str, rows: int = 5, columns_only: bool = False,
                 column: str = None, stats: bool = False, full: bool = False):
    if not os.path.isfile(path):
        sys.exit(f"文件不存在: {path}")

    # 先读文件级元数据 (无需加载全部数据)
    pf = pq.ParquetFile(path)
    meta = pf.metadata
    print("=" * 70)
    print(f"文件: {path}")
    print(f"大小: {human_size(os.path.getsize(path))}")
    print(f"行数: {meta.num_rows}    列数: {meta.num_columns}    "
          f"Row Group 数: {meta.num_row_groups}")
    try:
        print(f"压缩: {meta.row_group(0).column(0).compression}")
    except Exception:
        pass
    print("=" * 70)

    # 列名与类型 (Arrow schema)
    print("\n[列结构 Schema]")
    for field in pf.schema_arrow:
        print(f"  - {field.name:<45} {field.type}")

    if columns_only:
        return

    # 加载为 DataFrame
    df = pf.read().to_pandas()
    # 某些 parquet 会把某列标记为 pandas 索引(如 tasks 的 task 列),
    # 这里统一还原成普通列, 保证 --column 可访问到全部字段
    if df.index.name is not None or list(df.index.names) != [None]:
        df = df.reset_index()

    if full:
        pd.set_option("display.max_columns", None)
        pd.set_option("display.max_rows", None)
        pd.set_option("display.width", None)

    if column:
        if column not in df.columns:
            sys.exit(f"列不存在: {column}\n可用列: {list(df.columns)}")
        print(f"\n[列 '{column}' 前 {rows} 行]")
        print(df[column].head(rows).to_string())
    else:
        print(f"\n[前 {rows} 行数据]  (整体形状: {df.shape})")
        # 列很多时转置显示更易读
        preview = df.head(rows)
        print(preview.T if df.shape[1] > 12 else preview.to_string())

    if stats:
        print("\n[数值列统计 describe()]")
        num = df.select_dtypes(include="number")
        if num.empty:
            print("  (无数值列)")
        else:
            print(num.describe().T.to_string())

    return df


def main():
    p = argparse.ArgumentParser(
        description="通用 Parquet 读取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    p.add_argument("path", help="parquet 文件路径")
    p.add_argument("-n", "--rows", type=int, default=5, help="预览行数 (默认 5)")
    p.add_argument("-c", "--columns", action="store_true", help="只看列结构")
    p.add_argument("--column", help="只看某一列")
    p.add_argument("--stats", action="store_true", help="打印数值列统计")
    p.add_argument("--full", action="store_true", help="不折叠完整打印")
    args = p.parse_args()

    read_parquet(args.path, rows=args.rows, columns_only=args.columns,
                 column=args.column, stats=args.stats, full=args.full)


if __name__ == "__main__":
    main()
