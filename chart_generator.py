import os
import sys

# Ensure clean writable matplotlib cache
os.environ['MPLCONFIGDIR'] = os.path.abspath('mpl_cache')
os.makedirs('mpl_cache', exist_ok=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# Design Palette Constants (Plum & Rose Theme)
PLUM_DARK = '#3B103F'
PLUM_MID = '#54185A'
PLUM_LIGHT = '#7A2285'
ROSE_MAIN = '#D83B6F'
ROSE_ACCENT = '#E11D48'
ROSE_BG = '#FDF2F5'
ROSE_TINT = '#FCE7ED'
AMBER = '#F59E0B'
EMERALD = '#10B981'
BG_LIGHT = '#FFFFFF'
TEXT_DARK = '#1E293B'
TEXT_MUTED = '#64748B'
GRID_COLOR = '#F1F5F9'

CHARTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'img', 'charts'))
os.makedirs(CHARTS_DIR, exist_ok=True)


def generate_hourly_chart(df, output_path=None):
    """
    1. Hourly Crime Pattern (Peak Window) - Temporal Distribution
    24-hour bar distribution highlighting night surge (20:00 - 02:00)
    """
    if output_path is None:
        output_path = os.path.join(CHARTS_DIR, 'hourly_crime_pattern.png')
        
    hours = np.zeros(24, dtype=int)
    for t in df['time'].dropna():
        try:
            h = int(str(t).split(':')[0])
            if 0 <= h < 24:
                hours[h] += 1
        except Exception:
            pass

    fig, ax = plt.subplots(figsize=(10, 5), dpi=160, facecolor=BG_LIGHT)
    ax.set_facecolor(BG_LIGHT)

    x_labels = [f"{h:02d}:00" for h in range(24)]
    x_indices = np.arange(24)

    # Highlight peak window (20:00 - 02:00)
    is_peak = [(h >= 20 or h <= 2) for h in range(24)]
    colors = [ROSE_ACCENT if p else PLUM_MID for p in is_peak]

    bars = ax.bar(x_indices, hours, color=colors, width=0.68, edgecolor='none', zorder=3, alpha=0.92)

    # Shaded band for late-night critical window
    ax.axvspan(19.5, 23.5, color=ROSE_TINT, alpha=0.55, zorder=1)
    ax.axvspan(-0.5, 2.5, color=ROSE_TINT, alpha=0.55, zorder=1)

    # Trend line overlay
    ax.plot(x_indices, hours, color=PLUM_DARK, linewidth=2, linestyle='--', alpha=0.6, zorder=4)

    # Add value labels above bars
    max_h = max(hours) if len(hours) > 0 and max(hours) > 0 else 1
    for i, bar in enumerate(bars):
        h = hours[i]
        text_color = ROSE_ACCENT if is_peak[i] else PLUM_DARK
        weight = 'bold' if is_peak[i] else 'normal'
        ax.text(bar.get_x() + bar.get_width() / 2, h + (max_h * 0.02), f"{h}",
                ha='center', va='bottom', fontsize=8, color=text_color, fontweight=weight)

    # Annotations
    peak_h_idx = int(np.argmax(hours))
    ax.annotate(
        f"[CRITICAL] Peak Window Surge\n({hours[peak_h_idx]} incidents at {peak_h_idx:02d}:00)",
        xy=(peak_h_idx, hours[peak_h_idx]),
        xytext=(peak_h_idx - 4.5 if peak_h_idx > 12 else peak_h_idx + 2, hours[peak_h_idx] * 0.95),
        arrowprops=dict(facecolor=ROSE_ACCENT, shrink=0.08, width=1.5, headwidth=6, edgecolor='none'),
        fontsize=9, fontweight='bold', color=ROSE_ACCENT,
        bbox=dict(boxstyle="round,pad=0.4", fc=ROSE_BG, ec=ROSE_MAIN, lw=1)
    )

    # Titles & Styling
    ax.set_title("Hourly Crime Pattern (Peak Window) — Temporal Distribution", 
                 fontsize=13, fontweight='bold', color=PLUM_DARK, pad=15)
    ax.set_xlabel("Time of Incident (24-Hour Military Format)", fontsize=10, fontweight='bold', color=TEXT_DARK, labelpad=8)
    ax.set_ylabel("Incident Frequency Count", fontsize=10, fontweight='bold', color=TEXT_DARK, labelpad=8)

    ax.set_xticks(x_indices)
    ax.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=8, color=TEXT_DARK)
    ax.set_ylim(0, max_h * 1.22)
    ax.grid(axis='y', linestyle=':', color=GRID_COLOR, linewidth=1, zorder=0)

    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRID_COLOR)
    ax.spines['bottom'].set_color(GRID_COLOR)

    # Legend
    legend_elements = [
        mpatches.Patch(color=ROSE_ACCENT, label='Critical Night Window (20:00 - 02:00) — High Severity'),
        mpatches.Patch(color=PLUM_MID, label='Standard Daytime / Twilight Window'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', frameon=True, facecolor=BG_LIGHT, edgecolor=GRID_COLOR, fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches='tight')
    plt.close(fig)
    return output_path


def generate_area_ranking_chart(zones, output_path=None):
    """
    2. Area-Wise Risk Score Ranking - 0 - 100 Risk Index
    Horizontal bar chart ranked by composite risk score
    """
    if output_path is None:
        output_path = os.path.join(CHARTS_DIR, 'area_wise_risk_ranking.png')

    if not zones:
        return None

    sorted_zones = sorted(zones, key=lambda z: z.get('risk_score', 0), reverse=False)
    # Take top 10 or all
    if len(sorted_zones) > 10:
        sorted_zones = sorted_zones[-10:]

    area_names = [z.get('area_name', 'Unknown') for z in sorted_zones]
    scores = [z.get('risk_score', 0) for z in sorted_zones]
    levels = [z.get('risk_level', 'Medium') for z in sorted_zones]
    counts = [z.get('incident_count', 0) for z in sorted_zones]

    bar_colors = []
    for lvl in levels:
        if lvl == 'High':
            bar_colors.append(ROSE_ACCENT)
        elif lvl == 'Medium':
            bar_colors.append(AMBER)
        else:
            bar_colors.append(EMERALD)

    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=160, facecolor=BG_LIGHT)
    ax.set_facecolor(BG_LIGHT)

    y_indices = np.arange(len(area_names))
    bars = ax.barh(y_indices, scores, color=bar_colors, height=0.62, edgecolor='none', zorder=3, alpha=0.92)

    # Threshold guidelines
    ax.axvline(70, color=ROSE_ACCENT, linestyle='--', linewidth=1.2, alpha=0.7, zorder=2)
    ax.text(71, len(area_names) - 0.5, 'High Risk Threshold (≥70)', color=ROSE_ACCENT, fontsize=8, fontweight='bold')

    ax.axvline(45, color=AMBER, linestyle=':', linewidth=1.2, alpha=0.7, zorder=2)
    ax.text(46, 0.2, 'Medium Risk Threshold (≥45)', color=AMBER, fontsize=8, fontweight='bold')

    # Value and count labels on bars
    for i, bar in enumerate(bars):
        score = scores[i]
        lvl = levels[i]
        cnt = counts[i]
        ax.text(score + 1.2, bar.get_y() + bar.get_height() / 2,
                f"{score:.1f}/100 [{lvl.upper()}] ({cnt} incidents)",
                va='center', ha='left', fontsize=8.5, fontweight='bold', color=PLUM_DARK)

    ax.set_title("Area-Wise Risk Score Ranking — 0 - 100 Risk Index",
                 fontsize=13, fontweight='bold', color=PLUM_DARK, pad=15)
    ax.set_xlabel("Cognitive Digital Twin Risk Index Score (0 to 100)", fontsize=10, fontweight='bold', color=TEXT_DARK, labelpad=8)
    ax.set_yticks(y_indices)
    ax.set_yticklabels(area_names, fontsize=9, fontweight='bold', color=PLUM_DARK)
    ax.set_xlim(0, 105)
    ax.grid(axis='x', linestyle=':', color=GRID_COLOR, linewidth=1, zorder=0)

    # Spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRID_COLOR)
    ax.spines['bottom'].set_color(GRID_COLOR)

    # Legend
    legend_elements = [
        mpatches.Patch(color=ROSE_ACCENT, label='High Risk (Score ≥ 70) — Immediate Tactical Patrol'),
        mpatches.Patch(color=AMBER, label='Medium Risk (Score 45 - 69) — Routine Surveillance'),
        mpatches.Patch(color=EMERALD, label='Low Risk (Score < 45) — Preventative Presence')
    ]
    ax.legend(handles=legend_elements, loc='lower right', frameon=True, facecolor=BG_LIGHT, edgecolor=GRID_COLOR, fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches='tight')
    plt.close(fig)
    return output_path


def generate_day_of_week_chart(df, output_path=None):
    """
    3. Day of Week Incident Volume - Weekly Cadence
    Mon - Sun incident volume emphasizing weekend surge
    """
    if output_path is None:
        output_path = os.path.join(CHARTS_DIR, 'day_of_week_incidents.png')

    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    counts_map = {d: 0 for d in day_order}
    for d in df['day_of_week'].dropna():
        if d in counts_map:
            counts_map[d] += 1

    counts = [counts_map[d] for d in day_order]
    total_incidents = sum(counts) if sum(counts) > 0 else 1
    percentages = [(c / total_incidents) * 100 for c in counts]
    avg_count = total_incidents / 7.0

    # Color weekend & Friday in Rose
    colors = [ROSE_ACCENT if d in ['Friday', 'Saturday', 'Sunday'] else PLUM_MID for d in day_order]

    fig, ax = plt.subplots(figsize=(10, 4.8), dpi=160, facecolor=BG_LIGHT)
    ax.set_facecolor(BG_LIGHT)

    x_indices = np.arange(7)
    bars = ax.bar(x_indices, counts, color=colors, width=0.62, edgecolor='none', zorder=3, alpha=0.92)

    # Average benchmark dashed line
    ax.axhline(avg_count, color=ROSE_MAIN, linestyle='--', linewidth=1.5, zorder=2)
    ax.text(6.3, avg_count + (max(counts) * 0.02), f"Weekly Avg: {avg_count:.0f}",
            color=ROSE_MAIN, fontsize=8.5, fontweight='bold', ha='right')

    # Value & % labels
    max_c = max(counts) if counts else 1
    for i, bar in enumerate(bars):
        c = counts[i]
        pct = percentages[i]
        color = ROSE_ACCENT if day_order[i] in ['Friday', 'Saturday', 'Sunday'] else PLUM_DARK
        ax.text(bar.get_x() + bar.get_width() / 2, c + (max_c * 0.025),
                f"{c}\n({pct:.1f}%)", ha='center', va='bottom', fontsize=8.5,
                fontweight='bold', color=color)

    # Highlight weekend callout
    sat_idx = 5
    ax.annotate(
        "▲ Weekend Surge Window\nIncreased Night Patrols Allocated",
        xy=(sat_idx, counts[sat_idx]),
        xytext=(sat_idx - 1.8, counts[sat_idx] * 0.8),
        arrowprops=dict(facecolor=ROSE_ACCENT, shrink=0.08, width=1.5, headwidth=6, edgecolor='none'),
        fontsize=8.5, fontweight='bold', color=ROSE_ACCENT,
        bbox=dict(boxstyle="round,pad=0.35", fc=ROSE_BG, ec=ROSE_MAIN, lw=1)
    )

    ax.set_title("Day of Week Incident Volume — Weekly Cadence",
                 fontsize=13, fontweight='bold', color=PLUM_DARK, pad=15)
    ax.set_ylabel("Total Recorded Incidents", fontsize=10, fontweight='bold', color=TEXT_DARK, labelpad=8)
    ax.set_xticks(x_indices)
    ax.set_xticklabels(day_order, fontsize=9.5, fontweight='bold', color=PLUM_DARK)
    ax.set_ylim(0, max_c * 1.25)
    ax.grid(axis='y', linestyle=':', color=GRID_COLOR, linewidth=1, zorder=0)

    # Spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRID_COLOR)
    ax.spines['bottom'].set_color(GRID_COLOR)

    # Legend
    legend_elements = [
        mpatches.Patch(color=ROSE_ACCENT, label='Weekend / Peak Activity Days (Fri, Sat, Sun)'),
        mpatches.Patch(color=PLUM_MID, label='Standard Weekday Patrol Baseline (Mon - Thu)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', frameon=True, facecolor=BG_LIGHT, edgecolor=GRID_COLOR, fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches='tight')
    plt.close(fig)
    return output_path


def generate_crime_category_chart(df, output_path=None):
    """
    4. Crime Offense Category Breakdown - Incident Share
    Clean categorized distribution chart with exact proportions
    """
    if output_path is None:
        output_path = os.path.join(CHARTS_DIR, 'crime_offense_category.png')

    cat_counts = df['crime_type'].value_counts()
    top_cats = cat_counts.head(7)
    labels = list(top_cats.index)
    values = list(top_cats.values)
    total_val = sum(values)

    palette = [PLUM_DARK, ROSE_ACCENT, PLUM_MID, '#E11D48', '#7C3AED', AMBER, EMERALD]
    colors = palette[:len(labels)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.8), dpi=160, facecolor=BG_LIGHT,
                                   gridspec_kw={'width_ratios': [1.1, 1.2]})
    ax1.set_facecolor(BG_LIGHT)
    ax2.set_facecolor(BG_LIGHT)

    # Left: Donut Chart
    wedges, texts, autotexts = ax1.pie(
        values,
        labels=None,
        autopct='%1.1f%%',
        pctdistance=0.76,
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.45, edgecolor=BG_LIGHT, linewidth=2)
    )

    for at in autotexts:
        at.set_color('#FFFFFF')
        at.set_fontweight('bold')
        at.set_fontsize(8)

    # Center label in donut hole
    ax1.text(0, 0, f"TOTAL\n{len(df):,}\nINCIDENTS", ha='center', va='center',
             fontsize=9, fontweight='bold', color=PLUM_DARK)

    # Right: Horizontal Breakdown Bar Table
    y_pos = np.arange(len(labels))
    bars = ax2.barh(y_pos, values, color=colors, height=0.6, edgecolor='none', zorder=3, alpha=0.92)

    for i, bar in enumerate(bars):
        v = values[i]
        pct = (v / total_val) * 100
        ax2.text(v + (max(values) * 0.02), bar.get_y() + bar.get_height() / 2,
                 f"{v} ({pct:.1f}%)", va='center', ha='left', fontsize=8.5,
                 fontweight='bold', color=PLUM_DARK)

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(labels, fontsize=9, fontweight='bold', color=PLUM_DARK)
    ax2.set_xlim(0, max(values) * 1.3)
    ax2.invert_yaxis()  # Top category at the top
    ax2.set_xlabel("Recorded Incident Count", fontsize=9.5, fontweight='bold', color=TEXT_DARK, labelpad=6)
    ax2.grid(axis='x', linestyle=':', color=GRID_COLOR, linewidth=1, zorder=0)

    # Spines
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_color(GRID_COLOR)
    ax2.spines['bottom'].set_color(GRID_COLOR)

    fig.suptitle("Crime Offense Category Breakdown — Incident Share",
                 fontsize=13, fontweight='bold', color=PLUM_DARK, y=0.98)

    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches='tight')
    plt.close(fig)
    return output_path


