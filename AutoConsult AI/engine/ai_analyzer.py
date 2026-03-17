"""
AutoConsult AI — engine/ai_analyzer.py
========================================
Core AI Analysis Engine

Responsibilities:
  1. Load questionnaire (questionnaire.json) and transcript (transcript.txt) from inputs/
  2. Construct System Prompt and User Prompt
  3. Call LLM (Groq / Google Gemini / OpenAI GPT-4o) for business diagnosis
  4. Parse and validate the returned JSON results
  5. Write results to the outputs/ folder

Usage:
  python engine/ai_analyzer.py                    # Use default (Gemini)
  python engine/ai_analyzer.py --provider groq    # Switch to Groq (Fastest)
  python engine/ai_analyzer.py --provider gemini  # Switch to Google Gemini
  python engine/ai_analyzer.py --provider openai  # Switch to OpenAI GPT-4o
  python engine/ai_analyzer.py --dry-run          # Print prompt only
"""

import argparse
import io
import json
import os
import sys
import datetime
from pathlib import Path
from typing import Optional

# ── Windows cp950 Compatibility: Force stdout/stderr to use UTF-8 ────────
def _safe_print(*args, **kwargs):
    """Safely print Unicode content in cp950/gbk environments."""
    try:
        print(*args, **kwargs)
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Substitute Unicode symbols with '?'
        safe_args = [str(a).encode('ascii', errors='replace').decode('ascii')
                     for a in args]
        print(*safe_args, **kwargs)


# ──────────────────────────────────────────────
# Path Configuration (Auto-detect project root)
# ──────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUTS_DIR   = PROJECT_ROOT / "inputs"
OUTPUTS_DIR  = PROJECT_ROOT / "outputs"

QUESTIONNAIRE_PATH = INPUTS_DIR / "questionnaire.json"
TRANSCRIPT_PATH    = INPUTS_DIR / "transcript.txt"


# ══════════════════════════════════════════════
# 1. Data Loading
# ══════════════════════════════════════════════

def load_inputs() -> tuple[dict, str]:
    """
    Reads questionnaire JSON and transcript TXT.
    Returns: (questionnaire_dict, transcript_text)
    """
    if not QUESTIONNAIRE_PATH.exists():
        raise FileNotFoundError(f"Questionnaire file not found: {QUESTIONNAIRE_PATH}")
    if not TRANSCRIPT_PATH.exists():
        raise FileNotFoundError(f"Transcript file not found: {TRANSCRIPT_PATH}")

    with open(QUESTIONNAIRE_PATH, "r", encoding="utf-8") as f:
        questionnaire = json.load(f)

    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        transcript = f.read()

    _safe_print(f"[OK] Questionnaire loaded: {QUESTIONNAIRE_PATH.name}")
    _safe_print(f"[OK] Transcript loaded: {TRANSCRIPT_PATH.name} ({len(transcript)} chars)")
    return questionnaire, transcript


# ══════════════════════════════════════════════
# 2. Prompt Construction
# ══════════════════════════════════════════════

