# Dellni Deployment Guide

This build is prepared for cloud deployment as a Web Application URL.

## Recommended option for hackathon submission

Use Render or Railway and deploy from a GitHub repository. For a judge-facing demo, use a paid/always-on service if possible. Free web services may sleep after inactivity, which can make the first request slow.

## Files added for deployment

- `Procfile`: production start command for Gunicorn.
- `runtime.txt`: Python version hint.
- `render.yaml`: Render blueprint configuration.
- `railway.json`: Railway deployment configuration.
- `requirements.txt`: includes Flask, tzdata, OpenAI SDK, and Gunicorn.

## Render steps

1. Create a GitHub repository named `dellni`.
2. Upload all files from this folder to the repository.
3. Go to Render and create a new Web Service from that repository.
4. Use these settings:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`
5. Add environment variables:
   - `OPENAI_MODEL=gpt-4o-mini`
   - `OPENAI_API_KEY=your_real_key` only if you want the advanced AI layer.
6. Deploy and copy the public URL.

## Railway steps

1. Create a GitHub repository named `dellni`.
2. Upload all files from this folder to the repository.
3. Go to Railway and create a new project from GitHub.
4. Railway should detect Python/Nixpacks automatically.
5. Add environment variables:
   - `OPENAI_MODEL=gpt-4o-mini`
   - `OPENAI_API_KEY=your_real_key` only if needed.
6. Deploy and copy the public URL.

## Local production test before deployment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PORT=8000 gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
$env:PORT="8000"
gunicorn app:app --bind 0.0.0.0:$env:PORT --workers 2 --threads 4 --timeout 120
```

Note: Gunicorn is mainly for Linux cloud hosting. On Windows local testing, `python app.py` is still fine.

## Submission file

After deployment, create a text file named `Dellni_Website_Link.txt` with the public URL and include it with the final submission package.
