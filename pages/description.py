import base64
import re
from pathlib import Path

import streamlit as st

st.title("Description")

_repo_root = Path(__file__).resolve().parents[1]
_md_text = (_repo_root / "README.md").read_text(encoding="utf-8")


def _embed_image(match: re.Match) -> str:
    alt, path = match.group(1), match.group(2)
    img_file = _repo_root / path
    if img_file.exists():
        ext = img_file.suffix.lstrip(".")
        mime = "image/svg+xml" if ext == "svg" else f"image/{ext}"
        b64 = base64.b64encode(img_file.read_bytes()).decode()
        return f'<img alt="{alt}" src="data:{mime};base64,{b64}" style="max-width:100%">'
    return match.group(0)


_md_text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _embed_image, _md_text)

st.markdown(_md_text, unsafe_allow_html=True)