SYSTEM_PROMPT = """You are a senior business consultant and sales operations expert specializing in \
SMB (Small and Medium Business) diagnostics. You have 15+ years of experience analyzing B2B sales \
processes, GTM strategies, and revenue operations.

Your task is to analyze the provided client data — which includes a structured business questionnaire \
(JSON) and a verbatim interview transcript (TXT) — and produce a comprehensive diagnostic report \
in a STRICT JSON format.

═══════════════════════════════════════════════════════════
ANALYSIS FRAMEWORK — You MUST analyze ALL 5 dimensions:
═══════════════════════════════════════════════════════════

【DIMENSION 1 — SALES FUNNEL GAPS】
Identify where leads are being lost in the funnel. Calculate:
- Estimated lead-to-quote conversion rate
- Quote-to-close conversion rate and benchmark gap
- Stages with the highest friction (time delays, inconsistency, human error)
- Specific process breakdowns mentioned in the transcript
Provide 3 prioritized gap findings with supporting evidence from the data.
Assess the client's current automation level using a 0–5 maturity scale:
  0 = No tools, fully manual
  1 = Basic spreadsheets, no automation
  2 = Some digital tools, disconnected
  3 = Partially integrated tools with sporadic automation
  4 = Integrated stack with consistent automation
  5 = Full automation with AI/predictive capabilities
Score each sub-area: lead capture, lead nurturing, quoting, follow-up, reporting.
Identify the top 2 automation opportunities with estimated time-savings per week.

【DIMENSION 3 — PRODUCT DIFFERENTIATION ANALYSIS】
Based on the transcript and questionnaire, assess:
- Current differentiation strategy (explicit and implicit)
- Strength of the value proposition communicated by sales reps
- Consistency of differentiation messaging across the team
- Untapped differentiation angles not currently leveraged
- Risk level of commoditization (Low / Medium / High)

【DIMENSION 4 — OBJECTION ANALYSIS】
Extract ALL objections mentioned in the transcript. For each objection:
- Classify the objection type: Price / Timeline / Trust / Authority / Urgency / Fit / Logistics
- Assess the current rebuttal effectiveness: Weak / Moderate / Strong
- Prescribe a recommended rebuttal script (2–3 sentences, professional English)
- Indicate training priority: Critical / High / Medium / Low

【DIMENSION 5 — ROI PROJECTION】
Using the financial data from the questionnaire, calculate a 12-month ROI projection:
- Baseline metrics (current state from questionnaire data)
- Target metrics (improved state, conservative +30–40% estimates)
- Incremental revenue projection (USD/Local Currency)
- Estimated implementation cost range (based on budget_for_improvement_twd)
- Projected payback period (months)
- Confidence level: Low / Medium / High, with rationale

═══════════════════════════════════════════════════════════
OUTPUT RULES — STRICTLY ENFORCED:
═══════════════════════════════════════════════════════════

1. You MUST return ONLY valid JSON. No markdown, no prose, no code blocks, no triple backticks.
2. All string values MUST be written in English.
3. Every finding MUST cite evidence — quote directly from the transcript or reference specific fields.
4. Do NOT fabricate data. If information is insufficient, set value to null and add "evidence_gap" note.
5. The JSON schema is FIXED — do not add, rename, or remove any top-level keys.
6. overall_health_score must be an integer between 0–100.

═══════════════════════════════════════════════════════════
REQUIRED JSON OUTPUT SCHEMA:
═══════════════════════════════════════════════════════════

{
  "meta": {
    "company_name": "string",
    "industry": "string",
    "analysis_timestamp": "ISO8601 string",
    "analyzer_version": "1.0",
    "overall_health_score": 0,
    "overall_health_label": "Critical | Needs Improvement | Fair | Good | Excellent",
    "executive_summary": "string (100–150 words in English)"
  },
  "sales_funnel_gaps": {
    "current_conversion_rate_percent": 0.0,
    "benchmark_conversion_rate_percent": 0.0,
    "conversion_gap_percent": 0.0,
    "top_gaps": [
      {
        "rank": 1,
        "stage": "string",
        "gap_description": "string",
        "evidence": "string (direct quote or field reference)",
        "severity": "High | Medium | Low",
        "recommended_action": "string"
      }
    ],
    "estimated_monthly_revenue_leak_twd": 0
  },
  "marketing_automation": {
    "overall_maturity_score": 0.0,
    "maturity_label": "string",
    "sub_scores": {
      "lead_capture": 0.0,
      "lead_nurturing": 0.0,
      "quoting_process": 0.0,
      "follow_up": 0.0,
      "reporting": 0.0
    },
    "top_opportunities": [
      {
        "area": "string",
        "current_state": "string",
        "recommended_tool_type": "string",
        "estimated_weekly_time_savings_hours": 0.0,
        "implementation_complexity": "Low | Medium | High"
      }
    ]
  },
  "product_differentiation": {
    "commoditization_risk": "Low | Medium | High",
    "current_strategy_assessment": "string",
    "messaging_consistency_score": 0,
    "untapped_angles": ["string"],
    "recommendations": ["string"]
  },
  "objection_analysis": {
    "objections": [
      {
        "objection_text": "string",
        "type": "Price | Timeline | Trust | Authority | Urgency | Fit | Logistics",
        "current_rebuttal_effectiveness": "Weak | Moderate | Strong",
        "recommended_rebuttal_en": "string (English, 2–3 sentences)",
        "training_priority": "Critical | High | Medium | Low"
      }
    ],
    "highest_priority_training_area": "string"
  },
  "roi_projection": {
    "baseline": {
      "monthly_leads": 0,
      "close_rate_percent": 0.0,
      "monthly_deals_closed": 0,
      "monthly_revenue_twd": 0
    },
    "target": {
      "monthly_leads": 0,
      "close_rate_percent": 0.0,
      "monthly_deals_closed": 0,
      "monthly_revenue_twd": 0
    },
    "incremental_annual_revenue_twd": 0,
    "estimated_implementation_cost_min_twd": 0,
    "estimated_implementation_cost_max_twd": 0,
    "payback_period_months": 0.0,
    "confidence_level": "Low | Medium | High",
    "confidence_rationale": "string"
  }
}"""


