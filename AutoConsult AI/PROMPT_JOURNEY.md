# 🧭 Prompt Engineering Journey: Building AutoConsult AI
## Prompt 開發歷程：從對話到自動化系統的實踐

This document details the actual prompts used to guide the development of this project. It showcases the transition from conceptualization to a production-ready SaaS tool.

這份文件記錄了開發過程中所使用的實際 Prompt，展示了如何將概念轉化為可落地生產的 SaaS 工具。

---

### Phase 1: Foundation & Data Simulation | 第一階段：架構初始化與數據模擬

**Core Prompt Strategy**: Multi-file project structure and context-rich mock data.

> **Original Prompt (Excerpt):**
> 「我現在要開發一個名為『AutoConsult AI』的自動化業務診斷系統。請幫我完成以下初始化工作：建立一個專案資料夾結構（inputs, engine, outputs）。在 inputs/ 中建立模擬檔案：questionnaire.json（規模、目標、痛點）與 transcript.txt（10 分鐘訪談逐字稿）。」

**Why this worked**: It established the "Sandbox" environment immediately. Starting with the data structure ensured the subsequent AI logic had a concrete target to process.

---

### Phase 2: Intelligent Engine & AI Persona | 第二階段：核心分析引擎與角色定義

**Core Prompt Strategy**: Persona-based prompting and rigid output formatting (JSON).

> **Original Prompt (Excerpt):**
> 「請扮演一位『資深提示詞工程師』，幫我撰寫 engine/ai_analyzer.py。核心任務：讀取 inputs/ 中的問卷和逐字稿並分析。診斷邏輯需包含：銷售漏斗缺口、行銷自動化程度、產品差異化、客戶反對意見、預估 ROI。要求 AI 必須回傳『結構化的 JSON 格式』。」

**Why this worked**: By assigning the "Senior Prompt Engineer" role, I forced the AI to focus on precision. The JSON requirement was the "Contract" that allowed the frontend and backend to talk to each other.

---

### Phase 3: Automated Workflow Logic | 第三階段：自動化工作流邏輯

**Core Prompt Strategy**: Pipeline orchestration and professional document rendering.

> **Original Prompt (Excerpt):**
> 「實現『自動化工作流』：撰寫 main.py 作為入口，自動抓取 inputs/ 新檔案丟給 analyzer。處理後將 JSON 轉換成一份『專業的 Markdown 診斷報告』存於 outputs/。報告需含：現況總結、診斷圖表（文字模擬）、短中長期建議及執行方案。」

**Why this worked**: It decoupled the "Analysis" (AI) from the "Presentation" (Markdown). This phased approach made the code easier to debug and maintain.

---

### Phase 4: Premium B2B SaaS UI | 第四階段：高階 B2B SaaS 前端實作

**Core Prompt Strategy**: Aesthetic directives and user-centric features.

> **Original Prompt (Excerpt):**
> 「用 Streamlit 建立前端介面：功能包含上傳檔案、開始診斷。用卡片 (Cards) 展示關鍵指標。提供按鈕讓使用者下載 Markdown 或 PDF。整體風格要像是一個高階的 B2B SaaS 工具，配色偏向專業深藍或簡約風。」

**Why this worked**: Specific aesthetic keywords like "B2B SaaS" and "Deep Blue Professional" gave the AI a clear visual boundary, preventing generic UI styles.

---

### Phase 5: Production Refinement (PDF & Security) | 第五階段：產品化優化（PDF 與安全性）

**Core Prompt Strategy**: Feature expansion and "Bring Your Own Key" (BYOK) model.

> **Original Prompt (Excerpt):**
> 「由於後續要給客戶使用，請移除內建 API Key，留下輸入框讓客戶自填。最後把輸出 PDF 的功能加上去，支援中文顯示。」

**Why this worked**: It transitioned the project from a "Personal Tool" to a "Client Tool." Implementing the PDF engine solved the final mile of professional delivery.

---

### Summary of Prompting Mastery | 提示詞技巧總結

1. **Structural Anchoring (結構錨點)**: Before writing logic, define the input/output structure first.
2. **Constraint Enforcement (強制約束)**: Forcing JSON responses to enable coding automation.
3. **Aesthetic Anchoring (風格錨點)**: Using industry-standard terms (SaaS, Deep Blue, Minimal) to guide UI generation.
4. **Bilingual Documentation (雙語文件範式)**: Ensuring the project is globally presentable.

---
**AutoConsult AI** stands as a testament to the power of AI-assisted software architecture.
**AutoConsult AI** 證明了 AI 輔助軟體架構的強大潛力。
