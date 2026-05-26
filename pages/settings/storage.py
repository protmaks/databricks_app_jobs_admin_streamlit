"""Settings storage: Workspace Files → local JSON fallback (for local dev).

On Databricks the files are stored at:
  /Shared/databricks_admin_app/settings.json          (global)
  /Shared/databricks_admin_app/user_prefs/<user>.json (per-user)

These paths persist across app re-deployments.
"""
import base64
import json
import re
from pathlib import Path

import streamlit as st
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ExportFormat, ImportFormat

# Workspace Files paths (persist across deploys, not affected by DBFS settings)
_WS_SETTINGS_PATH = "/Shared/databricks_admin_app/settings.json"
_WS_USER_PREFS_DIR = "/Shared/databricks_admin_app/user_prefs"

# Local fallback — sits in the project root, git-ignored
_LOCAL_PATH = Path(__file__).parent.parent.parent / "settings_local.json"
_LOCAL_USER_PREFS_DIR = Path(__file__).parent.parent.parent / "user_prefs_local"

DEFAULT_SETTINGS: dict = {
    "version": 1,
    "timezone": "UTC",
    "teams": [],
    "default_teams": [],
}


def _migrate(data: dict) -> dict:
    """Backfill new fields added to settings without a version bump."""
    data.setdefault("default_teams", [])
    return data


# ── Workspace Files helpers ───────────────────────────────────────────────────

def _ws_read(w: WorkspaceClient, path: str) -> bytes:
    resp = w.workspace.export(path=path, format=ExportFormat.SOURCE)
    return base64.b64decode(resp.content)


def _ws_write(w: WorkspaceClient, path: str, raw: bytes) -> None:
    parent = path.rsplit("/", 1)[0]
    try:
        w.workspace.mkdirs(path=parent)
    except Exception:
        pass
    encoded = base64.b64encode(raw).decode("ascii")
    w.workspace.import_(path=path, content=encoded, format=ImportFormat.AUTO, overwrite=True)


# ── Local helpers ─────────────────────────────────────────────────────────────

def _load_local() -> dict:
    try:
        data = json.loads(_LOCAL_PATH.read_text(encoding="utf-8"))
        return _migrate(data) if data.get("version") == 1 else DEFAULT_SETTINGS.copy()
    except Exception:
        return DEFAULT_SETTINGS.copy()


def _save_local(settings: dict) -> None:
    _LOCAL_PATH.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Global settings ───────────────────────────────────────────────────────────

def load_settings(w: WorkspaceClient) -> dict:
    """Load settings from Workspace Files, falling back to local file on error."""
    try:
        data = json.loads(_ws_read(w, _WS_SETTINGS_PATH).decode("utf-8"))
        return _migrate(data) if data.get("version") == 1 else DEFAULT_SETTINGS.copy()
    except Exception:
        return _load_local()


def save_settings(w: WorkspaceClient, settings: dict) -> None:
    """Write settings to Workspace Files, falling back to local file.

    Raises RuntimeError if both fail.
    """
    raw = json.dumps(settings, indent=2, ensure_ascii=False).encode("utf-8")
    ws_error = None
    try:
        _ws_write(w, _WS_SETTINGS_PATH, raw)
        return
    except Exception as ws_exc:
        ws_error = ws_exc  # save for error message
        pass  # try local fallback

    try:
        _save_local(settings)
    except Exception as local_exc:
        raise RuntimeError(
            f"Failed to save settings. Workspace: {ws_error}. Local: {local_exc}"
        ) from local_exc


def get_cached_settings(w: WorkspaceClient) -> dict:
    """Return settings from session_state cache, loading from storage on first call.

    Invalidated by the Settings page when the user saves new settings.
    """
    if "global_settings" not in st.session_state:
        st.session_state["global_settings"] = load_settings(w)
    return st.session_state["global_settings"]


# ── Per-user preferences ──────────────────────────────────────────────────────

def _get_username(w: WorkspaceClient) -> str:
    """Return current user's email/username, sanitized for use in file paths."""
    try:
        me = w.current_user.me()
        name = me.user_name or me.display_name or "default"
    except Exception:
        name = "default"
    return re.sub(r"[^a-zA-Z0-9@._-]", "_", name)


def _user_prefs_ws_path(w: WorkspaceClient) -> str:
    return f"{_WS_USER_PREFS_DIR}/{_get_username(w)}.json"


def _user_prefs_local_path(w: WorkspaceClient) -> Path:
    _LOCAL_USER_PREFS_DIR.mkdir(parents=True, exist_ok=True)
    return _LOCAL_USER_PREFS_DIR / f"{_get_username(w)}.json"


def load_user_prefs(w: WorkspaceClient) -> dict:
    """Load per-user preferences from Workspace Files, falling back to local file."""
    try:
        data = json.loads(_ws_read(w, _user_prefs_ws_path(w)).decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    try:
        path = _user_prefs_local_path(w)
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_user_prefs(w: WorkspaceClient, prefs: dict) -> None:
    """Save per-user preferences to Workspace Files, falling back to local file."""
    raw = json.dumps(prefs, indent=2, ensure_ascii=False).encode("utf-8")
    ws_error = None
    try:
        _ws_write(w, _user_prefs_ws_path(w), raw)
        return
    except Exception as ws_exc:
        ws_error = ws_exc  # save for error message
        pass
    try:
        _user_prefs_local_path(w).write_text(
            json.dumps(prefs, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as local_exc:
        raise RuntimeError(
            f"Failed to save user prefs. Workspace: {ws_error}. Local: {local_exc}"
        ) from local_exc


def get_cached_user_prefs(w: WorkspaceClient) -> dict:
    """Return user prefs from session_state cache, loading from storage on first call."""
    if "user_prefs" not in st.session_state:
        st.session_state["user_prefs"] = load_user_prefs(w)
    return st.session_state["user_prefs"]
