# Deploy to a Databricks App Space

## 1. Prerequisites

In Databricks, enable the **Governed agentic app-building** preview and create a space under **Databricks Apps → App Spaces → New space**. Workspace administrator permissions are required.

Install the Databricks CLI, configure a profile, and check the connection:

```bash
databricks auth profiles
databricks current-user me -p <PROFILE>
```

If authentication fails, run `databricks auth login --profile <PROFILE>`.

For example, using the `dbc-e4ddf0e5-117a` profile:

```bash
databricks current-user me -p dbc-e4ddf0e5-117a
```

## 2. Create the app

In a terminal, go to the project root and set the parameters, replacing `<PROFILE>` and `<USER>`:

```bash
PROFILE="<PROFILE>"
SPACE="space1"
APP="jobs-admin-space1"
SOURCE="/Workspace/Users/<USER>/databricks_apps/${APP}-source"
```

Example for `user@example.com`:

```bash
PROFILE="dbc-e4ddf0e5-117a"
SPACE="space1"
APP="jobs-admin-space1"
SOURCE="/Workspace/Users/user@example.com/databricks_apps/jobs-admin-space1-source"
```

Create the app. Skip this step if it already exists:

```bash
databricks apps create "$APP" --space "$SPACE" -p "$PROFILE"
```

## 3. Upload and deploy

Create a temporary directory with the required files and upload it to the workspace:

```bash
STAGING_DIR="$(mktemp -d)"
cp app.py app.yaml requirements.txt README.md "$STAGING_DIR/"
cp -R pages assets "$STAGING_DIR/"
find "$STAGING_DIR" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$STAGING_DIR" -type f -name .DS_Store -delete

databricks sync --full "$STAGING_DIR" "$SOURCE" -p "$PROFILE"
```

Do not copy `.env`, secrets, or local user data into this directory. `README.md` is required by the Description page.

Deploy the uploaded version:

```bash
databricks apps deploy "$APP" \
  --mode SNAPSHOT \
  --source-code-path "$SOURCE" \
  -p "$PROFILE"
```

To update the app, repeat this section. Local changes are not published automatically.

## 4. Verify

```bash
databricks apps get "$APP" -p "$PROFILE" -o json
databricks apps logs "$APP" --tail-lines 100 -p "$PROFILE"
```

Find `url` in the `get` output and open it in a browser. A successful deployment has status `SUCCEEDED`; a running app has status `RUNNING`.

Example of the key fields:

```json
{
  "name": "jobs-admin-space1",
  "space": "space1",
  "app_status": {"state": "RUNNING"},
  "active_deployment": {"status": {"state": "SUCCEEDED"}},
  "url": "https://jobs-admin-space1-<workspace-id>.aws.databricksapps.com"
}
```

The actual `url` contains your workspace address.

## 5. Access to Jobs

In the App Space settings, add the required Jobs as resources and grant the necessary permissions. Without them, the app may not see the jobs: it calls the API as its own service principal. Space resources are available to apps in that space.

In the tested workspace, the API rejected the `jobs` scope for user authorization. It also rejected adding the Databricks-managed space group to `admins`. For a large number of Jobs, resource and permission management can be automated; this project does not currently include that automation.

If jobs do not appear, check the permissions and selected period: the page displays only jobs with runs in that period. The current temporary diagnostic code in `app.py` prints the identity, Jobs, and Clusters to the server log.

Documentation: [App Spaces](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-spaces).
