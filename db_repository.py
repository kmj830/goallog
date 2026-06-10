"""
GoalLog - DuckDB Repository 구현체
설계서의 Repository Interface를 DuckDB로 구현
"""
import duckdb
import pandas as pd
from repository import ITeamRepository, IPlayerRepository, IMatchRepository, IWorldCupQueryRepository

DB_PATH = "worldcup.duckdb"


def _get_conn(read_only: bool = False):
    return duckdb.connect(DB_PATH, read_only=read_only)


# ─────────────────────────────────────────────
# 팀 Repository
# ─────────────────────────────────────────────
class TeamRepository(ITeamRepository):

    def find_all(self) -> pd.DataFrame:
        with _get_conn(read_only=True) as conn:
            return conn.execute(
                'SELECT name, flag_icon, flag_url, fifa_code, "group", confed, continent '
                'FROM teams ORDER BY "group", name'
            ).fetchdf()

    def find_by_id(self, team_fifa_code: str) -> pd.DataFrame:
        with _get_conn(read_only=True) as conn:
            return conn.execute(
                'SELECT name, flag_icon, flag_url, fifa_code, "group", confed, continent '
                'FROM teams WHERE fifa_code = ?',
                [team_fifa_code]
            ).fetchdf()


# ─────────────────────────────────────────────
# 선수 Repository
# ─────────────────────────────────────────────
class PlayerRepository(IPlayerRepository):

    def save(self, name: str, team_fifa_code: str, position: str,
             jersey_number: int, birth_date: str) -> bool:
        try:
            with _get_conn() as conn:
                # player_id는 SEQUENCE로 자동 생성
                conn.execute("CREATE SEQUENCE IF NOT EXISTS player_id_seq START 1")
                conn.execute(
                    """INSERT INTO players (player_id, name, team_fifa_code, position, jersey_number, birth_date)
                       VALUES (nextval('player_id_seq'), ?, ?, ?, ?, ?)""",
                    [name, team_fifa_code, position, jersey_number,
                     birth_date if birth_date else None]
                )
            return True
        except Exception as e:
            print(f"[PlayerRepo] save error: {e}")
            return False

    def find_by_team_id(self, team_fifa_code: str) -> pd.DataFrame:
        with _get_conn(read_only=True) as conn:
            return conn.execute(
                """SELECT player_id, name, position, jersey_number, birth_date
                   FROM players
                   WHERE team_fifa_code = ?
                   ORDER BY CASE position
                       WHEN 'GK' THEN 1
                       WHEN 'DF' THEN 2
                       WHEN 'MF' THEN 3
                       WHEN 'FW' THEN 4
                       ELSE 5
                   END, jersey_number""",
                [team_fifa_code]
            ).fetchdf()

    def update(self, player_id: int, position: str, jersey_number: int) -> bool:
        try:
            with _get_conn() as conn:
                conn.execute(
                    "UPDATE players SET position = ?, jersey_number = ? WHERE player_id = ?",
                    [position, jersey_number, player_id]
                )
            return True
        except Exception as e:
            print(f"[PlayerRepo] update error: {e}")
            return False

    def delete_by_id(self, player_id: int) -> bool:
        try:
            with _get_conn() as conn:
                conn.execute("DELETE FROM players WHERE player_id = ?", [player_id])
            return True
        except Exception as e:
            print(f"[PlayerRepo] delete error: {e}")
            return False


# ─────────────────────────────────────────────
# 경기 Repository
# ─────────────────────────────────────────────
class MatchRepository(IMatchRepository):

    def find_all_matches(self) -> pd.DataFrame:
        with _get_conn(read_only=True) as conn:
            return conn.execute(
                """SELECT m.date, m.time, m.round, m."group",
                          m.team1, m.team2, m.ground,
                          t1.flag_icon AS flag1, t1.flag_url AS flag_url1, t1.fifa_code AS code1,
                          t2.flag_icon AS flag2, t2.flag_url AS flag_url2, t2.fifa_code AS code2
                   FROM matches m
                   LEFT JOIN teams t1 ON t1.name = m.team1
                   LEFT JOIN teams t2 ON t2.name = m.team2
                   ORDER BY m.date, m.time"""
            ).fetchdf()

    def find_by_date(self, date_str: str) -> pd.DataFrame:
        with _get_conn(read_only=True) as conn:
            return conn.execute(
                """SELECT m.date, m.time, m.round, m."group",
                          m.team1, m.team2, m.ground,
                          t1.flag_icon AS flag1, t1.flag_url AS flag_url1, t1.fifa_code AS code1,
                          t2.flag_icon AS flag2, t2.flag_url AS flag_url2, t2.fifa_code AS code2
                   FROM matches m
                   LEFT JOIN teams t1 ON t1.name = m.team1
                   LEFT JOIN teams t2 ON t2.name = m.team2
                   WHERE m.date = ?
                   ORDER BY m.time""",
                [date_str]
            ).fetchdf()


# ─────────────────────────────────────────────
# Join Query Repository (설계서 8.4)
# ─────────────────────────────────────────────
class WorldCupQueryRepository(IWorldCupQueryRepository):

    def find_match_with_teams_and_players(self, match_key: str) -> dict:
        """
        match_key = "team1::team2::date"
        MATCH + TEAM + PLAYER 3개 테이블 LEFT JOIN
        """
        parts = match_key.split("::")
        if len(parts) != 3:
            return {}
        team1_name, team2_name, date = parts

        with _get_conn(read_only=True) as conn:
            # 경기 + 팀 정보
            match_df = conn.execute(
                """SELECT m.date, m.time, m.round, m."group", m.ground,
                          m.team1, m.team2,
                          t1.flag_icon AS flag1, t1.flag_url AS flag_url1,
                          t1.fifa_code AS code1,
                          t1.confed AS confed1, t1.continent AS continent1,
                          t2.flag_icon AS flag2, t2.flag_url AS flag_url2,
                          t2.fifa_code AS code2,
                          t2.confed AS confed2, t2.continent AS continent2
                   FROM matches m
                   LEFT JOIN teams t1 ON t1.name = m.team1
                   LEFT JOIN teams t2 ON t2.name = m.team2
                   WHERE m.team1 = ? AND m.team2 = ? AND m.date = ?
                   LIMIT 1""",
                [team1_name, team2_name, date]
            ).fetchdf()

            # 홈팀 선수 (3테이블 JOIN: matches ← teams ← players)
            players1_df = conn.execute(
                """SELECT p.player_id, p.name, p.position, p.jersey_number, p.birth_date
                   FROM players p
                   JOIN teams t ON t.fifa_code = p.team_fifa_code
                   WHERE t.name = ?
                   ORDER BY CASE p.position
                       WHEN 'GK' THEN 1
                       WHEN 'DF' THEN 2
                       WHEN 'MF' THEN 3
                       WHEN 'FW' THEN 4
                       ELSE 5
                   END, p.jersey_number""",
                [team1_name]
            ).fetchdf()

            # 어웨이팀 선수
            players2_df = conn.execute(
                """SELECT p.player_id, p.name, p.position, p.jersey_number, p.birth_date
                   FROM players p
                   JOIN teams t ON t.fifa_code = p.team_fifa_code
                   WHERE t.name = ?
                   ORDER BY CASE p.position
                       WHEN 'GK' THEN 1
                       WHEN 'DF' THEN 2
                       WHEN 'MF' THEN 3
                       WHEN 'FW' THEN 4
                       ELSE 5
                   END, p.jersey_number""",
                [team2_name]
            ).fetchdf()

        return {
            "match": match_df,
            "players1": players1_df,
            "players2": players2_df,
        }