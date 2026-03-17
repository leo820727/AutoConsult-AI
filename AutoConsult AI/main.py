# -*- coding: utf-8 -*-
"""
AutoConsult AI — main.py
=========================
自動化工作流執行入口

工作流程：
  1. 掃描 inputs/ 資料夾，偵測可用的輸入檔案
  2. 驗證檔案格式（JSON Schema 檢查 + TXT 非空檢查）
  3. 呼叫 engine/ai_analyzer.py 進行 AI 診斷
  4. 呼叫 engine/report_generator.py 生成 Markdown 報告
  5. 輸出最終摘要，顯示報告路徑

使用方式：
  python main.py                       # 標準執行（GPT-4o）
  python main.py --provider gemini     # 使用 Gemini
  python main.py --dry-run             # 只驗證資料，不呼叫 API
  python main.py --watch               # 監控模式：偵測到新檔自動觸發
"""

import argparse
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import json
import time
import datetime
import hashlib
from pathlib import Path
from typing import Optional

# ── 加入 engine/ 至搜尋路徑 ──────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "engine"))

import ai_analyzer
import report_generator

INPUTS_DIR  = PROJECT_ROOT / "inputs"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

QUESTIONNAIRE_PATH = INPUTS_DIR / "questionnaire.json"
TRANSCRIPT_PATH    = INPUTS_DIR / "transcript.txt"

# 必填的問卷頂層欄位
REQUIRED_QUESTIONNAIRE_FIELDS = [
    "client_profile",
    "business_scale",
    "business_goals",
    "pain_points",
    "current_tools",
]

# 問卷中必填的子欄位（client_profile 層）
REQUIRED_CLIENT_FIELDS = ["company_name", "industry", "annual_revenue_twd"]


# ══════════════════════════════════════════════
# STEP 0：啟動畫面
# ══════════════════════════════════════════════

BANNER = """
+==================================================+
|                                                  |
|   [AI]  AutoConsult AI  -  自動化業務診斷系統    |
|         Automated SMB Business Diagnostic Engine  |
|                                                  |
+==================================================+
"""


def print_banner():
    print(BANNER)
    print(f"  啟動時間：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  專案根目錄：{PROJECT_ROOT}\n")


# ══════════════════════════════════════════════
# STEP 1：書面偵測
# ══════════════════════════════════════════════

class InputFileError(Exception):
    """輸入檔案不存在或格式錯誤時拋出。"""


def detect_inputs() -> tuple[Path, Path]:
    """
    確認 inputs/ 中有且只有一份問卷與逐字稿。
    回傳 (questionnaire_path, transcript_path)。
    若有問題，拋出 InputFileError。
    """
    print("─" * 50)
    print("[1/4] STEP 1 - 偵測輸入檔案")
    print("─" * 50)

    missing = []
    if not QUESTIONNAIRE_PATH.exists():
        missing.append(str(QUESTIONNAIRE_PATH))
    if not TRANSCRIPT_PATH.exists():
        missing.append(str(TRANSCRIPT_PATH))

    if missing:
        raise InputFileError(
            "找不到以下必要輸入檔案，請確認 inputs/ 資料夾內容：\n"
            + "\n".join(f"  ✗ {p}" for p in missing)
        )

    q_size = QUESTIONNAIRE_PATH.stat().st_size
    t_size = TRANSCRIPT_PATH.stat().st_size

    print(f"  [OK] questionnaire.json  ({q_size:,} bytes)")
    print(f"  [OK] transcript.txt      ({t_size:,} bytes)")

    if q_size == 0:
        raise InputFileError("questionnaire.json 是空檔案，請填入有效資料。")
    if t_size == 0:
        raise InputFileError("transcript.txt 是空檔案，請填入訪談逐字稿。")

    print()
    return QUESTIONNAIRE_PATH, TRANSCRIPT_PATH


# ══════════════════════════════════════════════
# STEP 2：格式驗證
# ══════════════════════════════════════════════

class ValidationError(Exception):
    """資料驗證失敗時拋出。"""


