import pandas as pd
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from datetime import datetime
import urllib.request
import io

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🔗 [중요] 구글 시트의 '웹에 게시' 링크를 각각의 시트(탭)에 맞춰 넣어주세요.
URL_NORMAL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRlp7nLeaypE0j2nKqqW_pU2UNQIl0S-4fx4GuK1H0rOaR0Qr5OkfTUV4cQ9QI7__tv8I-hKr0vTK0L/pub?gid=0&single=true&output=csv"
URL_SHORT = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRlp7nLeaypE0j2nKqqW_pU2UNQIl0S-4fx4GuK1H0rOaR0Qr5OkfTUV4cQ9QI7__tv8I-hKr0vTK0L/pub?gid=1947865401&single=true&output=csv"

def clean_val(val):
    """데이터 소수점 제거 및 공백 정리"""
    if pd.isna(val) or val == "":
        return ""
    s = str(val).strip()
    if s.endswith('.0'):
        return s[:-2]
    return s

def get_processed_data(url):
    """지정된 URL에서 시트 데이터를 가져와 지역별/건물별로 정리합니다."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        csv_data = response.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data), dtype=str).fillna("")
        
        areas_dict = {}
        for _, row in df.iterrows():
            area = clean_val(row.get("지역", ""))
            b_name = clean_val(row.get("건물명", ""))
            
            if not area or not b_name: continue
                
            if area not in areas_dict:
                areas_dict[area] = {}
                
            if b_name not in areas_dict[area]:
                areas_dict[area][b_name] = {
                    "b_name": b_name,
                    "address": clean_val(row.get("주소", "")),
                    "tenant_phone": clean_val(row.get("임차인연락처", "")),
                    "entrance_pw": clean_val(row.get("현관비번", "")),
                    "rooms": []
                }
            
            areas_dict[area][b_name]["rooms"].append({
                "no": clean_val(row.get("호실", "")),
                "type": clean_val(row.get("타입", "")),
                "deposit": clean_val(row.get("보증금", "")),
                "rent": clean_val(row.get("월세", "")),
                "maintenance": clean_val(row.get("관리비", "")),
                "unit_pw": clean_val(row.get("세대비번", "")),
                "status": clean_val(row.get("상태", "")),
                "note": clean_val(row.get("비고", ""))
            })
            
        return areas_dict
    except Exception as e:
        print(f"❌ 데이터 로드 오류: {e}")
        return {}

@app.get("/")
async def read_root(request: Request):
    # 일반 및 단기 데이터를 각각 로드
    normal_data = get_processed_data(URL_NORMAL)
    short_data = get_processed_data(URL_SHORT)
    
    # 통계 계산
    total_normal = sum(len(b["rooms"]) for a in normal_data.values() for b in a.values())
    total_short = sum(len(b["rooms"]) for a in short_data.values() for b in a.values())
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={
            "company_name": "수성 주택관리",
            "normal_data": normal_data,
            "short_data": short_data,
            "total_normal": total_normal,
            "total_short": total_short,
            "today": datetime.now().strftime("%Y.%m.%d")
        }
    )
