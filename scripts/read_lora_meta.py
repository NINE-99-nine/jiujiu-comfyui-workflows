# 从 safetensors LoRA/模型文件内部提取训练元数据（CivitAI 连不上时的权威角色标签来源）
# 用法: python read_lora_meta.py <path_to.safetensors> [--full]
import json
import struct
import sys

def read_metadata(path):
    with open(path, 'rb') as f:
        n = struct.unpack('<Q', f.read(8))[0]   # 前 8 字节 = JSON 头长度
        hdr = json.loads(f.read(n))
    return hdr.get('__metadata__', {})

if __name__ == '__main__':
    path = sys.argv[1]
    meta = read_metadata(path)
    if '--full' in sys.argv:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    else:
        keys = ('ss_output_name', 'ss_base_model_version', 'ss_sd_model_name',
                'ss_tag_frequency', 'ss_clip_skip', 'ss_network_dim', 'ss_network_alpha',
                'ss_num_train_images', 'ss_learning_rate')
        for k in keys:
            if k in meta:
                print(f'{k}: {str(meta[k])[:500]}')

# 要点:
# - ss_tag_frequency: 训练时用的真实 Danbooru 标签（触发词、外貌特征）→ 直接当提示词素材
# - ss_base_model_version: 基座架构（sdxl_base_v1-0 / flux 等）→ 决定 LoRA 与模型的兼容性
# - 旁边的 *.metadata.json 经常是空壳，一定要读 safetensors 头
# - ss_clip_skip=2 等训练参数影响出图风格，写提示词时值得参考
