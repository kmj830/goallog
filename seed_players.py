"""
GoalLog - 선수 데이터 DB 적재 스크립트
players_2026.json → worldcup.duckdb players 테이블

실행: python seed_players.py
"""

import json
import duckdb

JSON_PATH = "players_2026.json"
DB_PATH   = "worldcup.duckdb"


def load_json(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def seed(players: list[dict]) -> None:
    with duckdb.connect(DB_PATH) as conn:

        # ── 기존 데이터 & 시퀀스 초기화 ──────────────────
        conn.execute("DELETE FROM players")
        conn.execute("DROP SEQUENCE IF EXISTS player_id_seq")
        conn.execute("CREATE SEQUENCE player_id_seq START 1")
        print("기존 선수 데이터 초기화 완료")

        # ── teams 테이블에 있는 fifa_code만 필터 ─────────
        valid_codes = set(
            row[0] for row in conn.execute("SELECT fifa_code FROM teams").fetchall()
        )
        skipped = [p for p in players if p["team_fifa_code"] not in valid_codes]
        to_insert = [p for p in players if p["team_fifa_code"] in valid_codes]

        if skipped:
            skip_codes = sorted({p["team_fifa_code"] for p in skipped})
            print(f"[경고] teams 테이블에 없는 팀 코드 → 스킵: {skip_codes}")
            print(f"  스킵 선수 수: {len(skipped)}명")

        # ── INSERT ────────────────────────────────────────
        conn.executemany(
            """
            INSERT INTO players (player_id, name, team_fifa_code, position, jersey_number, birth_date)
            VALUES (nextval('player_id_seq'), ?, ?, ?, ?, ?)
            """,
            [
                (
                    p["name"],
                    p["team_fifa_code"],
                    p["position"],
                    p["jersey_number"],
                    p["birth_date"],
                )
                for p in to_insert
            ],
        )

        total = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        print(f"\n✅ 적재 완료: {total}명 삽입")

        # ── 확인: 팀별 선수 수 ────────────────────────────
        print("\n팀별 선수 수:")
        rows = conn.execute("""
            SELECT team_fifa_code, COUNT(*) AS cnt
            FROM players
            GROUP BY team_fifa_code
            ORDER BY team_fifa_code
        """).fetchall()
        for code, cnt in rows:
            print(f"  {code}: {cnt}명")


if __name__ == "__main__":
    players = load_json(JSON_PATH)
    print(f"JSON 로드 완료: {len(players)}명")
    seed(players)