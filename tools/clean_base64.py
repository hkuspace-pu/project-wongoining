"""
Step 1: CSV Cleaner
====================
清理Base64垃圾行，輸出乾淨嘅CSV供之後labeling用。
只需跑一次。

使用方法:
  pip install pandas
  python step1_clean.py
"""

import re
import pandas as pd

# ── 設定 ──────────────────────────────────────────────────────────────────────

INPUT_CSV  = "phishing_cleaned_.csv"  # 原始檔案
OUTPUT_CSV = "phishing_cleaned.csv"            # 清理後輸出

BINARY_LABELS = ["Urgency", "Scarcity", "Authority", "Fear", "Social Proof", "Reciprocity", "Liking"]

# ── 清理邏輯 ──────────────────────────────────────────────────────────────────

def is_junk(text) -> bool:
    """判斷係咪Base64垃圾或空行"""
    if pd.isna(text):
        return True
    text = str(text).strip()
    if len(text) < 5:
        return True
    # Base64特徵：只有英數 + / =，冇空格
    return bool(re.match(r'^[A-Za-z0-9+/=\n\r]+$', text)) and ' ' not in text

# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    import os
    if os.path.exists(OUTPUT_CSV):
        print(f"⚠️  {OUTPUT_CSV} 已存在，跳過清理（如需重新清理請先刪除該檔案）")
        return

    print(f"📂 讀取: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"   原始行數: {len(df)}")

    junk_mask = df['Email Text'].apply(is_junk)
    df_clean = df[~junk_mask].reset_index(drop=True)

    # 確保所有label欄位存在
    for col in ['Email Type'] + BINARY_LABELS:
        if col not in df_clean.columns:
            df_clean[col] = None

    df_clean.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    labeled = df_clean['Email Type'].notna() & (df_clean['Email Type'].astype(str).str.strip() != '')

    print(f"   🗑️  Drop垃圾行: {junk_mask.sum()}")
    print(f"   ✅ 清理後行數: {len(df_clean)}")
    print(f"   已標注: {labeled.sum()}")
    print(f"   待標注: {(~labeled).sum()}")
    print(f"   儲存至: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
