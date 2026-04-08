import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. अंकों की चाल (Digit Transition Logic) ---
def get_digit_logic_v40(df, s_name, target_date):
    try:
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        # A. आपकी 'अंकों वाली थ्योरी' के नियम (Digit Transition Rules)
        mapping_rules = {
            3: [0, 5, 8, 9], 
            0: [8, 9, 5],
            1: [6, 2, 7],
            2: [7, 3, 8],
            4: [9, 0, 5],
            5: [0, 1, 6],
            6: [1, 2, 7],
            7: [2, 3, 8],
            8: [3, 4, 9],
            9: [4, 5, 0]
        }

        # B. पिछला रिजल्ट चेक करना
        yesterday_data = df_clean[df_clean['DATE'] < target_date].tail(1)
        if yesterday_data.empty: return "No Data", "N/A", []
        
        last_val = int(yesterday_data['NUM'].values[0])
        h_andar, h_bahar = last_val // 10, last_val % 10

        # C. अंकों का चयन (Target Digits)
        target_digits = set()
        for h in [h_andar, h_bahar]:
            if h in mapping_rules:
                target_digits.update(mapping_rules[h])

        # D. 10 सबसे मजबूत नंबर बनाना (00-99)
        # हम उन नंबरों को चुनेंगे जिनमें ये Target Digits शामिल हैं
        potential_nums = []
        for d in target_digits:
            for i in range(10):
                potential_nums.append(d * 10 + i) # अंदर का अंक
                potential_nums.append(i * 10 + d) # बाहर का अंक
        
        # स्कोरिंग (5 साल के इतिहास के साथ मिलान)
        hist_recent = df_clean[df_clean['DATE'] < target_date].tail(200)['NUM'].astype(int).tolist()
        final_scores = Counter([n for n in potential_nums if n in hist_recent or n % 11 == 0])
        
        # अगर 10 से कम हैं, तो रैंडमली उस ग्रुप के नंबर जोड़ें
        if len(final_scores) < 10:
            for n in potential_nums:
                if n not in final_scores:
                    final_scores[n] = 1
                if len(final_scores) >= 10: break

        final_10 = [n for n, c in final_scores.most_common(10)]
        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_10)])
        
        analysis = f"🎯 कल {last_val:02d} था -> आज के अंक: {list(target_digits)}"
        
        return analysis, top_10_str, final_10
    except Exception as e:
        return f"Error: {e}", "N/A", []

# --- 2. UI सेटअप ---
st.set_page_config(page_title="MAYA AI Digit Fix", layout="wide")
st.title("🛡️ MAYA AI: Digit Mapping v40 (Final Fix)")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        target_date = st.date_input("📅 तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 विश्लेषण शुरू करें"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            day_results = []
            for s in shift_cols:
                if s not in df.columns: continue
                info, t_10, r_list = get_digit_logic_v40(df_match, s, target_date)
                
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    try:
                        v = str(selected_row[s].values[0]).strip()
                        if v.replace('.','',1).isdigit():
                            actual = f"{int(float(v)):02d}"
                            res_emoji = "✅ PASS" if int(actual) in r_list else "❌"
                        else: actual = v
                    except: pass

                day_results.append({"शिफ्ट": s, "असली नतीजा": actual, "परिणाम": res_emoji, "मैपिंग": info, "टॉप 10 अंक": t_10})
            
            st.table(pd.DataFrame(day_results))
            st.success("✅ **फिक्स:** अब सिर्फ 00-99 के बीच के 10 अंक ही दिखाई देंगे।")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
            