def validate_questionnaire(path: Path) -> dict:
    """
    驗證問卷 JSON 格式：
    - 必須是合法的 JSON
    - 必須包含所有必填頂層欄位
    - client_profile 必須包含必填子欄位
    - pain_points 必須是非空陣列
    - annual_revenue_twd 必須是正數
    回傳解析後的 dict。
    """
    print("─" * 50)
    print("[2/4] STEP 2 - 驗證輸入檔案格式")
    print("─" * 50)

    # 驗證 JSON 語法
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(
            f"questionnaire.json 不是合法的 JSON 格式。\n"
            f"  語法錯誤位置：第 {e.lineno} 行，第 {e.colno} 欄\n"
            f"  錯誤訊息：{e.msg}"
        )

    errors = []

    # 頂層必填欄位
    for field in REQUIRED_QUESTIONNAIRE_FIELDS:
        if field not in data:
            errors.append(f"問卷缺少必填欄位：'{field}'")

    # client_profile 子欄位
    client = data.get("client_profile", {})
    if not isinstance(client, dict):
        errors.append("'client_profile' 必須是 JSON 物件（{}）")
    else:
        for field in REQUIRED_CLIENT_FIELDS:
            if field not in client:
                errors.append(f"client_profile 缺少必填子欄位：'{field}'")

        revenue = client.get("annual_revenue_twd")
        if revenue is not None:
            if not isinstance(revenue, (int, float)) or revenue <= 0:
                errors.append(
                    f"'annual_revenue_twd' 必須是正數，目前值：{revenue}"
                )

    # pain_points 格式
    pain_points = data.get("pain_points", [])
    if not isinstance(pain_points, list) or len(pain_points) == 0:
        errors.append("'pain_points' 必須是非空陣列（至少填一個痛點）")
    else:
        for i, pp in enumerate(pain_points):
            if not isinstance(pp, dict):
                errors.append(f"pain_points[{i}] 必須是 JSON 物件")
            elif "description" not in pp:
                errors.append(f"pain_points[{i}] 缺少 'description' 欄位")

    if errors:
        error_list = "\n".join(f"  ✗ {e}" for e in errors)
        raise ValidationError(
            f"問卷格式驗證失敗，發現 {len(errors)} 個問題：\n{error_list}"
        )

    print(f"  [OK] questionnaire.json 驗證通過（{len(pain_points)} 個痛點）")

    # 驗證逐字稿（非空、長度足夠）
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        transcript_text = f.read()

    if len(transcript_text.strip()) < 100:
        raise ValidationError(
            "transcript.txt 內容太短（少於 100 字元），"
            "請確認已填入完整的訪談逐字稿。"
        )

    word_count = len(transcript_text)
    print(f"  [OK] transcript.txt 驗證通過（{word_count:,} 字元）")
    print()

    return data


# ══════════════════════════════════════════════
# STEP 3：AI 分析
# ══════════════════════════════════════════════

def run_analysis(provider: str, dry_run: bool) -> Optional[dict]:
    """
    呼叫 ai_analyzer.run()，回傳診斷結果 dict。
    dry-run 模式回傳 None。
    """
    print("─" * 50)
    print(f"[3/4] STEP 3 - AI 分析（供應商：{provider.upper()}）")
    if dry_run:
        print("   [!] DRY-RUN 模式：只印出 Prompt，不呼叫 API")
    print("─" * 50)

    result = ai_analyzer.run(
        provider=provider,
        dry_run=dry_run,
    )
    print()
    return result


# ══════════════════════════════════════════════
# STEP 4：報告生成
# ══════════════════════════════════════════════

def generate_report(diagnosis_data: dict) -> Path:
    """呼叫 report_generator 生成 Markdown 報告。"""
    print("─" * 50)
    print("[4/4] STEP 4 - 生成 Markdown 診斷報告")
    print("─" * 50)

    out_path = report_generator.generate_from_dict(diagnosis_data)
    print()
    return out_path


# ══════════════════════════════════════════════
# 監控模式（--watch）
# ══════════════════════════════════════════════

def get_inputs_fingerprint() -> str:
    """計算 inputs/ 資料夾中所有檔案內容的 hash，用於偵測變動。"""
    hasher = hashlib.md5()
    for path in sorted(INPUTS_DIR.glob("*")):
        if path.is_file() and not path.name.startswith("."):
            hasher.update(path.name.encode())
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


def watch_mode(provider: str, interval: int = 10):
    """
    監控模式：每隔 interval 秒掃描 inputs/ 是否有變動，
    有變動則自動觸發完整工作流程。
    按 Ctrl+C 停止。
    """
    print(f"\n[WATCH] 監控模式啟動（每 {interval} 秒掃描一次 inputs/）")
    print("   按 Ctrl+C 停止監控\n")
    # (emoji removed for Windows cp950 compatibility)

    last_fingerprint = get_inputs_fingerprint()
    print(f"   初始狀態 hash：{last_fingerprint[:12]}…")

    try:
        while True:
            time.sleep(interval)
            current_fp = get_inputs_fingerprint()

            if current_fp != last_fingerprint:
                print(f"\n[!] [{datetime.datetime.now().strftime('%H:%M:%S')}] "
                      f"偵測到 inputs/ 資料夾變動！啟動工作流程...\n")
                last_fingerprint = current_fp
                try:
                    execute_workflow(provider=provider, dry_run=False)
                except (InputFileError, ValidationError) as e:
                    print(f"[X] 工作流程失敗：{e}\n")
            else:
                print(f"   [{datetime.datetime.now().strftime('%H:%M:%S')}] "
                      f"無變動，繼續等待...", end="\r")

    except KeyboardInterrupt:
        print("\n\n[WATCH] 監控模式已停止。")


