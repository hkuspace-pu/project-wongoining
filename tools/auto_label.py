"""
Step 2: Batch AI Labeler
=========================
小批量AI labeling，可以隨時停、隨時繼續。
每次跑都會從上次停嘅地方接續。

使用方法:
  pip install anthropic pandas
  export ANTHROPIC_API_KEY="sk-ant-..."
  python step2_label.py
"""

import os
import sys
import json
import pandas as pd
import anthropic

# ── 設定 ──────────────────────────────────────────────────────────────────────

CSV_PATH   = "phishing_cleaned.csv"   # Step 1輸出嘅清理版CSV
BATCH_SIZE = 10                       # 每次處理幾多封（建議10-20）

EMAIL_TYPES   = ["Spam Other", "Marketing Spam", "Phishing Email", "Scam Email"]
BINARY_LABELS = ["Urgency", "Scarcity", "Authority", "Fear", "Social Proof", "Reciprocity", "Liking"]

# ── AI分析 ────────────────────────────────────────────────────────────────────

def get_ai_labels(client, email_text: str) -> dict:
    prompt = f"""You are an expert email analyst specializing in spam, phishing, and scam detection.

Analyze the following email and classify it. Respond ONLY with a valid JSON object, no other text, no markdown.

Email:
{email_text[:3000]}

Return this exact JSON structure:
{{
  "Email Type": "<one of: Spam Other | Marketing Spam | Phishing Email | Scam Email>",
  "Urgency": <1 or 0>,
  "Scarcity": <1 or 0>,
  "Authority": <1 or 0>,
  "Fear": <1 or 0>,
  "Social Proof": <1 or 0>,
  "Reciprocity": <1 or 0>,
  "Liking": <1 or 0>,
  "reason": "<one sentence explanation>"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

# ── 顯示 ─────────────────────────────────────────────────────────────────────

def display_result(i, batch_total, email_text, suggestion):
    print(f"\n{'─'*60}")
    print(f"📧 Email {i}/{batch_total}")
    print(f"{'─'*60}")
    preview = str(email_text)[:300].replace('\n', ' ')
    if len(str(email_text)) > 300:
        preview += "..."
    print(preview)
    print(f"\n🤖 AI 建議:")
    print(f"   {'Type':<14}: {suggestion.get('Email Type', '?')}")
    for label in BINARY_LABELS:
        val = suggestion.get(label, '?')
        bar = "█" if val == 1 else "░"
        print(f"   {label:<14}: {bar} {val}")
    print(f"   {'Reason':<14}: {suggestion.get('reason', '')}")

# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    # 確認CSV存在
    if not os.path.exists(CSV_PATH):
        print(f"❌ 搵唔到 {CSV_PATH}")
        print(f"   請先跑 step1_clean.py")
        sys.exit(1)

    # 確認API Key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("❌ 冇搵到 ANTHROPIC_API_KEY")
        print("   請先: export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # 讀CSV
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    # 搵未標注嘅row
    labeled_mask = df['Email Type'].notna() & (df['Email Type'].astype(str).str.strip() != '')
    unlabeled = df[~labeled_mask].index.tolist()

    print(f"{'='*60}")
    print(f"📊 進度: 已標注 {labeled_mask.sum()} / {len(df)} 封")
    print(f"   待標注: {len(unlabeled)} 封")
    print(f"   今次處理: {min(BATCH_SIZE, len(unlabeled))} 封")
    print(f"{'='*60}")
    print("操作: Enter=接受  e=手動編輯  s=跳過  q=儲存退出")

    if len(unlabeled) == 0:
        print("🎉 所有row已標注完畢！")
        return

    batch = unlabeled[:BATCH_SIZE]
    completed = 0

    for i, row_idx in enumerate(batch):
        email_text = str(df.at[row_idx, 'Email Text'])

        print(f"\n⏳ AI分析中 ({i+1}/{len(batch)})...")
        try:
            suggestion = get_ai_labels(client, email_text)
        except Exception as e:
            print(f"⚠️  AI出錯: {e}")
            suggestion = {"Email Type": "Spam Other", **{l: 0 for l in BINARY_LABELS}, "reason": "AI error"}

        display_result(i+1, len(batch), email_text, suggestion)

        while True:
            choice = input("\n> ").strip().lower()

            if choice == '':
                # 接受AI建議
                df.at[row_idx, 'Email Type'] = suggestion.get('Email Type', 'Spam Other')
                for label in BINARY_LABELS:
                    df.at[row_idx, label] = suggestion.get(label, 0)
                completed += 1
                print("  ✅ 接受")
                break

            elif choice == 'e':
                # 手動編輯
                print("\n  Email Type:")
                for idx, et in enumerate(EMAIL_TYPES):
                    print(f"    [{idx+1}] {et}")
                et_in = input("  選擇 (1-4，Enter=用AI建議): ").strip()
                try:
                    email_type = EMAIL_TYPES[int(et_in)-1]
                except:
                    email_type = suggestion.get('Email Type', 'Spam Other')

                print(f"\n  Binary labels（0/1，Enter=用AI建議）:")
                labels = {}
                for label in BINARY_LABELS:
                    ai_val = suggestion.get(label, 0)
                    val = input(f"  {label:<14} [AI:{ai_val}] > ").strip()
                    labels[label] = int(val) if val in ('0', '1') else ai_val

                df.at[row_idx, 'Email Type'] = email_type
                for label in BINARY_LABELS:
                    df.at[row_idx, label] = labels[label]
                completed += 1
                print("  ✅ 已儲存")
                break

            elif choice == 's':
                print("  ⏭️  跳過")
                break

            elif choice == 'q':
                df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
                print(f"\n💾 已儲存（今次完成 {completed} 封）")
                print(f"   下次跑 step2_label.py 會從第 {labeled_mask.sum() + completed + 1} 封繼續")
                return

            else:
                print("  請輸入 Enter / e / s / q")

    # Batch完成，自動儲存
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    remaining = len(unlabeled) - completed
    print(f"\n{'='*60}")
    print(f"✅ 今批完成！標注了 {completed} 封")
    print(f"   仍剩 {remaining} 封 — 再跑 step2_label.py 繼續")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
