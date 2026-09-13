import os
from pathlib import Path
from typing import Optional

DEFAULT_PEST_MODEL = "pest_classifier_moderate.h5"
DEFAULT_SEVERITY_MODEL = "severity_classifier_severe_boost.h5"


def resolve_model_path(
    env_var_name: str,
    default_filename: str = DEFAULT_PEST_MODEL,
    model_dir: Optional[str] = None,
    env_value: Optional[str] = None,
) -> str:
    """Resolve a model path from environment config, falling back to the local model folder."""
    candidates = []
    resolved_model_dir = Path(model_dir) if model_dir else (Path(__file__).resolve().parent.parent / "model")

    # If an explicit model_dir is specified (e.g. in tests or custom override), check it first
    if model_dir:
        candidates.extend([
            str((resolved_model_dir / default_filename).resolve()),
            str((resolved_model_dir / DEFAULT_PEST_MODEL).resolve()),
            str((resolved_model_dir / DEFAULT_SEVERITY_MODEL).resolve()),
        ])

    configured_value = env_value if env_value is not None else os.getenv(env_var_name, "")
    if configured_value:
        cleaned_value = os.path.expandvars(os.path.expanduser(configured_value.strip()))
        if os.path.isabs(cleaned_value):
            candidates.append(cleaned_value)
        else:
            project_root = Path(__file__).resolve().parent.parent
            candidates.extend([
                str((resolved_model_dir / cleaned_value).resolve()),
                str((project_root / cleaned_value).resolve()),
                str((project_root / "model" / cleaned_value).resolve()),
            ])

    if not model_dir:
        candidates.extend([
            str((resolved_model_dir / default_filename).resolve()),
            str((resolved_model_dir / DEFAULT_PEST_MODEL).resolve()),
            str((resolved_model_dir / DEFAULT_SEVERITY_MODEL).resolve()),
        ])

    for candidate in candidates:
        if os.path.exists(candidate) and not candidate.endswith(".tflite"):
            return candidate

    return str((resolved_model_dir / default_filename).resolve())
