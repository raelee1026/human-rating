"""
Pairwise Comparison Analysis — 3 Methods, Thurstone Case V MLE
================================================================
Install:  pip install numpy scipy pandas matplotlib
Run:      python analyze_jod.py
Input:    results.csv  (from Google Sheets)
Output:   jod_results.png / jod_results.pdf / jod_summary.csv
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats, optimize

# ── Config ────────────────────────────────────────────────────────
METHODS     = ['base', 'imagebase', 'pointbase']
BASELINE    = 'base'      # no perceptual wrapper — fixed at JOD = 0
N_BOOTSTRAP = 500
CI_ALPHA    = 0.05
OUTPUT_PDF  = 'jod_results.pdf'
OUTPUT_PNG  = 'jod_results.png'

COLORS = {
    'base':      '#aaaaaa',   # grey  — no wrapper (baseline)
    'imagebase': '#5b8fff',   # blue  — image-based wrapper
    'pointbase': '#ff6b6b',   # red   — point-based wrapper
}
SCALE = stats.norm.ppf(0.75)   # JOD: 1 unit = 75% preference

# ── 1. Load & preprocess ──────────────────────────────────────────
df = pd.read_csv('results.csv')

def method_of(s):
    # Sort by length DESC to avoid 'base' matching inside 'imagebase'/'pointbase'
    for m in sorted(METHODS, key=len, reverse=True):
        if s.endswith(m):
            return m
    return s

df['mA'] = df['stimulus_A'].apply(method_of)
df['mB'] = df['stimulus_B'].apply(method_of)
df['mW'] = df['selected_condition'].apply(method_of)

M_IDX = {m: i for i, m in enumerate(METHODS)}
K  = len(METHODS)
BI = M_IDX[BASELINE]

df['iA'] = df['mA'].map(M_IDX)
df['iB'] = df['mB'].map(M_IDX)
df['iW'] = df['mW'].map(M_IDX)
df = df.dropna(subset=['iA','iB','iW'])
df[['iA','iB','iW']] = df[['iA','iB','iW']].astype(int)

print(f"Loaded {len(df)} trials  |  "
      f"{df['observer'].nunique()} observers  |  "
      f"{df['scene'].nunique()} scenes\n")

# ── 2. Wins matrix (vectorised) ───────────────────────────────────
def wins_matrix(iA, iB, iW):
    iL = np.where(iW == iA, iB, iA)
    W  = np.zeros((K, K), dtype=np.float64)
    np.add.at(W, (iW, iL), 1)
    return W

# ── 3. Thurstone Case V MLE ───────────────────────────────────────
def thurstone_mle(iA, iB, iW):
    W = wins_matrix(iA, iB, iW)

    def neg_ll(mu_free):
        mu   = np.insert(mu_free, BI, 0.0)
        diff = mu[:, None] - mu[None, :]
        p    = np.clip(stats.norm.cdf(diff), 1e-9, 1-1e-9)
        return -(W * np.log(p)).sum()

    res = optimize.minimize(neg_ll, np.zeros(K-1), method='L-BFGS-B',
                            options={'ftol':1e-10, 'gtol':1e-7})
    mu  = np.insert(res.x, BI, 0.0)
    return mu / SCALE

# ── 4. Bootstrap CI ───────────────────────────────────────────────
def bootstrap_ci(sub_df, n_boot=N_BOOTSTRAP):
    obs_ids    = sub_df['observer'].unique()
    obs_groups = {o: sub_df[sub_df['observer'] == o][['iA','iB','iW']].values
                  for o in obs_ids}
    n_obs = len(obs_ids)
    boot  = np.zeros((n_boot, K))

    for b in range(n_boot):
        samp  = np.random.choice(obs_ids, size=n_obs, replace=True)
        bdata = np.concatenate([obs_groups[o] for o in samp], axis=0)
        try:
            boot[b] = thurstone_mle(bdata[:,0], bdata[:,1], bdata[:,2])
        except Exception:
            boot[b] = np.nan

    valid = ~np.isnan(boot[:,0])
    if valid.sum() < 10:
        return {m: (np.nan, np.nan) for m in METHODS}

    b = boot[valid]
    return {m: (np.percentile(b[:,i], 100*CI_ALPHA/2),
                np.percentile(b[:,i], 100*(1-CI_ALPHA/2)))
            for i, m in enumerate(METHODS)}

# ── 5. Compute per group ──────────────────────────────────────────
scenes    = sorted(df['scene'].unique())
groups    = ['All'] + scenes
all_rows  = []

print(f"{'Group':<12}  " + '  '.join(f"{m:>10}" for m in METHODS))
print('-' * 50)

for grp in groups:
    sub = df if grp == 'All' else df[df['scene'] == grp]
    iA, iB, iW = sub['iA'].values, sub['iB'].values, sub['iW'].values

    jods = thurstone_mle(iA, iB, iW)
    ci   = bootstrap_ci(sub)

    row   = {'group': grp}
    parts = []
    for i, m in enumerate(METHODS):
        lo, hi = ci[m]
        row[f'jod_{m}']   = round(jods[i], 3)
        row[f'ci_lo_{m}'] = round(lo, 3) if not np.isnan(lo) else np.nan
        row[f'ci_hi_{m}'] = round(hi, 3) if not np.isnan(hi) else np.nan
        parts.append(f'{jods[i]:+7.3f}')

    all_rows.append(row)
    print(f"{grp:<12}  " + '  '.join(parts), flush=True)

pd.DataFrame(all_rows).to_csv('jod_summary.csv', index=False)
print(f"\nSaved → jod_summary.csv")

# ── 6. Plot — Figure 4 style ──────────────────────────────────────
PLOT_METHODS = [m for m in METHODS if m != BASELINE]   # skip base bar
n_g  = len(groups)
bw   = 0.22
gs   = len(PLOT_METHODS) * bw + 0.25
xc   = np.arange(n_g) * gs
offs = np.linspace(-(len(PLOT_METHODS)-1)/2, (len(PLOT_METHODS)-1)/2,
                   len(PLOT_METHODS)) * bw

fig, ax = plt.subplots(figsize=(max(12, n_g * 1.4), 5.5))

for gi, (grp, row) in enumerate(zip(groups, all_rows)):
    for pi, m in enumerate(PLOT_METHODS):
        j  = row[f'jod_{m}']
        lo = row[f'ci_lo_{m}']
        hi = row[f'ci_hi_{m}']
        xb = xc[gi] + offs[pi]

        ax.bar(xb, j, bw * 0.88,
               color=COLORS[m], edgecolor='white', linewidth=0.4, zorder=3)

        if not np.isnan(lo):
            ax.errorbar(xb, j, yerr=[[j - lo], [hi - j]],
                        fmt='none', color='black', capsize=2.5, linewidth=1, zorder=4)

        va = 'bottom' if j >= 0 else 'top'
        ax.text(xb, j + (0.04 if j >= 0 else -0.04), f'{j:+.2f}',
                ha='center', va=va, fontsize=6.5, color='black')

ax.axhline(0, color='black', linewidth=0.8, zorder=2)
ax.axvline((xc[0] + xc[1]) / 2, color='#cccccc', linewidth=0.8, linestyle='--', zorder=1)

ax.set_xticks(xc)
ax.set_xticklabels(groups, fontsize=9)
ax.set_ylabel('Quality [JOD]', fontsize=11)
ax.set_title(
    f'Effect of perceptual wrapper  (baseline: {BASELINE} = 0 JOD)\n'
    f'Positive = better than {BASELINE}  |  Error bars = 95% CI (bootstrap n={N_BOOTSTRAP})',
    fontsize=10, pad=10
)

legend_labels = {
    'imagebase': 'imagebase  — image-based wrapper',
    'pointbase': 'pointbase  — point-based wrapper',
}
ax.legend(
    handles=[mpatches.Patch(color=COLORS[m], label=legend_labels[m]) for m in PLOT_METHODS],
    loc='upper right', framealpha=0.9, fontsize=9
)
ax.grid(axis='y', linestyle='--', linewidth=0.4, alpha=0.5, zorder=0)
ax.spines[['top', 'right']].set_visible(False)

all_vals = [row[f'{k}_{m}']
            for row in all_rows for m in METHODS
            for k in ['jod', 'ci_lo', 'ci_hi']
            if not np.isnan(row.get(f'{k}_{m}', np.nan))]
if all_vals:
    pad = max(0.3, (max(all_vals) - min(all_vals)) * 0.2)
    ax.set_ylim(min(all_vals) - pad, max(all_vals) + pad)

ax.set_xlim(xc[0] - gs * 0.6, xc[-1] + gs * 0.6)
plt.tight_layout()
plt.savefig(OUTPUT_PDF, dpi=150, bbox_inches='tight')
plt.savefig(OUTPUT_PNG, dpi=150, bbox_inches='tight')
print(f'Saved → {OUTPUT_PDF}  /  {OUTPUT_PNG}')