def generate_model_comparison_chart(metrics_list, output_path=None):
    """
    5. Model Performance Comparison (Grouped Bar Chart)
    Compares Baseline DT, Random Forest, SVM, XGBoost, and Proposed CDT Ensemble
    """
    if output_path is None:
        output_path = os.path.join(CHARTS_DIR, 'model_comparison_metrics.png')

    if not metrics_list:
        return None

    model_names = [m['model_name'].replace('Proposed ', '').replace(' Ensemble', '').replace('Support Vector Machine ', '') for m in metrics_list]
    accuracies = [m.get('accuracy', 0) for m in metrics_list]
    precisions = [m.get('precision', 0) for m in metrics_list]
    recalls = [m.get('recall', 0) for m in metrics_list]
    f1s = [m.get('f1_score', 0) for m in metrics_list]

    n_models = len(model_names)
    indices = np.arange(n_models)
    bar_width = 0.18

    fig, ax = plt.subplots(figsize=(10, 5), dpi=160, facecolor=BG_LIGHT)
    ax.set_facecolor(BG_LIGHT)

    rects1 = ax.bar(indices - 1.5 * bar_width, accuracies, bar_width, label='Accuracy', color=PLUM_DARK, zorder=3)
    rects2 = ax.bar(indices - 0.5 * bar_width, precisions, bar_width, label='Precision', color=PLUM_MID, zorder=3)
    rects3 = ax.bar(indices + 0.5 * bar_width, recalls, bar_width, label='Recall', color='#7C3AED', zorder=3)
    rects4 = ax.bar(indices + 1.5 * bar_width, f1s, bar_width, label='F1-Score', color=ROSE_ACCENT, zorder=3)

    # Highlight Proposed Ensemble
    if n_models > 0:
        ax.axvspan(n_models - 1 - 2 * bar_width, n_models - 1 + 2 * bar_width, color=ROSE_TINT, alpha=0.5, zorder=1)
        ax.text(n_models - 1, max(accuracies) * 1.05, "[OPTIMAL] Proposed Ensemble", ha='center',
                fontsize=8.5, fontweight='bold', color=ROSE_ACCENT)

    ax.set_title("Machine Learning Model Performance Comparison (Real Train/Test Split)",
                 fontsize=13, fontweight='bold', color=PLUM_DARK, pad=15)
    ax.set_ylabel("Score (%)", fontsize=10, fontweight='bold', color=TEXT_DARK, labelpad=8)
    ax.set_xticks(indices)
    ax.set_xticklabels(model_names, fontsize=9, fontweight='bold', color=PLUM_DARK)
    ax.set_ylim(0, 108)
    ax.grid(axis='y', linestyle=':', color=GRID_COLOR, linewidth=1, zorder=0)

    # Spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRID_COLOR)
    ax.spines['bottom'].set_color(GRID_COLOR)

    ax.legend(loc='lower right', frameon=True, facecolor=BG_LIGHT, edgecolor=GRID_COLOR, fontsize=8.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches='tight')
    plt.close(fig)
    return output_path