USER_PROMPT_TEMPLATE = """Based on the following two client data sources, perform a complete 5-dimensional business diagnosis and return the results strictly according to the JSON Schema defined in the System Prompt.

════════════════════════════════
[DATA 1: QUESTIONNAIRE questionnaire.json]
════════════════════════════════
{questionnaire_json}

════════════════════════════════
[DATA 2: TRANSCRIPT transcript.txt]
════════════════════════════════
{transcript_text}

════════════════════════════════
Please start the analysis now. Output ONLY JSON, no conversational filler.
════════════════════════════════"""


def build_user_prompt(questionnaire: dict, transcript: str) -> str:
    """Fills the questionnaire and transcript into the User Prompt template."""
    return USER_PROMPT_TEMPLATE.format(
        questionnaire_json=json.dumps(questionnaire, ensure_ascii=False, indent=2),
        transcript_text=transcript,
    )


# ══════════════════════════════════════════════
# 3. LLM 呼叫 — OpenAI GPT-4o
# ══════════════════════════════════════════════

def call_openai(system_prompt: str, user_prompt: str) -> str:
    """
    Calls OpenAI GPT-4o API.
    Requires environment variable OPENAI_API_KEY.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Please install openai package: pip install openai")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY not found.\n"
            "Please set environment variable: set OPENAI_API_KEY=sk-xxxx (Windows)\n"
            "Or create a .env file with: OPENAI_API_KEY=sk-xxxx"
        )

    client = OpenAI(api_key=api_key)
    _safe_print("[->] Calling OpenAI GPT-4o...")

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        # low temperature for stable JSON
        temperature=0.2,        
        max_tokens=4096,
        response_format={"type": "json_object"},  # Force JSON mode
    )

    raw = response.choices[0].message.content
    usage = response.usage
    _safe_print(f"[OK] GPT-4o responded | tokens: prompt={usage.prompt_tokens}, "
          f"completion={usage.completion_tokens}, total={usage.total_tokens}")
    return raw


# ══════════════════════════════════════════════
# 4. LLM 呼叫 — Google Gemini
# ══════════════════════════════════════════════

def call_gemini(system_prompt: str, user_prompt: str,
                model: str = "gemini-2.0-flash") -> str:
    """
    Calls Google Gemini API.
    Requires environment variable GEMINI_API_KEY.
    Default model: gemini-2.0-flash
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise ImportError("Please install google-genai package: py -m pip install google-genai")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY not found.\n"
            "Please get an API Key at https://aistudio.google.com/app/apikey"
        )

    client = genai.Client(api_key=api_key)
    _safe_print(f"[->] Calling Google Gemini ({model})...")

    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.2,
            response_mime_type="application/json",   # Force JSON output
        ),
    )

    _safe_print("[OK] Gemini responded")
    return response.text


# ══════════════════════════════════════════════
# 5. LLM 呼叫 — Groq
# ══════════════════════════════════════════════

# Groq 支援的模型（速度從快到慢）
GROQ_MODELS = [
    "llama-3.3-70b-versatile",   # 推薦：70B，品質最佳
    "llama-3.1-8b-instant",       # 備用：8B，極速
    "mixtral-8x7b-32768",         # 備用：長上下文
]


