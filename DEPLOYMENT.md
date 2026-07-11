# Railway deployment guide

## Runtime
- Python 3.11
- FFmpeg is installed in the build image

## Required environment variables
- `ENVIRONMENT=production`
- `DEBUG=false`
- `LOG_LEVEL=info`
- `ALLOWED_HOSTS=<your-railway-domain>,www.<your-domain>`
- `UPLOAD_DIR=/app/uploads`
- `OUTPUT_DIR=/app/outputs`
- `APP_NAME=Convertin`
- `APP_VERSION=3.0.0`

## Start command
- Railway can start the service with:
  - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Volume recommendation
- Use a persistent volume mounted at `/app/uploads` and `/app/outputs` for uploaded files and generated outputs.
- This prevents data loss after deploys or app restarts.

## Production notes
- Keep `DEBUG=false` in production.
- Set `ALLOWED_HOSTS` to the actual Railway domain and any custom domain.
- Ensure the app has write access to the storage directories.
- Health checks should target `/health`.
