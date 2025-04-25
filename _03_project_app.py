import streamlit as st
import pandas as pd
import mysql.connector
import plotly.express as px
import requests
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
KAKAO_API_KEY = os.getenv("KAKAO_API_KEY")

# DB 연결 함수
def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='skn14',
        password='skn14',
        database='projectdb'
    )

# 카카오맵 주변 장소 검색 함수
def search_places_nearby(lat, lng, category='CE7', radius=1000):
    url = "https://dapi.kakao.com/v2/local/search/category.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {
        "category_group_code": category,
        "x": lng,
        "y": lat,
        "radius": radius
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()["documents"]
    else:
        return []

# 충전소 요약 데이터
@st.cache_data(show_spinner="\ud83d\udcca 데이터를 불러오는 중입니다...")
def load_summary_data():
    conn = get_connection()
    query = """
    SELECT 
        r.zname AS region,
        COUNT(DISTINCT s.statId) AS station_count,
        e.vehicle_count
    FROM stations s
    JOIN region_map r ON s.zcode = r.zcode
    JOIN ev_registered_yearly e ON r.zname = e.zname
    WHERE e.year = 2025
    GROUP BY r.zname, e.vehicle_count
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df["보급률(%)"] = (df["station_count"] / df["vehicle_count"]) * 100
    return df

# 전체 충전소 주소 → 시/구/동 추출
@st.cache_data(show_spinner="\ud83d\udd0d 충전소 주소를 불러오는 중입니다...")
def load_all_address_data():
    conn = get_connection()
    df = pd.read_sql("SELECT statId, statNm, addr, lat, lng FROM stations", conn)
    conn.close()
    addr_split = df["addr"].str.split(" ", expand=True)
    df["시"] = addr_split[0]
    df["구"] = addr_split[1]
    df["동"] = addr_split[2]
    return df

# 충전소 상세정보
def load_station_detail(statId):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM stations WHERE statId = %s", conn, params=(statId,))
    conn.close()
    return df.iloc[0] if not df.empty else None

# 페이지 구성
st.set_page_config(layout="wide")
st.sidebar.title("📋 메뉴")
page = st.sidebar.radio("페이지를 선택하세요", ["📊 충전소 현황 분석", "📍 지역별 충전소 조회"])

if page == "📊 충전소 현황 분석":
    st.title("🚗 전기차 충전소 시각화 대시보드")
    st.markdown("전국 **전기차 충전소 수**와 **전기차 등록 수 대비 보급률**을 시각화합니다.")

    summary_df = load_summary_data()

    st.subheader("📊 지역별 충전소 수")
    fig1 = px.bar(summary_df, x="region", y="station_count", title="시도별 충전소 수", text_auto=True)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("✅ 전기차 대비 충전소 보급률 TOP 5")
    top5 = summary_df.sort_values("보급률(%)", ascending=False).head(5)
    st.dataframe(top5[["region", "station_count", "vehicle_count", "보급률(%)"]])

    st.subheader("⚠️ 보급률 낮은 지역 TOP 5")
    bottom5 = summary_df.sort_values("보급률(%)", ascending=True).head(5)
    st.dataframe(bottom5[["region", "station_count", "vehicle_count", "보급률(%)"]])

    st.subheader("📈 지역별 보급률 차트")
    fig2 = px.bar(
        summary_df.sort_values("보급률(%)", ascending=False),
        x="region", y="보급률(%)",
        title="충전소 보급률",
        text_auto=True, color="보급률(%)",
        color_continuous_scale="YlGnBu"
    )
    st.plotly_chart(fig2, use_container_width=True)

elif page == "📍 지역별 충전소 조회":
    st.title("📍 구별 전기차 충전소 조회")
    df = load_all_address_data()

    cities = sorted(df["시"].dropna().unique())
    selected_city = st.selectbox("시 선택", cities)

    if selected_city:
        gu_list = sorted(df[df["시"] == selected_city]["구"].dropna().unique())
        selected_gu = st.selectbox("구 선택", gu_list)

        if selected_gu:
            filtered = df[(df["시"] == selected_city) & (df["구"] == selected_gu)]

            st.markdown(f"### 🔌 {selected_city} {selected_gu} 충전소 목록")
            stat_names = filtered["statNm"].tolist()
            selected_statNm = st.selectbox("충전소 선택", stat_names)

            if selected_statNm:
                statId = filtered[filtered["statNm"] == selected_statNm]["statId"].values[0]
                detail = load_station_detail(statId)

                st.markdown("### 📋 충전소 상세 정보")
                st.write(f"**이름:** {detail['statNm']}")
                st.write(f"**주소:** {detail['addr']}")
                st.write(f"**운영기관:** {detail['busiNm']}")
                st.write(f"**설치년도:** {detail['year']}")
                st.write(f"**운영시간:** {detail['useTime']}")
                st.write(f"**주차요금 무료:** {detail['parkingFree']}")
                st.write(f"**이용제한:** {detail['limitYn']} / {detail['limitDetail']}")
                st.write(f"**비고:** {detail['note']}")
                st.write(f"**삭제여부:** {detail['delYn']}")
                st.write(f"**상태 갱신일시:** {detail['statUpdDt']}")

                selected_categories = st.multiselect(
                    "🔎 주변 편의시설 보기",
                    options=["카페", "음식점", "편의점"],
                    default=["카페"]
                )

                category_map = {
                    "카페": ("CE7", "카페"),
                    "음식점": ("FD6", "음식점"),
                    "편의점": ("CS2", "편의점")
                }

                poi_rows = []
                for category in selected_categories:
                    code, label = category_map[category]
                    places = search_places_nearby(detail["lat"], detail["lng"], category=code)
                    for p in places:
                        poi_rows.append({
                            "name": p["place_name"],
                            "lat": float(p["y"]),
                            "lng": float(p["x"]),
                            "type": label,
                            "size": 10
                        })

                poi_df = pd.DataFrame(poi_rows)
                station_df = pd.DataFrame([{
                    "name": detail["statNm"],
                    "lat": detail["lat"],
                    "lng": detail["lng"],
                    "type": "충전소",
                    "size": 20
                }])
                map_df = pd.concat([station_df, poi_df], ignore_index=True)

                st.markdown("### 🗺️ 충전소 + 주변 편의시설 지도")
                fig = px.scatter_mapbox(
                    map_df,
                    lat="lat", lon="lng", hover_name="name", color="type",
                    zoom=15, mapbox_style="carto-positron", height=500,
                    size="size",
                    hover_data={"lat": False, "lng": False, "size": False}
                )
                fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig, use_container_width=True)
