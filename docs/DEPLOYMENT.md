# Local serving and later deployment

This project is a Flask website with a real Python inference backend, not a static export. Keep the browser and API on the same origin. The deployment entry point reuses `app.create_app()` and the trained artifacts; it does not change model selection or invent fallback predictions.

## Localhost

From PowerShell in the project directory:

```powershell
uv sync --frozen --python 3.12
# Only needed when artifacts are absent, corrupt or model source changed:
uv run python scripts/train.py
uv run python serve.py
```

Open `http://127.0.0.1:5050`. `serve.py` stops before binding if the model did not load. The existing `start.ps1` and `app.py --port` workflow remains available.

For an alternate port:

```powershell
$env:PORT = '5057'
uv run python serve.py
```

`HOST` defaults to `127.0.0.1`; `PORT` defaults to `5050`. HOST accepts an IP address or `localhost`, without a URL scheme or port. PORT must be an integer from 1 through 65535. A managed container host should set HOST to `0.0.0.0` and provide PORT. `0.0.0.0` is a bind address, not the URL to type in a browser.

The server uses Waitress, which supports Windows and Linux. It uses the application's bounded request size and raises Waitress's buffering threshold to that same limit, keeping permitted upload bodies in memory before Flask receives them. Waitress's own error response can reject an oversized body before the Flask route runs. Flask recommends a production WSGI server rather than its development server. [Flask deployment guide](https://flask.palletsprojects.com/en/stable/deploying/), [Waitress integration](https://flask.palletsprojects.com/en/stable/deploying/waitress/).

## Container build

Docker Desktop must be running with its Linux engine, or use a Linux Docker host. The image uses Python 3.12 and uv 0.13.7; application dependencies come from `uv.lock`, without development tools. The build regenerates the data/model artifacts inside Linux. Windows `.venv`, model artifacts and download provenance are excluded from the context, so a Windows pickle is not silently reused in a Linux environment. The dataset downloader still requires the canonical pinned SHA-256.

```powershell
docker build --progress=plain -t retain-churn:local .
docker run --rm --name retain-churn -p 127.0.0.1:8080:8080 retain-churn:local
```

Open `http://127.0.0.1:8080`. From another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8080/api/health
docker inspect --format '{{.State.Health.Status}}' retain-churn
docker stop retain-churn
```

The runtime is a non-root user. It starts the model that was generated during the build and has a readiness health check. Builds require access to package registries, Debian repositories and the IBM dataset host/GitHub API. No network fetch or retraining is required when the finished image starts. A failed data download, hash check, training run or artifact load must fail the build/start instead of creating a dummy model.

The image uses a dependency lock and a fixed uv version. The Python base-image tag can still receive updates; this is not a claim of byte-identical image builds. Before a controlled release, record the built image digest and run metadata. uv's official guidance supports locked non-editable installs and exclusion of host environments; Docker recommends non-root runtime users. [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/), [Docker build practices](https://docs.docker.com/build/building/best-practices/), [health-check reference](https://docs.docker.com/reference/dockerfile/#healthcheck).

## Publishing later

Deploy the image to a host that runs Linux containers and supports an HTTP service. Configure the host's supplied PORT, route traffic to that port, and use `/api/health` as the readiness path. Retain the image's own model, manifest, summary and plots together. Export `artifacts/summary.json` and `data/provenance.json` from a release image if recording that release's exact Linux-generated model evidence. Do not overwrite host-run results with container-run metrics or vice versa.

For a public service, terminate HTTPS at the hosting platform/reverse proxy. Restrict direct access to the application port so the proxy cannot be bypassed. This app currently uses relative same-origin paths and does not automatically trust forwarded headers. If a deployment later needs external absolute URLs or client-IP-based controls, configure only the actual trusted proxy hops; blindly trusting forwarded headers is unsafe. [Flask proxy configuration](https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/).

The current product is an anonymous benchmark demonstrator. Publishing private customer data requires access control and a privacy/storage policy first. Public anonymous scoring also needs measured resource limits/rate limiting at the platform or proxy. The app already validates files and bounds their size/row count, but that is not a multi-user load test. Do not enable debug mode or add private customer files to the image.

## Executed verification

Deployment configuration/startup tests, real localhost serving and a Linux container build/run were executed during this revision. Overall application/browser results remain in [VERIFICATION.md](VERIFICATION.md).

Executed during this revision:

- `uv run pytest tests/test_deployment.py -q`: 10 passed; targeted Ruff check passed.
- `uv run python serve.py` with loopback HOST and PORT `5058`: `/api/health` reported ready.
- Docker Desktop's Linux engine was initially stopped. After launching the installed Docker Desktop, engine `29.8.0` became available. No Docker installation or settings changes were needed.
- `docker build --progress=plain -t retain-churn:local .` completed, including a fresh Linux data download and training. The tested image ID was `sha256:625f87899d72d5c280ca09ba3abca25587210b46ccea34332214899c0c049a49`; its measured image size was 1,262,697,617 bytes. This is a build snapshot; rebuilding after source changes creates a different image.
- The container ran as UID `10001` and reached `healthy`. Its Python was `3.12.16`. Its generated source SHA-256 matched the canonical CSV. The Linux-generated selected model's ROC-AUC was `0.8324730682786947` and average precision `0.6242117062478064`; these were read from that image's own summary, not copied into host artifacts.
- A genuine held-out customer scored through container HTTP matched its saved probability `0.8281108068942341`; explanation additivity error was `4.4408920985006262e-16`.
- A separate container with an empty temporary artifacts mount exited `1` before serving, verifying that unavailable models fail startup.

No hosted deployment, TLS endpoint, private-user authentication or public concurrency/load test was performed. The complete website/browser checks are separate from these server/container checks. The final website source should be rebuilt into an image after its last UI change before publication.

### Historical V2 website image check

After the screen rebuild and final chart fixes, `docker build --progress=plain -t retain-churn:website .` succeeded again. The tested image was `sha256:c3f7468ffe6a2b44b3522960a36f8c58cb93e86cfc0522def96e51b57c1892f3`, with a measured size of 1,263,005,040 bytes. It was run as the temporary `retain-churn-website-check` container, bound only to `127.0.0.1:8080`.

The container reached `healthy` and `id -u` returned `10001`. The complete `scripts/browser_check.py --url http://127.0.0.1:8080` run passed all 11 workflow groups with zero unexpected console errors. This exercised the actual home/guide, direct routes, model/SHAP inference, cohort filters and failure recovery, CSV downloads, responsive pages and keyboard checks against Linux-built model artifacts. Host model files were not overwritten with container artifacts.

The final browser record is `artifacts/browser/results.json`; the native localhost record was retained under `artifacts/browser-native/`. Test containers are stopped/removed after verification. The locally built image remains available for a later `docker run`; use the deployment steps above to build a new image when source changes.


### Current V3 UI rebuild attempt

The hero/home and shared UI were redesigned after the V2 image above. Native localhost passed 54 Python tests and 13 actual browser workflow groups. The current rebuild was not completed: after restarting a build to include final UI source, public registry token retrieval failed with a TLS handshake timeout. A retry found the Docker Desktop Linux engine unavailable (`dockerDesktopLinuxEngine` pipe missing). The old image does not contain this redesign. Run the documented build and container checks when Docker and registry access are available; no current V3 container or public deployment is claimed. See [VERIFICATION.md](VERIFICATION.md).
