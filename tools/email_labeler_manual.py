"""
Email Labeling Tool (手動版)
=============================
使用方法:
  1. pip install pandas
  2. 將你的CSV放喺同一個folder
  3. python email_labeler_manual.py
"""

import os
import sys
import pandas as pd

EMAIL_TYPES = [
    "Spam Other",
    "Marketing Spam",
    "Phishing Email",
    "Scam Email",
]

BINARY_LABELS = [
    "Urgency",
    "Scarcity",
    "Authority",
    "Fear",
    "Social Proof",
    "Reciprocity",
    "Liking",
]

# ── 顯示 helper ───────────────────────────────────────────────────────────────

def print_divider():
    print("\n" + "─" * 70)

def display_email(idx, total, email_text):
    print_divider()
    print(f"📧  Email {idx + 1} / {total}")
    print_divider()
    print(email_text)  # 顯示全文，唔截斷

# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    # 揀CSV
    csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]
    if not csv_files:
        print("❌ 目前資料夾冇CSV檔案。請將CSV放喺同一個folder再跑。")
        sys.exit(1)

    if len(csv_files) == 1:
        csv_path = csv_files[0]
        print(f"📂 找到CSV: {csv_path}")
    else:
        print("📂 找到多個CSV，請選擇：")
        for i, f in enumerate(csv_files):
            print(f"  [{i+1}] {f}")
        choice = input("選擇: ").strip()
        csv_path = csv_files[int(choice) - 1]

    # 讀CSV，用 Python csv module 處理含換行/base64 attachment 嘅 email field
    import csv, io

    df = None
    last_error = None

    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252", "gbk"]:
        try:
            with open(csv_path, encoding=enc, newline="") as f:
                reader = csv.reader(f, quotechar='"', skipinitialspace=True)
                rows = list(reader)

            if len(rows) < 2:
                continue

            headers = rows[0]
            data_rows = rows[1:]

            # 過濾掉欄數不符（嚴重損壞行），但容許多/少1欄
            expected = len(headers)
            clean_rows = []
            skipped = 0
            for r in data_rows:
                if abs(len(r) - expected) <= 1:
                    # 補齊或截斷至 expected 長度
                    r = (r + [""] * expected)[:expected]
                    clean_rows.append(r)
                else:
                    skipped += 1

            df = pd.DataFrame(clean_rows, columns=headers)
            print(f"✅ 讀取成功：{len(df)} 行，{len(df.columns)} 欄（encoding: {enc}）")
            if skipped:
                print(f"  ⚠️  跳過 {skipped} 行格式異常（欄數差距 >1）")
            break

        except (UnicodeDecodeError, Exception) as e:
            last_error = e
            continue

    if df is None:
        # 最後手段：pandas engine=python，on_bad_lines=skip
        for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252", "gbk"]:
            try:
                df = pd.read_csv(
                    csv_path, encoding=enc,
                    engine="python",
                    quotechar='"',
                    on_bad_lines="skip"
                )
                print(f"✅ 備用方式讀取成功：{len(df)} 行（encoding: {enc}）")
                print("  ⚠️  部分格式異常行已略過")
                break
            except Exception as e:
                last_error = e
                continue

    if df is None:
        print(f"❌ 無法讀取CSV：{last_error}")
        sys.exit(1)

    # 確保欄位存在
    for col in ["Email Type"] + BINARY_LABELS:
        if col not in df.columns:
            df[col] = ""

    # 搵未完成嘅行
    pending_mask = df["Email Type"].isna() | (df["Email Type"].astype(str).str.strip() == "")
    pending_indices = df[pending_mask].index.tolist()
    total_pending = len(pending_indices)

    print(f"📋 待標注：{total_pending} 行 / 已完成：{len(df) - total_pending} 行\n")
    print("操作提示：")
    print("  標注時輸入數字選Email Type，再逐個輸入0或1")
    print("  [s] = Skip，[q] = 儲存並退出\n")

    if total_pending == 0:
        print("🎉 所有行已標注完畢！")
        return

    completed = 0
    for loop_idx, row_idx in enumerate(pending_indices):
        email_text = str(df.at[row_idx, "Email Text"])
        display_email(loop_idx, total_pending, email_text)

        print_divider()

        # 選 Email Type
        print("📌  Email Type：")
        for i, t in enumerate(EMAIL_TYPES):
            print(f"  [{i+1}] {t}")

        while True:
            et_input = input("\n選擇 Email Type (1-4 / s=skip / q=quit): ").strip().lower()
            if et_input == "q":
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                print(f"\n✅ 已儲存，共完成 {completed} 行。")
                return
            if et_input == "s":
                print("  ⏭️  已Skip")
                break
            if et_input.isdigit() and 1 <= int(et_input) <= len(EMAIL_TYPES):
                email_type = EMAIL_TYPES[int(et_input) - 1]

                # 填 Binary Labels
                print(f"\n📌  Binary Labels（輸入 0 或 1，直接Enter = 0）：")
                label_values = {}
                valid = True
                for label in BINARY_LABELS:
                    while True:
                        val = input(f"  {label}: ").strip()
                        if val == "":
                            val = "0"
                        if val in ("0", "1"):
                            label_values[label] = int(val)
                            break
                        elif val.lower() == "q":
                            # 儲存並退出
                            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                            print(f"\n✅ 已儲存，共完成 {completed} 行。")
                            return
                        else:
                            print("    請輸入 0 或 1")

                # 寫入DataFrame
                df.at[row_idx, "Email Type"] = email_type
                for label, val in label_values.items():
                    df.at[row_idx, label] = val

                completed += 1
                print(f"  ✅ 已記錄")

                # 每5行自動儲存
                if completed % 5 == 0:
                    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                    print(f"  💾 Auto-saved ({completed} 行完成)")
                break
            else:
                print("  請輸入 1-4、s 或 q")

    # 最終儲存
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n🎉 全部完成！共標注 {completed} 行，已儲存至 {csv_path}")


if __name__ == "__main__":
    main()