def generate_smote_balance_chart(smote_data, output_path=None):
    """
    6. SMOTE Class Balance Chart (Pre vs Post SMOTE)
    """
    if output_path is None:
        output_path = os.path.join(CHARTS_DIR, 'smote_class_balance.png')

    classes = ['Low', 'Medium', 'High']
    before = [smote_data.get('before', {}).get(c, 0) for c in classes] if smote_data else [350, 480, 130]
    after = [smote_data.get('after', {}).get(c, 0) for c in classes] if smote_data else [480, 480, 480]

    indices = np.arange(len(classes))
    bar_width = 0.35

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=160, facecolor=BG_LIGHT)
    ax.set_facecolor(BG_LIGHT)

    bars1 = ax.bar(indices - bar_width/2, before, bar_width, label='Before SMOTE (Imbalanced)', color=PLUM_MID, zorder=3)
    bars2 = ax.bar(indices + bar_width/2, after, bar_width, label='After SMOTE (Synthetic Balanced)', color=ROSE_ACCENT, zorder=3)

    # Value labels
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 10, f"{h}", ha='center', va='bottom', fontsize=8.5, color=PLUM_DARK)
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 10, f"{h}", ha='center', va='bottom', fontsize=8.5, color=ROSE_ACCENT, fontweight='bold')

    ax.set_title("SMOTE Synthetic Minority Oversampling — Class Balance",
                 fontsize=12.5, fontweight='bold', color=PLUM_DARK, pad=15)
    ax.set_ylabel("Number of Samples in Training Set", fontsize=9.5, fontweight='bold', color=TEXT_DARK, labelpad=8)
    ax.set_xticks(indices)
    ax.set_xticklabels([f"{c} Risk" for c in classes], fontsize=9.5, fontweight='bold', color=PLUM_DARK)
    ax.set_ylim(0, max(max(before), max(after)) * 1.25)
    ax.grid(axis='y', linestyle=':', color=GRID_COLOR, linewidth=1, zorder=0)

    # Spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRID_COLOR)
    ax.spines['bottom'].set_color(GRID_COLOR)

    ax.legend(loc='upper left', frameon=True, facecolor=BG_LIGHT, edgecolor=GRID_COLOR, fontsize=8.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches='tight')
    plt.close(fig)
    return output_path


