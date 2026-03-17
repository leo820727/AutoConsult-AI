"""
AutoConsult AI — engine/report_generator.py
============================================
Diagnostic Report Generator

Responsibility:
  Receives diagnosis JSON from ai_analyzer.py,
  renders it into a complete Markdown and PDF professional report,
  and saves it to the outputs/ folder.

Standalone Usage (pass an existing JSON):
  python engine/report_generator.py outputs/2026-03-17_xxx_diagnosis.json
"""

import json
import sys
import datetime
from pathlib import Path
from typing import Optional

def _safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except (UnicodeEncodeError, UnicodeDecodeError):
        safe_args = [str(a).encode('ascii', errors='replace').decode('ascii') for a in args]
        print(*safe_args, **kwargs)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR  = PROJECT_ROOT / "outputs"


# ══════════════════════════════════════════════
# 工具函式：文字圖表產生器
# ══════════════════════════════════════════════

def bar_chart(value: float, max_value: float = 100, width: int = 20, fill: str = "█", empty: str = "░") -> str:
    """Generates an ASCII horizontal bar chart."""
    ratio     = max(0.0, min(1.0, value / max_value))
    filled    = round(ratio * width)
    bar       = fill * filled + empty * (width - filled)
    pct       = f"{value:.1f}"
    return f"[{bar}] {pct}"


def health_meter(score: int) -> str:
    """Generates a health meter dashboard (0–100)."""
    if score >= 80:
        icon = "🟢"
    elif score >= 60:
        icon = "🟡"
    elif score >= 40:
        icon = "🟠"
    else:
        icon = "🔴"
    bar = bar_chart(score, 100, width=25)
    return f"{icon}  {bar}  **{score} / 100**"


def funnel_diagram(conversion_rate: float, benchmark: float) -> str:
    """Generates a sales funnel diagram (Text version)."""
    lines = [
        "```",
        "  ┌─────────────────────────────┐",
        "  │       Potential Leads       │  100%",
        "  └──────────┬──────────────────┘",
        "             │ Quote Conversion",
        "  ┌──────────▼──────────┐",
        "  │    Quoted Pipeline   │  ~80% (Est.)",
        "  └──────────┬──────────┘",
        "             │ Negotiate / Closing",
        f"  ┌──────┬──────────┐",
        f"  │  Deals Closed   │  {conversion_rate:.1f}%  ⚠ Benchmark: {benchmark:.1f}%",
        "  └─────────────────┘",
        "```",
    ]
    return "\n".join(lines)


def maturity_radar(sub_scores: dict) -> str:
    """Generates a maturity radar table (Text version)."""
    label_map = {
        "lead_capture":    "Lead Capture",
        "lead_nurturing":  "Lead Nurturing",
        "quoting_process": "Quoting Process",
        "follow_up":       "Follow-up",
        "reporting":       "Reporting",
    }
    lines = ["| Dimension | Maturity (0–5) | Visualization |", "|------|-------------|--------|"]
    for key, label in label_map.items():
        score = sub_scores.get(key, 0)
        bar   = bar_chart(score, 5.0, width=10)
        lines.append(f"| {label} | {score:.1f} | `{bar}` |")
    return "\n".join(lines)


