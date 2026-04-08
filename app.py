import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. A/B ग्रुप ट्रांजिशन इंजन (v44) ---
def get_v44_group_transition_logic(df, s_name, target_date):
    try:
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        all_vals = df_clean[df_clean['DATE'] < target_date]['NUM'].astype(int).tolist()
        if len(all_vals) < 50: return "Data Kam", "N/A", []

        # A. ग्रुप ट्रांजिशन हिस्ट्री बनाना
        # 0-49 = A, 50-99 = B
        def get_g(n): return "A" if 0 <= n <= 49 else "B"
        
        group_series = [get_g(n) for n in all_vals]
        
        # ट्रांजिशन मैप (A के बाद क्या आया, B के बाद क्या आया)
        trans_map = {"A": [], "B": []}
        for i in range(len(group_series) - 1):
            curr_g = group_series[i]
            next_g = group_series[i+1]
            trans_map[curr_g].append(next_g)

        # B. आज के लिए 'टारगेट ग्रुप' का फैसला
        last_val = all_vals[-1]
        last_group = get_g(last_val)
        
        # इतिहास से पूछो: पिछले ग्रुप (last_group) के बाद सबसे ज्यादा क्या आया?
        counts = Counter(trans_map[last_group])
        target_group = counts.most_common(1)[0][0] # A या B में से जो सबसे ज्यादा बार आया

        # C. डिजिट ट्रांजिशन (0-9 Mapping) - जैसा आपने पहले बताया था
        digit_trans = {i: [] for i in range(10)}
        for i in range(len(all_vals) - 1):
            c_ds = [all_vals[i] // 10, all_vals[i] % 10]
            n_ds = [all_vals[i+1] // 10, all_vals[i+1] % 10]
            for d in c_ds: digit_trans[d].extend(n_ds)

        y_ds = [last_val // 10, last_val % 10]
        target_digits = []
        for d in y_ds:
            target_digits.extend([digit for digit, count in Counter(digit_trans[d]).most_common(5)])
        
        target_digits = list(set(target_digits))

        # D. फाइनल नंबरों का चयन (टारगेट ग्रुप के हिसाब से)
        candidate_nums = []
        for d in target_digits:
            for i in range(10):
                n1, n2 = d * 10 + i, i * 10 + d
                if get_g(n1) == target_group: candidate_nums.append(n1)
                if get_g(n2) == target_group: candidate_nums.append(n2)

        # स्कोरिंग (ताज़ा इतिहास में पकड़)
        final_picks = [n for n, c in Counter([n for n in candidate_nums if n in all_vals[-300:]]).most_common(10)]
        
        # अगर 10 नहीं पूरे हुए तो टारगेट ग्रुप के हॉट नंबर जोड़ें
        if len(final_picks) < 10:
            hot_in_group = [n for n, c in Counter(all_vals[-100:]).most_common(30) if get_g(n) == target_group]
            for n in hot_in_group:
                if n not in final_picks: final_picks.append(n)
                if len(final_picks) >= 10: break

        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_picks)])
        analysis = f"पिछला {last_group} था -> आज {target_group} के चांस ज्यादा हैं"
        
        return analysis, top_10_str, final_picks
    except:
        return "Analyzing Transitions..", "N/A", []

# --- 2. UI डैशबोर्ड ---
st.set_page_config(page_title="MAYA AI Group Transition", layout="wide")
st.title("🛡️ MAYA AI: v44 Group Transition Engine")
st.markdown("### ए (0-49) और बी (50-99) के बदलाव की चाल पर आधारित")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        target_date = st.date_input("📅 विश्लेषण की तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 ग्रुप ट्रांजिशन स्कैन शुरू करें"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            report = []
            for s in shift_cols:
                if s not in df.columns: continue
                info, picks, raw_list = get_v44_group_transition_logic(df_match, s, target_date)
                
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    v = str(selected_row[s].values[0]).strip()
                    if v.replace('.','',1).isdigit():
                        actual = f"{int(float(v)):02d}"
                        res_emoji = "✅ PASS" if int(actual) in raw_list else "❌"
                    else: actual = v

                report.append({"शिफ्ट": s, "असली नतीजा": actual, "परिणाम": res_emoji, "ग्रुप चाल विश्लेषण": info, "टॉप 10 अंक": picks})
            
            st.table(pd.DataFrame(report))
            st.info("💡 **ट्रांजिशन लॉजिक:** कोड यह देख रहा है कि अगर कल ग्रुप A आया था, तो इतिहास में उसके बाद A ज्यादा आया है या B। प्रेडिक्शन उसी 'अगले ग्रुप' की दी जा रही है।")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
        
