from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import pandas as pd
from datetime import datetime
import urllib.request
import io

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 구글 시트 링크 (본인의 링크인지 다시 한번 확인하세요)
URL_NORMAL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRlp7nLeaypE0j2nKqqW_pU2UNQIl0S-4fx4GuK1H0rOaR0Qr5OkfTUV4cQ9QI7__tv8I-hKr0vTK0L/pub?gid=0&single=true&output=csv"
URL_SHORT = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRlp7nLeaypE0j2nKqqW_pU2UNQIl0S-4fx4GuK1H0rOaR0Qr5OkfTUV4cQ9QI7__tv8I-hKr0vTK0L/pub?gid=1947865401&single=true&output=csv"

def fetch_csv(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        csv_data = response.read().decode('utf-8')
        return pd.read_csv(io.StringIO(csv_data), dtype=str).fillna("")
    except Exception as e:
        print(f"Data fetch error: {e}")
        return pd.DataFrame()

@app.get("/")
async def index(request: Request):
    # 1. 일반 매물 데이터 처리
    df_normal = fetch_csv(URL_NORMAL)
    normal_data = {}
    total_normal_rooms = 0
    if not df_normal.empty:
        for _, row in df_normal.iterrows():
            area = row.get("지역", "")
            b_name = row.get("건물명", "")
            if not area or not b_name: continue
            
            if area not in normal_data: normal_data[area] = {}
            if b_name not in normal_data[area]:
                normal_data[area][b_name] = {
                    "address": row.get("주소", ""),
                    "landlord": row.get("건물주연락처", ""),
                    "entrance_pw": row.get("현관비번", ""),
                    "rooms": []
                }
            normal_data[area][b_name]["rooms"].append({
                "no": row.get("호실", ""), "type": row.get("타입", ""),
                "deposit": row.get("보증금", ""), "rent": row.get("월세", ""),
                "maintenance": row.get("관리비", ""), "pw": row.get("방비번", ""),
                "status": row.get("상태", ""), "note": row.get("비고", "")
            })
            total_normal_rooms += 1

    # 2. 단기 렌탈 데이터 처리
    df_short = fetch_csv(URL_SHORT)
    short_data = {}
    total_short_rooms = 0
    if not df_short.empty:
        for _, row in df_short.iterrows():
            area = row.get("지역", "")
            b_name = row.get("건물명", "")
            if not area or not b_name: continue
            
            if area not in short_data: short_data[area] = {}
            if b_name not in short_data[area]:
                short_data[area][b_name] = {
                    "address": row.get("번지", ""),
                    "entrance_pw": row.get("공동현관비번", ""),
                    "rooms": []
                }
            short_data[area][b_name]["rooms"].append({
                "no": row.get("호실", ""), "type": row.get("구조", ""),
                "deposit": row.get("예치금", ""), "rent": row.get("렌탈료", ""),
                "maintenance": row.get("기본관리비", ""), "options": row.get("옵션", ""),
                "months": row.get("렌탈개월수", ""), "note": row.get("특이사항", ""),
                "pw": row.get("세대비번", "")
            })
            total_short_rooms += 1

    context = {
        "request": request,
        "company_name": "수성 주택관리",
        "normal_data": normal_data,
        "short_data": short_data,
        "total_normal": total_normal_rooms,
        "total_short": total_short_rooms,
        "today": datetime.now().strftime("%Y.%m.%d")
    }
    return templates.TemplateResponse("index.html", context)