def severity_badge(severity: str) -> str:
    """Converts severity to Markdown badge style."""
    mapping = {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low", "高": "🔴 High", "中": "🟡 Medium", "低": "🟢 Low"}
    return mapping.get(severity, severity)


def priority_badge(priority: str) -> str:
    mapping = {
        "Critical": "🔴 Critical",
        "High":     "🟠 High",
        "Medium":   "🟡 Medium",
        "Low":      "🟢 Low",
    }
    return mapping.get(priority, priority)


def effectiveness_badge(eff: str) -> str:
    mapping = {
        "Strong":   "✅ Strong",
        "Moderate": "⚠️ Moderate",
        "Weak":     "❌ Weak",
    }
    return mapping.get(eff, eff)


def twd_fmt(value) -> str:
    """格式化新台幣金額。"""
    try:
        return f"NT$ {int(value):,}"
    except (TypeError, ValueError):
        return "N/A"


def _safe(data: dict, *keys, default="N/A"):
    """安全地從巢狀 dict 取值。"""
    cur = data
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
        if cur is None:
            return default
    return cur


# ══════════════════════════════════════════════
# 報告各章節渲染函式
# ══════════════════════════════════════════════

def render_header(data: dict, generated_at: str) -> str:
    meta = data.get("meta", {})
    company  = _safe(meta, "company_name")
    industry = _safe(meta, "industry")
    score    = meta.get("overall_health_score", 0)
    label    = _safe(meta, "overall_health_label")

    return f"""# 🏥 AutoConsult AI — Business Diagnosis Report

> **Client:** {company}　｜　**Industry:** {industry}
> **Generated:** {generated_at}　｜　**Analyzer Version:** {_safe(meta, "analyzer_version")}

---

## 📊 Overall Health Score

{health_meter(score)}

**Status Label: {label}**

---
"""


def render_executive_summary(data: dict) -> str:
    summary = _safe(data, "meta", "executive_summary")
    return f"""## 📋 Executive Summary

{summary}

---
"""


def render_sales_funnel(data: dict) -> str:
    sfg         = data.get("sales_funnel_gaps", {})
    current_cr  = sfg.get("current_conversion_rate_percent", 0)
    benchmark   = sfg.get("benchmark_conversion_rate_percent", 0)
    gap         = sfg.get("conversion_gap_percent", 0)
    leak        = sfg.get("estimated_monthly_revenue_leak_twd", 0)
    top_gaps    = sfg.get("top_gaps", [])

    gaps_md = ""
    for g in top_gaps:
        rank   = g.get("rank", "-")
        stage  = g.get("stage", "N/A")
        desc   = g.get("gap_description", "")
        evid   = g.get("evidence", "")
        sev    = severity_badge(g.get("severity", ""))
        action = g.get("recommended_action", "")
        gaps_md += f"""
### Gap #{rank}: {stage}  {sev}

**Problem Description:** {desc}

> 📎 **Direct Evidence:** *"{evid}"*

**Recommended Action:** {action}
"""

    return f"""## 🔻 Sales Funnel Gap Analysis

{funnel_diagram(current_cr, benchmark)}

| Metric | Value |
|------|------|
| Current Conversion Rate | **{current_cr:.1f}%** |
| Industry Benchmark | {benchmark:.1f}% |
| Gap to Benchmark | 🔴 **{gap:.1f}%** |
| Est. Monthly Revenue Leak | 🔴 {twd_fmt(leak)} |

### 🔍 Top 3 Funnel Gaps
{gaps_md}
---
"""


def render_automation(data: dict) -> str:
    ma       = data.get("marketing_automation", {})
    overall  = ma.get("overall_maturity_score", 0)
    label    = _safe(ma, "maturity_label")
    sub      = ma.get("sub_scores", {})
    opps     = ma.get("top_opportunities", [])

    opps_md = ""
    for i, opp in enumerate(opps, 1):
        area       = opp.get("area", "N/A")
        current    = opp.get("current_state", "")
        tool       = opp.get("recommended_tool_type", "")
        saving     = opp.get("estimated_weekly_time_savings_hours", 0)
        complexity = opp.get("implementation_complexity", "")
        opps_md += f"""
**{i}. {area}**
- Current State: {current}
- Recommended Tool Type: `{tool}`
- Weekly Time Saving: **{saving} hours**
- Implementation Complexity: {complexity}
"""

    return f"""## ⚙️ Marketing Automation Maturity

**Overall Score: {overall:.1f} / 5.0　｜　{label}**

```
Overall Maturity: {bar_chart(overall, 5.0, width=25)}
```

### Sub-dimension Scores

{maturity_radar(sub)}

### 🚀 Highest Value Automation Opportunities
{opps_md}
---
"""


def render_differentiation(data: dict) -> str:
    pd        = data.get("product_differentiation", {})
    risk      = _safe(pd, "commoditization_risk")
    strategy  = _safe(pd, "current_strategy_assessment")
    score     = pd.get("messaging_consistency_score", 0)
    untapped  = pd.get("untapped_angles", [])
    recs      = pd.get("recommendations", [])

    risk_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢", "高": "🔴", "中": "🟡", "低": "🟢"}.get(risk, "⚪")
    untapped_md = "\n".join(f"- 💡 {a}" for a in untapped) if untapped else "- (Insufficient data)"
    recs_md     = "\n".join(f"- ✅ {r}" for r in recs) if recs else "- (Insufficient data)"

    return f"""## 🎯 Product Differentiation Analysis

| Metric | Assessment |
|------|------|
| Commoditization Risk | {risk_icon} **{risk}** |
| Messaging Consistency Score | `{bar_chart(score, 100, width=15)}` |

**Current Differentiation Assessment:**
{strategy}

### 🔓 Untapped Differentiation Angles
{untapped_md}

### 📌 Strengthening Recommendations
{recs_md}

---
"""


def render_objections(data: dict) -> str:
    oa         = data.get("objection_analysis", {})
    objections = oa.get("objections", [])
    top_area   = _safe(oa, "highest_priority_training_area")

    if not objections:
        return """## 🗣️ Objection Analysis\n\n> ⚠️ No sufficient objection data extracted from the interview.\n\n---\n"""

    rows = "| # | Objection | Type | Current Effectiveness | Training Priority |\n|---|---------|------|------------|----------|\n"
    for i, obj in enumerate(objections, 1):
        text   = obj.get("objection_text", "")[:30] + "…"
        otype  = obj.get("type", "")
        eff    = effectiveness_badge(obj.get("current_rebuttal_effectiveness", ""))
        prio   = priority_badge(obj.get("training_priority", ""))
        rows  += f"| {i} | {text} | `{otype}` | {eff} | {prio} |\n"

    details_md = ""
    for i, obj in enumerate(objections, 1):
        text     = obj.get("objection_text", "N/A")
        rebuttal = obj.get("recommended_rebuttal_en", obj.get("recommended_rebuttal_zh", "N/A"))
        prio     = priority_badge(obj.get("training_priority", ""))
        details_md += f"""
<details>
<summary>🗨️ Objection #{i}: "{text[:40]}…"　{prio}</summary>

**Full Text:** {text}

**📣 Recommended Rebuttal:**
> {rebuttal}

</details>
"""

    return f"""## 🗣️ Objection Analysis

{rows}

### 🎓 Rebuttal Details (Collapsible)
{details_md}

> 🏆 **Highest Training Priority Area:** {top_area}

---
"""


def render_roi(data: dict) -> str:
    roi      = data.get("roi_projection", {})
    baseline = roi.get("baseline", {})
    target   = roi.get("target", {})

    b_leads   = baseline.get("monthly_leads", 0)
    b_rate    = baseline.get("close_rate_percent", 0)
    b_deals   = baseline.get("monthly_deals_closed", 0)
    b_rev     = baseline.get("monthly_revenue_twd", 0)

    t_leads   = target.get("monthly_leads", 0)
    t_rate    = target.get("close_rate_percent", 0)
    t_deals   = target.get("monthly_deals_closed", 0)
    t_rev     = target.get("monthly_revenue_twd", 0)

    incr      = roi.get("incremental_annual_revenue_twd", 0)
    cost_min  = roi.get("estimated_implementation_cost_min_twd", 0)
    cost_max  = roi.get("estimated_implementation_cost_max_twd", 0)
    payback   = roi.get("payback_period_months", 0)
    conf      = _safe(roi, "confidence_level")
    rationale = _safe(roi, "confidence_rationale")

    conf_icon = {"High": "🟢", "Medium": "🟡", "Low": "🔴", "高": "🟢", "中": "🟡", "低": "🔴"}.get(conf, "⚪")

    return f"""## 💰 12-Month ROI Projection

| Metric | Baseline | Target (Conservative) | Growth |
|------|---------|--------------|------|
| Monthly Leads | {b_leads} | {t_leads} | +{t_leads - b_leads} |
| Monthly Close Rate | {b_rate:.1f}% | {t_rate:.1f}% | +{t_rate - b_rate:.1f}% |
| Monthly Deals Closed | {b_deals} | {t_deals} | +{t_deals - b_deals} |
| Monthly Revenue | {twd_fmt(b_rev)} | {twd_fmt(t_rev)} | +{twd_fmt(t_rev - b_rev)} |

```
Est. Annual Revenue Uplift: {twd_fmt(incr)}
Implementation Cost Range: {twd_fmt(cost_min)} ~ {twd_fmt(cost_max)}
Est. Payback Period:      {payback:.1f} months
```

**Confidence Level: {conf_icon} {conf}**

> {rationale}

---
"""


def render_action_plan(data: dict) -> str:
    """
    Dynamically generates short, medium, and long-term action plans based on diagnosis.
    Consolidates from recommended_action / recommendations across all dimensions.
    """
    sfg  = data.get("sales_funnel_gaps", {})
    ma   = data.get("marketing_automation", {})
    pd_  = data.get("product_differentiation", {})
    oa   = data.get("objection_analysis", {})

    # ── Short Term (0–30 Days) Quick Wins ──────────────
    short_term = []
    for g in sfg.get("top_gaps", []):
        if g.get("severity") in ("High", "高"):
            short_term.append(f"📌 **[Sales Funnel]** {g.get('recommended_action', '')}")
    for opp in ma.get("top_opportunities", []):
        if opp.get("implementation_complexity") == "Low":
            short_term.append(f"📌 **[Automation]** Deploy `{opp.get('recommended_tool_type', '')}` for \"{opp.get('area', '')}\"")
    top_obj = next((o for o in oa.get("objections", []) if o.get("training_priority") == "Critical"), None)
    if top_obj:
        short_term.append(f"📌 **[Training]** Skills workshop for \"{top_obj.get('type', '')}\" objections")
    if not short_term:
        short_term.append("📌 Establish standardized sales tracking SOP")

    # ── Medium Term (1–3 Months) System Building ───────────────
    mid_term = []
    for opp in ma.get("top_opportunities", []):
        if opp.get("implementation_complexity") in ("Medium", "High", "中", "高"):
            mid_term.append(f"🔧 **[Automation]** Setup `{opp.get('recommended_tool_type', '')}` system")
    for rec in pd_.get("recommendations", []):
        mid_term.append(f"🔧 **[Differentiation]** {rec}")
    for g in sfg.get("top_gaps", []):
        if g.get("severity") in ("Medium", "中"):
            mid_term.append(f"🔧 **[Sales Funnel]** {g.get('recommended_action', '')}")
    if not mid_term:
        mid_term.append("🔧 Select and implement CRM tool")

    # ── Long Term (3–12 Months) Strategic Growth ──────────────
    long_term = [
        "🚀 **[Scaling]** Build customer health score models based on CRM data to predict churn",
        "🚀 **[Expansion]** Develop GTM strategy for new markets based on existing customer profiles",
        "🚀 **[AI Upgrade]** Implement AI-assisted quotation system to improve consistency and speed",
        "🚀 **[Team Playbook]** Systematize successful top-sales techniques into an evergreen Playbook",
    ]

    short_md = "\n".join(f"- {s}" for s in short_term[:4])
    mid_md   = "\n".join(f"- {m}" for m in mid_term[:4])
    long_md  = "\n".join(f"- {l}" for l in long_term)

    return f"""## 🗺️ Action Plan Roadmap

### ⚡ Short-Term Quick Wins (0–30 Days)
> Goal: Immediate impact, addressing high-severity friction points.

{short_mid if (short_mid := short_md) else "- See specific recommendations in diagnostic chapters"}

---

### 🔧 Medium-Term System Building (1–3 Months)
> Goal: Close tool gaps, establish repeatable processes.

{mid_md if mid_md else "- See Marketing Automation chapter"}

---

### 🚀 Long-Term Strategic Growth (3–12 Months)
> Goal: Scaling, predictability, and market expansion.

{long_md}

---
"""


def render_footer(generated_at: str) -> str:
    return f"""## ℹ️ Report Information

| Item | Description |
|------|------|
| Generated by | AutoConsult AI Automated Diagnostic Engine |
| Generated at | {generated_at} |
| Data Sources | inputs/questionnaire.json, inputs/transcript.txt |
| Disclaimer | This report is AI-assisted. Consult human advisors for final decisions. |

---
*© 2026 AutoConsult AI — All rights reserved.*
"""


# ══════════════════════════════════════════════
# 主渲染函式
# ══════════════════════════════════════════════

def render_report(diagnosis_data: dict) -> str:
    """
    將完整的診斷 JSON 渲染為 Markdown 報告字串。
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sections = [
        render_header(diagnosis_data, now),
        render_executive_summary(diagnosis_data),
        render_sales_funnel(diagnosis_data),
        render_automation(diagnosis_data),
        render_differentiation(diagnosis_data),
        render_objections(diagnosis_data),
        render_roi(diagnosis_data),
        render_action_plan(diagnosis_data),
        render_footer(now),
    ]
    return "\n".join(sections)


# ══════════════════════════════════════════════
# 檔案儲存
# ══════════════════════════════════════════════

def save_report(diagnosis_data: dict, markdown_content: str) -> Path:
    """
    Saves the Markdown report to outputs/.
    Filename matches the diagnosis JSON but with .md extension.
    """
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    today    = datetime.date.today().strftime("%Y-%m-%d")
    company  = diagnosis_data.get("meta", {}).get("company_name", "unknown")
    safe_co  = "".join(c for c in company if c not in r'\/:*?"<>|')
    filename = f"{today}_{safe_co}_report.md"
    out_path = OUTPUTS_DIR / filename

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    _safe_print(f"[OK] Markdown report saved: {out_path}")
    return out_path


# ══════════════════════════════════════════════
# PDF 生成
# ══════════════════════════════════════════════

def _find_cjk_font() -> tuple[str, str]:
    """
    尋找系統 CJK 字型。
    回傳 (font_path, font_name)，找不到則回傳 (None, None)。
    """
    import os
    candidates = [
        # Windows — Traditional Chinese
        (r"C:\Windows\Fonts\msjh.ttc",    "MSJH"),       # Microsoft JhengHei
        (r"C:\Windows\Fonts\mingliu.ttc", "MingLiU"),    # 細明體
        (r"C:\Windows\Fonts\kaiu.ttf",    "KaiU"),       # 標楷體
        # Windows — Simplified / Any CJK
        (r"C:\Windows\Fonts\msyh.ttc",    "MSYH"),       # Microsoft YaHei
        # macOS
        ("/System/Library/Fonts/PingFang.ttc", "PingFang"),
        ("/Library/Fonts/Arial Unicode MS.ttf", "ArialUni"),
    ]
    for path, name in candidates:
        if os.path.exists(path):
            return path, name
    return None, None


def generate_pdf_bytes(data: dict) -> bytes:
    """
    Renders diagnostic JSON as PDF (A4), returns bytes for Streamlit download.
    Requires reportlab: py -m pip install reportlab
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, PageBreak
        )
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        from reportlab.pdfbase.ttfonts import TTFont
        from io import BytesIO
    except ImportError:
        raise ImportError("請安裝 reportlab：py -m pip install reportlab")

    # ── 字型設定 ────────────────────────────────
    FONT_NORMAL = "Helvetica"
    FONT_BOLD   = "Helvetica-Bold"

    font_path, font_name = _find_cjk_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            FONT_NORMAL = font_name
            FONT_BOLD   = font_name
        except Exception:
            pass  # 字型載入失敗則 fallback 到 Helvetica

    # 若無系統 CJK 字型，使用 ReportLab 內建 CID
    if FONT_NORMAL == "Helvetica":
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            FONT_NORMAL = "STSong-Light"
            FONT_BOLD   = "STSong-Light"
        except Exception:
            pass

    # ── 顏色定義 ─────────────────────────────────
    C_NAVY    = colors.HexColor("#0d1f3c")
    C_BLUE    = colors.HexColor("#2563eb")
    C_LIGHT   = colors.HexColor("#f1f5f9")
    C_MUTED   = colors.HexColor("#64748b")
    C_GREEN   = colors.HexColor("#16a34a")
    C_RED     = colors.HexColor("#dc2626")
    C_ORANGE  = colors.HexColor("#ea580c")
    C_WHITE   = colors.white

    W = A4[0] - 40*mm   # usable width

    # ── Styles ──────────────────────────────────
    def S(name, font=None, size=10, leading=None, color=colors.black,
          align=TA_LEFT, space_before=0, space_after=2, bold=False):
        f = font or (FONT_BOLD if bold else FONT_NORMAL)
        return ParagraphStyle(
            name, fontName=f, fontSize=size,
            leading=leading or size * 1.4,
            textColor=color, alignment=align,
            spaceBefore=space_before * mm,
            spaceAfter=space_after * mm,
        )

    s_title    = S("title",    size=22, color=C_WHITE,  align=TA_CENTER, bold=True, leading=28)
    s_subtitle = S("subtitle", size=11, color=C_LIGHT,  align=TA_CENTER, space_after=4)
    s_h1       = S("h1",       size=14, color=C_NAVY,   bold=True, space_before=4, space_after=2)
    s_body     = S("body",     size=9,  color=colors.HexColor("#334155"), space_after=1)
    s_kpi_lbl  = S("kpi_lbl",  size=7.5,color=C_MUTED,  align=TA_CENTER)

    def tbl_style(header_color=C_NAVY, alt_color=colors.HexColor("#f8fafc")):
        return TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0),  header_color),
            ("TEXTCOLOR",    (0, 0), (-1, 0),  C_WHITE),
            ("FONTNAME",     (0, 0), (-1, 0),  FONT_BOLD),
            ("FONTSIZE",     (0, 0), (-1, -1), 8),
            ("FONTNAME",     (0, 1), (-1, -1), FONT_NORMAL),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, alt_color]),
            ("GRID",         (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ])

    # ── 資料提取 ────────────────────────────────
    meta   = data.get("meta", {})
    sfg    = data.get("sales_funnel_gaps", {})
    ma     = data.get("marketing_automation", {})
    pd_    = data.get("product_differentiation", {})
    oa     = data.get("objection_analysis", {})
    roi    = data.get("roi_projection", {})

    company = meta.get("company_name", "N/A")
    score   = meta.get("overall_health_score", 0)
    label   = meta.get("overall_health_label", "")
    summary = meta.get("executive_summary", "")
    score_color = C_GREEN if score >= 70 else C_ORANGE if score >= 45 else C_RED
    now_str     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    def ntd(v):
        try: return f"NT$ {int(v):,}"
        except: return "N/A"

    story = []

    # Cover Page
    cover_data = [
        [Paragraph("AutoConsult AI — Business Diagnosis Report", s_title)],
        [Spacer(1, 4*mm)],
        [Paragraph(company, S("cv2", size=16, color=C_LIGHT, align=TA_CENTER, bold=True))],
        [Spacer(1, 2*mm)],
        [Paragraph(f"Generated at: {now_str}", s_subtitle)],
    ]
    cover_tbl = Table(cover_data, colWidths=[W])
    cover_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), C_NAVY),
        ("TOPPADDING",  (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(cover_tbl)
    story.append(Spacer(1, 8*mm))

    # Health Score
    score_data = [[
        Paragraph(f"{score}", S("sc", size=40, color=score_color, bold=True, align=TA_CENTER)),
        Paragraph(f"Overall Health Rating: {label}", S("sl", size=12, color=C_MUTED, align=TA_LEFT)),
    ]]
    score_tbl = Table(score_data, colWidths=[40*mm, W-40*mm])
    score_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(score_tbl)
    story.append(Spacer(1, 5*mm))

    # KPI Row
    cr   = sfg.get("current_conversion_rate_percent", 0)
    leak = sfg.get("estimated_monthly_revenue_leak_twd", 0)
    mat  = ma.get("overall_maturity_score", 0)
    n_obj= len(oa.get("objections", []))

    kpi_data = [[
        Paragraph(f"{cr:.1f}%", S("k1", size=18, color=C_BLUE, bold=True, align=TA_CENTER)),
        Paragraph(f"${leak/1e3:.0f}K", S("k2", size=18, color=C_RED, bold=True, align=TA_CENTER)),
        Paragraph(f"{mat:.1f}/5", S("k3", size=18, color=C_ORANGE, bold=True, align=TA_CENTER)),
        Paragraph(f"{n_obj}", S("k4", size=18, color=colors.purple, bold=True, align=TA_CENTER)),
    ],[
        Paragraph("Conversion Rate", s_kpi_lbl),
        Paragraph("Monthly Revenue Leak", s_kpi_lbl),
        Paragraph("Automation Maturity", s_kpi_lbl),
        Paragraph("Identified Objections", s_kpi_lbl),
    ]]
    kpi_tbl = Table(kpi_data, colWidths=[W/4]*4)
    story.append(kpi_tbl)
    story.append(Spacer(1, 5*mm))

    # Executive Summary
    story.append(Paragraph("Executive Summary", s_h1))
    story.append(HRFlowable(width=W, thickness=1, color=C_BLUE))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(summary, s_body))
    story.append(PageBreak())

    # Sales Funnel
    story.append(Paragraph("Sales Funnel Gap Analysis", s_h1))
    story.append(HRFlowable(width=W, thickness=1, color=C_BLUE))
    story.append(Spacer(1, 2*mm))

    gap_rows = [["Rank", "Stage", "Severity", "Description", "Action"]]
    for g in sfg.get("top_gaps", []):
        gap_rows.append([
            str(g.get("rank", "")),
            g.get("stage", ""),
            g.get("severity", ""),
            Paragraph(g.get("gap_description", ""), s_body),
            Paragraph(g.get("recommended_action", ""), s_body),
        ])
    if len(gap_rows) > 1:
        gt = Table(gap_rows, colWidths=[12*mm, 25*mm, 15*mm, W*0.35, W*0.28])
        gt.setStyle(tbl_style())
        story.append(gt)
    story.append(Spacer(1, 5*mm))

    # ROI
    story.append(Paragraph("12-Month ROI Projection", s_h1))
    story.append(HRFlowable(width=W, thickness=1, color=C_BLUE))
    story.append(Spacer(1, 2*mm))

    baseline = roi.get("baseline", {})
    target   = roi.get("target", {})
    incr     = roi.get("incremental_annual_revenue_twd", 0)
    payback  = roi.get("payback_period_months", 0)

    roi_rows = [
        ["Metric", "Baseline", "Target (Est.)", "Uplift"],
        ["Close Rate", f"{baseline.get('close_rate_percent',0):.1f}%", f"{target.get('close_rate_percent',0):.1f}%", f"+{target.get('close_rate_percent',0)-baseline.get('close_rate_percent',0):.1f}%"],
        ["Monthly Rev", f"${baseline.get('monthly_revenue_twd',0)/1e3:.1f}K", f"${target.get('monthly_revenue_twd',0)/1e3:.1f}K", f"+${(target.get('monthly_revenue_twd',0)-baseline.get('monthly_revenue_twd',0))/1e3:.1f}K"],
        ["Annual Growth", "—", "—", f"${incr/1e3:.1f}K"],
        ["Payback Period", "—", "—", f"{payback:.1f} months"],
    ]
    roi_tbl = Table(roi_rows, colWidths=[W/4]*4)
    roi_tbl.setStyle(tbl_style(C_NAVY))
    story.append(roi_tbl)

    # Footer
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width=W, thickness=0.5, color=C_MUTED))
    story.append(Paragraph(
        f"Generated by AutoConsult AI Diagnostic Engine · {now_str} · Confidential",
        S("ft", size=7, color=C_MUTED, align=TA_CENTER)
    ))

    # ── Build PDF ───────────────────────────────
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm
    )
    doc.build(story)
    return buf.getvalue()