# ══════════════════════════════════════════════
# 完整工作流程
# ══════════════════════════════════════════════

def execute_workflow(provider: str = "openai", dry_run: bool = False) -> None:
    """
    執行完整的四步驟自動化工作流程。
    任何步驟失敗都會拋出對應的例外。
    """
    start_time = time.time()

    # Step 1：偵測輸入
    detect_inputs()

    # Step 2：格式驗證
    validate_questionnaire(QUESTIONNAIRE_PATH)

    # Step 3：AI 分析
    diagnosis = run_analysis(provider=provider, dry_run=dry_run)

    if dry_run or diagnosis is None:
        print("[OK] Dry-run 完成。驗證通過，Prompt 已印出，未呼叫 API。")
        return

    # Step 4：報告生成
    report_path = generate_report(diagnosis)

    # ── 完成摘要 ──────────────────────────────
    elapsed = time.time() - start_time
    company = diagnosis.get("meta", {}).get("company_name", "N/A")
    score   = diagnosis.get("meta", {}).get("overall_health_score", "N/A")
    label   = diagnosis.get("meta", {}).get("overall_health_label", "")

    print("=" * 50)
    print(">> 任務完成！")
    print("=" * 50)
    print(f"  客戶：      {company}")
    print(f"  健康評分：  {score} / 100  （{label}）")
    print(f"  診斷 JSON： {OUTPUTS_DIR}")
    print(f"  MD 報告：   {report_path.name}")
    print(f"  總耗時：    {elapsed:.1f} 秒")
    print("=" * 50 + "\n")


# ══════════════════════════════════════════════
# CLI 入口
# ══════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AutoConsult AI — 自動化業務診斷工作流入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例：
  python main.py                        # 標準執行（gemini）
  python main.py --provider groq        # 用 Groq（最快免費）
  python main.py --provider gemini      # 用 Gemini 2.0
  python main.py --provider openai      # 用 GPT-4o
  python main.py --dry-run              # 驗證資料 + 印出 Prompt，不花 API 費用
  python main.py --watch                # 監控模式（偵測 inputs/ 變動自動觸發）
  python main.py --watch --interval 30  # 監控模式，每 30 秒掃一次
        """,
    )
    parser.add_argument(
        "--provider",
        choices=["groq", "gemini", "openai"],
        default="gemini",
        help="LLM 供應商（預設：gemini）｜groq=最快免費｜openai=GPT-4o",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="驗證輸入資料並印出 Prompt，不呼叫 API",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="啟動監控模式：偵測 inputs/ 變動時自動執行",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=10,
        help="監控模式的掃描間隔秒數（預設：10）",
    )
    return parser.parse_args()


if __name__ == "__main__":
    # ── 載入 .env ──────────────────────────────
    try:
        from dotenv import load_dotenv
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass

    print_banner()
    args = parse_args()

    try:
        if args.watch:
            # 先執行一次，再進入監控迴圈
            execute_workflow(provider=args.provider, dry_run=args.dry_run)
            watch_mode(provider=args.provider, interval=args.interval)
        else:
            execute_workflow(provider=args.provider, dry_run=args.dry_run)

    except InputFileError as e:
        print(f"\n[✗] 輸入檔案錯誤：\n{e}", file=sys.stderr)
        print("\n💡 提示：請確認 inputs/ 資料夾中同時存在 questionnaire.json 與 transcript.txt", file=sys.stderr)
        sys.exit(1)

    except ValidationError as e:
        print(f"\n[✗] 資料驗證失敗：\n{e}", file=sys.stderr)
        print("\n💡 提示：請對照 inputs/questionnaire.json 的 Schema 格式進行修正", file=sys.stderr)
        sys.exit(2)

    except EnvironmentError as e:
        print(f"\n[✗] 環境設定錯誤：\n{e}", file=sys.stderr)
        print("\n💡 提示：請複製 .env.example 為 .env，並填入對應的 API Key", file=sys.stderr)
        sys.exit(3)

    except KeyboardInterrupt:
        print("\n\n[STOP] 使用者中止執行。")
        sys.exit(0)
