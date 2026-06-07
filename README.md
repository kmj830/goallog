# GoalLog ⚽
**2026 FIFA World Cup™ 정보 앱**  
Flet + DuckDB 기반 데스크탑 GUI 애플리케이션

---

## 📁 프로젝트 구조

```
goallog/
├── main.py            # Flet GUI 앱 진입점
├── repository.py      # Repository Interface (ABC) — 설계서 8장
├── db_repository.py   # DuckDB 구현체
├── worldcup.duckdb    # 데이터베이스 파일
└── README.md
```

---

## 🚀 실행 방법

### 1. 의존성 설치
```bash
pip install flet duckdb
```

### 2. 앱 실행
```bash
cd goallog
python main.py
```

---

## 📱 기능 (설계서 Use Case 기반)

| Use Case | 화면 | 구현 |
|---|---|---|
| 3.1 국가대표팀 정보 조회 | Teams 탭 → 팀 상세 | ✅ |
| 3.2 선수 정보 조회 (CRUD) | 팀 상세 → 선수 명단 | ✅ |
| 3.3 매치 일정 조회 | Matches 탭 (날짜 탐색) | ✅ |
| 3.4 팀+선수 통합 JOIN 조회 | 경기 카드 클릭 → 라인업 | ✅ |

---

## 🗄️ 데이터베이스 (DuckDB)

- **teams** — 48개국 국가대표팀 (A~L 그룹)
- **matches** — 104경기 일정 (그룹스테이지 ~ 결승)
- **stadiums** — 경기장 정보
- **players** — 선수 명단 (앱 내 CRUD 가능)

---

## 🏗️ 아키텍처

```
Flet GUI (main.py)
    ↓
Repository Interface (repository.py)   ← ABC 추상화
    ↓
DuckDB Repository (db_repository.py)   ← SQL 구현
    ↓
DuckDB (worldcup.duckdb)
```

설계서 Repository Pattern 완전 준수:
- `ITeamRepository` → `TeamRepository`
- `IPlayerRepository` → `PlayerRepository`  
- `IMatchRepository` → `MatchRepository`
- `IWorldCupQueryRepository` → `WorldCupQueryRepository` (3-table LEFT JOIN)
