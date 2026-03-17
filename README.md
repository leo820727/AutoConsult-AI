# ⬡ AutoConsult AI — Automated Business Diagnosis System
## 自動化業務診斷系統 (Bilingual: EN/ZH)

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg)
![AI Providers](https://img.shields.io/badge/AI-Groq%20%7C%20Gemini%20%7C%20OpenAI-green.svg)

**AutoConsult AI** is a professional-grade automated diagnostic tool designed for SMBs. By analyzing client questionnaires and discovery call transcripts, it leverages state-of-the-art LLMs to generate 5-dimensional business audits in under 60 seconds.

**AutoConsult AI** 是一款專為中小型企業設計的自動化業務診斷工具。透過分析客戶問卷與訪談逐字稿，利用 LLM 在 60 秒內生成含五大維度的專業業務審計報告。

---

## 🚀 Core Features | 核心功能

- **Multi-LLM Support | 多模型整合**：
  - **Groq (Llama 3.3)**: Ultra-fast, high-quality free-tier performance.
  - **Google Gemini 2.0 Flash**: High-context windows for long transcripts.
  - **OpenAI GPT-4o**: Industry-standard logic.
- **5-Dimensional Diagnosis Framework | 五維度診斷框架**：
  - **Sales Funnel Gaps (銷售漏斗缺口)**: Identifies conversion leaks.
  - **Marketing Automation (行銷自動化)**: Maturity scoring.
  - **Product Differentiation (產品差異化)**: Competitive positioning.
  - **Objection Analysis (反對意見處理)**: Rebuttal strategy.
  - **ROI Projection (投資回報預估)**: 12-month revenue uplift simulation.
- **Professional Outputs | 專業報告輸出**：
  - **Bento UI Dashboard**: Clean, interactive web interface.
  - **PDF Export**: Print-ready reports with CJK font support.
  - **Markdown & JSON**: Raw data for further editing.

---

## 🧭 Prompt Engineering Journey | Prompt 開發歷程

This entire project was developed through **Prompt-Driven Development (PDD)**:
整個專案完全透過 **Prompt 驅動開發 (PDD)** 完成，展現了高階提示詞工程如何構建複雜系統：

1. **Persona Architecture**: Used Senior Prompt Engineer roles to define the diagnostic core. (以「資深提示詞工程師」角色設計診斷核心)
2. **Structural Constraint**: Forced AI to output 100% valid JSON for frontend rendering. (強制 AI 輸出結構化 JSON 供前端渲染)
3. **Iterative Refinement**: Evolved from a CLI script to a high-end B2B SaaS UI through aesthetic prompting. (透過視覺化提示詞，將其從 CLI 工具進化為高階 SaaS 介面)

---

## 📂 Structure | 專案結構

```text
AutoConsult AI/
├── app.py                # Streamlit Web UI (前端網頁)
├── main.py               # CLI Interface (命令行入口)
├── requirements.txt      # Dependencies (開發依賴)
├── engine/               # AI Core Logic (AI 核心邏輯)
│   ├── ai_analyzer.py    # Prompting & LLM orchestration
│   └── report_generator.py # PDF/Markdown rendering engine
├── inputs/               # Raw Data (原始數據：問卷、逐字稿)
└── outputs/              # Results (診斷報告輸出區)
```

---

## 🛠️ Quick Start | 快速開始

### 1. Install | 安裝環境
```bash
git clone https://github.com/your-username/autoconsult-ai.git
cd autoconsult-ai
pip install -r requirements.txt
```

### 2. Launch | 啟動
**Web UI (Recommended):**
```bash
streamlit run app.py
```
*Note: You can input your API key directly in the UI dashboard.*  
*註：可在網頁介面中直接輸入 API Key 使用。*

---

## 🎨 Technology Stack | 技術棧

- **Frontend**: Streamlit (B2B SaaS Theme)
- **AI Backend**: Groq, Google Gemini, OpenAI
- **PDF Engine**: ReportLab (Windows CJK Fonts Integrated)
- **Language**: Python 3.10+

---

## ⚖️ Disclaimer | 免責聲明
Diagnostic results are AI-generated for reference only. Consult professional advisors for final business decisions.  
診斷結果由 AI 生成僅供參考，最終商業決策建議諮詢專業顧問。