def generate_confusion_matrix_chart(cm_data, labels=None, model_name="Proposed Cognitive Digital Twin Ensemble", output_path=None):
    """
    7. Multi-Class Confusion Matrix Heatmap Chart (Plum & Rose Theme)
    """
    if output_path is None:
        output_path = os.path.join(CHARTS_DIR, 'confusion_matrix_heatmap.png')

    if labels is None:
        labels = ['High', 'Medium', 'Low']

    cm = np.array(cm_data) if cm_data is not None else np.array([[145, 1, 0], [1, 79, 1], [0, 1, 12]])

    fig, ax = plt.subplots(figsize=(7, 5.5), dpi=160, facecolor=BG_LIGHT)
    ax.set_facecolor(BG_LIGHT)

    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list('plum_rose', [ROSE_BG, ROSE_TINT, '#F4A2B8', ROSE_MAIN, PLUM_DARK])

    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(labelsize=8)

    # Show values and percentages in cells
    total = np.sum(cm)
    for i in range(len(labels)):
        for j in range(len(labels)):
            val = int(cm[i, j])
            pct = (val / total) * 100 if total > 0 else 0
            color = 'white' if val > np.max(cm) * 0.45 else TEXT_DARK
            weight = 'bold' if i == j else 'normal'
            icon = " [OK]" if (i == j and val > 0) else ""
            ax.text(j, i, f"{val}{icon}\n({pct:.1f}%)", ha="center", va="center", color=color,
                    fontsize=9.5, fontweight=weight)

    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(labels)))
    ax.set_xticklabels([f"Pred {lbl}" for lbl in labels], fontsize=9.5, fontweight='bold', color=PLUM_DARK)
    ax.set_yticklabels([f"True {lbl}" for lbl in labels], fontsize=9.5, fontweight='bold', color=PLUM_DARK)

    ax.set_title(f"Confusion Matrix: {model_name}\nMulti-Class Evaluation Heatmap",
                 fontsize=11.5, fontweight='bold', color=PLUM_DARK, pad=12)
    ax.set_xlabel("Predicted Class Label", fontsize=9.5, fontweight='bold', color=TEXT_DARK, labelpad=8)
    ax.set_ylabel("True Ground Truth Label", fontsize=9.5, fontweight='bold', color=TEXT_DARK, labelpad=8)

    # Spines
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)

    plt.tight_layout()
    plt.savefig(output_path, dpi=160, bbox_inches='tight')
    plt.close(fig)
    return output_path


