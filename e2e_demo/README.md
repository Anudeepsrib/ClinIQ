# True Full-Stack E2E Demo

This folder contains a complete mock API server and a Playwright test script to demonstrate all features of the ClinIQ application in a deterministic, zero-cost way.

## Instructions

1. **Install dependencies**:
   ```bash
   pip install -r e2e_demo/requirements.txt
   playwright install
   ```

2. **Start the Mock Server**:
   ```bash
   python e2e_demo/mock_server.py
   ```

3. **Start the Frontend**:
   ```bash
   cd frontend
   npm install
   NEXT_PUBLIC_API_URL=http://localhost:8001 npm run dev
   ```

4. **Run the E2E Demo**:
   Open a new terminal and run:
   ```bash
   # Make sure the frontend and mock server are both running first!
   python e2e_demo/mock_demo.py
   ```

The script signs in with the mock account, launches a headless browser, exercises clarification, masking, and standard retrieval, and saves screenshots in the `e2e_demo/` folder.
