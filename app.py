import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. एडवांस डिजिट-फिल्टर लॉजिक (v45) ---
def get_v45_digit_filter_logic(df, s_name, target_date):
    try:
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        all_vals = df_clean[df_clean['DATE'] < target_date]['NUM'].astype(int).tolist()
        if len(all_vals) < 30: return "Data Kam", "N/A", []

        # पिछला नतीजा
        last_v = all_vals[-1]
        d_last, e_last = last_v // 10, last_v % 10 # दहाई और इकाई

        # --- A. दहाई अंक (Dahine Ank) विश्लेषण ---
        # नियम: Odd/Even, Big(5-9)/Small(0-4), Rashi
        recent_d = [n // 10 for n in all_vals[-20:]]
        d_mode = Counter(recent_d).most_common(3)
        target_d = [d for d, c in d_mode]
        # राशि और काट जोड़ना
        target_d.extend([(d_last + 5) % 10, d_last]) 
        target_d = list(set(target_d))

        # --- B. इकाई अंक (Ekai Ank) विश्लेषण ---
        recent_e = [n % 10 for n in all_vals[-20:]]
        e_mode = Counter(recent_e).most_common(3)
        target_e = [e for e, c in e_mode]
        # आपकी थ्योरी: अगर कल 3 था तो आज 0,5,8,9 (Digit Mapping)
        mapping = {3:[0,5,8,9], 0:[8,9,5], 1:[6,2,7], 2:[7,3,8], 4:[9,0,5], 
                   5:[0,1,6], 6:[1,2,7], 7:[2,3,8], 8:[3,4,9], 9:[4,5,0]}
        if e_last in mapping: target_e.extend(mapping[e_last])
        target_e = list(set(target_e))

        # --- C. फिल्टरिंग और जोड़ी निर्माण ---
        candidate_jodi = []
        for d in target_d:
            for e in target_e:
                jodi = d * 10 + e
                
                # फिल्टर: JODI, DOUBLE (11, 22), PALAT
                score = 0
                if jodi == last_v: score += 10 # Repeat
                if jodi == (e_last * 10 + d_last): score += 50 # Palat logic
                if d == e: score += 30 # Double (Jora)
                
                # Big/Small & Odd/Even Balance
                if (jodi > 50 and last_v <= 50) or (jodi <= 50 and last_v > 50):
                    score += 40 # Transition bonus
                
                candidate_jodi.append((jodi, score))

        # स्कोर के आधार पर टॉप 10
        final_picks = [n for n, s in sorted(candidate_jodi, key=lambda x: x[1], reverse=True)[:10]]
        
        # अगर 10 नहीं हुए, तो रैंडम रोटेशन से भरें
        if len(final_picks) < 10:
            for n in range(100):
                if n not in final_picks: final_picks.append(n)
                if len(final_picks) >= 10: break

        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_picks)])
        analysis = f"दहाई: {target_d} | इकाई: {target_e} | पिछले से पलट/जोड़ा पर फोकस"
        
        return analysis, top_10_str, final_picks
    except:
        return "Filtering..", "N/A", []

# --- 2. UI डैशबोर्ड ---
st.set_page_config(page_title="MAYA AI Digit-Filter", layout="wide")
st.title("🛡️ MAYA AI: v45 Multi-Dimensional Digit Filter")
st.markdown("### दहाई और इकाई पर अलग-अलग नियमों का सटीक अनुप्रयोग")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        target_date = st.date_input("📅 तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 एडवांस फिल्टर रन करें"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            report = []
            for s in shift_cols:
                if s not in df.columns: continue
                info, picks, raw_list = get_v45_digit_filter_logic(df_match, s, target_date)
                
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    v = str(selected_row[s].values[0]).strip()
                    if v.replace('.','',1).isdigit():
                        actual = f"{int(float(v)):02d}"
                        res_emoji = "✅ PASS" if int(actual) in raw_list else "❌"
                    else: actual = v

                report.append({"शिफ्ट": s, "असली": actual, "परिणाम": res_emoji, "डिजिट विश्लेषण": info, "टॉप 10 जोड़ी": picks})
            
            st.table(pd.DataFrame(report))
            st.info("💡 **प्रो टिप:** यह कोड दहाई को 'बेस' मानकर इकाई की 'मैपिंग' करता है, जिससे फालतू नंबर हट जाते हैं।")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
                
