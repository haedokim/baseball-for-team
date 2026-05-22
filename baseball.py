import streamlit as st
import pandas as pd
import time

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
SHEET_ID = "1HyOhf-WC6mTf9QKjX1LgLsklFM02-GWIYewBu_R8J6M"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1944623840"
SHEET_ID = "1HyOhf-WC6mTf9QKjX1LgLsklFM02-GWIYewBu_R8J6M"
CSV_URL        = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1944623840"  # 응답 시트
MISSION_URL    = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"           # 시트1 (미션용)

SCORE_COL = "최종점수"   # M열 헤더명 (실제 시트 헤더와 맞춰주세요)
NAME_COL  = "1. 본인의 이름을 입력해주세요."       # 이름 열 헤더명 (실제 시트 헤더와 맞춰주세요)
MISSION_COL_IDX = 13     # N열 = 0-based index 13

# ─────────────────────────────────────────
# 데이터 로드
# ─────────────────────────────────────────
@st.cache_data(ttl=15)  # 15초마다 자동 갱신
def load_data():
    try:
        df = pd.read_csv(CSV_URL, header=0)
        if df.empty or len(df.columns) == 0:
            return None, None, "시트에 데이터가 없습니다"
    except Exception as e:
        return None, None, f"시트 연결 오류: {e}"

    # 2행(index 0) = 정답칸 → 분리
    answer_row = df.iloc[0]

    # N2 셀 = 현재 미션 안내 (answer_row의 N열)
    # 기존 mission_text 읽는 코드 전체를 아래로 교체
    try:
        df_mission = pd.read_csv(MISSION_URL, header=None)
        mission_text = str(df_mission.iloc[0, 0]).strip()
        if not mission_text or mission_text == "nan":
            mission_text = "현재 진행 중인 미션이 없습니다"
    except Exception:
         mission_text = "현재 진행 중인 미션이 없습니다"

    # 3행~(index 1~) = 참가자 데이터
    participants = df.iloc[1:].copy()
    participants = participants.dropna(subset=[NAME_COL])  # 이름 없는 행 제거

    if participants.empty:
        return None, mission_text, "아직 응답한 참가자가 없습니다 ⏳"

    # 점수 열 숫자 변환
    participants[SCORE_COL] = pd.to_numeric(participants[SCORE_COL], errors="coerce").fillna(0)

    # 순위 계산 (동점 처리 포함)
    participants = participants.sort_values(SCORE_COL, ascending=False).reset_index(drop=True)
    participants["순위"] = participants[SCORE_COL].rank(method="min", ascending=False).astype(int)

    return participants, mission_text, None

# ─────────────────────────────────────────
# UI
# ─────────────────────────────────────────
st.set_page_config(
    page_title="⚾ 선실전장과 사설토토",
    page_icon="⚾",
    layout="centered"
)

# 모바일 최적화 CSS
st.markdown("""
<style>
    /* 전체 폰트 키우기 */
    html, body, [class*="css"] { font-size: 16px; }

    /* 미션 배너 */
    .mission-box {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 2px solid #e94560;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 20px;
        text-align: center;
    }
    .mission-label { color: #e94560; font-size: 13px; font-weight: 700; letter-spacing: 2px; }
    .mission-text  { color: #ffffff; font-size: 20px; font-weight: 700; margin-top: 6px; }

    /* 순위 카드 */
    .rank-card {
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .rank-1  { background: linear-gradient(90deg, #f6d365, #fda085); }
    .rank-2  { background: linear-gradient(90deg, #c9d6df, #a8a8a8); }
    .rank-3  { background: linear-gradient(90deg, #f7971e, #c8a95b); }
    .rank-etc{ background: #1e2a3a; border: 1px solid #2d3f55; }
    .rank-me { border: 2px solid #00d4ff !important; }

    .rank-num  { font-size: 22px; font-weight: 900; min-width: 40px; }
    .rank-name { font-size: 18px; font-weight: 600; flex: 1; padding: 0 12px; color: #fff; }
    .rank-score{ font-size: 20px; font-weight: 800; color: #fff; }

    /* 검색창 */
    .stTextInput input {
        font-size: 18px !important;
        padding: 12px !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── 헤더 ───
st.markdown("## ⚾ 선실전장 실시간 스코어보드")
st.markdown("🔵 **롯데 자이언츠** vs 🟢 **NC 다이노스**")
st.divider()

# ─── 데이터 로드 ───
df, mission_text, error_msg = load_data()

# ─── 미션 안내 배너 (전 참가자 공통) ───
if mission_text:
    st.markdown(f"""
    <div class="mission-box">
        <div class="mission-label">🎯 현재 미션</div>
        <div class="mission-text">{mission_text}</div>
    </div>
    """, unsafe_allow_html=True)

# ─── 에러 / 빈 데이터 처리 ───
if error_msg:
    st.info(f"⏳ {error_msg}")
    st.stop()

# ─── 이름 검색 (내 순위 찾기) ───
search_name = st.text_input("🔍 내 이름 검색", placeholder="이름을 입력하면 내 순위를 강조합니다")

# ─── 순위표 ───
st.markdown("### 🏆 전체 순위")

rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}

for _, row in df.iterrows():
    rank  = int(row["순위"])
    name  = str(row[NAME_COL])
    score = int(row[SCORE_COL])

    if rank == 1:
        card_class = "rank-card rank-1"
    elif rank == 2:
        card_class = "rank-card rank-2"
    elif rank == 3:
        card_class = "rank-card rank-3"
    else:
        card_class = "rank-card rank-etc"

    # 내 이름 강조
    if search_name and search_name.strip() in name:
        card_class += " rank-me"
        name_display = f"⭐ {name}"
    else:
        name_display = name

    icon = rank_icons.get(rank, f"{rank}위")

    st.markdown(f"""
    <div class="{card_class}">
        <span class="rank-num">{icon}</span>
        <span class="rank-name">{name_display}</span>
        <span class="rank-score">{score}점</span>
    </div>
    """, unsafe_allow_html=True)

# ─── 갱신 안내 ───
st.divider()
st.caption(f"🔄 15초마다 자동 갱신 | 마지막 갱신: {time.strftime('%H:%M:%S')}")
st.button("🔄 지금 새로고침", on_click=st.cache_data.clear)
