import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import datetime
import io

# --- 1. हाई-एक्यूरेसी बूस्टर इंजन (Static-Vision Fix) ---
def get_high_accuracy_picks(df, s_name, target_date):
    try:
        # डेटा क्लीनिंग
        df_clean = df.iloc[:, [1, df.columns.get_loc(s_name)]].copy()
        df_clean.columns = ['DATE', 'NUM']
        df_clean['DATE'] = pd.to_datetime(df_clean['DATE'], dayfirst=True, errors='coerce').dt.date
        df_clean['NUM'] = pd.to_numeric(df_clean['NUM'], errors='coerce')
        df_clean = df_clean.dropna(subset=['DATE', 'NUM'])

        # 🛑 CRITICAL FIX: केवल चुनी गई तारीख से पहले का डेटा इस्तेमाल करना
        # इससे आज का डेटा डालने पर भी प्रेडिक्शन नहीं बदलेगी
        hist_data = df_clean[df_clean['DATE'] < target_date]
        
        # आज का डेटा (सिर्फ प्रेडिक्शन की तुलना के लिए)
        current_day_data = df_clean[df_clean['DATE'] == target_date]

        if len(hist_data) < 50:
            return "History Data Kam", "N/A", []

        # A. साल दर साल (Yearly Connection) - सिर्फ पुराने सालों का डेटा
        t_day, t_month = target_date.day, target_date.month
        yearly_list = hist_data[(hist_data['DATE'].apply(lambda x: x.day == t_day and x.month == t_month))]['NUM'].astype(int).tolist()

        # B. वार की ताकत (Day-wise Power) - पुराने डेटा से आज के वार का टॉप 3
        t_day_name = target_date.strftime('%A')
        day_history = hist_data[hist_data['DATE'].apply(lambda x: x.strftime('%A')) == t_day_name]['NUM'].astype(int).tolist()
        top_3_day = [n for n, c in Counter(day_history[-100:]).most_common(3)]

        # C. कल की चाल (Last Result from History)
        last_val = int(hist_data.iloc[-1]['NUM'])
        mirror = (last_val + 50) % 100
        neighbors = [(last_val + 1) % 100, (last_val - 1) % 100]

        # D. महीने का किंग (Monthly Hot from History)
        monthly_data = hist_data[hist_data['DATE'].apply(lambda x: x.month == t_month)]['NUM'].astype(int).tolist()
        hot_month = Counter(monthly_data[-200:]).most_common(1)[0][0]

        # --- मास्टर पूल निर्माण ---
        combined_pool = list(set(yearly_list + top_3_day + [mirror] + neighbors + [hot_month]))
        
        # टॉप 8 नंबर (Fixed Selection)
        final_picks_raw = combined_pool[:8]
        final_picks_formatted = [f"{n:02d}" for n in final_picks_raw]
        
        analysis = f"📅 {t_day_name} HOT: {top_3_day[0]:02d} | 🪞 मिरर: {mirror:02d} | जंप: {neighbors[0]:02d}"
        
        return analysis, " | ".join(final_picks_formatted), final_picks_raw

    except Exception as e:
        return f"Error: {str(e)}", "N/A", []

# --- 2. UI सेटअप ---
st.set_page_config(page_title="MAYA AI Static Vision", layout="wide")
st.title("🛡️ MAYA AI: v55 Static-Vision Booster")
st.info("💡 **सुधार अपडेट:** अब डेटा अपडेट करने के बाद भी प्रेडिक्शन नहीं बदलेगी क्योंकि कोड केवल चुनी गई तारीख से पहले का इतिहास देखता है।")

uploaded_file = st.file_uploader("📂 अपनी 5 साल की Excel फ़ाइल अपलोड करें", type=['xlsx'])

if uploaded_file:
    try:
        data_bytes = uploaded_file.getvalue()
        df = pd.read_excel(io.BytesIO(data_bytes), engine='openpyxl')
        
        df_match = df.copy()
        df_match['DATE_COL'] = pd.to_datetime(df_match.iloc[:, 1], dayfirst=True, errors='coerce').dt.date
        
        all_shifts = ['DS', 'FD', 'GD', 'GL', 'DB', 'SG', 'ZA']
        shift_cols = [c for c in all_shifts if c in df.columns]

        # डिफॉल्ट तारीख आज की (9 अप्रैल 2026)
        target_date = st.date_input("📅 विश्लेषण की तारीख चुनें:", datetime.date.today())

        if st.button("🚀 फिक्स्ड प्रेडिक्शन स्कैन"):
            selected_row = df_match[df_match['DATE_COL'] == target_date]
            results_list = []

            for s in shift_cols:
                logic_info, top_picks_str, raw_picks = get_high_accuracy_picks(df_match, s, target_date)
                
                actual_val = "--"
                res_emoji = "⚪"
                
                if not selected_row.empty:
                    raw_v = str(selected_row[s].values[0]).strip()
                    if raw_v.replace('.','',1).isdigit():
                        val_int = int(float(raw_v))
                        actual_val = f"{val_int:02d}"
                        # असली चेकिंग: क्या प्रेडिक्शन में यह नंबर था?
                        res_emoji = "✅ PASS" if val_int in raw_picks else "❌"
                    else:
                        actual_val = raw_v

                results_list.append({
                    "Shift": s,
                    "📍 Result": actual_val,
                    "परिणाम": res_emoji,
                    "📊 मास्टर लॉजिक": logic_info,
                    "🌟 टॉप सिलेक्शन": top_picks_str
                })

            st.table(pd.DataFrame(results_list))
            st.warning("🔒 **Static vision active:** प्रेडिक्शन अब फिक्स है। आप एक्सेल में कल का डेटा भी डाल देंगे तो भी आज की प्रेडिक्शन नहीं बदलेगी।")
            st.balloons()

    except Exception as e:
        st.error(f"Error: {e}")
                
