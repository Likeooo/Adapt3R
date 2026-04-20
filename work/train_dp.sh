export LD_LIBRARY_PATH="/meta_eon_cfs/home/lhs/miniconda3/envs/vggt/lib:$LD_LIBRARY_PATH" # 这个egl库用别人的conda环境下的，因为uv好像不能装c库
export CUDA_VISIBLE_DEVICES=6
uv run scripts/train.py \
    --config-name=train.yaml \
    task=libero \
    algo=diffusion_policy \
    algo/encoder=adapt3r  \
    algo.chunk_size=8 \
    exp_name=reproduce_libero90_dp_adapt3r_8 \