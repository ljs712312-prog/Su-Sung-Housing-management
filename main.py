from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
from datetime import datetime
import urllib.request
import io

app = FastAPI()

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

# 🔗 구글 스프레드시트 CSV 출력 링크 (본인의 링크로 교체하세요)
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQcWQI2th_ihK8nx_qbdxB_1FeFo3Xhvqyr0lW-0m651YZ-GmvgmblPaML3fZB03qRMOphtuPA7j5aM/pub?output=csv"

def get_real_estate_data():
    try:
        req = urllib.request.Request(GOOGLE_SHEET_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        csv_data = response.read().decode('utf-8')
        df = pd.read_csv(io.StringIO(csv_data), dtype=str).fillna("")
        
        areas_dict = {}
        for _, row in df.iterrows():
            area = row.get("지역", "미지정")
            b_name = row.get("건물명", "이름없음")
            
            if area not in areas_dict:
                areas_dict[area] = {}
            
            if b_name not in areas_dict[area]:
                areas_dict[area][b_name] = {
                    "info": {
                        "address": row.get("주소", ""),
                        "landlord": row.get("건물주연락처", ""),
                        "entrance_pw": row.get("현관비번", "")
                    },
                    "rooms": []
                }
            
            areas_dict[area][b_name]["rooms"].append({
                "no": row.get("호실", ""),
                "type": row.get("타입", ""),
                "deposit": row.get("보증금", "0"),
                "rent": row.get("월세", "0"),
                "maintenance": row.get("관리비", "0"),
                "pw": row.get("방비번", ""),
                "status": row.get("상태", "상담문의"),
                "note": row.get("비고", "")
            })
        return areas_dict
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {}

@app.get("/")
async def index(request: Request):
    data = get_real_estate_data()
    
    # 요약 통계 계산
    total_buildings = sum(len(buildings) for buildings in data.values())
    total_listings = sum(len(b["rooms"]) for area in data.values() for b in area.values())
    
    context = {
        "request": request,
        "company_name": "수성 주택관리",
        "data": data,
        "total_buildings": total_buildings,
        "total_listings": total_listings,
        "today": datetime.now().strftime("%Y.%m.%d")
    }
    return templates.TemplateResponse("index.html", context)