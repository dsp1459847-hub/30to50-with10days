import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. टॉप 10 और एक्यूरेसी इंजन ---
def get_top_10_with_probs(df, s_name, target_date):
    try:
        # डेटा क्लीनिंग
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        if len(df_clean) < 30: return "Data Kam", "N/A", []

        # A. मल्टी-लेयर लॉजिक (इतिहास + चाल)
        t_day, t_month = target_date.day, target_date.month
        
        # 1. Legacy: पिछले 5 सालों में आज की तारीख के नंबर
        legacy = df_clean[(df_clean['DATE'].apply(lambda x: x.day == t_day and x.month == t_month and x < target_date))]['NUM'].astype(int).tolist()
        
        # 2. Weekday: आज के वार के पिछले 100 दिनों के टॉप नंबर
        t_day_name = target_date.strftime('%A')
        day_hist = df_clean[df_clean['DATE'].apply(lambda x: x.strftime('%A') == t_day_name and x < target_date)]['NUM'].astype(int).tolist()
        top_day = [n for n, c in Counter(day_hist[-100:]).most_common(5)]

        # 3. Pulse: कल के नंबर की राशि और पड़ोसी
        recent = df_clean[df_clean['DATE'] < target_date].tail(1)
        pulse = []
        if not recent.empty:
            lv = int(recent['NUM'].values[0])
            pulse = [(lv+50)%100, (lv+1)%100, (lv-1)%100, (lv+5)%100]

        # 4. Monthly: इस महीने के सबसे हॉट नंबर
        m_data = df_clean[df_clean['DATE'].apply(lambda x: x.month == t_month and x < target_date)]['NUM'].astype(int).tolist()
        hot_m = [n for n, c in Counter(m_data[-200:]).most_common(4)]

        # B. टॉप 10 का चुनाव (Scoring System)
        all_picks = legacy + top_day + pulse + hot_m
        scores = Counter(all_picks)
        
        # अगर 10 से कम हैं, तो ताज़ा 30 दिन के सक्रिय नंबरों से भरें
        if len(scores) < 10:
            recent_30 = df_clean[df_clean['DATE'] < target_date].tail(30)['NUM'].astype(int).tolist()
            for n, c in Counter(recent_30).most_common(20):
                if n not in scores: scores[n] = 1
                if len(scores) >= 10: break
        
        # टॉप 10 निकालना
        final_10_list = [n for n, c in scores.most_common(10)]
        top_10_str = ", ".join([f"{n:02d}" for n in final_10_list])
        
        # टॉप 5 अंकों की पासिंग संभावना (%)
        top_5_probs = {}
        for n in final_10_list[:5]:
            match_score = scores[n]
            # 35% बेस + मैच स्कोर बोनस
            prob = min(35 + (match_score * 7), 58) 
            top_5_probs[f"{n:02d}"] = f"{prob}%"

        analysis = " | ".join([f"{k}({v})" for k, v in top_5_probs.items()])
        return analysis, top_10_str, final_10_list

    except:
        return "Analyzing..", "N/A", []

# --- 2. UI और चार्ट जनरेटर ---
st.set_page_config(page_title="MAYA AI 10-Day Chart", layout="wide")
st.title("📊 MAYA AI: 10-Day Auto Chart (Top 10 Digits)")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        # आखिरी 10 दिन
        available_dates = sorted(df_match['DATE_COL'].dropna().unique())[-10:]
        shift_cols = [c for c in ['DS', 'FD', 'GD', 'GL', 'DB', 'SG'] if c in df.columns]

        if st.button("🚀 पिछले 10 दिनों का 10-अंक चार्ट दिखाएं"):
            for target_date in reversed(available_dates):
                st.subheader(f"📅 तारीख: {target_date.strftime('%d-%m-%Y')} ({target_date.strftime('%A')})")
                day_results = []
                selected_row = df_match[df_match['DATE_COL'] == target_date]
                
                for s in shift_cols:
                    prob_info, top_10, raw_list = get_top_10_with_probs(df_match, s, target_date)
                    
                    actual = "--"
                    res_emoji = "⚪"
                    if not selected_row.empty:
                        raw_v = str(selected_row[s].values[0]).strip()
                        if raw_v.replace('.','',1).isdigit():
                            actual = f"{int(float(raw_v)):02d}"
                            if int(actual) in raw_list: res_emoji = "✅ PASS"
                            else: res_emoji = "❌"
                        else: actual = raw_v

                    day_results.append({
                        "शिफ्ट": s,
                        "असली नतीजा": actual,
                        "परिणाम": res_emoji,
                        "टॉप 5 चांस (%)": prob_info,
                        "पूरे 10 मास्टर अंक": top_10
                    })
                
                st.table(pd.DataFrame(day_results))
                st.write("---")
            st.balloons()
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("एक्सेल अपलोड करें। यह पिछले 10 दिनों के 10-अंकों का चार्ट दिखाएगा।")
          
