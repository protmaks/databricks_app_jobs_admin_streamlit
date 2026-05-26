import os
from databricks.sdk import WorkspaceClient

COMMON_TZ = [
    "UTC",
    "US/Eastern",
    "US/Central",
    "US/Pacific",
    "Europe/London",
    "Europe/Berlin",
    "Europe/Moscow",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Australia/Sydney",
]

def make_workspace_client(user_token: str | None = None) -> WorkspaceClient:
    host = os.getenv("DATABRICKS_HOST")
    if user_token and host:
        _saved_id = os.environ.pop("DATABRICKS_CLIENT_ID", None)
        _saved_secret = os.environ.pop("DATABRICKS_CLIENT_SECRET", None)
        try:
            client = WorkspaceClient(host=host, token=user_token)
        finally:
            if _saved_id is not None:
                os.environ["DATABRICKS_CLIENT_ID"] = _saved_id
            if _saved_secret is not None:
                os.environ["DATABRICKS_CLIENT_SECRET"] = _saved_secret
        return client
    if host and os.getenv("DATABRICKS_CLIENT_ID"):
        _saved = os.environ.pop("DATABRICKS_TOKEN", None)
        try:
            client = WorkspaceClient()
        finally:
            if _saved is not None:
                os.environ["DATABRICKS_TOKEN"] = _saved
        return client
    if os.getenv("DATABRICKS_TOKEN"):
        return WorkspaceClient()
    return WorkspaceClient(profile="DEFAULT")


def match_team_rules(job_name: str, creator: str, teams_config: list, tags: dict | None = None) -> list[str]:
    job_tags = tags or {}
    matched = []
    for team in teams_config:
        conditions = team.get("conditions", [])
        fallback_logic = team.get("logic", "OR").upper()
        if not conditions:
            continue

        def _eval(cond):
            field = cond.get("field")
            op = cond.get("operator", "")
            if field == "tags":
                tag_key = cond.get("tag_key", "")
                if op == "has_key":
                    return tag_key.lower() in {k.lower() for k in job_tags}
                tag_val = next((v for k, v in job_tags.items() if k.lower() == tag_key.lower()), None)
                if tag_val is None:
                    return False
                s, v = tag_val.lower(), cond.get("value", "").lower()
            else:
                subject = job_name if field == "job_name" else creator
                s, v = subject.lower(), cond.get("value", "").lower()
            if op == "starts_with":
                return s.startswith(v)
            elif op == "ends_with":
                return s.endswith(v)
            elif op == "contains":
                return v in s
            elif op == "equals":
                return s == v
            return False

        result = _eval(conditions[0])
        for cond in conditions[1:]:
            logic = cond.get("logic", fallback_logic).upper()
            hit = _eval(cond)
            result = (result and hit) if logic == "AND" else (result or hit)

        if result:
            matched.append(team["name"])
    return matched
