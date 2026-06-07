"""
GoalLog - Repository Interface (설계서 8장 기반)
team, player, match 3개 테이블 + Join 쿼리 인터페이스
"""
from abc import ABC, abstractmethod
import pandas as pd


# 8.1 팀 테이블 인터페이스
class ITeamRepository(ABC):
    @abstractmethod
    def find_all(self) -> pd.DataFrame:
        """전체 국가대표팀 목록 조회 (READ)"""
        pass

    @abstractmethod
    def find_by_id(self, team_fifa_code: str) -> pd.DataFrame:
        """단일 팀 상세 정보 조회 (READ)"""
        pass


# 8.2 선수 테이블 인터페이스
class IPlayerRepository(ABC):
    @abstractmethod
    def save(self, name: str, team_fifa_code: str, position: str,
             jersey_number: int, birth_date: str) -> bool:
        """선수 명단 추가 (CREATE)"""
        pass

    @abstractmethod
    def find_by_team_id(self, team_fifa_code: str) -> pd.DataFrame:
        """특정 국가의 선수 명단 전체 조회 (READ)"""
        pass

    @abstractmethod
    def update(self, player_id: int, position: str, jersey_number: int) -> bool:
        """선수 스탯(포지션, 등번호) 수정 (UPDATE)"""
        pass

    @abstractmethod
    def delete_by_id(self, player_id: int) -> bool:
        """선수 명단에서 삭제 (DELETE)"""
        pass


# 8.3 경기(매치) 테이블 인터페이스
class IMatchRepository(ABC):
    @abstractmethod
    def find_all_matches(self) -> pd.DataFrame:
        """모든 경기 일정 시간순 조회 (READ)"""
        pass

    @abstractmethod
    def find_by_date(self, date_str: str) -> pd.DataFrame:
        """날짜별 경기 조회 (READ)"""
        pass


# 8.4 Join 정보 인터페이스
class IWorldCupQueryRepository(ABC):
    @abstractmethod
    def find_match_with_teams_and_players(self, match_key: str) -> pd.DataFrame:
        """
        MATCH, TEAM, PLAYER 3개 테이블을 Join하여
        특정 경기의 상세 정보와 양 팀의 출전 선수 명단을 한 번에 조회
        """
        pass
