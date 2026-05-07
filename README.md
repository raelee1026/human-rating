# Perceptual Quality Study — MipNeRF360

Pairwise comparison experiment to evaluate the effect of **perceptual wrappers**
on Neural View Synthesis (NVS) quality, following the methodology of
[Liang et al. 2023](https://arxiv.org/abs/2303.15206).

---

## Project Structure

```
├── experiment.html               # Experiment web app (share this link)
├── apps_script.gs                # Google Apps Script — paste into Google Sheets
├── analyze_jod.py                # Computes JOD scores and plots results
├── videos/
│   ├── bicycle.mp4               ← base (no perceptual wrapper)
│   ├── bicycle_imagebase.mp4     ← image-based perceptual wrapper
│   ├── bicycle_pointbase.mp4     ← point-based perceptual wrapper
│   ├── bonsai.mp4
│   └── ...                       # 9 scenes × 3 methods = 27 files total
└── README.md
```

---

## Methods & Research Question

| Method | Filename pattern | Description |
|--------|-----------------|-------------|
| `base` | `{scene}.mp4` | **No perceptual wrapper** — baseline |
| `imagebase` | `{scene}_imagebase.mp4` | Image-based perceptual wrapper |
| `pointbase` | `{scene}_pointbase.mp4` | Point-based perceptual wrapper |

**Research question:** Do perceptual wrappers (`imagebase`, `pointbase`) improve
perceived video quality compared to the base method without any wrapper?

**Scenes (9):** bicycle, bonsai, counter, flowers, garden, kitchen, room, stump, treehill

---

## Experiment Design

- **Type:** Pairwise comparison (side-by-side, forced choice)
- **Trials per participant:** 27 (9 scenes × C(3,2) = 3 pairs per scene)
  - `base` vs `imagebase`
  - `base` vs `pointbase`
  - `imagebase` vs `pointbase`
- **Trial order:** Fully randomised per participant
- **Left/right position:** Randomly flipped per trial (controls position bias)
- **Scoring:** JOD (Just-Objectionable-Difference) via Thurstone Case V MLE
  - 1 JOD = 75% of participants prefer one method over the other
  - Baseline: `base` (no wrapper) = 0 JOD

---

## Setup

### Step 1 — Google Sheets (automatic data collection)

1. Create a new Google Sheet
2. Open **Extensions → Apps Script**
3. Paste the contents of `apps_script.gs` and save
4. Click **Deploy → New deployment → Web app**
   - Execute as: **Me**
   - Who has access: **Anyone**
5. Copy the Web App URL and paste it into `experiment.html` at `APPS_SCRIPT_URL`

### Step 2 — Deploy experiment

**Option A: GitHub Pages (recommended)**
```bash
git init && git add . && git commit -m "init"
gh repo create my-nvs-study --public --source=. --push
# Settings → Pages → main branch → Save
# Share: https://YOUR_USERNAME.github.io/my-nvs-study/experiment.html
```

**Option B: Local server (lab setting)**
```bash
python3 -m http.server 8080
# Open: http://localhost:8080/experiment.html
```

> ⚠️ Must use a server — browsers block local video files when opened via `file://`

---

## Analysis

### Install
```bash
pip install numpy scipy pandas matplotlib
```

### Run
```bash
# Export Google Sheet: File → Download → CSV → rename to results.csv
python analyze_jod.py
```

### Output

| File | Description |
|------|-------------|
| `jod_summary.csv` | JOD + 95% CI per method per scene |
| `jod_results.png` | Bar chart (Figure 4 style, Liang et al.) |
| `jod_results.pdf` | Same, vector format for paper |

### Interpreting results

```
Baseline: base (no wrapper) = 0 JOD

imagebase  +0.80 JOD  →  ~70% of participants prefer imagebase over base
pointbase  +1.30 JOD  →  ~80% of participants prefer pointbase over base
```

| JOD difference | Preference rate |
|---------------|----------------|
| 0.0 | 50% (chance) |
| 0.5 | ~63% |
| 1.0 | 75% |
| 1.5 | ~85% |
| 2.0 | ~92% |

**Error bars** = 95% CI via bootstrapping (500 resamples of observers).
If the CI does not overlap 0, the improvement is statistically significant.

---

## Data Format (Google Sheet)

| Column | Description |
|--------|-------------|
| `observer` | Participant ID |
| `scene` | Scene name (e.g. `bicycle`) |
| `stimulus_A` | Left video (e.g. `bicycle_imagebase`) |
| `stimulus_B` | Right video (e.g. `bicycle_base`) |
| `response` | `1` = left preferred, `2` = right preferred |
| `selected_condition` | Winning condition name |
| `timestamp` | Client-side ISO timestamp |
| `submitted_at` | Server-side receipt time |

---

## References

- Liang et al. (2023). *Perceptual Quality Assessment of NeRF and Neural View Synthesis Methods.* arXiv:2303.15206
- Perez-Ortiz & Mantiuk (2017). *A practical guide for analysing pairwise comparison experiments.* [github.com/mantiuk/pwcmp](https://github.com/mantiuk/pwcmp)
- Thurstone (1927). *A law of comparative judgment.* Psychological Review.
