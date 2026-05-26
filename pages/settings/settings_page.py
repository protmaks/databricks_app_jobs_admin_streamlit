import uuid
import streamlit as st
from pages.utils import COMMON_TZ, make_workspace_client
from pages.settings.storage import get_cached_settings, save_settings, get_cached_user_prefs, save_user_prefs

st.header("Settings")

w = make_workspace_client()

_loaded = get_cached_settings(w)
_user_prefs = get_cached_user_prefs(w)
if "settings_tz" not in st.session_state:
    st.session_state["settings_tz"] = _loaded["timezone"]
if "settings_teams" not in st.session_state:
    st.session_state["settings_teams"] = [{**t} for t in _loaded["teams"]]
if "settings_default_teams" not in st.session_state:
    st.session_state["settings_default_teams"] = list(_user_prefs.get("default_teams", []))

# ── Section 1: Timezone ──────────────────────────────────────────────────────
tz_index = (
    COMMON_TZ.index(st.session_state["settings_tz"])
    if st.session_state["settings_tz"] in COMMON_TZ
    else 0
)
_tz_label, _tz_col, _tz_desc = st.columns([0.05, 0.1, 0.85])
_tz_label.markdown(
    "<div style='padding-top:8px'>Timezone:</div>",
    unsafe_allow_html=True,
)
_tz_col.selectbox(
    "Timezone",
    options=COMMON_TZ,
    index=tz_index,
    key="settings_tz",
    label_visibility="collapsed",
)
_tz_desc.caption("Applied as the default timezone on all pages. Can be overridden per page.")

# ── Section 2: Teams ─────────────────────────────────────────────────────────
st.subheader("Teams")

FIELD_OPTIONS = ["job_name", "creator", "tags"]
FIELD_LABELS = {"job_name": "Job Name", "creator": "Creator", "tags": "Tags"}
OP_OPTIONS = ["starts_with", "ends_with", "contains", "equals"]
OP_OPTIONS_TAGS = ["has_key", "equals", "contains", "starts_with", "ends_with"]
OP_LABELS = {
    "starts_with": "starts with",
    "ends_with": "ends with",
    "contains": "contains",
    "equals": "equals",
    "has_key": "has key",
}
LOGIC_OPTIONS = ["AND", "OR"]

_col_btn, _col_hint = st.columns([0.08, 0.92])
_col_hint.caption(
    "Define teams by combining job-name and creator conditions. "
    "The Teams filter on every page will show these team names."
)
if _col_btn.button("＋ Add Team", key="add_team_btn"):
    st.session_state["settings_teams"].append(
        {
            "id": str(uuid.uuid4()),
            "name": "",
            "conditions": [],
        }
    )
    st.rerun()

teams: list[dict] = st.session_state["settings_teams"]

