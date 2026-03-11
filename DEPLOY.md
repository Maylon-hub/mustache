# Deployment Guide for MustaCHE

This guide outlines how to deploy the MustaCHE application using the provided Docker configuration.

## Recommended Hosting Platforms

For scientific applications like MustaCHE that require significant memory (RAM) for clustering large datasets (HDBSCAN, HAI Matrix), we recommend the following free/low-cost platforms:

### 1. **Hugging Face Spaces (Strongly Recommended)**
*   **Why:** Provides **16GB RAM** and **2 vCPU** on the free tier (CPU Basic). This is ideal for memory-intensive Python apps using `pandas` and `scikit-learn`.
*   **Type:** Docker Space.
*   **Setup:**
    1.  Create a new Space on [huggingface.co](https://huggingface.co/new-space).
    2.  Select **Docker** as the SDK.
    3.  Upload the project files (ensure `Dockerfile` is at the root).
    4.  The space will build and run automatically.

### 2. **Render**
*   **Why:** Good Docker support and easy setup.
*   **Limitation:** Free tier includes only **512MB RAM**, which may cause crashes (`OOM Killed`) if you process large datasets.
*   **Setup:**
    1.  Connect your GitHub repository to Render.
    2.  Select "Web Service".
    3.  Render will auto-detect the Dockerfile.

### 3. **Fly.io**
*   **Why:** Good for lightweight global deployment.
*   **Limitation:** Free allowance is small (256MB RAM VMs), likely insufficient for this app without upgrading to paid instances.

## Docker Configuration

The included `Dockerfile` is optimized for:
1.  **Multi-Stage Build**: Keeps the final image size small by removing build tools (`gcc`) after compilation.
2.  **Scientific Stack**: Pre-installs `numpy`, `pandas`, and `scikit-learn`.
3.  **Legacy Support**: Includes a step to compile legacy Cython modules (`legacy/mustache/resources/*.pyx`) if they exist.
4.  **Stability**: Increases Gunicorn timeout to 120s to prevent timeouts during long clustering tasks.

### Local Testing

To build and run the Docker container locally:

```bash
# Build
docker build -t mustache-v2 .

# Run
docker run -p 5001:5000 mustache-v2
```

Access the app at `http://localhost:5001`.
