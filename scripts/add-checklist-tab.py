"""
하와이 신혼여행 체크리스트 → 기존 예약 DB 시트에 새 탭으로 추가.

사전 준비:
1. GCP Console → IAM → Service Accounts → newtrand → 키 추가 → JSON 다운로드
2. JSON 파일을 ~/.secrets/newtrand-sa.json 으로 이동
3. 대상 시트를 newtrand@arctic-robot-468723-i4.iam.gserviceaccount.com 에 편집자 공유

실행:
    python add-checklist-tab.py
"""
import os
import sys
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SA_KEY = Path.home() / ".secrets" / "newtrand-sa.json"
SPREADSHEET_ID = "1nmbZgOjqGVgeq24JMTlF1LjK9s4XtgYD8ro7MAMcvmE"
SHEET_TITLE = "전체체크리스트"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ─── 53개 체크리스트 항목 (hawaii-trip-dashboard.html BOOKING_CHECKLIST 동일) ───
HEADER = ["카테고리", "항목", "담당", "기한", "긴급", "완료", "메모"]

CHECKLIST = [
    # 📄 서류·법적
    ("📄 서류·법적", "여권 유효기간 확인 (잔여 6개월+)", "둘다", "즉시", True, ""),
    ("📄 서류·법적", "ESTA 신청 — $21/인", "둘다", "출발 72h 전", True, "esta.cbp.dhs.gov"),
    ("📄 서류·법적", "국제운전면허증 발급", "형구오빠", "6월까지", False, "운전면허시험장"),
    ("📄 서류·법적", "여행자 보험 가입 (캠핑·스노클링 포함 확인)", "둘다", "6월까지", False, ""),
    ("📄 서류·법적", "e-티켓 저장·출력 (KE053/KE054)", "지혜", "출발 전", False, ""),
    ("📄 서류·법적", "여권 번호·사진 서로 메모", "둘다", "6월", False, "분실 대비"),
    # ✈️ 항공·이동
    ("✈️ 항공·이동", "HNL→OGG 국내선 예약 (7/12 도착 후)", "지혜", "즉시", True, "Hawaiian Air ~$80/인"),
    ("✈️ 항공·이동", "OGG→HNL 국내선 예약 (7/16 마우이→오아후)", "지혜", "즉시", True, ""),
    ("✈️ 항공·이동", "마우이 렌트카 예약 (7/12~7/16, SUV)", "형구오빠", "즉시", True, "Costco Travel 권장"),
    ("✈️ 항공·이동", "오아후 렌트카 예약 (7/16~7/20, Compact)", "형구오빠", "즉시", True, "마우이와 별도 계약"),
    ("✈️ 항공·이동", "카드사 렌트카 LDW 보험 적용 여부 확인", "형구오빠", "렌트카 예약 전", False, "Visa Plat/Amex Gold"),
    ("✈️ 항공·이동", "KE054 좌석 web check-in (출발 24h 전)", "지혜", "7/19", False, ""),
    # 🏨 숙박·캠핑
    ("🏨 숙박·캠핑 예약", "Paia Inn 예약 (Day 1-2, 7/12~7/13)", "지혜", "즉시", True, ""),
    ("🏨 숙박·캠핑 예약", "Camp Olowalu 텐탈로/텐트 (Day 4, 7/15)", "지혜", "즉시", True, "🚨 매진 임박 campolowalu.com"),
    ("🏨 숙박·캠핑 예약", "Kailua/Lanikai 호텔 (Day 5, 7/16)", "지혜", "즉시", True, ""),
    ("🏨 숙박·캠핑 예약", "Malaekahana 유르트 (Day 6, 7/17)", "지혜", "즉시", True, "🚨 매진 임박 malaekahana.net"),
    ("🏨 숙박·캠핑 예약", "Waikiki 호텔 (Day 8, 7/19)", "지혜", "즉시", True, ""),
    ("🏨 숙박·캠핑 예약", "Wai'ānapanapa 캠핑 예약 (Day 3, 7/14)", "지혜", "6/14 오픈", False, "gostateparks.hawaii.gov"),
    ("🏨 숙박·캠핑 예약", "Wai'ānapanapa 입장 예약 (별도 2건)", "지혜", "6/14 오픈", False, "캠핑과 따로 예약"),
    ("🏨 숙박·캠핑 예약", "Bellows Field Beach 캠핑 (Day 7, 7/18)", "지혜", "7/4 12:00 PM HST", False, "camping.honolulu.gov"),
    # 🎟️ 입장권·액티비티
    ("🎟️ 입장권·액티비티", "⭐ Haleakalā 일출 예약 (Day 2, 7/13)", "지혜", "5/13 07:00 HST", True, "매진 5분 안 — 알람 필수"),
    ("🎟️ 입장권·액티비티", "ʻĪao Valley 입장 예약 (Day 2)", "지혜", "6/13", False, "gostateparks"),
    ("🎟️ 입장권·액티비티", "Diamond Head 입장 예약 (Day 7)", "지혜", "6/18", False, "gostateparks"),
    ("🎟️ 입장권·액티비티", "⭐ Hanauma Bay 예약 (Day 7, 7/18)", "지혜", "7/16 07:00 HST", True, "트립 중 — pros.hnl.info"),
    ("🎟️ 입장권·액티비티", "USS Arizona Memorial 예약 (Day 7)", "형구오빠", "8주 전 + 7/19 24h 전", False, "recreation.gov $1"),
    ("🎟️ 입장권·액티비티", "신혼 디너 예약 (Senia/Mariposa, Day 8)", "지혜", "6/22~", False, "2~4주 전"),
    ("🎟️ 입장권·액티비티", "Star Noodle 예약 (Day 4)", "지혜", "7/8~", False, "OpenTable 1주 전"),
    ("🎟️ 입장권·액티비티", "Maita'i Catamaran 크루즈 (Day 8)", "지혜", "7/12~", False, ""),
    ("🎟️ 입장권·액티비티", "Buzz's Steakhouse 예약 (Day 5)", "지혜", "7/9~", False, "저녁 권장"),
    # 🧳 짐 — 한국 구매
    ("🧳 짐 — 한국 구매", "패딩·장갑·비니 (Haleakalā 5~10°C)", "둘다", "6월", False, ""),
    ("🧳 짐 — 한국 구매", "Reef-safe 미네랄 선크림 (옥시벤존 X)", "지혜", "6월", False, ""),
    ("🧳 짐 — 한국 구매", "텐트 2인용 구매 또는 대여 결정", "형구오빠", "6월", False, "현지 대여 $25~40/일 대안"),
    ("🧳 짐 — 한국 구매", "침낭 (하계용, 압축형)", "둘다", "6월", False, ""),
    ("🧳 짐 — 한국 구매", "에어매트/슬리핑패드", "형구오빠", "6월", False, ""),
    ("🧳 짐 — 한국 구매", "헤드램프 + 여분 배터리 2개", "형구오빠", "6월", False, "야간 캠프 필수"),
    ("🧳 짐 — 한국 구매", "스노클링 마스크+스노클", "지혜", "6월", False, "오리발은 현지 대여"),
    ("🧳 짐 — 한국 구매", "멀티어댑터 (110V) + 멀티탭", "형구오빠", "6월", False, ""),
    ("🧳 짐 — 한국 구매", "보조배터리 10000mAh+", "둘다", "출발 전", False, "기내 반입만 가능"),
    ("🧳 짐 — 한국 구매", "멀미약 (기내 + Hana Hwy용)", "지혜", "출발 전", False, "620 커브 필수"),
    ("🧳 짐 — 한국 구매", "스마트 캐주얼 1세트 (신혼 디너)", "둘다", "출발 전", False, ""),
    ("🧳 짐 — 한국 구매", "트레킹화/운동화", "둘다", "출발 전", False, "Pillbox·Diamond Head"),
    # 🇺🇸 현지 구매
    ("🇺🇸 현지 구매 (Day 1-2)", "가스통/연료 (부탄·이소)", "형구오빠", "7/12 현지 즉시", True, "기내 반입 절대 X"),
    ("🇺🇸 현지 구매 (Day 1-2)", "쿨러/아이스박스", "형구오빠", "7/12~13", False, ""),
    ("🇺🇸 현지 구매 (Day 1-2)", "캠핑 의자 2개", "형구오빠", "7/12~13", False, ""),
    ("🇺🇸 현지 구매 (Day 1-2)", "DEET 모기 스프레이", "지혜", "7/12 현지", False, "Hana·정글 필수"),
    ("🇺🇸 현지 구매 (Day 1-2)", "생수 4L 통", "형구오빠", "7/12~13", False, "캠핑 음수용"),
    # 💳 금융·통신
    ("💳 금융·통신", "트래블카드 발급 (트래블월렛/하나비바X)", "둘다", "6월", False, ""),
    ("💳 금융·통신", "달러 현금 환전 $100", "지혜", "출발 전", False, "팁·소액용"),
    ("💳 금융·통신", "Airalo eSIM 구매 및 활성화 (7일)", "둘다", "출발 전 한국에서", False, ""),
    ("💳 금융·통신", "해외 결제 카드 한도 확인", "둘다", "6월", False, ""),
    # 🤝 둘이 함께 확인
    ("🤝 둘이 함께 확인", "Haleakalā 예약 알람 설정 (5/14 02:00 KST)", "둘다", "5/13", True, ""),
    ("🤝 둘이 함께 확인", "Hanauma Bay 예약 알람 설정 (7/17 02:00 KST)", "둘다", "7/16", False, "트립 중"),
    ("🤝 둘이 함께 확인", "캠핑 장비 최종 점검 (함께)", "둘다", "7월 첫째주", False, ""),
    ("🤝 둘이 함께 확인", "출발 전날 짐 최종 체크 (함께)", "둘다", "7/11", False, ""),
    ("🤝 둘이 함께 확인", "상대방 여권·ESTA 크로스체크", "둘다", "7/11", False, ""),
]


