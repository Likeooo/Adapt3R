export LD_LIBRARY_PATH="/meta_eon_cfs/home/lhs/miniconda3/envs/vggt/lib:$LD_LIBRARY_PATH" # 这个egl库用别人的conda环境下的，因为uv好像不能装c库
export CUDA_VISIBLE_DEVICES=6,7
uv run scripts/process_libero_data.py  task=libero