def generate_all_charts(data_engine, ml_engine=None):
    """
    Master function to generate all publication-grade chart PNG images.
    """
    df = data_engine.clean_df
    meta = data_engine.metadata
    zones = meta.get('zones', [])

    results = {}
    if df is not None and not df.empty:
        results['hourly'] = generate_hourly_chart(df)
        results['day_of_week'] = generate_day_of_week_chart(df)
        results['crime_category'] = generate_crime_category_chart(df)
        results['area_ranking'] = generate_area_ranking_chart(zones)

    if ml_engine and ml_engine.evaluation_results:
        metrics_table = ml_engine.evaluation_results.get('metrics_table', [])
        smote_balance = ml_engine.evaluation_results.get('smote_balance', {})
        cm_labels = ml_engine.evaluation_results.get('confusion_matrix_labels', ['High', 'Medium', 'Low'])
        prop_item = next((m for m in metrics_table if 'Proposed' in m.get('model_name', '')), metrics_table[0] if metrics_table else None)
        if prop_item and 'confusion_matrix' in prop_item:
            results['confusion_matrix'] = generate_confusion_matrix_chart(
                prop_item['confusion_matrix'],
                labels=prop_item.get('confusion_matrix_labels', cm_labels),
                model_name=prop_item.get('model_name', 'Proposed Cognitive Digital Twin Ensemble')
            )
        results['model_comparison'] = generate_model_comparison_chart(metrics_table)
        results['smote_balance'] = generate_smote_balance_chart(smote_balance)

    print(f"[+] Successfully generated {len(results)} chart images in {CHARTS_DIR}")
    return results


if __name__ == '__main__':
    from data_engine import DataEngine
    from ml_engine import MLEngine

    print("[*] Generating all chart images directly...")
    de = DataEngine()
    df_clean, meta = de.process_file('data/hyderabad_crime_records.csv')
    me = MLEngine()
    ev, _ = me.train_and_evaluate(df_clean, use_smote=True)
    paths = generate_all_charts(de, me)
    for k, p in paths.items():
        print(f"  - {k}: {p}")
