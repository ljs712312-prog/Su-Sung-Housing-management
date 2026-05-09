import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 페이지 설정
st.set_page_config(page_title="수성 주택관리", page_icon="🏢", layout="wide")

DATA_FILE = "data.xlsx"

def clean_val(val):
    """데이터에서 소수점 .0을 제거하고 문자열로 변환"""
    if pd.isna(val) or val == "":
        return ""
    s = str(val).strip()
    if s.endswith('.0'):
        return s[:-2]
    return s

def init_or_load_data():
    """엑셀 파일이 없으면 양식을 생성하고, 있으면 데이터를 불러옵니다."""
    if not os.path.exists(DATA_FILE):
        # 엑셀 기본 양식 컬럼 정의
        columns = [
            "지역", "건물명", "주소", "건물주연락처", "현관비번",
            "호실", "타입", "보증금", "월세", "관리비",
            "방비번", "세입자연락처", "상태", "비고"
        ]
        df = pd.DataFrame(columns=columns)
        # 빈 양식 엑셀 파일 생성
        df.to_excel(DATA_FILE, index=False)
        return df
    else:
        # 엑셀 파일 로드 (모든 데이터를 문자열로 처리)
        df = pd.read_excel(DATA_FILE, dtype=str).fillna("")
        for col in df.columns:
            df[col] = df[col].apply(clean_val)
        return df

# 데이터 로드
df = init_or_load_data()

current_time = datetime.now().strftime("%Y.%m.%d 기준")
current_hour = datetime.now().strftime("%H:%M")

st.title("🏢 수성 주택관리 (로컬 엑셀 버전)")
st.caption(f"업데이트: {current_time} {current_hour}")

tab1, tab2 = st.tabs(["📋 요약 보기", "✏️ 데이터 직접 수정"])

with tab1:
    if df.empty:
        st.warning(f"데이터가 없습니다. '{DATA_FILE}' 파일을 열어 데이터를 입력하거나 '데이터 직접 수정' 탭을 이용하세요.")
    else:
        total_buildings = df['건물명'].nunique()
        total_rooms = len(df)
        
        col1, col2 = st.columns(2)
        col1.metric("총 건물 수", f"{total_buildings}개")
        col2.metric("총 호실 수", f"{total_rooms}개")
        
        st.divider()

        areas = df['지역'].unique()
        for area in areas:
            if not area: continue
            st.subheader(f"📍 {area}")
            
            area_df = df[df['지역'] == area]
            buildings = area_df['건물명'].unique()
            
            for bldg in buildings:
                if not bldg: continue
                bldg_df = area_df[area_df['건물명'] == bldg]
                
                bldg_address = bldg_df['주소'].iloc[0] if '주소' in bldg_df.columns else ""
                landlord_phone = bldg_df['건물주연락처'].iloc[0] if '건물주연락처' in bldg_df.columns else ""
                door_pw = bldg_df['현관비번'].iloc[0] if '현관비번' in bldg_df.columns else ""
                
                with st.expander(f"🏠 {bldg} ({len(bldg_df)}개 호실)"):
                    st.markdown(f"**주소:** {bldg_address} | **건물주:** {landlord_phone} | **현관비번:** {door_pw}")
                    
                    display_cols = ["호실", "타입", "보증금", "월세", "관리비", "방비번", "세입자연락처", "상태", "비고"]
                    existing_cols = [c for c in display_cols if c in bldg_df.columns]
                    st.dataframe(bldg_df[existing_cols], use_container_width=True, hide_index=True)

with tab2:
    st.markdown("### 웹에서 데이터 수정하기")
    st.info("여기서 수정한 내용은 컴퓨터에 있는 `data.xlsx` 파일에 즉시 덮어쓰기 됩니다.")
    
    # st.data_editor로 데이터 수정 창 제공
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=600)
    
    if st.button("💾 엑셀 파일에 저장하기", type="primary"):
        for col in edited_df.columns:
            edited_df[col] = edited_df[col].apply(clean_val)
        
        # 수정한 데이터를 엑셀로 저장
        edited_df.to_excel(DATA_FILE, index=False)
        st.success(f"{DATA_FILE}에 성공적으로 저장되었습니다!")
        st.rerun()