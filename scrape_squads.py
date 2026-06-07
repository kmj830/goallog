"""
2026 FIFA World Cup 선수 명단 스크래퍼
Wikipedia → players_2026.json
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from collections import Counter

TEAM_FIFA_CODE = {
    "Afghanistan": "AFG", "Albania": "ALB", "Algeria": "ALG",
    "Angola": "ANG", "Argentina": "ARG", "Armenia": "ARM",
    "Australia": "AUS", "Austria": "AUT", "Azerbaijan": "AZE",
    "Bahrain": "BHR", "Belarus": "BLR", "Belgium": "BEL",
    "Bolivia": "BOL", "Bosnia and Herzegovina": "BIH", "Brazil": "BRA",
    "Bulgaria": "BUL", "Burkina Faso": "BFA", "Cameroon": "CMR",
    "Canada": "CAN", "Cape Verde": "CPV", "Chile": "CHI",
    "China PR": "CHN", "Colombia": "COL", "Comoros": "COM",
    "Congo": "CGO", "Costa Rica": "CRC", "Croatia": "CRO",
    "Czech Republic": "CZE", "DR Congo": "COD", "Denmark": "DEN",
    "Ecuador": "ECU", "Egypt": "EGY", "El Salvador": "SLV",
    "England": "ENG", "Estonia": "EST", "Finland": "FIN",
    "France": "FRA", "Gabon": "GAB", "Gambia": "GAM",
    "Georgia": "GEO", "Germany": "GER", "Ghana": "GHA",
    "Greece": "GRE", "Guatemala": "GUA", "Guinea": "GUI",
    "Honduras": "HON", "Hungary": "HUN", "Iceland": "ISL",
    "Indonesia": "IDN", "Iran": "IRN", "Iraq": "IRQ",
    "Israel": "ISR", "Italy": "ITA", "Ivory Coast": "CIV",
    "Jamaica": "JAM", "Japan": "JPN", "Jordan": "JOR",
    "Kenya": "KEN", "Kuwait": "KUW", "Latvia": "LVA",
    "Lebanon": "LIB", "Lithuania": "LTU", "Luxembourg": "LUX",
    "Mali": "MLI", "Malta": "MLT", "Mauritania": "MTN",
    "Mexico": "MEX", "Moldova": "MDA", "Montenegro": "MNE",
    "Morocco": "MAR", "Namibia": "NAM", "Netherlands": "NED",
    "New Zealand": "NZL", "Nigeria": "NGA", "North Macedonia": "MKD",
    "Norway": "NOR", "Oman": "OMA", "Panama": "PAN",
    "Paraguay": "PAR", "Peru": "PER", "Philippines": "PHI",
    "Poland": "POL", "Portugal": "POR", "Qatar": "QAT",
    "Romania": "ROU", "Rwanda": "RWA", "Saudi Arabia": "KSA",
    "Senegal": "SEN", "Serbia": "SRB", "Slovakia": "SVK",
    "Slovenia": "SVN", "South Africa": "RSA", "South Korea": "KOR",
    "Spain": "ESP", "Sweden": "SWE", "Switzerland": "SUI",
    "Syria": "SYR", "Thailand": "THA", "Togo": "TOG",
    "Trinidad and Tobago": "TRI", "Tunisia": "TUN", "Turkey": "TUR",
    "Uganda": "UGA", "Ukraine": "UKR", "United Arab Emirates": "UAE",
    "United States": "USA", "Uruguay": "URU", "Uzbekistan": "UZB",
    "Venezuela": "VEN", "Vietnam": "VIE", "Wales": "WAL",
    "Zambia": "ZAM", "Zimbabwe": "ZIM",
    "Korea Republic": "KOR", "IR Iran": "IRN",
    "Côte d'Ivoire": "CIV", "Cote d'Ivoire": "CIV",
}

# 포지션 셀 텍스트 예: "1 GK", "2 DF", "3 MF", "4 FW"
# → 마지막 토큰이 실제 포지션
POSITION_MAP = {"GK": "GK", "DF": "DF", "MF": "MF", "FW": "FW"}


def find_team_code(text: str) -> str | None:
    text_clean = re.sub(r"\[.*?\]", "", text).strip()
    for team_name, code in TEAM_FIFA_CODE.items():
        if team_name.lower() in text_clean.lower():
            return code
    return None


def parse_table(table, team_code: str) -> list[dict]:
    results = []
    rows = table.find_all("tr")
    for row in rows[1:]:  # 헤더 스킵
        cells = row.find_all(["td", "th"])
        if len(cells) < 4:
            continue

        # [0] 등번호
        jersey_raw = cells[0].get_text(strip=True)
        jersey_number = int(jersey_raw) if jersey_raw.isdigit() else None

        # [1] 포지션: "1 GK" → 마지막 토큰
        pos_tokens = cells[1].get_text(" ", strip=True).split()
        pos_raw = pos_tokens[-1] if pos_tokens else ""
        position = POSITION_MAP.get(pos_raw.upper())
        if not position:
            continue

        # [2] 선수 이름
        name = cells[2].get_text(" ", strip=True)
        name = re.sub(r"\s*\(captain\)|\s*\(c\)", "", name, flags=re.IGNORECASE).strip()

        # [3] 생년월일: <span class="bday">2000-05-17</span> 직접 추출
        bday_span = cells[3].find("span", class_="bday")
        birth_date = bday_span.get_text(strip=True) if bday_span else None

        results.append({
            "name": name,
            "team_fifa_code": team_code,
            "position": position,
            "jersey_number": jersey_number,
            "birth_date": birth_date,
        })
    return results


def scrape() -> list[dict]:
    url = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
    print(f"Fetching: {url}")
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; GoalLogBot/1.0)"},
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # h3 중 팀명인 것만 수집
    team_headings = []
    for h3 in soup.find_all("h3"):
        code = find_team_code(h3.get_text())
        if code:
            team_headings.append((code, h3))

    print(f"  팀 헤딩 수: {len(team_headings)}")
    print(f"  wikitable 수: {len(soup.find_all('table', class_='wikitable'))}")

    players = []
    for team_code, h3_tag in team_headings:
        table = h3_tag.find_next("table", class_="wikitable")
        if table is None:
            print(f"  [경고] {team_code}: 테이블 없음")
            continue
        found = parse_table(table, team_code)
        print(f"  {team_code}: {len(found)}명")
        players.extend(found)

    return players


if __name__ == "__main__":
    players = scrape()
    print(f"\n총 {len(players)}명 파싱 완료")

    out = "players_2026.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(players, f, ensure_ascii=False, indent=2)
    print(f"저장 완료: {out}")

    print("\n--- 미리보기 (첫 5명) ---")
    for p in players[:5]:
        print(p)

    team_counts = Counter(p["team_fifa_code"] for p in players)
    if team_counts:
        print(f"\n파싱된 팀 수: {len(team_counts)}")
        print(f"팀별 평균 선수 수: {len(players)/len(team_counts):.1f}명")