def main() -> int:
    if not SA_KEY.exists():
        print(f"❌ 서비스 계정 키 없음: {SA_KEY}", file=sys.stderr)
        print("   GCP Console → IAM → Service Accounts → newtrand → 키 추가 → JSON", file=sys.stderr)
        return 1

    creds = service_account.Credentials.from_service_account_file(str(SA_KEY), scopes=SCOPES)
    svc = build("sheets", "v4", credentials=creds, cache_discovery=False)

    # 1. 기존 탭 확인 (중복 방지)
    meta = svc.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    existing = [s["properties"]["title"] for s in meta["sheets"]]
    if SHEET_TITLE in existing:
        print(f"⚠️  '{SHEET_TITLE}' 탭이 이미 존재. 기존 데이터 유지하고 종료.")
        print(f"   기존 탭: {existing}")
        return 0

    # 2. 새 탭 추가
    print(f"🔧 '{SHEET_TITLE}' 탭 생성 중...")
    add_resp = svc.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={
            "requests": [{
                "addSheet": {
                    "properties": {
                        "title": SHEET_TITLE,
                        "gridProperties": {"rowCount": 100, "columnCount": 7, "frozenRowCount": 1},
                        "tabColorStyle": {"rgbColor": {"red": 0.4, "green": 0.3, "blue": 0.7}},
                    }
                }
            }]
        },
    ).execute()
    new_sheet_id = add_resp["replies"][0]["addSheet"]["properties"]["sheetId"]
    print(f"   ✓ 탭 생성됨 (sheetId={new_sheet_id})")

    # 3. 데이터 입력
    rows = [HEADER] + [
        [cat, task, who, deadline, "TRUE" if urgent else "FALSE", "FALSE", note]
        for (cat, task, who, deadline, urgent, note) in CHECKLIST
    ]
    print(f"📝 {len(rows)}행 입력 중 (헤더 1 + 데이터 {len(CHECKLIST)})...")
    svc.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_TITLE}!A1",
        valueInputOption="RAW",
        body={"values": rows},
    ).execute()

    # 4. 헤더 굵게 + 동결
    print("🎨 헤더 서식 적용 중...")
    svc.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={
            "requests": [
                {
                    "repeatCell": {
                        "range": {"sheetId": new_sheet_id, "startRowIndex": 0, "endRowIndex": 1},
                        "cell": {
                            "userEnteredFormat": {
                                "textFormat": {"bold": True},
                                "backgroundColorStyle": {"rgbColor": {"red": 0.92, "green": 0.92, "blue": 0.96}},
                            }
                        },
                        "fields": "userEnteredFormat(textFormat,backgroundColorStyle)",
                    }
                },
                {
                    "autoResizeDimensions": {
                        "dimensions": {"sheetId": new_sheet_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 7}
                    }
                },
            ]
        },
    ).execute()

    print(f"✅ 완료. https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={new_sheet_id}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except HttpError as e:
        print(f"❌ Google API 에러: {e.status_code} {e.reason}", file=sys.stderr)
        if e.status_code == 403:
            print("   → 시트가 newtrand@arctic-robot-468723-i4.iam.gserviceaccount.com 에 공유됐는지 확인", file=sys.stderr)
        sys.exit(2)
