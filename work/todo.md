你需要帮我写一个新的3d encoder，请在adapt3r/algos/encoders/目录下新增一个pg3.py文件实现这个PG3Encoder，并且增加相关的实例化配置文件，请你一边写代码一边把代码注释写好。

scripts/train.py中data_loader每次迭代加载出来的data是这样的：
- obs: 
    - agentview_image: torch.Size([64, 1, 3, 128, 128])，外部图像
    - robot0_eye_in_hand_image: torch.Size([64, 1, 3, 128, 128])，腕部图像
    - agentview_depth: torch.Size([64, 1, 1, 128, 128])
    - robot0_eye_in_hand_depth: torch.Size([64, 1, 1, 128, 128])
    - agentview_extrinsic: torch.Size([64, 1, 4, 4])，外部相机在世界坐标系中的位姿
    - robot0_eye_in_hand_extrinsic: torch.Size([64, 1, 4, 4])，腕部相机在世界坐标系中的位姿
    - agentview_intrinsic: torch.Size([64, 1, 3, 3])
    - robot0_eye_in_hand_intrinsic: torch.Size([64, 1, 3, 3])
    - 还有一些其他东西
- task_id: torch.Size([64])，每个样本对应的task_id（0到89）
- task_emb: torch.Size([64, 512])
- actions: torch.Size([64, 15, 7])



现在定义PG3Encoder的各个模块的输入输出：
- 整理OOI_names：参照work/demo.py下的代码实现OOI_names的构造
    - 输入：data['task_id']
    - 输出：
        - OOI_names: Tensor(batch_size, max_num_OOI)，max_num_OOI应该可配置
        - OOI_names_mask: Tensor(batch_size, max_num_OOI)

- 分割模块：对两个视角的相机图像都按照OOI_names进行分割
    - 输入：data['obs']['agentview_image'], data['obs']['robot0_eye_in_hand_image'], OOI_names，OOI_names_mask
    - 中间：使用sam3，我已经以开发者模式安装了sam3,它在third_party/sam3，我想要使用类似于work/sam3.py这种实现方式，腕部相机离物体比较近，因此如果分割出来的物体区域很小，则判断为噪声
        - 在腕部视角中，如果分割区域太小，过滤
    - 输出：
        - OOI_ext: Tensor(batch_size, max_num_OOI, h, w)
        - OOI_ext_mask: Tensor(batch_size, max_num_OOI)
        - OOI_wrist: Tensor(batch_size, max_num_OOI, h, w)
        - OOI_wrist_mask: Tensor(batch_size, max_num_OOI)

- 反投影点云：使用相机参数和深度图将感兴趣物体反投影回点云（世界坐标系下）
    - 输入：OOI_ext, OOI_ext_mask, OOI_wrist，OOI_wrist_mask, data['obs']['agentview_depth'], data['obs']['robot0_eye_in_hand_depth'], data['obs']['agentview_extrinsic'], data['obs']['robot0_eye_in_hand_extrinsic'], data['obs']['agentview_intrinsic'], data['obs']['robot0_eye_in_hand_intrinsic']
    - 中间：分别对OOI_ext, OOI_wrist反投影回点云，然后对应进行融合这两个
    - 输出：
        - OOI_pcds_world,：Tensor(batch_size, max_num_OOI, 后面这些维度应该是点云的形状),
        - OOI_pcds_mask：Tensor(batch_size, max_num_OOI)表示哪些不是padding的
- 特征构造：
    - 输入：OOI_pcds_world，OOI_pcds_mask
    - 中间：
        - 根据OOI_pcds_world得到各个感兴趣物体的3d bbox，具体方法你来决定
        - 将OOI_pcds_world输入dp3的轻量点云头提取特征得到OOI_embeddings，具体来说合并batch_size和max_num_OOI这两个维度再送进点云头这样可以一次性forward
    - 输出：
        - OOI_embeddings：Tensor(batch_size, max_num_OOI，dp3_latent_dim)
        - OOI_embeddings_mask: Tensor(batch_size, max_num_OOI)
        - OOI_3d_bboxs: Tensor(batch_size, max_num_OOI, 6),这里的6表示bbox的中心点xyz以及bbox的长宽高
        - OOI_3d_bboxs_mask: Tensor(batch_size, max_num_OOI)
- 特征融合：
    - 输入：OOI_embeddings，OOI_embeddings_mask, OOI_names，OOI_names_mask, OOI_3d_bboxs, OOI_3d_bboxs_mask
    - 中间：先将OOI_names和OOI_3d_bboxs都分别嵌入并投影成Tensor(batch_size, max_num_OOI，dp3_latent_dim)，然后再将OOI_names和OOI_3d_bboxs和OOI_embeddings在维度2拼接，得到Tensor(batch_size, max_num_OOI，3*dp3_latent_dim)，最后通过一个投影层映射成动作解码器需要的维度
    - 输出：perception_encodings, lowdim_encodings，这里的形状参考其他的encoder比如adapt3r.py