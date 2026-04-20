export LD_LIBRARY_PATH="/meta_eon_cfs/home/lhs/miniconda3/envs/vggt/lib:$LD_LIBRARY_PATH" # 这个egl库用别人的conda环境下的，因为uv好像不能装c库
export CUDA_VISIBLE_DEVICES=7
uv run scripts/evaluate.py \
    task=libero \
    exp_name=reproduce_libero90_baku_adapt3r_15_large \
    task.cam_shift=large \
    variant_name=epoch_0080 \
    checkpoint_path=experiments/libero/libero_90/reproduce_libero90_baku_adapt3r_15/multitask_model_epoch_0080.pth