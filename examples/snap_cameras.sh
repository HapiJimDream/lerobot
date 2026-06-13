#!/usr/bin/env bash
# 摄像头快照脚本 —— 逐个用 ffmpeg 抓取单帧保存
#
# 配合 udev 规则 /etc/udev/rules.d/99-fixed-cameras.rules 使用,
# 通过固定符号链接 /dev/camLeft /dev/camRight /dev/camHead 访问摄像头。
#
# 为什么这样写:
#   - 单设备逐个抓帧,不同时 open,避免多路 UVC 抢 USB 带宽导致卡死(D 状态)。
#   - 强制 MJPEG,带宽是 YUYV 未压缩的 1/10,USB 2.0 才扛得住。
#   - timeout 兜底,某路摄像头卡住时自动放弃,不拖死整个脚本。
#   - 注意:遥操作运行时摄像头容易卡,建议在没跑遥操作时执行本脚本。
#
# 用法:
#   ./examples/snap_cameras.sh                 # 截默认三个摄像头
#   ./examples/snap_cameras.sh camLeft camHead # 只截指定摄像头
#   SIZE=1280x720 OUTDIR=/tmp ./examples/snap_cameras.sh

set -u

CAMS=("$@")
if [ ${#CAMS[@]} -eq 0 ]; then
  CAMS=(camLeft camRight camHead)
fi

SIZE="${SIZE:-640x480}"          # 分辨率
OUTDIR="${OUTDIR:-examples}"     # 输出目录
FMT="${FMT:-mjpeg}"              # 输入像素格式
TIMEOUT="${TIMEOUT:-15}"         # 单个摄像头超时(秒)

mkdir -p "$OUTDIR"

rc_all=0
for cam in "${CAMS[@]}"; do
  dev="/dev/$cam"
  if [ ! -e "$dev" ]; then
    echo "FAIL $cam: 设备 $dev 不存在(检查摄像头是否插好 / udev 规则)"
    rc_all=1
    continue
  fi
  real=$(readlink -f "$dev")
  out="$OUTDIR/snap_$cam.jpg"
  echo "=== $cam ($real) -> $out ==="
  if timeout "$TIMEOUT" ffmpeg -y -loglevel error \
       -f v4l2 -input_format "$FMT" -video_size "$SIZE" \
       -i "$dev" -frames:v 1 "$out" </dev/null; then
    echo "OK   $cam ($(du -h "$out" | cut -f1))"
  else
    echo "FAIL $cam: 抓帧失败或超时(${TIMEOUT}s)"
    rc_all=1
  fi
done

exit $rc_all
