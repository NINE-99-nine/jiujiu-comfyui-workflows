# ComfyUI Custom Node Load-Failure Diagnosis

How to diagnose a custom node that shows `IMPORT FAILED` in ComfyUI startup logs
(and why shell reproduction often disagrees with the real process). Verified
2026-08-05 on the seedvr2_videoupscaler failure after torch 2.10 → 2.13+xpu.

## Fast triage
1. `curl http://127.0.0.1:8188/system_stats` — confirm pytorch_version, argv (vram flags, extra paths).
2. `grep -inE "seedvr|Traceback|ImportError|Cannot import" <install>/ComfyUI/user/comfyui.log | tail -40`
   — the real Traceback is logged here, NOT in the Comfy Desktop app.log.
3. `curl http://127.0.0.1:8188/object_info | python -c "import json,sys; d=json.load(sys.stdin); print(sorted(k for k in d if '<node>' in k.lower()))"`
   — nodes registered by a FAILED plugin are **partial-import residue**: modules imported
   before the failing line already mutated the global node registry. Missing main nodes =
   still broken; do not trust a partial node list as "working".
4. `ls <install>/ComfyUI/custom_nodes/<name>/` + read `__init__.py` first import lines — the
   failure often lives in the first few imports (the last frame of the traceback is the trigger).

## Shell-reproduction trap (Comfy Desktop)
A plain `python -c "import <custom_node>"` against `<install>/ComfyUI/.venv/Scripts/python.exe`
often **succeeds** where the real process fails. Differences that matter:
- Prestartup scripts (`prestartup_script.py` of rgthree-comfy, comfyui-easy-use …) run before nodes.
- `comfy_aimdo.control.init()` — in a plain shell it logs "Could not autodetect AIMDO
  implementation, assuming Nvidia"; the Comfy Desktop process may detect XPU differently.
- Load order = `sorted(os.listdir(custom_nodes))`; nodes load before/after each other matters.
- env: `python -s` (no user site), cwd = ComfyUI root, PATH includes standalone-env bins.
To simulate closer: `sys.path.insert(0, <ComfyUI>); import comfy, comfy_kitchen` first, then
load nodes via `importlib.util.spec_from_file_location(name, node/__init__.py)` in sorted order.
Even then some differences remain — the swallowed-exception path is the one to chase, not the repro.

## Case study: `<module 'bitsandbytes'> is a built-in module` (seedvr2)
Symptom: seedvr2_videoupscaler `IMPORT FAILED`; traceback ends in diffusers import →
`torch/_library/custom_ops.py _register_fake` → `inspect.getframeinfo` → `inspect.getmodule`
loop → `inspect.getfile(bitsandbytes)` raises `TypeError: <module 'bitsandbytes'> is a built-in module`.

Root chain (all verified):
1. torch 2.13's `_register_fake` calls `torch._library.utils.get_source(stacklevel)` — it needs
   **source-file location** of the fake impl. torch 2.10 did not; this is why old code worked.
2. seedvr2's `src/optimization/compatibility.py` runs `ensure_bitsandbytes_safe()` at import:
   it tries `import bitsandbytes`; on ANY ImportError/OSError/RuntimeError/ValueError it builds a
   stub `types.ModuleType('bitsandbytes')` with **`stub.__file__ = None`** and plants it in
   `sys.modules`. The real exception is **swallowed silently** (no log line).
3. Why the stub explodes only for bitsandbytes (not the flash_attn/xformers stubs the same file
   creates): `inspect.getmodule`'s loop uses `hasattr(module,'__file__')` (True for `__file__=None`)
   but `inspect.getfile` uses `getattr(module,'__file__',None)` (falsy → "built-in module"). The
   `inspect._filesbymodname` cache decides: a module never successfully imported has no cache
   entry → `f=None == cache.get(name,None)=None` → `continue` (skipped, harmless). But
   bitsandbytes exec'd PARTWAY (its `backends/xpu/ops.py` prints "Register sycl bitsandbytes
   kernels for XPU" then `register_kernel` calls torch.library → triggers a get_source →
   caches the REAL path) before failing → cache holds real path ≠ stub's None → getabsfile →
   `getfile` → TypeError.

## Fix pattern: give stubs a real `__file__`
Any module stub planted in `sys.modules` must set `__file__` to a **real, existing path**
(original or its `__init__.py`), not `None`:
```python
stub.__file__ = next(
    (os.path.join(p, "bitsandbytes", "__init__.py")
     for p in sys.path
     if os.path.isfile(os.path.join(p, "bitsandbytes", "__init__.py"))),
    None,
)
```
Double safety: if `__file__ == _filesbymodname[name]` cache → `continue` (short-circuit);
else `getfile` returns a valid path instead of raising. Do NOT patch the flash_attn/xformers
stubs — those never had a successful partial import, so no cache entry exists and `None`
short-circuits safely; leave them alone (KISS).

## Verification without restarting ComfyUI
Simulate the exact crash state in the venv python (no server needed):
1. `builtins.__import__` monkey-patch: raise ImportError for `bitsandbytes` → then
   `spec_from_file_location`-load the PATCHED compatibility.py (it has no relative imports).
2. Assert `sys.modules['bitsandbytes'].__file__` == real site-packages path.
3. `inspect.getfile(stub)` must return the path (was: TypeError).
4. Import diffusers fresh (`del sys.modules[k]` for diffusers.* first) → must succeed.
Print PASS/FAIL per check; exit code 0 = all pass. Real end-to-end confirmation still needs a
ComfyUI restart (nodes load at boot), then re-check object_info + comfyui.log.

## Other pitfalls hit here
- MSYS path vs Windows path: `python -m py_compile /f/Comfy-Desktop/...` fails "No such file";
  pass `F:\Comfy-Desktop\...` style to python.exe. (`/f/...` works for bash commands, not as a
  python argument on this host.)
- "Register sycl bitsandbytes kernels for XPU" appears once per import ATTEMPT of bitsandbytes —
  N occurrences in a startup log = N failed re-imports (each failure purges sys.modules).
- `standalone-env/Lib/inspect.py` in a traceback means the .venv python is using the
  standalone-env standard library (Comfy Desktop layout) — normal, not a bug.
- `_import_backends()` (bitsandbytes entry_points group "bitsandbytes.backends") was empty here —
  check `grep -rn "bitsandbytes.backends" site-packages/*/entry_points.txt` before blaming it.
- Before restarting for the user: confirm `/queue` is empty and ask how they want to restart
  (Comfy Desktop button vs `POST /api/manager/reboot` from ComfyUI-Manager).
