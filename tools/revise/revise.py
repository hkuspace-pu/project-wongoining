"""
修復CSV：將被拆散的email row重新合併
原理：正常row有9欄，被拆散的base64行只有1欄，
      找到開頭是 quote 的行，將之後的1-col行全部合併回去
"""
import csv
import sys

def fix_csv(input_path, output_path):
    with open(input_path, encoding='utf-8', newline='', errors='replace') as f:
        content = f.read()

    # 用 csv.reader 讀，skipinitialspace
    import io
    reader = csv.reader(io.StringIO(content), quotechar='"', skipinitialspace=True)
    raw_rows = list(reader)

    header = raw_rows[0]
    expected_cols = len(header)  # 9
    print(f"Header: {header}")
    print(f"Expected cols: {expected_cols}")
    print(f"Raw rows (before fix): {len(raw_rows) - 1}")

    fixed_rows = []
    i = 1
    while i < len(raw_rows):
        row = raw_rows[i]
        if len(row) == expected_cols:
            # 正常row，直接加
            fixed_rows.append(row)
            i += 1
        elif len(row) < expected_cols:
            # 可能係被拆散的row，嘗試合併後面的行
            merged = row[:]
            # 如果第一欄唔係空，嘗試合併
            while i + 1 < len(raw_rows):
                next_row = raw_rows[i + 1]
                if len(next_row) == 1 and len(merged) < expected_cols:
                    # 單欄行，合併入第一欄
                    merged[0] = merged[0] + '\n' + next_row[0]
                    i += 1
                elif len(next_row) == expected_cols:
                    break
                elif len(next_row) < expected_cols and len(merged) < expected_cols:
                    # 多欄但唔夠，繼續合併
                    merged[0] = merged[0] + '\n' + next_row[0]
                    i += 1
                else:
                    break
            
            # pad/trim to expected
            merged = (merged + [''] * expected_cols)[:expected_cols]
            fixed_rows.append(merged)
            i += 1
        else:
            # 多咗欄，截斷
            fixed_rows.append(row[:expected_cols])
            i += 1

    print(f"Fixed rows: {len(fixed_rows)}")

    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        writer.writerows(fixed_rows)

    print(f"✅ 已儲存至 {output_path}")

if __name__ == '__main__':
    inp = sys.argv[1] if len(sys.argv) > 1 else 'new_3.csv'
    out = sys.argv[2] if len(sys.argv) > 2 else 'fixed_' + inp
    fix_csv(inp, out)