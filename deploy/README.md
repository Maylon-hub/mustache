# MustaCHE on Docker

This branch uses CPython 3.11 and the qualified CORE-SG 0.4.5 wheel for Linux x86-64. The build verifies the wheel's SHA-256. It installs the MustaCHE source from this branch and resolves the remaining dependencies from PyPI.

## Hosted Iris preview

Build and run:

```powershell
docker build --platform linux/amd64 -f Dockerfile.vercel -t mustache-vercel-preview .
docker run --rm -p 127.0.0.1:8080:8080 mustache-vercel-preview
```

Visit http://127.0.0.1:8080 and click **Run Iris example**. The page returns five real CORE-SG hierarchies, flat cluster and noise counts, condensed tree edge counts, and the HAI similarity matrix. The endpoint `/healthz` checks the Python version and imports both native CORE-SG extensions.

On Vercel, use the Container preset and `Dockerfile.vercel`, set the Preview environment variable `PORT=8080`, and enable Deployment Protection. Keep the container mode set to `preview`. The Iris example computes everything in one request, so a new instance can handle it without prior state.

## Full local application

Use a named volume to preserve saved projects when the local container is replaced:

```powershell
docker run --rm -p 127.0.0.1:8080:8080 --env MUSTACHE_CONTAINER_MODE=local --mount type=volume,source=mustache-projects,target=/data mustache-vercel-preview
```

This mode runs the existing single-process application and is intended for one user on localhost. For a hosted version with uploads, interactive exploration and project management, the application needs analysis state isolated per session and durable project storage across instances. Vercel container memory and its writable filesystem may disappear when an instance stops. See the [Vercel Container documentation](https://vercel.com/docs/functions/runtimes/container).
