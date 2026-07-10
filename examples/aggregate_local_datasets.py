#!/usr/bin/env python3
"""
将多个本地 LeRobot 子数据集合并为一个统一数据集，用于多任务训练。

用法:
    # 自动扫描父目录下所有子数据集并合并
    uv run python examples/aggregate_local_datasets.py \
        --source_dir /personal/bimanual_multi_task.tar/bimanual_multi_task \
        --output_dir /personal/bimanual_multi_task_merged \
        --repo_id jim1234321/smolvla_multi_task
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from lerobot.datasets.aggregate import aggregate_datasets

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def find_sub_datasets(source_dir: Path) -> list[tuple[str, Path]]:
    """扫描 source_dir 下所有包含 meta/info.json 的有效数据集子目录。"""
    datasets = []
    for sub in sorted(source_dir.iterdir()):
        if sub.is_dir() and (sub / "meta" / "info.json").exists():
            with open(sub / "meta" / "info.json") as f:
                info = json.load(f)
            repo_id = info.get("repo_id", sub.name)
            datasets.append((repo_id, sub))
            logger.info(f"  找到数据集: repo_id={repo_id}, path={sub}")
    return datasets


def main():
    parser = argparse.ArgumentParser(description="合并多个本地 LeRobot 子数据集")
    parser.add_argument(
        "--source_dir",
        type=Path,
        required=True,
        help="包含多个子数据集的父目录",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        required=True,
        help="合并后数据集的输出目录",
    )
    parser.add_argument(
        "--repo_id",
        type=str,
        default=None,
        help="合并后数据集的 repo_id（不指定则用第一个子数据集的 repo_id）",
    )
    args = parser.parse_args()

    source_dir = args.source_dir
    if not source_dir.is_dir():
        logger.error(f"源目录不存在: {source_dir}")
        sys.exit(1)

    logger.info(f"扫描目录: {source_dir}")
    sub_datasets = find_sub_datasets(source_dir)

    if not sub_datasets:
        logger.error(
            f"在 {source_dir} 下没有找到有效的 LeRobot 数据集（需要有 meta/info.json）"
        )
        sys.exit(1)

    logger.info(f"共找到 {len(sub_datasets)} 个子数据集")

    repo_ids = [r for r, _ in sub_datasets]
    roots = [p for _, p in sub_datasets]

    aggr_repo_id = args.repo_id or repo_ids[0]
    logger.info(f"合并后 repo_id: {aggr_repo_id}")
    logger.info(f"输出目录: {args.output_dir}")

    aggregate_datasets(
        repo_ids=repo_ids,
        roots=roots,
        aggr_repo_id=aggr_repo_id,
        aggr_root=args.output_dir,
    )

    logger.info("=" * 50)
    logger.info("合并完成！现在可以用以下命令训练：")
    logger.info(
        f"  lerobot-train \\\n"
        f"    --policy.path=lerobot/smolvla_base \\\n"
        f"    --dataset.repo_id={aggr_repo_id} \\\n"
        f"    --dataset.root={args.output_dir} \\\n"
        f"    --batch_size=32 \\\n"
        f"    --steps=35000 \\\n"
        f"    --policy.device=cuda \\\n"
        f"    --wandb.enable=true \\\n"
        f"    --policy.repo_id={aggr_repo_id}"
    )


if __name__ == "__main__":
    main()