def call_groq(system_prompt: str, user_prompt: str,
              model: str = GROQ_MODELS[0]) -> str:
    """
    Calls Groq API (OpenAI compatible).
    Requires environment variable GROQ_API_KEY.
    """
    try:
        from groq import Groq
    except ImportError:
        raise ImportError(
            "Please install groq package: pip install groq"
        )

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not found.\n"
            "Please get an API Key at https://console.groq.com/keys"
        )

    client = Groq(api_key=api_key)
    _safe_print(f"[->] Calling Groq ({model})...")

    # Groq 用加強版 system prompt 取代 JSON mode
    groq_system = system_prompt + (
        "\n\nCRITICAL REMINDER: Your ENTIRE response must be a single valid JSON object. "
        "Start with '{' and end with '}'. No text before or after."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": groq_system},
            {"role": "user",   "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=8192,
    )

    raw = response.choices[0].message.content
    usage = response.usage
    _safe_print(f"[OK] Groq 回應完成 | tokens: "
          f"prompt={usage.prompt_tokens}, "
          f"completion={usage.completion_tokens}, "
          f"total={usage.total_tokens}")
    return raw


# ══════════════════════════════════════════════
# 5. JSON 解析與驗證
# ══════════════════════════════════════════════

REQUIRED_TOP_LEVEL_KEYS = {
    "meta",
    "sales_funnel_gaps",
    "marketing_automation",
    "product_differentiation",
    "objection_analysis",
    "roi_projection",
}


def parse_and_validate(raw_response: str) -> dict:
    """
    Parses LLM JSON response and validates required fields.
    """
    # Clean possible markdown code blocks
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Unable to parse LLM response as JSON.\n"
            f"Error: {e}\n"
            f"Raw content snippet:\n{cleaned[:500]}"
        )

    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(result.keys())
    if missing_keys:
        _safe_print(f"[!] Warning: Response missing keys: {missing_keys}")

    _safe_print("[OK] JSON parsed and validated")
    return result


# ══════════════════════════════════════════════
# 6. 結果輸出
# ══════════════════════════════════════════════

def save_output(result: dict) -> Path:
    """
    Saves JSON result to outputs/ folder.
    """
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().strftime("%Y-%m-%d")
    company = result.get("meta", {}).get("company_name", "unknown")
    safe_company = "".join(c for c in company if c not in r'\/:*?"<>|')
    filename = f"{today}_{safe_company}_diagnosis.json"
    output_path = OUTPUTS_DIR / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    _safe_print(f"[OK] Diagnosis results saved: {output_path}")
    return output_path


def print_summary(result: dict) -> None:
    """Prints human-readable summary to terminal."""
    meta = result.get("meta", {})
    roi  = result.get("roi_projection", {})

    _safe_print("\n" + "=" * 60)
    _safe_print("  AutoConsult AI -- Diagnosis Summary")
    _safe_print("=" * 60)
    _safe_print(f"  Company:  {meta.get('company_name', 'N/A')}")
    _safe_print(f"  Industry: {meta.get('industry', 'N/A')}")
    _safe_print(f"  Health Score: {meta.get('overall_health_score', 'N/A')} / 100 "
          f"({meta.get('overall_health_label', '')})")
    _safe_print(f"\n  Executive Summary:\n  {meta.get('executive_summary', 'N/A')}")

    baseline = roi.get("baseline", {})
    target   = roi.get("target", {})
    _safe_print(f"\n  --- ROI Projection ---")
    _safe_print(f"  Current Rev:  ${baseline.get('monthly_revenue_twd', 0):,.0f}")
    _safe_print(f"  Target Rev:   ${target.get('monthly_revenue_twd', 0):,.0f}")
    _safe_print(f"  Annual Growth: ${roi.get('incremental_annual_revenue_twd', 0):,.0f}")
    _safe_print(f"  Payback:     {roi.get('payback_period_months', 'N/A')} months")
    _safe_print(f"  Confidence:  {roi.get('confidence_level', 'N/A')}")
    _safe_print("=" * 60 + "\n")


