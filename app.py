import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. टॉप 10 और एक्यूरेसी इंजन ---
def get_top_10_logic(df, s_name, target_date):
    try:
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        if len(df_clean) < 15: return "Data Kam", "N/A", []

        # लॉजिक लेयर्स
        t_day, t_month = target_date.day, target_date.month
        legacy = df_clean[(df_clean['DATE'].apply(lambda x: x.day == t_day and x.month == t_month and x < target_date))]['NUM'].astype(int).tolist()
        
        t_day_name = target_date.strftime('%A')
        day_hist = df_clean[df_clean['DATE'].apply(lambda x: x.strftime('%A') == t_day_name and x < target_date)]['NUM'].astype(int).tolist()
        top_day = [n for n, c in Counter(day_hist[-100:]).most_common(5)]

        recent = df_clean[df_clean['DATE'] < target_date].tail(1)
        pulse = []
        if not recent.empty:
            lv = int(recent['NUM'].values[0])
            pulse = [(lv+50)%100, (lv+1)%100, (lv-1)%100, (lv+5)%100]

        all_picks = legacy + top_day + pulse
        scores = Counter(all_picks)
        
        if len(scores) < 10:
            recent_30 = df_clean[df_clean['DATE'] < target_date].tail(30)['NUM'].astype(int).tolist()
            for n, c in Counter(recent_30).most_common(20):
                if n not in scores: scores[n] = 1
                if len(scores) >= 10: break
        
        final_10 = [n for n, c in scores.most_common(10)]
        top_5_probs = {f"{n:02d}": f"{min(35 + (scores[n] * 7), 58)}%" for n in final_10[:5]}
        
        return " | ".join([f"{k}({v})" for k, v in top_5_probs.items()]), ", ".join([f"{n:02d}" for n in final_10]), final_10
    except:
        return "Analyzing..", "N/A", []

# --- 2. UI और अप्रैल चार्ट डिस्प्ले ---
st.set_page_config(page_title="MAYA AI April Pro", layout="wide")
st.title("🎯 MAYA AI: April Chart & Date Selector")

uploaded_file = st.file_uploader("📂 अपनी Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        df = pd.read_excel(io.BytesIO(uploaded_file.getvalue()), engine='openpyxl')
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        # 💡 स्मार्ट अप्रैल फ़िल्टर: सिर्फ अप्रैल महीने का डेटा जिसमें रिजल्ट मौजूद हो
        april_data = df_match[(df_match['DATE_COL'].apply(lambda x: x.month == 4 if pd.notnull(x) else False))]
        valid_april_dates = sorted(april_data['DATE_COL'].dropna().unique())

        # विकल्प 1: तारीख चुनें
        st.subheader("🔍 तारीख के हिसाब से देखें")
        col1, col2 = st.columns([2,1])
        with col1:
            custom_date = st.date_input("विश्लेषण के लिए तारीख चुनें:", datetime.date(2026, 4, 8))
        
        if st.button("🚀 इस तारीख का विश्लेषण करें"):
            st.write(f"### 📅 {custom_date.strftime('%d-%m-%Y')} का रिजल्ट और प्रेडिक्शन")
            shift_cols = [c for c in ['DS', 'FD', 'GD', 'GL', 'DB', 'SG'] if c in df.columns]
            day_results = []
            selected_row = df_match[df_match['DATE_COL'] == custom_date]
            for s in shift_cols:
                p_info, t_10, r_list = get_top_10_logic(df_match, s, custom_date)
                actual = "--"
                res_emoji = "⚪"
                if not selected_row.empty:
                    raw_v = str(selected_row[s].values[0]).strip()
                    if raw_v.replace('.','',1).isdigit():
                        actual = f"{int(float(raw_v)):02d}"
                        res_emoji = "✅ PASS" if int(actual) in r_list else "❌"
                    else: actual = raw_v
                day_results.append({"शिफ्ट": s, "असली": actual, "परिणाम": res_emoji, "टॉप 5 (%)": p_info, "टॉप 10 अंक": t_10})
            st.table(pd.DataFrame(day_results))

        st.markdown("---")

        # विकल्प 2: अप्रैल महीने का चार्ट
        if st.button("📅 अप्रैल महीने का पूरा चार्ट दिखाएं"):
            st.write("### 📊 अप्रैल 2026 का चार्ट (ताज़ा से पुराना)")
            for target_date in reversed(valid_april_dates):
                st.write(f"**तारीख: {target_date.strftime('%d-%m-%Y')} ({target_date.strftime('%A')})**")
                shift_cols = [c for c in ['DS', 'FD', 'GD', 'GL', 'DB', 'SG'] if c in df.columns]
                day_results = []
                selected_row = df_match[df_match['DATE_COL'] == target_date]
                for s in shift_cols:
                    p_info, t_10, r_list = get_top_10_logic(df_match, s, target_date)
                    actual = "--"
                    res_emoji = "⚪"
                    if not selected_row.empty:
                        raw_v = str(selected_row[s].values[0]).strip()
                        if raw_v.replace('.','',1).isdigit():
                            actual = f"{int(float(raw_v)):02d}"
                            res_emoji = "✅ PASS" if int(actual) in r_list else "❌"
                        else: actual = raw_v
                    day_results.append({"शिफ्ट": s, "असली": actual, "परिणाम": res_emoji, "टॉप 5 (%)": p_info, "टॉप 10 अंक": t_10})
                st.table(pd.DataFrame(day_results))
                st.markdown("---")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("अप्रैल महीने का डेटा देखने के लिए एक्सेल अपलोड करें।")
        
