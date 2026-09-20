# Demo Automation

Demo tooling lives here so it stays separate from application code and automated tests.

## Deterministic Mock Demo

The `mock` directory contains a FastAPI mock server and a Playwright browser script. From the repository root:

```bash
pip install -r tools/demo/mock/requirements.txt
playwright install
python tools/demo/mock/mock_server.py
```

Start the frontend in another terminal with `NEXT_PUBLIC_API_URL=http://localhost:8001`, then run:

```bash
python tools/demo/mock/run_demo.py
```

## Browser Demo

The `browser` directory contains a Puppeteer script for an already-running local app:

```bash
cd tools/demo/browser
npm ci
npm run demo
```

Both scripts refresh the screenshots in `frontend/public/assets`.
