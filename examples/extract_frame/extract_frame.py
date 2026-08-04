#!/usr/bin/env python3
"""
extract_frame.py — LeRobot v3 数据集截帧提取工具

从 LeRobot v3 格式的帧数据 parquet 中定位目标帧,
再从对应视频文件中用 PyAV 解码并保存截帧图片。

依赖:
    pip install pyarrow pandas av pillow numpy

用法:
    python3 extract_frame.py <数据集根目录> <全局帧序号> [--camera CAMERA_KEY]

示例:
    # 提取全局第 500 帧的所有相机截帧
    python3 extract_frame.py cube_stacking_merged 500

    # 只提取 left_head 相机
    python3 extract_frame.py cube_stacking_merged 500 --camera observation.images.left_head

    # 输出到指定目录
    python3 extract_frame.py cube_stacking_merged 500 --output ./frames
"""

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
import pandas as pd
from PIL import Image


def load_info(dataset_root: Path) -> dict:
    info_path = dataset_root / "meta" / "info.json"
    if not info_path.exists():
        sys.exit(f"错误: 找不到 info.json -> {info_path}")
    with open(info_path) as f:
        return json.load(f)


def load_data_parquet(dataset_root: Path, info: dict) -> pd.DataFrame:
    data_path_tpl = info["data_path"]
    data_path = dataset_root / data_path_tpl.format(chunk_index=0, file_index=0)
    if not data_path.exists():
        sys.exit(f"错误: 找不到数据文件 -> {data_path}")
    return pd.read_parquet(data_path)


def load_episodes_parquet(dataset_root: Path) -> pd.DataFrame:
    ep_path = dataset_root / "meta" / "episodes" / "chunk-000" / "file-000.parquet"
    if not ep_path.exists():
        sys.exit(f"错误: 找不到 episodes 文件 -> {ep_path}")
    return pd.read_parquet(ep_path)


def get_video_keys(info: dict) -> list[str]:
    video_keys = []
    for key, feat in info["features"].items():
        if feat.get("dtype") == "video":
            video_keys.append(key)
    return video_keys


def resolve_video_path(dataset_root: Path, info: dict, ep_row: pd.Series, video_key: str) -> Path:
    video_path_tpl = info["video_path"]
    chunk_col = f"videos/{video_key}/chunk_index"
    file_col = f"videos/{video_key}/file_index"

    if chunk_col in ep_row.index:
        chunk_idx = int(ep_row[chunk_col])
        file_idx = int(ep_row[file_col])
    else:
        chunk_idx, file_idx = 0, 0

    return dataset_root / video_path_tpl.format(
        video_key=video_key, chunk_index=chunk_idx, file_index=file_idx
    )


def extract_frame_pyav(video_path: Path, target_frame_idx: int, fps: int) -> np.ndarray | None:
    """用 PyAV 从视频文件中精确提取第 target_frame_idx 帧 (0-based)。

    策略: seek 到最近的前一个关键帧, 然后逐帧解码直到目标帧。
    """
    container = av.open(str(video_path))
    try:
        stream = container.streams.video[0]
        time_base = stream.time_base
        avg_rate = stream.average_rate or stream.base_rate or fps

        target_ts_sec = Fraction(target_frame_idx, int(avg_rate))
        target_pts = int(target_ts_sec / time_base)

        container.seek(
            target_pts,
            any_frame=False,
            backward=True,
            stream=stream,
        )

        prev_frame = None
        for frame in container.decode(video=0):
            if frame.pts is not None and frame.pts >= target_pts:
                return frame.to_ndarray(format="rgb24")
            prev_frame = frame

        if prev_frame is not None:
            return prev_frame.to_ndarray(format="rgb24")
    finally:
        container.close()

    return None


def main():
    parser = argparse.ArgumentParser(
        description="LeRobot v3 截帧提取工具 (PyAV)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("dataset", type=str, help="LeRobot v3 数据集根目录路径")
    parser.add_argument("frame_index", type=int, help="全局帧序号 (data parquet 中的 index 列)")
    parser.add_argument(
        "--camera", "-c", type=str, default=None,
        help="指定相机 key (如 observation.images.left_head), 默认提取所有相机"
    )
    parser.add_argument(
        "--output", "-o", type=str, default="./frames",
        help="输出目录 (默认 ./frames)"
    )
    args = parser.parse_args()

    dataset_root = Path(args.dataset)
    if not dataset_root.is_dir():
        sys.exit(f"错误: 数据集目录不存在 -> {dataset_root}")

    info = load_info(dataset_root)
    fps = info["fps"]
    all_video_keys = get_video_keys(info)

    if args.camera:
        if args.camera not in all_video_keys:
            sys.exit(f"错误: 相机 key '{args.camera}' 不存在\n可用相机: {all_video_keys}")
        video_keys = [args.camera]
    else:
        video_keys = all_video_keys

    print(f"数据集: {dataset_root}")
    print(f"FPS: {fps}  |  可用相机: {all_video_keys}")
    print(f"目标: 全局帧序号 = {args.frame_index}")
    print()

    df = load_data_parquet(dataset_root, info)
    target_row = df[df["index"] == args.frame_index]
    if target_row.empty:
        available_min, available_max = int(df["index"].min()), int(df["index"].max())
        sys.exit(
            f"错误: 全局帧序号 {args.frame_index} 不存在\n"
            f"可用范围: [{available_min}, {available_max}]"
        )

    row = target_row.iloc[0]
    episode_index = int(row["episode_index"])
    frame_index_in_ep = int(row["frame_index"])
    timestamp = float(row["timestamp"])

    print("=" * 70)
    print(f"  截帧序号 (全局 index):  {args.frame_index}")
    print(f"  episode_index:          {episode_index}")
    print(f"  frame_index (集内序号):  {frame_index_in_ep}")
    print(f"  timestamp:              {timestamp:.4f}s")
    print("=" * 70)

    episodes_df = load_episodes_parquet(dataset_root)
    ep_row = episodes_df[episodes_df["episode_index"] == episode_index]
    if ep_row.empty:
        sys.exit(f"错误: episode {episode_index} 在 episodes parquet 中不存在")
    ep_row = ep_row.iloc[0]

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    for vk in video_keys:
        video_path = resolve_video_path(dataset_root, info, ep_row, vk)
        from_ts_col = f"videos/{vk}/from_timestamp"
        if from_ts_col in ep_row.index:
            from_timestamp = float(ep_row[from_ts_col])
        else:
            from_timestamp = 0.0

        video_frame_idx = round(from_timestamp * fps) + frame_index_in_ep

        print(f"\n  [{vk}]")
        print(f"    视频文件: {video_path}")
        print(f"    视频内帧偏移 (from_timestamp): {from_timestamp:.4f}s")
        print(f"    视频内目标帧号: {video_frame_idx}")

        if not video_path.exists():
            print(f"    ⚠ 视频文件不存在, 跳过")
            continue

        frame_rgb = extract_frame_pyav(video_path, video_frame_idx, fps)
        if frame_rgb is None:
            print(f"    ⚠ 帧提取失败, 跳过")
            continue

        safe_key = vk.replace(".", "_").replace("/", "_")
        out_path = output_dir / f"frame_{args.frame_index}_{safe_key}.jpg"
        Image.fromarray(frame_rgb).save(out_path, quality=95)
        print(f"    分辨率: {frame_rgb.shape[1]}x{frame_rgb.shape[0]}")
        print(f"    ✅ 已保存: {out_path}")

    print("\n完成。")


if __name__ == "__main__":
    main()