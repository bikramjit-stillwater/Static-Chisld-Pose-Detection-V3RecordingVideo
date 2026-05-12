# Child's Pose Analysis

A web app that analyzes Child's Pose (Utthita Balasana) using MediaPipe BlazePose
and a rule-based scoring engine. Three input methods:

1. **Upload Video** - upload a pre-recorded video file
2. **Upload Photo** - upload a photo
3. **Record Video** - record live in the browser (uses MediaRecorder API,
   no third-party API key needed)

Built with **Flask** (no Streamlit dependency).

## Project structure

```
childpose-app/
├── app.py                      # Flask web app
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render deployment config
├── .python-version             # Python 3.10.14
├── .gitignore
├── README.md
├── src/                        # Core pose-analysis logic
│   ├── __init__.py
│   ├── pose_detector.py        # MediaPipe wrapper (pose-agnostic)
│   ├── pose_analyzer.py        # Frame loop + features + visibility rules
│   ├── scorer.py               # 6-step Child's Pose rule engine
│   └── feedback.py             # Gemini / rule-based coaching feedback
├── templates/                  # Jinja2 HTML
│   ├── base.html
│   ├── index.html              # Upload + record page
│   └── result.html             # 6-step results dashboard
└── static/
    ├── css/styles.css          # Dark theme
    └── js/
        ├── recorder.js         # MediaRecorder API integration
        └── main.js             # Tab switching, form submission
```

## Scoring rules (6 steps)

| # | Step | Weight | What it measures |
|---|------|--------|------------------|
| 1 | Hips on Heels | 20% | Hips sit close to heels |
| 2 | Torso Folded Forward | 25% | Torso bent down over thighs |
| 3 | Arms Extended Forward | 20% | Elbows straight, arms reaching out |
| 4 | Spine Lengthened | 15% | Straight line: hips -> shoulders -> wrists |
| 5 | Forehead Down | 10% | Nose at mat level (near wrist height) |
| 6 | Shoulders Relaxed | 10% | Shoulders below ears |

### Key rules

- **One-side visibility**: A step is visible if ONE full side of the body is
  visible (Child's Pose is recorded from the side, so only one side faces the
  camera). If neither side is visible, the step scores 0 with a "not visible"
  message.
- **Floor-pose check**: If the user is standing (torso vertical), the analysis
  is rejected with a "not Child's Pose" message.
- **Compound penalties**: Multiple very-bad steps reduce the final score.

## Running locally

```bash
# 1. Create a virtual environment
python3.10 -m venv .venv
source .venv/bin/activate  # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Set Gemini API key for better coaching feedback
export GEMINI_API_KEY=your_key_here

# 4. Run
python app.py

# 5. Open in browser
# http://localhost:5000
```

## Deploying to Render

This repo is configured for Render's auto-deploy via `render.yaml`.

1. Push this directory as a GitHub repo.
2. In Render dashboard: **New +** -> **Blueprint** -> connect your repo.
3. (Optional) In the service's **Environment** tab, set `GEMINI_API_KEY` for
   AI-generated coaching feedback (rule-based feedback is used otherwise).
4. Wait for the build (~3-5 minutes first time).

The start command (`gunicorn app:app --timeout 180`) is configured in
`render.yaml`.

## Browser requirements

- **Upload Video / Photo**: any modern browser
- **Record Video** (browser-side): requires
  - HTTPS (Render provides this automatically)
  - Camera permission granted by user
  - Chrome / Firefox / Safari / Edge - all support MediaRecorder API
  - On iOS Safari, requires iOS 14.3+

## What changed from the Streamlit version

Same core scoring/analysis logic - only the web framework changed:

- `app.py` is now a Flask app instead of Streamlit
- New `templates/` directory with Jinja2 HTML
- New `static/` directory with custom CSS and JS
- `static/js/recorder.js` adds in-browser video recording (no Twilio / no API keys)

The pose-analysis logic in `src/` is identical.