# ══════════════════════════════════════════════
# 7. 主程式入口
# ══════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AutoConsult AI — Automated business diagnostic engine"
    )
    parser.add_argument(
        "--provider",
        choices=["groq", "gemini", "openai"],
        default="gemini",
        help="Select LLM provider (default: gemini)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只印出 Prompt 內容，不實際呼叫 API（用於除錯）",
    )
    parser.add_argument(
        "--questionnaire",
        type=str,
        default=str(QUESTIONNAIRE_PATH),
        help="問卷 JSON 的自訂路徑",
    )
    parser.add_argument(
        "--transcript",
        type=str,
        default=str(TRANSCRIPT_PATH),
        help="逐字稿 TXT 的自訂路徑",
    )
    return parser.parse_args()


def run(
    provider: str = "openai",
    dry_run: bool = False,
    questionnaire_path: Optional[str] = None,
    transcript_path: Optional[str] = None,
) -> Optional[dict]:
    """
    主執行函式（可從其他模組 import 呼叫）。
    回傳診斷結果 dict，dry-run 模式下回傳 None。
    """
    # ── 支援自訂路徑 ──────────────────────────
    global QUESTIONNAIRE_PATH, TRANSCRIPT_PATH
    if questionnaire_path:
        QUESTIONNAIRE_PATH = Path(questionnaire_path)
    if transcript_path:
        TRANSCRIPT_PATH = Path(transcript_path)

    # ── Step 1: Load Data ──────────────────────
    print("\n[1/5] Loading input data...")
    questionnaire, transcript = load_inputs()

    # ── Step 2: Build Prompt ───────────────────
    print("[2/5] Building analysis prompt...")
    user_prompt = build_user_prompt(questionnaire, transcript)
    total_chars = len(SYSTEM_PROMPT) + len(user_prompt)
    print(f"      System Prompt: {len(SYSTEM_PROMPT):,} chars")
    print(f"      User Prompt:   {len(user_prompt):,} chars")
    print(f"      Total:          {total_chars:,} chars (~{total_chars // 4:,} tokens)")

    # ── Dry-run Mode ──────────────────────────
    if dry_run:
        _safe_print("\n" + "-" * 60)
        _safe_print("[DRY-RUN] System Prompt:")
        _safe_print("-" * 60)
        _safe_print(SYSTEM_PROMPT)
        _safe_print("\n" + "-" * 60)
        _safe_print("[DRY-RUN] User Prompt (first 1000 chars):")
        _safe_print("-" * 60)
        _safe_print(user_prompt[:1000] + "\n... (truncated)")
        _safe_print("\n[!] Dry-run complete, API not called.")
        return None

    # ── Step 3: Call LLM ─────────────────────
    _safe_print(f"[3/5] Calling LLM (Provider: {provider})...")
    if provider == "groq":
        raw_response = call_groq(SYSTEM_PROMPT, user_prompt)
    elif provider == "gemini":
        raw_response = call_gemini(SYSTEM_PROMPT, user_prompt)
    elif provider == "openai":
        raw_response = call_openai(SYSTEM_PROMPT, user_prompt)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    # ── Step 4: Parse & Validate ────────────────────
    print("[4/5] Parsing and validating JSON response...")
    result = parse_and_validate(raw_response)

    # ── Step 5: Save Output ──────────────────────
    print("[5/5] Saving diagnosis results...")
    save_output(result)

    # ── Print Summary ──────────────────────────────
    print_summary(result)

    return result


# ──────────────────────────────────────────────
if __name__ == "__main__":
    # Load .env if exists
    try:
        from dotenv import load_dotenv
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"[✓] Loaded .env: {env_path}")
    except ImportError:
        pass 

    args = parse_args()

    try:
        run(
            provider=args.provider,
            dry_run=args.dry_run,
            questionnaire_path=args.questionnaire,
            transcript_path=args.transcript,
        )
    except (FileNotFoundError, EnvironmentError, ValueError, ImportError) as e:
        print(f"\n[✗] Execution failed: {e}", file=sys.stderr)
        sys.exit(1)