# ══════════════════════════════════════════════
# 公開 API（供 main.py 呼叫）
# ══════════════════════════════════════════════

def generate_from_dict(diagnosis_data: dict) -> Path:
    """從已解析的診斷 dict 生成報告，回傳輸出路徑。"""
    md = render_report(diagnosis_data)
    return save_report(diagnosis_data, md)


def generate_from_json_file(json_path: Path) -> Path:
    """從磁碟上的診斷 JSON 檔生成報告。"""
    if not json_path.exists():
        raise FileNotFoundError(f"找不到診斷 JSON 檔：{json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return generate_from_dict(data)


# ══════════════════════════════════════════════
# Standalone Execution Entry
# ══════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Auto-detect latest JSON in outputs/
        json_files = sorted(OUTPUTS_DIR.glob("*_diagnosis.json"), reverse=True)
        if not json_files:
            print("[X] No diagnosis JSON found. Run main.py or ai_analyzer.py first.")
            sys.exit(1)
        target = json_files[0]
        print(f"[->] Auto-detecting latest result: {target.name}")
    else:
        target = Path(sys.argv[1])

    try:
        out = generate_from_json_file(target)
        print(f"[OK] Complete! Report path: {out}")
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"[X] Report generation failed: {e}", file=sys.stderr)
        sys.exit(1)
