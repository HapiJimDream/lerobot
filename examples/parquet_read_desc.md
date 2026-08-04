调用示例:
# 预览主数据前 3 行
python3 read_parquet.py cube_stacking_merged/data/chunk-000/file-000.parquet -n 3

# 只看列结构(适合 121 列的元数据文件)
python3 read_parquet.py cube_stacking_merged/meta/episodes/chunk-000/file-000.parquet -c

# 查看某一列
python3 read_parquet.py cube_stacking_merged/meta/tasks.parquet --column task

# 数值列统计
python3 read_parquet.py cube_stacking_merged/data/chunk-000/file-000.parquet --stats