for team_idx, team in enumerate(teams):
    team_id = team["id"]

    confirm_key = f"confirm_del_{team_id}"
    expanded_key = f"expanded_{team_id}"
    is_expanded = st.session_state.get(expanded_key, False) or st.session_state.get(confirm_key, False)

    _default_marker = "★ " if team_id in st.session_state["settings_default_teams"] else ""
    with st.expander(_default_marker + (team["name"] or f"Team {team_idx + 1}"), expanded=is_expanded):
        col_default, col_name, col_del = st.columns([0.08, 0.83, 0.09])

        def _on_default_change(tid=team_id):
            if st.session_state[f"team_default_{tid}"]:
                if tid not in st.session_state["settings_default_teams"]:
                    st.session_state["settings_default_teams"].append(tid)
            else:
                st.session_state["settings_default_teams"] = [
                    x for x in st.session_state["settings_default_teams"] if x != tid
                ]

        col_default.checkbox(
            "Default",
            value=team_id in st.session_state["settings_default_teams"],
            key=f"team_default_{team_id}",
            on_change=_on_default_change,
            help="Pre-select this team on all filter pages",
        )

        def _on_name_change(tidx=team_idx, tid=team_id):
            teams[tidx]["name"] = st.session_state[f"team_name_{tid}"]

        col_name.text_input(
            "Team name",
            value=team["name"],
            key=f"team_name_{team_id}",
            on_change=_on_name_change,
            placeholder="e.g. Alpha Team",
        )

        if st.session_state.get(confirm_key):
            c1, c2 = col_del.columns(2)
            if c1.button("✓", key=f"confirm_yes_{team_id}", type="primary", help="Yes, delete"):
                teams.pop(team_idx)
                st.session_state.pop(confirm_key, None)
                st.session_state.pop(expanded_key, None)
                st.rerun()
            if c2.button("✕", key=f"confirm_no_{team_id}", help="Cancel"):
                st.session_state.pop(confirm_key, None)
                st.rerun()
        else:
            col_del.markdown("<div style='padding-top:28px'></div>", unsafe_allow_html=True)
            if col_del.button("Delete", key=f"del_team_{team_id}"):
                st.session_state[confirm_key] = True
                st.rerun()

        # ── Conditions ───────────────────────────────────────────────────────
        conditions: list[dict] = team["conditions"]

        if conditions:
            st.markdown("**Conditions**")

        for cond_idx, cond in enumerate(conditions):
            cond_key = f"{team_id}_{cond_idx}"
            _is_tags = cond.get("field") == "tags"

            if _is_tags:
                ccol_logic, ccol_field, ccol_tag_key, ccol_op, ccol_val, ccol_del = st.columns(
                    [0.07, 0.13, 0.23, 0.1, 0.4, 0.07]
                )
            else:
                ccol_logic, ccol_field, ccol_op, ccol_val, ccol_del = st.columns(
                    [0.07, 0.15, 0.1, 0.61, 0.07]
                )

            if cond_idx == 0:
                ccol_logic.markdown(
                    "<div style='padding-top:28px;font-weight:600;color:rgba(250,250,250,0.5)'>IF</div>",
                    unsafe_allow_html=True,
                )
            else:
                def _on_logic_change(tidx=team_idx, cidx=cond_idx, ck=cond_key):
                    teams[tidx]["conditions"][cidx]["logic"] = st.session_state[
                        f"cond_logic_{ck}"
                    ]

                _cur_logic = cond.get("logic", "AND")
                ccol_logic.selectbox(
                    "Logic",
                    options=LOGIC_OPTIONS,
                    index=LOGIC_OPTIONS.index(_cur_logic) if _cur_logic in LOGIC_OPTIONS else 0,
                    key=f"cond_logic_{cond_key}",
                    label_visibility="collapsed",
                    on_change=_on_logic_change,
                )

            def _on_field_change(tidx=team_idx, cidx=cond_idx, ck=cond_key):
                f = st.session_state[f"cond_field_{ck}"]
                teams[tidx]["conditions"][cidx]["field"] = f
                if f == "tags" and teams[tidx]["conditions"][cidx].get("operator") not in OP_OPTIONS_TAGS:
                    teams[tidx]["conditions"][cidx]["operator"] = "has_key"
                elif f != "tags" and teams[tidx]["conditions"][cidx].get("operator") not in OP_OPTIONS:
                    teams[tidx]["conditions"][cidx]["operator"] = "starts_with"

            def _on_op_change(tidx=team_idx, cidx=cond_idx, ck=cond_key):
                teams[tidx]["conditions"][cidx]["operator"] = st.session_state[f"cond_op_{ck}"]

            def _on_val_change(tidx=team_idx, cidx=cond_idx, ck=cond_key):
                teams[tidx]["conditions"][cidx]["value"] = st.session_state[f"cond_val_{ck}"].strip()

            def _on_tag_key_change(tidx=team_idx, cidx=cond_idx, ck=cond_key):
                teams[tidx]["conditions"][cidx]["tag_key"] = st.session_state[f"cond_tag_key_{ck}"].strip()

            ccol_field.selectbox(
                "Field",
                options=FIELD_OPTIONS,
                format_func=lambda x: FIELD_LABELS[x],
                index=FIELD_OPTIONS.index(cond.get("field", "job_name")),
                key=f"cond_field_{cond_key}",
                label_visibility="collapsed",
                on_change=_on_field_change,
            )

            if _is_tags:
                ccol_tag_key.text_input(
                    "Tag Key",
                    value=cond.get("tag_key", ""),
                    key=f"cond_tag_key_{cond_key}",
                    label_visibility="collapsed",
                    placeholder="tag key",
                    on_change=_on_tag_key_change,
                )
                _cur_op = cond.get("operator", "has_key")
                _op_opts = OP_OPTIONS_TAGS
            else:
                _cur_op = cond.get("operator", "starts_with")
                _op_opts = OP_OPTIONS

            ccol_op.selectbox(
                "Operator",
                options=_op_opts,
                format_func=lambda x: OP_LABELS[x],
                index=_op_opts.index(_cur_op) if _cur_op in _op_opts else 0,
                key=f"cond_op_{cond_key}",
                label_visibility="collapsed",
                on_change=_on_op_change,
            )

            _show_val = not (_is_tags and cond.get("operator", "has_key") == "has_key")
            if _show_val:
                ccol_val.text_input(
                    "Value",
                    value=cond.get("value", ""),
                    key=f"cond_val_{cond_key}",
                    label_visibility="collapsed",
                    placeholder="tag value" if _is_tags else "e.g. alpha_",
                    on_change=_on_val_change,
                )

            if ccol_del.button("✕", key=f"del_cond_{cond_key}"):
                conditions.pop(cond_idx)
                st.session_state[expanded_key] = True
                st.rerun()

        if st.button("＋ Add Condition", key=f"add_cond_{team_id}"):
            new_cond = {"field": "job_name", "operator": "starts_with", "value": ""}
            if conditions:
                new_cond["logic"] = "AND"
            conditions.append(new_cond)
            st.session_state[expanded_key] = True
            st.rerun()

# ── Save ─────────────────────────────────────────────────────────────────────
st.divider()

col_save, col_msg = st.columns([0.2, 0.8])

if col_save.button("Save Settings", type="primary", key="save_settings_btn"):
    settings_to_save = {
        "version": 1,
        "timezone": st.session_state["settings_tz"],
        "teams": st.session_state["settings_teams"],
    }

    errors: list[str] = []
    for t in settings_to_save["teams"]:
        if not t.get("name", "").strip():
            errors.append(f"A team has no name (id: {t['id'][:8]}…).")
        if not t.get("conditions"):
            name = t.get("name") or f"(id: {t['id'][:8]}…)"
            errors.append(f"Team '{name}' has no conditions.")
        for c in t.get("conditions", []):
            if not c.get("value", "").strip():
                name = t.get("name") or f"(id: {t['id'][:8]}…)"
                errors.append(f"Team '{name}': a condition has an empty value.")

    if errors:
        col_msg.error("Fix before saving:\n" + "\n".join(f"- {e}" for e in errors))
    else:
        valid_team_ids = {t["id"] for t in settings_to_save["teams"]}
        user_default_teams = [
            tid for tid in st.session_state["settings_default_teams"] if tid in valid_team_ids
        ]
        try:
            save_settings(w, settings_to_save)
            save_user_prefs(w, {"default_teams": user_default_teams})
            st.session_state.pop("global_settings", None)
            st.session_state.pop("user_prefs", None)
            col_msg.success("Settings saved.")
        except RuntimeError as exc:
            col_msg.error(str(exc))
