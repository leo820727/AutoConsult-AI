# -*- coding: utf-8 -*-
"""
AutoConsult AI — app.py
========================
Streamlit 前端介面

執行方式：
  streamlit run app.py
"""

import sys
import io
import json
import datetime
from pathlib import Path

import streamlit as st

# ── 路徑設定 ─────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "engine"))

import ai_analyzer
import report_generator

OUTPUTS_DIR = PROJECT_ROOT / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════
# 全域 CSS — B2B SaaS 深藍質感
# ══════════════════════════════════════════════
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* ── Background ── */
.stApp {
    background: linear-gradient(135deg, #050d1a 0%, #0a1628 50%, #0d1f3c 100%);
    min-height: 100vh;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1100px; }

/* ── Top Nav Bar ── */
.nav-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 0 2rem;
    border-bottom: 1px solid rgba(59,130,246,0.2);
    margin-bottom: 2.5rem;
}
.nav-logo {
    font-size: 1.3rem; font-weight: 800; letter-spacing: -0.5px;
    background: linear-gradient(90deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.nav-badge {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 1px;
    padding: 0.25rem 0.7rem; border-radius: 999px;
    background: rgba(96,165,250,0.12); color: #60a5fa;
    border: 1px solid rgba(96,165,250,0.25); text-transform: uppercase;
}

/* ── Hero Section ── */
.hero {
    text-align: center; padding: 2.5rem 1rem 3rem;
}
.hero h1 {
    font-size: 2.8rem; font-weight: 800; letter-spacing: -1px;
    color: #f1f5f9; margin: 0 0 0.75rem; line-height: 1.15;
}
.hero h1 span {
    background: linear-gradient(90deg, #60a5fa 0%, #a78bfa 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero p {
    font-size: 1.05rem; color: #94a3b8; max-width: 560px;
    margin: 0 auto 2rem; line-height: 1.7;
}

/* ── Upload Zone ── */
.upload-zone {
    background: rgba(15,23,42,0.7);
    border: 1.5px dashed rgba(96,165,250,0.35);
    border-radius: 16px; padding: 2rem;
    transition: border-color 0.2s, background 0.2s;
    margin-bottom: 1.5rem;
}
.upload-zone:hover {
    border-color: rgba(96,165,250,0.65);
    background: rgba(15,23,42,0.9);
}
.upload-label {
    font-size: 0.8rem; font-weight: 600; letter-spacing: 0.8px;
    color: #60a5fa; text-transform: uppercase; margin-bottom: 0.5rem;
}
.upload-hint {
    font-size: 0.78rem; color: #64748b; margin-top: 0.4rem;
}

/* ── File Status Pills ── */
.file-pill {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 0.78rem; font-weight: 500;
    padding: 0.3rem 0.8rem; border-radius: 999px;
    background: rgba(34,197,94,0.1); color: #4ade80;
    border: 1px solid rgba(34,197,94,0.2); margin: 0.2rem;
}
.file-pill-missing {
    background: rgba(239,68,68,0.1); color: #f87171;
    border: 1px solid rgba(239,68,68,0.2);
}

/* ── Divider ── */
.section-divider {
    border: none; border-top: 1px solid rgba(148,163,184,0.1);
    margin: 2rem 0;
}

/* ── Section Title ── */
.section-title {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 1.5px;
    color: #475569; text-transform: uppercase; margin-bottom: 1.2rem;
}

/* ── KPI Cards Row ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem; margin-bottom: 2rem;
}
.kpi-card {
    background: rgba(15,23,42,0.8);
    border: 1px solid rgba(59,130,246,0.15);
    border-radius: 14px; padding: 1.4rem 1.2rem;
    position: relative; overflow: hidden;
    transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
}
.kpi-card:hover {
    transform: translateY(-3px);
    border-color: rgba(96,165,250,0.35);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}
.kpi-icon { font-size: 1.5rem; margin-bottom: 0.6rem; }
.kpi-label {
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px;
    color: #64748b; text-transform: uppercase; margin-bottom: 0.3rem;
}
.kpi-value {
    font-size: 1.9rem; font-weight: 800; line-height: 1;
    color: #f1f5f9; margin-bottom: 0.25rem;
}
.kpi-sub { font-size: 0.75rem; color: #475569; }
.kpi-badge-good {
    display: inline-block; font-size: 0.65rem; font-weight: 700;
    padding: 0.15rem 0.5rem; border-radius: 4px;
    background: rgba(34,197,94,0.15); color: #4ade80;
}
.kpi-badge-warn {
    background: rgba(251,146,60,0.15); color: #fb923c;
}
.kpi-badge-bad {
    background: rgba(239,68,68,0.15); color: #f87171;
}

/* ── Score Ring ── */
.score-ring-wrap {
    display: flex; align-items: center; justify-content: center;
    padding: 1.5rem;
    background: rgba(15,23,42,0.8);
    border: 1px solid rgba(59,130,246,0.15); border-radius: 14px;
    margin-bottom: 1rem;
}
.score-ring {
    position: relative; width: 90px; height: 90px;
}
.score-ring svg { transform: rotate(-90deg); }
.score-ring-label {
    position: absolute; inset: 0;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
}
.score-ring-num { font-size: 1.6rem; font-weight: 800; color: #f1f5f9; }
.score-ring-txt { font-size: 0.6rem; color: #64748b; letter-spacing: 0.5px; }

/* ── Dimension Card ── */
.dim-card {
    background: rgba(15,23,42,0.7);
    border: 1px solid rgba(59,130,246,0.12);
    border-radius: 12px; padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}
.dim-card-title {
    font-size: 0.82rem; font-weight: 700; color: #93c5fd;
    margin-bottom: 0.8rem; display: flex; align-items: center; gap: 6px;
}
.dim-card p { font-size: 0.85rem; color: #94a3b8; line-height: 1.65; margin: 0; }

/* ── Progress Bar ── */
.prog-wrap { margin-bottom: 0.6rem; }
.prog-label-row {
    display: flex; justify-content: space-between;
    font-size: 0.75rem; color: #64748b; margin-bottom: 3px;
}
.prog-label-row span:last-child { color: #93c5fd; font-weight: 600; }
.prog-track {
    height: 5px; border-radius: 999px;
    background: rgba(51,65,85,0.8); overflow: hidden;
}
.prog-fill {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    transition: width 1s ease;
}

/* ── Objection Tag ── */
.obj-tag {
    display: inline-block; font-size: 0.7rem; font-weight: 600;
    padding: 0.2rem 0.55rem; border-radius: 4px; margin-right: 4px;
}
.tag-price    { background:rgba(239,68,68,0.15);   color:#f87171; }
.tag-timeline { background:rgba(251,146,60,0.15);  color:#fb923c; }
.tag-trust    { background:rgba(234,179,8,0.15);   color:#fbbf24; }
.tag-logistics{ background:rgba(99,102,241,0.15);  color:#a5b4fc; }
.tag-other    { background:rgba(148,163,184,0.1);  color:#94a3b8; }

/* ── Objeciton Row ── */
.obj-row {
    background: rgba(15,23,42,0.6);
    border: 1px solid rgba(59,130,246,0.1);
    border-radius: 10px; padding: 1rem 1.2rem;
    margin-bottom: 0.75rem;
}
.obj-text { font-size: 0.88rem; color: #e2e8f0; margin-bottom: 0.5rem; }
.obj-rebuttal {
    font-size: 0.8rem; color: #64748b; font-style: italic;
    border-left: 2px solid rgba(96,165,250,0.3); padding-left: 0.75rem;
    margin-top: 0.5rem; line-height: 1.6;
}

/* ── ROI Table ── */
.roi-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
.roi-table th {
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px;
    color: #475569; text-transform: uppercase; text-align: left;
    padding: 0.4rem 0.75rem; border-bottom: 1px solid rgba(51,65,85,0.8);
}
.roi-table td {
    font-size: 0.85rem; color: #94a3b8;
    padding: 0.55rem 0.75rem; border-bottom: 1px solid rgba(30,41,59,0.6);
}
.roi-table td.highlight {
    color: #4ade80; font-weight: 700;
}
.roi-table tr:last-child td { border: none; }

/* ── Action Plan ── */
.action-item {
    display: flex; gap: 0.75rem; align-items: flex-start;
    padding: 0.8rem 1rem;
    background: rgba(15,23,42,0.5);
    border-radius: 8px; margin-bottom: 0.5rem;
    border: 1px solid rgba(59,130,246,0.08);
}
.action-num {
    flex-shrink: 0; width: 22px; height: 22px;
    background: linear-gradient(135deg,#3b82f6,#8b5cf6);
    border-radius: 50%; display: flex; align-items:center; justify-content:center;
    font-size: 0.65rem; font-weight: 800; color: white; margin-top: 1px;
}
.action-text { font-size: 0.85rem; color: #94a3b8; line-height: 1.6; }
.action-text strong { color: #cbd5e1; }

/* ── Download Buttons ── */
.dl-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 1.5rem; }

/* ── Streamlit widget overrides ── */
.stFileUploader > div > div {
    background: rgba(15,23,42,0.001) !important;
    border: none !important; color: #94a3b8;
}
.stFileUploader label { color: #94a3b8 !important; }
div[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: none !important;
}
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
    color: white !important; font-weight: 700 !important;
    border: none !important; border-radius: 10px !important;
    padding: 0.65rem 2rem !important; font-size: 0.95rem !important;
    letter-spacing: 0.3px !important;
    box-shadow: 0 4px 20px rgba(37,99,235,0.35) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(37,99,235,0.5) !important;
    background: linear-gradient(135deg, #1d4ed8, #6d28d9) !important;
}
.stSelectbox > div > div {
    background: rgba(15,23,42,0.9) !important;
    border: 1px solid rgba(59,130,246,0.2) !important;
    color: #e2e8f0 !important; border-radius: 8px !important;
}
.stAlert { border-radius: 10px !important; }
div[data-testid="stSpinner"] > div { color: #60a5fa !important; }
</style>
"""


# ══════════════════════════════════════════════
# HTML 元件產生器
# ══════════════════════════════════════════════

def nav_bar() -> str:
    return """
<div class="nav-bar">
  <div class="nav-logo">⬡ AutoConsult AI</div>
  <div style="display:flex;gap:0.75rem;align-items:center">
    <span class="nav-badge">AI-Powered</span>
    <span class="nav-badge">SMB Diagnostic</span>
  </div>
</div>"""


def hero_section() -> str:
    return """
<div class="hero">
  <h1>Business Diagnosis, <span>Automated</span></h1>
  <p>Upload questionnaires and transcripts. Let AI perform a 5-dimensional health check in 60 seconds, 
     delivering professional-grade consultant insights and action plans.</p>
</div>"""


def file_pill(name: str, ok: bool) -> str:
    cls = "file-pill" if ok else "file-pill file-pill-missing"
    icon = "✓" if ok else "✗"
    return f'<span class="{cls}">{icon} {name}</span>'


def kpi_card(icon: str, label: str, value: str, sub: str = "", badge: str = "", badge_type: str = "good") -> str:
    badge_html = f'<br><span class="kpi-badge-{badge_type}">{badge}</span>' if badge else ""
    return f"""
<div class="kpi-card">
  <div class="kpi-icon">{icon}</div>
  <div class="kpi-label">{label}</div>
  <div class="kpi-value">{value}</div>
  <div class="kpi-sub">{sub}{badge_html}</div>
</div>"""


def score_ring(score: int, label: str = "Health Score") -> str:
    r = 38
    circ = 2 * 3.14159 * r
    arc = circ * score / 100
    color = "#4ade80" if score >= 70 else "#fb923c" if score >= 45 else "#f87171"
    return f"""
<div class="score-ring-wrap">
  <div class="score-ring">
    <svg width="90" height="90" viewBox="0 0 90 90">
      <circle cx="45" cy="45" r="{r}" fill="none" stroke="rgba(51,65,85,0.8)" stroke-width="7"/>
      <circle cx="45" cy="45" r="{r}" fill="none" stroke="{color}" stroke-width="7"
              stroke-dasharray="{arc:.1f} {circ:.1f}" stroke-linecap="round"/>
    </svg>
    <div class="score-ring-label">
      <div class="score-ring-num">{score}</div>
      <div class="score-ring-txt">{label}</div>
    </div>
  </div>
</div>"""


def progress_bar(label: str, value: float, max_val: float = 5.0) -> str:
    pct = min(100, round(value / max_val * 100))
    display = f"{value:.1f} / {max_val:.0f}"
    return f"""
<div class="prog-wrap">
  <div class="prog-label-row"><span>{label}</span><span>{display}</span></div>
  <div class="prog-track"><div class="prog-fill" style="width:{pct}%"></div></div>
</div>"""


def tag(text: str, category: str = "other") -> str:
    cat_map = {"Price": "price", "Timeline": "timeline", "Trust": "trust",
               "Logistics": "logistics"}
    cls = cat_map.get(category, "other")
    return f'<span class="obj-tag tag-{cls}">{text}</span>'


def section_title(text: str) -> str:
    return f'<div class="section-title">{text}</div>'


def dim_card(title: str, content: str) -> str:
    return f"""
<div class="dim-card">
  <div class="dim-card-title">{title}</div>
  <p>{content}</p>
</div>"""


def action_item(n: int, text: str) -> str:
    return f"""
<div class="action-item">
  <div class="action-num">{n}</div>
  <div class="action-text">{text}</div>
</div>"""


# ══════════════════════════════════════════════
# 診斷結果渲染
# ══════════════════════════════════════════════

def render_results(d: dict):
    meta  = d.get("meta", {})
    sfg   = d.get("sales_funnel_gaps", {})
    ma    = d.get("marketing_automation", {})
    pd_   = d.get("product_differentiation", {})
    oa    = d.get("objection_analysis", {})
    roi   = d.get("roi_projection", {})

    # ── Health Score & KPI Cards ──────────────────
    score = meta.get("overall_health_score", 0)
    label = meta.get("overall_health_label", "")

    col_ring, col_kpis = st.columns([1, 3])
    with col_ring:
        st.markdown(score_ring(score, label), unsafe_allow_html=True)

    with col_kpis:
        cr = sfg.get("current_conversion_rate_percent", 0)
        bm = sfg.get("benchmark_conversion_rate_percent", 0)
        leak = sfg.get("estimated_monthly_revenue_leak_twd", 0)
        mat  = ma.get("overall_maturity_score", 0)
        oi   = oa.get("objections", [])

        cr_type = "good" if cr >= bm else "bad"
        grid_html = '<div class="kpi-grid">'
        grid_html += kpi_card("📈", "Conversion Rate", f"{cr:.1f}%",
                               f"Benchmark {bm:.1f}%",
                               badge=f"{abs(cr - bm):.1f}% below" if cr < bm else "On Target",
                               badge_type=cr_type)
        grid_html += kpi_card("🔥", "Monthly Revenue Leak", f"${leak/1000:.1f}K",
                               "Est. Opportunity Loss", badge_type="bad",
                               badge="Urgent")
        grid_html += kpi_card("⚙️", "Automation Maturity", f"{mat:.1f}",
                               "Out of 5.0",
                               badge=f"Level {int(mat)}", badge_type="warn" if mat < 3 else "good")
        grid_html += kpi_card("🗣️", "Objections", str(len(oi)),
                               "Identified & Analyzed", badge_type="warn",
                               badge="Training Needed")
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Executive Summary ─────────────────────────────
    st.markdown(section_title("💡 Executive Summary"), unsafe_allow_html=True)
    st.markdown(dim_card("Executive Summary", meta.get("executive_summary", "N/A")),
                unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Sales Funnel & Automation ──────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown(section_title("🔻 Sales Funnel Gaps"), unsafe_allow_html=True)
        for g in sfg.get("top_gaps", [])[:3]:
            sev = g.get("severity", "")
            sev_trans = {"高": "High", "中": "Medium", "低": "Low"}.get(sev, sev)
            sev_color = {"High": "#f87171", "Medium": "#fb923c", "Low": "#4ade80", "高": "#f87171", "中": "#fb923c", "低": "#4ade80"}.get(sev, "#94a3b8")
            content = (f'<b style="color:{sev_color}">■ {sev_trans} Severity</b><br>'
                       f'{g.get("gap_description","")}<br>'
                       f'<span style="color:#475569;font-size:0.75rem">💡 {g.get("recommended_action","")}</span>')
            st.markdown(dim_card(f'#{g.get("rank","")} {g.get("stage","")}', content),
                        unsafe_allow_html=True)

    with col_r:
        st.markdown(section_title("⚙️ Automation Maturity"), unsafe_allow_html=True)
        sub = ma.get("sub_scores", {})
        label_map = {"lead_capture": "Lead Capture", "lead_nurturing": "Lead Nurturing",
                     "quoting_process": "Quoting", "follow_up": "Follow-up", "reporting": "Reporting"}
        bars = "".join(progress_bar(label_map.get(k, k), v) for k, v in sub.items())
        st.markdown(f'<div class="dim-card">'
                    f'<div class="dim-card-title">⚙️ Maturity Scores</div>{bars}</div>',
                    unsafe_allow_html=True)

        for opp in ma.get("top_opportunities", [])[:2]:
            content = (f'{opp.get("current_state","")}<br>'
                       f'<span style="color:#60a5fa">→ Recommended: {opp.get("recommended_tool_type","")}</span><br>'
                       f'<span style="color:#4ade80">Saves {opp.get("estimated_weekly_time_savings_hours",0)} hrs/week</span>')
            st.markdown(dim_card(f'💡 {opp.get("area","")}', content), unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── 差異化 & 反對意見（左右欄）──────────
    col_l2, col_r2 = st.columns(2)

    with col_l2:
        st.markdown(section_title("🎯 Product Differentiation"), unsafe_allow_html=True)
        risk  = pd_.get("commoditization_risk", "")
        risk_trans = {"高": "High", "中": "Medium", "低": "Low"}.get(risk, risk)
        risk_color = {"High": "#f87171", "Medium": "#fb923c", "Low": "#4ade80", "高": "#f87171", "中": "#fb923c", "低": "#4ade80"}.get(risk, "#94a3b8")
        st.markdown(
            dim_card("Current Assessment",
                     f'<b style="color:{risk_color}">Commoditization Risk: {risk_trans}</b><br>'
                     f'{pd_.get("current_strategy_assessment","")}'),
            unsafe_allow_html=True)
        for angle in pd_.get("untapped_angles", [])[:3]:
            st.markdown(f'<div class="action-item"><div class="action-num">→</div>'
                        f'<div class="action-text">{angle}</div></div>',
                        unsafe_allow_html=True)

    with col_r2:
        st.markdown(section_title("🗣️ Customer Objections"), unsafe_allow_html=True)
        for obj in oa.get("objections", [])[:4]:
            otype = obj.get("type", "")
            eff   = obj.get("current_rebuttal_effectiveness", "")
            eff_color = {"Strong": "#4ade80", "Moderate": "#fb923c", "Weak": "#f87171"}.get(eff, "#94a3b8")
            rebuttal = obj.get("recommended_rebuttal_en", obj.get("recommended_rebuttal_zh", ""))
            st.markdown(
                f'<div class="obj-row">'
                f'<div class="obj-text">{tag(otype, otype)} '
                f'<span style="color:{eff_color};font-size:0.72rem;font-weight:600">{eff}</span><br>'
                f'"{obj.get("objection_text","")[:60]}..."</div>'
                f'<div class="obj-rebuttal">{rebuttal}</div>'
                f'</div>',
                unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── ROI Projection ─────────────────────────────
    st.markdown(section_title("💰 12-Month ROI Projection"), unsafe_allow_html=True)
    baseline = roi.get("baseline", {})
    target   = roi.get("target", {})
    incr     = roi.get("incremental_annual_revenue_twd", 0)
    cmin     = roi.get("estimated_implementation_cost_min_twd", 0)
    cmax     = roi.get("estimated_implementation_cost_max_twd", 0)
    payback  = roi.get("payback_period_months", 0)
    conf     = roi.get("confidence_level", "")
    conf_trans = {"高": "High", "中": "Medium", "低": "Low"}.get(conf, conf)

    def ntd(v): return f"${int(v)/1000:,.1f}K" if v else "N/A"

    roi_html = f"""
<div class="dim-card">
  <table class="roi-table">
    <tr><th>Metric</th><th>Current Baseline</th><th>Target</th><th>Change</th></tr>
    <tr>
      <td>Close Rate</td>
      <td>{baseline.get('close_rate_percent',0):.1f}%</td>
      <td>{target.get('close_rate_percent',0):.1f}%</td>
      <td class="highlight">+{target.get('close_rate_percent',0)-baseline.get('close_rate_percent',0):.1f}%</td>
    </tr>
    <tr>
      <td>Monthly Deals</td>
      <td>{baseline.get('monthly_deals_closed',0)} deals</td>
      <td>{target.get('monthly_deals_closed',0)} deals</td>
      <td class="highlight">+{target.get('monthly_deals_closed',0)-baseline.get('monthly_deals_closed',0)} deals</td>
    </tr>
    <tr>
      <td>Monthly Revenue</td>
      <td>{ntd(baseline.get('monthly_revenue_twd',0))}</td>
      <td>{ntd(target.get('monthly_revenue_twd',0))}</td>
      <td class="highlight">+{ntd(target.get('monthly_revenue_twd',0)-baseline.get('monthly_revenue_twd',0))}</td>
    </tr>
    <tr>
      <td><b>Annual Growth</b></td><td colspan="2">—</td>
      <td class="highlight" style="font-size:1rem">{ntd(incr)}</td>
    </tr>
    <tr>
      <td>Setup Cost</td><td colspan="2">{ntd(cmin)} ~ {ntd(cmax)}</td>
      <td style="color:#60a5fa">Payback {payback:.1f} mo</td>
    </tr>
    <tr>
      <td>Confidence</td><td colspan="3" style="color:#a78bfa">{conf_trans} — {roi.get('confidence_rationale','')}</td>
    </tr>
  </table>
</div>"""
    st.markdown(roi_html, unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Action Plan ─────────────────────────────
    st.markdown(section_title("🗺️ Priority Action Plan"), unsafe_allow_html=True)
    tabs = st.tabs(["⚡ Short-Term (0–30 Days)", "🔧 Medium-Term (1–3 Months)", "🚀 Long-Term (3–12 Months)"])

    short_actions = [g.get("recommended_action") for g in sfg.get("top_gaps", []) if g.get("severity") in ("High", "高")]
    short_actions += [f"Deploy {o.get('recommended_tool_type','')} for '{o.get('area','')}'"
                      for o in ma.get("top_opportunities", []) if o.get("implementation_complexity") == "Low"]
    crit_obj = next((o for o in oa.get("objections", []) if o.get("training_priority") == "Critical"), None)
    if crit_obj:
        short_actions.append(f"Training workshop for '{crit_obj.get('type','')}' objections")

    mid_actions = [f"Setup {o.get('recommended_tool_type','')} system"
                   for o in ma.get("top_opportunities", []) if o.get("implementation_complexity") in ("Medium", "High", "中", "高")]
    mid_actions += pd_.get("recommendations", [])[:2]

    long_actions = [
        "Build customer health score models to predict churn risk",
        "Develop GTM strategy for new markets based on existing profile",
        "Implement AI quotation system to ensure speed and consistency",
        "Scale successful sales techniques into a repeatable Playbook",
    ]

    with tabs[0]:
        for i, a in enumerate(short_actions[:5], 1):
            st.markdown(action_item(i, a), unsafe_allow_html=True)
        if not short_actions:
            st.markdown(action_item(1, "Establish unified sales tracking SOP"), unsafe_allow_html=True)

    with tabs[1]:
        for i, a in enumerate(mid_actions[:5], 1):
            st.markdown(action_item(i, a), unsafe_allow_html=True)
        if not mid_actions:
            st.markdown(action_item(1, "Evaluate and select CRM tools"), unsafe_allow_html=True)

    with tabs[2]:
        for i, a in enumerate(long_actions, 1):
            st.markdown(action_item(i, a), unsafe_allow_html=True)


# ══════════════════════════════════════════════
# 報告下載區
# ══════════════════════════════════════════════

def download_section(diagnosis_data: dict):
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(section_title("⬇️ Download Results"), unsafe_allow_html=True)

    md_content = report_generator.render_report(diagnosis_data)
    pdf_bytes  = report_generator.generate_pdf_bytes(diagnosis_data)
    json_content = json.dumps(diagnosis_data, ensure_ascii=False, indent=2)
    company = diagnosis_data.get("meta", {}).get("company_name", "report")
    today   = datetime.date.today().strftime("%Y-%m-%d")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=f"{today}_{company}_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            label="📝 Download Markdown Report",
            data=md_content.encode("utf-8"),
            file_name=f"{today}_{company}_report.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            label="📊 Download Raw JSON",
            data=json_content.encode("utf-8"),
            file_name=f"{today}_{company}_diagnosis.json",
            mime="application/json",
            use_container_width=True,
        )


# ══════════════════════════════════════════════
# Streamlit 主程式
# ══════════════════════════════════════════════

st.set_page_config(
    page_title="AutoConsult AI — Business Diagnosis System",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(nav_bar(), unsafe_allow_html=True)
st.markdown(hero_section(), unsafe_allow_html=True)

# ── Upload Section ────────────────────────────────────
st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
st.markdown('<div class="upload-label">Step 1 — Upload Input Data</div>', unsafe_allow_html=True)

col_q, col_t = st.columns(2)
with col_q:
    st.markdown("**📋 Business Questionnaire**", help="JSON format including client_profile, pain_points, etc.")
    q_file = st.file_uploader("Questionnaire JSON", type=["json"], label_visibility="collapsed", key="q_upload")
with col_t:
    st.markdown("**🎙️ Interview Transcript**", help="TXT format of business interview recording")
    t_file = st.file_uploader("Transcript TXT", type=["txt"], label_visibility="collapsed", key="t_upload")

# File status indicator
pills = (file_pill("questionnaire.json", q_file is not None)
         + file_pill("transcript.txt", t_file is not None))
st.markdown(f'<div style="margin-top:0.75rem">{pills}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── LLM Provider Selection ────────────────────────────
st.markdown('<div class="upload-zone" style="border-style: solid; border-width: 1px;">', unsafe_allow_html=True)
st.markdown('<div class="upload-label">Step 2 — Configure AI Diagnostic Engine</div>', unsafe_allow_html=True)

ecol1, ecol2 = st.columns([1, 2])
with ecol1:
    provider = st.selectbox(
        "Select AI Model",
        ["groq", "gemini", "openai"],
        index=0,
        format_func=lambda x: {
            "groq":   "Groq (Fastest - LLaMA 3.3)",
            "gemini": "Google Gemini 2.0 Flash",
            "openai": "OpenAI GPT-4o",
        }[x],
    )
with ecol2:
    key_labels = {
        "groq":   ("Groq API Key (gsk_...)", "Enter your Groq Key (get at console.groq.com)"),
        "gemini": ("Gemini API Key (AIza...)", "Enter your Gemini Key (get at aistudio.google.com)"),
        "openai": ("OpenAI API Key (sk-...)", "Enter your OpenAI Key"),
    }
    key_label, key_placeholder = key_labels[provider]
    api_key_input = st.text_input(
        key_label,
        type="password",
        placeholder=key_placeholder,
        help="Our system does not store your API Key. It is used only for the current analysis session."
    )
    if api_key_input:
        import os
        env_var = {"groq": "GROQ_API_KEY", "gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY"}[provider]
        os.environ[env_var] = api_key_input
st.markdown('</div>', unsafe_allow_html=True)

# ── Diagnosis Button ─────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
btn_col = st.columns([1, 2, 1])[1]
with btn_col:
    start_btn = st.button("🚀  Start AI Diagnosis", use_container_width=True)

# ── Execute Diagnosis ─────────────────────────────────
if start_btn:
    if not q_file or not t_file:
        st.error("⚠️ Please upload both the questionnaire and transcript first.")
        st.stop()
    
    if not api_key_input:
        st.error(f"⚠️ Please enter your {provider.upper()} API Key to start.")
        st.stop()

    # Validate questionnaire format
    try:
        q_data = json.loads(q_file.getvalue().decode("utf-8"))
    except json.JSONDecodeError as e:
        st.error(f"❌ questionnaire.json format error: {e}")
        st.stop()

    required_fields = ["client_profile", "business_scale", "business_goals", "pain_points"]
    missing = [f for f in required_fields if f not in q_data]
    if missing:
        st.error(f"❌ Questionnaire is missing required fields: {', '.join(missing)}")
        st.stop()

    t_text = t_file.getvalue().decode("utf-8")
    if len(t_text.strip()) < 100:
        st.error("❌ Transcript content is too short. Please upload a full file.")
        st.stop()

    # 寫到臨時 inputs/ 覆蓋，讓 ai_analyzer 讀取
    tmp_q = PROJECT_ROOT / "inputs" / "questionnaire.json"
    tmp_t = PROJECT_ROOT / "inputs" / "transcript.txt"
    tmp_q.parent.mkdir(exist_ok=True)
    tmp_q.write_text(json.dumps(q_data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_t.write_text(t_text, encoding="utf-8")

    company_name = q_data.get("client_profile", {}).get("company_name", "Client")

    with st.spinner(f"🤖 AI is analyzing business data for '{company_name}', please wait..."):
        try:
            result = ai_analyzer.run(provider=provider, dry_run=False)
        except EnvironmentError as e:
            st.error(f"❌ API Key Error: {e}")
            st.stop()
        except Exception as e:
            st.error(f"❌ Error during analysis: {e}")
            st.stop()

    if result:
        st.session_state["diagnosis"] = result
        st.success(f"✅ Diagnosis Complete! Health Score: {result.get('meta', {}).get('overall_health_score', 'N/A')} / 100")

# ── Display Results ─────────────────────────────────
if "diagnosis" in st.session_state:
    d = st.session_state["diagnosis"]
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown(section_title("📊 Diagnosis Results Dashboard"), unsafe_allow_html=True)
    render_results(d)
    download_section(d)

# ── Default Demonstration (Empty State) ────────────
elif not start_btn:
    st.markdown("""
<div style="text-align:center;padding:3rem 1rem;color:#334155">
  <div style="font-size:3rem;margin-bottom:1rem;opacity:0.4">⬡</div>
  <div style="font-size:0.9rem;opacity:0.5">Results will appear here after you upload files and click "Start Diagnosis"</div>
</div>""", unsafe_allow_html=True)
