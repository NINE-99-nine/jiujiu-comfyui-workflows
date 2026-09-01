# User's ComfyUI Environment Map (verified 2026-08-19)

## Install (Comfy Desktop, standalone)
- Launcher: Comfy Desktop (Electron) — logs at `<用户配置目录>\Comfy Desktop\logs\` (C: — view only, never write)
- Server instance: `F:\Comfy-Desktop\ComfyUI-Installs\jiujiu-2\ComfyUI\` (real runtime env: `.venv\Scripts\python.exe`)
- ComfyUI **v0.33.1** (commit `72865f4f`), Python 3.13.12, **torch 2.13.0+xpu** / torchvision 0.28.0+xpu / torchaudio 2.11.0+xpu (2026-08-19 实查)

## 当前实例启动参数（installations.json instance[1]，2026-08-19 实查）

```
launchArgs: --enable-manager --supports-fp8-compute --enable-triton-backend --port 8188
```
- **禁加 `--enable-dynamic-vram`**（见下方教训）
- 实际进程 argv 可从 `/system_stats` 读到

## 当前实例环境变量（installations.json envVars，2026-08-19 实查）

```
TEMP/TMP = F:\Comfy-Desktop\ComfyUI-Installs\jiujiu_2\ComfyUI\temp
PYTHONUTF8=1
SYCL_PI_LEVEL_ZERO_DEVICE_SCOPE_EVENTS=0
ZE_DEVICE_SLEEP=0
TDR_LEVEL=3
TDR_DELAY=60
PYTORCH_XPU_ALLOC_CONF=max_split_size_mb:64
PYTHONGC=700,10,10
ONEAPI_DEVICE_SELECTOR=level_zero:0
OMNI_ATTN_BACKEND=esimd
OMNIXPU_ENABLE=1
OMNIXPU_ATTENTION=1
COMFYUI_GGUF_BACKEND=xpu
```

## 教训：--enable-dynamic-vram 致大图画风漂移（2026-08-19 确认）

- **现象**：int8 convrot 模型 + 大基础分辨率（≥832×1216 / 最终 ≥1248×1824，成品 ~3.3MB）画风漂移（不遵从 LoRA）；小图正常
- **根因**：`--enable-dynamic-vram` 让 int8 模型走「Dynamic VRAM loading + 448 patches attached」的部分加载路径（日志特征），大 latent 时补丁执行异常；Q8 GGUF 模型完全加载（`full load: True`，0 patches）无此问题
- **对照证据**：同工作流同参数，int8 convrot 错 / Q8 GGUF 对；关掉该参数后大图正常
- **结论**：启动参数/环境变量默认不加新东西（奥卡姆剃刀，习惯9）；排查出图问题时先看 `comfyui_8188.log` 的模型加载行（`loaded completely` vs `Dynamic VRAM loading … patches attached`）

## Environment structure — two "environments", don't mix them up
- **Real runtime env**: `<install>\ComfyUI\.venv\` — a uv-managed venv. Check torch here:
  `"<install>\ComfyUI\.venv\Scripts\python.exe" -c "import torch; print(torch.__version__)"`
- **`<install>\standalone-env\` is a BOOTSTRAP SHELL**: Python 3.13.12 + Intel runtime libs (intel-sycl-rt, intel-opencl-rt, mkl, oneMKL…) only — **NO torch inside**. Do not report "torch missing" from here; it's the launcher env, not the server env.
- Deps declared in `<install>\requirements-intel.txt` (XPU index + pinned torch) and `<install>\manifest.json`

## OmniXPU / TE-Speed（2026-08-17 23:52 安装批次）
- `ComfyUI-OmniXPU`（adapters/attention.py 等）、`omni_xpu_kernel-0.2.0b1+torch213.dg2`、`TE-Speed-MiniMaxH3`、`ComfyUI-ClipProj`、`ComfyUI-MiniMaxH3_LatentUpscaler`、`comfyui-minimax-h3-audio-T8` 同批安装
- aimdo ROCm 版备份：`<你的脚本目录>\backup_comfy_aimdo_rocM`（可回滚）
- **OmniXPU 与画风漂移无关**（迁移前即有该现象，已排除）

## GPU
- Intel Arc A770 16GB (`xpu:0`, XPU backend — NOT CUDA). SDXL-class fine; Flux/video heavy workflows struggle.

## Models (shared dir — survives reinstall)
- `F:\Comfy-Desktop\ComfyUI-Shared\models\`
- anima family in `unet\anima\`: `anima-turbo-v1.0-int8-convrot.safetensors`（[8] UNETLoader 默认）, `anima-turbo-v1.0-Q8_0.gguf`（[9] LoaderGGUF 备用）, anima_baseV10.safetensors, anima-aesthetic-v1.1-int8-convrot.safetensors, anima-preview3-base-Q8_0.gguf
- LoRA `anima\anima-turbo-lora-v0.1.safetensors`; clip `Qwen3-0.6B-Base.Q8_0.gguf` (text_encoders); VAE `qwen_image_vae.safetensors`

## Input / Output
- Input: `F:\Comfy-Desktop\ComfyUI-Shared\input`
- Output: `F:\Comfy-Desktop\ComfyUI-Shared\output\` (dated subfolders `YYYY-MM-DD\`) — user moved it off C: 2026-08-01

## Workflow library
- `F:\Comfy-Desktop\ComfyUI-Installs\jiujiu-2\ComfyUI\user\default\workflows\` — UI/editor format
- 主工作流 `anima模型.json`；API 模板与使用守则见本 skill 的 `workflows/anima/`

## Known install issues (from app.log 2026-08-01)
- Danbooru-Gallery sqlite "unable to open database file" — tag sync broken
- feishu_bitable DLL load failed — 2 nodes dead
- TTS-Audio-Suite deps missing; audio_separator missing
- ComfyUI-Manager SSL verify bypass ENABLED (user\__manager\config.ini) — security note

## Pitfalls — env checks
- **XPU wheel index is alphabetical**: `https://download.pytorch.org/whl/xpu/<pkg>/` sorts "2.10.0" BEFORE "2.13.0". Verify by listing ALL matching lines, or trust uv/pip resolution.
- **PYTHONPATH pollution in git-bash**: run external venv python with `env -u PYTHONPATH`.
- **2.10.0 vs 2.1.0 look-alike**: always confirm against the .venv's actual `torch.__version__`.

## How to verify server state
- `curl http://127.0.0.1:8188/system_stats` — version/GPU/argv
- `curl http://127.0.0.1:8188/queue` — running/pending
- 出图日志：`<install>\ComfyUI\user\comfyui_8188.log`（模型加载方式/attention fallback 均在此）
