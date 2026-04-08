import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. जीरो-पॉइंट रिकवरी इंजन (v50) ---
def get_v50_zero_point_logic(df, s_name, target_date):
    try:
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        # पिछले 15 दिनों का डेटा (Outlier ढूंढने के लिए)
        recent_all = df_clean[df_clean['DATE'] < target_date].tail(90)
        all_vals = recent_all['NUM'].astype(int).tolist()
        
        if len(all_vals) < 10: return "Data Kam", "N/A", []

        scores = Counter()

        # 🎯 स्ट्रैटेजी 1: 'कोल्ड नंबर' (The Hidden Numbers)
        # 30 के फेलियर के बाद अक्सर वो नंबर आते हैं जो पिछले 15 दिनों से गायब थे
        full_range = set(range(100))
        appeared_recently = set(all_vals[-60:]) # पिछले 10 दिन के नंबर
        hidden_nums = list(full_range - appeared_recently)
        
        for n in hidden_nums:
            scores[n] += 100 # गायब नंबरों को सबसे ज्यादा वजन

        # 🎯 स्ट्रैटेजी 2: 'हरूफ बैलेंस' (Haruf Balancing)
        # वो हरूफ़ (0-9) जो पिछले 3 दिन में नहीं दिखे
        last_20_digits = [d for n in all_vals[-20:] for d in [n//10, n%10]]
        digit_counts = Counter(last_20_digits)
        weak_digits = [d for d in range(10) if digit_counts[d] <= 1]
        
        for d in weak_digits:
            for i in range(10):
                scores[d*10 + i] += 50
                scores[i*10 + d] += 50

        # 🎯 स्ट्रैटेजी 3: 'कल की काट' (Immediate Mirror)
        last_val = all_vals[-1]
        r = lambda x: (x + 5) % 10
        m1 = (r(last_val//10)*10) + (last_val%10)
        m2 = (last_val//10*10) + r(last_val%10)
        scores[m1] += 80
        scores[m2] += 80

        # टॉप 10 चयन (Prioritize Hidden + Weak Digits)
        final_list = [n for n, s in scores.most_common(10)]
        top_10_str = ", ".join([f"{n:02d}" for n in sorted(final_list)])
        
        analysis = f"कमज़ोर अंक: {weak_digits} | फोकस: हिडन नंबर्स (Cold)"
        
        return analysis, top_10_str, final_list
    except:
        return "Resetting Logic..", "N/A", []

# --- 2. UI डैशबोर्ड ---
st.set_page_config(page_title="MAYA AI v50 Reset", layout="wide")
st.title("🛡️ MAYA AI: v50 Zero-Point Recovery")
st.markdown("### 30/0 फेलियर के बाद का 'महा-बदलाव' इंजन")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        target_date = st.date_input("📅 तारीख चुनें:", df_match['DATE_COL'].dropna().max())
        
        if st.button("🚀 जीरो-पॉइंट स्कैन रन करें"):
            shift_cols = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG']
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            
            report = []
            for s in shift_cols:
                if s not in df.columns: continue
                info, picks, raw_list = get_v50_zero_point_logic(df_match, s, target_date)
                
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    v = str(selected_row[s].values[0]).strip()
                    if v.replace('.','',1).isdigit():
                        actual = f"{int(float(v)):02d}"
                        res_emoji = "✅ PASS" if int(actual) in raw_list else "❌"
                    else: actual = v

                report.append({"शिफ्ट": s, "असली नतीजा": actual, "परिणाम": res_emoji, "एनालिसिस": info, "टॉप 10 रिकवरी अंक": picks})
            
            st.table(pd.DataFrame(report))
            st.warning("🔄 **सिस्टम रिसेट:** जब पुराना पैटर्न 100% फेल होता है, तो गेम 'Hidden Frequency' पर चला जाता है। यह कोड उन्हीं नंबरों को पकड़ रहा है जो बहुत दिनों से नहीं आए।")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
        
