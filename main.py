"""
GoalLog - 2026 월드컵 정보 앱
"""
import flet as ft
import pandas as pd
from db_repository import TeamRepository, PlayerRepository, MatchRepository, WorldCupQueryRepository

# ─────────────────────────────────────────────
# 색상 팔레트
# ─────────────────────────────────────────────
C_BG        = "#F0F4F8"
C_PRIMARY   = "#1A3B6E"   # 진한 남색
C_ACCENT    = "#E8473F"   # 월드컵 레드
C_CARD      = "#FFFFFF"
C_TEXT      = "#1C1C1E"
C_SUBTEXT   = "#6B7280"
C_BORDER    = "#E5E7EB"
C_NAV_BG    = "#FFFFFF"
C_SELECTED  = "#1A3B6E"

# ─────────────────────────────────────────────
# Repository 인스턴스
# ─────────────────────────────────────────────
team_repo    = TeamRepository()
player_repo  = PlayerRepository()
match_repo   = MatchRepository()
query_repo   = WorldCupQueryRepository()


# ══════════════════════════════════════════════
# 공통 UI 헬퍼
# ══════════════════════════════════════════════

def app_bar(title: str, on_back=None) -> ft.Container:
    """상단 앱바"""
    leading = ft.IconButton(
        icon=ft.Icons.ARROW_BACK_IOS_NEW,
        icon_color=C_PRIMARY,
        icon_size=20,
        on_click=on_back,
    ) if on_back else ft.Container(width=48)

    return ft.Container(
        content=ft.Row(
            [
                leading,
                ft.Text(title, size=18, weight=ft.FontWeight.W_700, color=C_PRIMARY, expand=True),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=C_CARD,
        padding=ft.Padding(left=8, top=12, right=8, bottom=12),
        shadow=ft.BoxShadow(blur_radius=4, color="#15000000", offset=ft.Offset(0, 2)),
    )


def section_chip(label: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(label, size=11, color=C_ACCENT, weight=ft.FontWeight.W_700),
        bgcolor="#FDECEA",
        border_radius=6,
        padding=ft.Padding(left=8, top=3, right=8, bottom=3),
    )


def divider() -> ft.Divider:
    return ft.Divider(height=1, color=C_BORDER)


# ══════════════════════════════════════════════
# 화면 1 – 팀 목록 (Teams Tab)
# ══════════════════════════════════════════════

def build_teams_tab(page: ft.Page) -> ft.Column:
    teams_df = team_repo.find_all()
    groups = teams_df["group"].unique().tolist()
    groups.sort()

    search_field = ft.TextField(
        hint_text="팀 이름으로 검색…",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=12,
        bgcolor=C_CARD,
        border_color=C_BORDER,
        focused_border_color=C_PRIMARY,
        height=46,
        text_size=13,
        content_padding=ft.Padding(left=14, top=0, right=14, bottom=0),
    )

    list_col = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

    def refresh_list(query: str = ""):
        list_col.controls.clear()
        filtered = teams_df[teams_df["name"].str.contains(query, case=False, na=False)] if query else teams_df
        cur_group = None
        for _, row in filtered.iterrows():
            grp = row["group"]
            if grp != cur_group:
                cur_group = grp
                list_col.controls.append(
                    ft.Container(
                        content=ft.Text(f"Group {grp}", size=12, weight=ft.FontWeight.W_700, color=C_PRIMARY),
                        padding=ft.Padding(left=16, top=12, right=0, bottom=4),
                    )
                )
            list_col.controls.append(_team_card(row, page))
        page.update()

    def on_search(e):
        refresh_list(search_field.value.strip())

    search_field.on_change = on_search

    refresh_list()

    return ft.Column(
        [
            ft.Container(search_field, padding=ft.Padding(left=12, top=8, right=12, bottom=8)),
            ft.Container(list_col, expand=True),
        ],
        expand=True,
        spacing=0,
    )


def _team_card(row, page: ft.Page) -> ft.Container:
    def on_tap(e):
        open_team_detail(page, row["fifa_code"])

    return ft.Container(
        content=ft.Row(
            [
                ft.Text(row["flag_icon"], size=32),
                ft.Column(
                    [
                        ft.Text(row["name"], size=14, weight=ft.FontWeight.W_600, color=C_TEXT),
                        ft.Text(f"{row['confed']}  ·  {row['continent']}", size=11, color=C_SUBTEXT),
                    ],
                    spacing=1,
                    expand=True,
                ),
                ft.Column(
                    [
                        ft.Container(
                            content=ft.Text(f"Group {row['group']}", size=10, color=C_CARD,
                                            weight=ft.FontWeight.W_700),
                            bgcolor=C_PRIMARY,
                            border_radius=4,
                            padding=ft.Padding(left=6, top=2, right=6, bottom=2),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=C_SUBTEXT, size=18),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        ),
        bgcolor=C_CARD,
        border_radius=12,
        padding=ft.Padding(left=14, top=10, right=14, bottom=10),
        margin=ft.Margin(left=12, top=3, right=12, bottom=3),
        shadow=ft.BoxShadow(blur_radius=4, color="#10000000", offset=ft.Offset(0, 1)),
        on_click=on_tap,
        ink=True,
    )


# ══════════════════════════════════════════════
# 화면 2 – 팀 상세 + 선수 관리 (설계서 3.1 / 3.2)
# ══════════════════════════════════════════════

def open_team_detail(page: ft.Page, fifa_code: str):
    team_df  = team_repo.find_by_id(fifa_code)
    if team_df.empty:
        return
    row      = team_df.iloc[0]
    team_name = row["name"]

    # ── 선수 목록 영역
    player_list = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)

    def refresh_players():
        player_list.controls.clear()
        df = player_repo.find_by_team_id(fifa_code)
        if df.empty:
            player_list.controls.append(
                ft.Container(
                    content=ft.Text("등록된 선수가 없습니다.", size=13, color=C_SUBTEXT,
                                    text_align=ft.TextAlign.CENTER),
                    padding=20,
                    alignment=ft.Alignment(0, 0),
                )
            )
        else:
            # 헤더
            player_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("포지션", size=11, color=C_SUBTEXT, width=52),
                            ft.Text("번호", size=11, color=C_SUBTEXT, width=36),
                            ft.Text("이름", size=11, color=C_SUBTEXT, expand=True),
                        ]
                    ),
                    padding=ft.Padding(left=14, top=4, right=14, bottom=4),
                )
            )
            pos_colors = {"GK": "#FFF3CD", "DF": "#D1FAE5", "MF": "#DBEAFE", "FW": "#FCE7F3"}
            pos_text   = {"GK": "#92400E", "DF": "#065F46", "MF": "#1E40AF", "FW": "#9D174D"}
            for _, p in df.iterrows():
                pc = pos_colors.get(str(p.get("position",""))[:2], "#F3F4F6")
                tc = pos_text.get(str(p.get("position",""))[:2], "#374151")
                player_list.controls.append(
                    _player_row(p, pc, tc)
                )
        page.update()

    refresh_players()

    # ── 팀 정보 카드
    team_info = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(row["flag_icon"], size=52),
                        ft.Column(
                            [
                                ft.Text(row["name"], size=20, weight=ft.FontWeight.W_700, color=C_TEXT),
                                ft.Text(f"FIFA 코드  {row['fifa_code']}", size=12, color=C_SUBTEXT),
                            ],
                            spacing=2, expand=True,
                        ),
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                divider(),
                _info_row("지역", f"{row['confed']}  ({row['continent']})"),
                _info_row("그룹 편성", f"Group {row['group']}"),
            ],
            spacing=10,
        ),
        bgcolor=C_CARD,
        border_radius=14,
        padding=16,
        margin=ft.Margin(left=12, top=8, right=12, bottom=8),
        shadow=ft.BoxShadow(blur_radius=6, color="#12000000", offset=ft.Offset(0, 2)),
    )

    # ── 선수 섹션 헤더
    player_header = ft.Container(
        content=ft.Row(
            [
                section_chip("선수 명단"),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(left=16, top=4, right=8, bottom=0),
    )

    content = ft.Column(
        [
            app_bar(team_name, on_back=lambda e: page.views.pop() or page.update()),
            ft.Container(
                content=ft.Column(
                    [team_info, player_header, ft.Container(player_list, expand=True, padding=ft.Padding(left=12, top=0, right=12, bottom=0))],
                    spacing=4,
                    expand=True,
                ),
                expand=True,
            ),
        ],
        spacing=0,
        expand=True,
    )

    page.views.append(
        ft.View(
            route="/team",
            controls=[content],
            bgcolor=C_BG,
            padding=0,
        )
    )
    page.update()


def _info_row(label: str, value: str) -> ft.Row:
    return ft.Row(
        [
            ft.Text(label, size=12, color=C_SUBTEXT, width=80),
            ft.Text(value, size=13, color=C_TEXT, weight=ft.FontWeight.W_500, expand=True),
        ]
    )


def _player_row(p, bg_color: str, txt_color: str) -> ft.Container:
    raw_name = str(p.get("name", ""))
    is_captain = "captain" in raw_name.lower()
    name = raw_name.replace("( captain )", "").replace("(captain)", "").strip()

    name_row = [
        ft.Text(name, size=13, color=C_TEXT, weight=ft.FontWeight.W_500),
    ]
    if is_captain:
        name_row.append(
            ft.Container(
                content=ft.Text("©", size=10, color="#FFFFFF", weight=ft.FontWeight.W_700),
                bgcolor=C_ACCENT,
                border_radius=10,
                padding=ft.Padding(left=5, top=1, right=5, bottom=1),
            )
        )

    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Text(str(p.get("position", ""))[:2], size=10,
                                    color=txt_color, weight=ft.FontWeight.W_700),
                    bgcolor=bg_color, border_radius=5,
                    padding=ft.Padding(left=5, top=2, right=5, bottom=2),
                    width=42,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Text(str(p.get("jersey_number", "")), size=13, color=C_SUBTEXT, width=36,
                        text_align=ft.TextAlign.CENTER),
                ft.Row(name_row, spacing=6, expand=True,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=6,
        ),
        bgcolor=C_CARD,
        border_radius=10,
        padding=ft.Padding(left=10, top=8, right=10, bottom=8),
        margin=ft.Margin(left=0, top=0, right=0, bottom=2),
        shadow=ft.BoxShadow(blur_radius=2, color="#08000000"),
    )


# ══════════════════════════════════════════════
# 화면 3 – 경기 일정 (Matches Tab)  설계서 3.3
# ══════════════════════════════════════════════

def build_matches_tab(page: ft.Page) -> ft.Column:
    all_matches = match_repo.find_all_matches()
    dates = sorted(all_matches["date"].dropna().unique().tolist())

    # 오늘 날짜와 가장 가까운 날짜를 기본값으로
    from datetime import date as dt_date
    today_str = str(dt_date.today())
    selected_date = dates[0] if dates else today_str
    for d in dates:
        if str(d) >= today_str:
            selected_date = d
            break

    date_label = ft.Text(str(selected_date), size=16, weight=ft.FontWeight.W_700,
                         color=C_PRIMARY, text_align=ft.TextAlign.CENTER, expand=True)

    match_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)

    date_idx = [0]
    try:
        date_idx[0] = dates.index(selected_date)
    except ValueError:
        date_idx[0] = 0

    def load_matches(d):
        match_col.controls.clear()
        df = all_matches[all_matches["date"] == d]
        if df.empty:
            match_col.controls.append(
                ft.Container(
                    content=ft.Text("이 날짜에 경기가 없습니다.", color=C_SUBTEXT,
                                    text_align=ft.TextAlign.CENTER),
                    padding=30, alignment=ft.Alignment(0, 0),
                )
            )
        else:
            cur_grp = None
            for _, row in df.iterrows():
                grp = row.get("group", "")
                rnd = row.get("round", "")
                section = grp if grp and str(grp).startswith("Group") else rnd
                if section != cur_grp:
                    cur_grp = section
                    match_col.controls.append(
                        ft.Container(
                            content=ft.Text(str(section), size=11,
                                            color=C_SUBTEXT, weight=ft.FontWeight.W_600),
                            padding=ft.Padding(left=4, top=8, right=0, bottom=2),
                        )
                    )
                match_col.controls.append(_match_card(row, page))
        page.update()

    def prev_date(e):
        if date_idx[0] > 0:
            date_idx[0] -= 1
            d = dates[date_idx[0]]
            date_label.value = str(d)
            load_matches(d)

    def next_date(e):
        if date_idx[0] < len(dates) - 1:
            date_idx[0] += 1
            d = dates[date_idx[0]]
            date_label.value = str(d)
            load_matches(d)

    load_matches(selected_date)

    date_nav = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(ft.Icons.CHEVRON_LEFT, icon_color=C_PRIMARY, on_click=prev_date),
                date_label,
                ft.IconButton(ft.Icons.CHEVRON_RIGHT, icon_color=C_PRIMARY, on_click=next_date),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=C_CARD,
        border_radius=12,
        margin=ft.Margin(left=12, top=8, right=12, bottom=8),
        shadow=ft.BoxShadow(blur_radius=4, color="#10000000", offset=ft.Offset(0, 1)),
    )

    return ft.Column([date_nav, ft.Container(match_col, expand=True, padding=ft.Padding(left=12, top=0, right=12, bottom=0))],
                     spacing=0, expand=True)


def _match_card(row, page: ft.Page) -> ft.Container:
    flag1 = row.get("flag1", "🏳️") or "🏳️"
    flag2 = row.get("flag2", "🏳️") or "🏳️"
    team1 = str(row.get("team1", ""))
    team2 = str(row.get("team2", ""))
    code1 = str(row.get("code1", ""))
    code2 = str(row.get("code2", ""))
    time_str = str(row.get("time", ""))
    ground   = str(row.get("ground", ""))
    date_str = str(row.get("date", ""))

    def on_tap(e):
        match_key = f"{team1}::{team2}::{date_str}"
        open_match_detail(page, match_key)

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [ft.Text(flag1, size=28), ft.Text(team1, size=11, color=C_TEXT,
                                                               weight=ft.FontWeight.W_600,
                                                               text_align=ft.TextAlign.CENTER)],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("VS", size=14, weight=ft.FontWeight.W_800,
                                            color=C_ACCENT, text_align=ft.TextAlign.CENTER),
                                    ft.Text(time_str[:5], size=10, color=C_SUBTEXT,
                                            text_align=ft.TextAlign.CENTER),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=2,
                            ),
                            width=56,
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Column(
                            [ft.Text(flag2, size=28), ft.Text(team2, size=11, color=C_TEXT,
                                                               weight=ft.FontWeight.W_600,
                                                               text_align=ft.TextAlign.CENTER)],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=True,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [ft.Icon(ft.Icons.STADIUM_OUTLINED, size=12, color=C_SUBTEXT),
                     ft.Text(ground, size=11, color=C_SUBTEXT)],
                    spacing=4,
                ),
            ],
            spacing=8,
        ),
        bgcolor=C_CARD,
        border_radius=14,
        padding=ft.Padding(left=14, top=12, right=14, bottom=12),
        margin=ft.Margin(left=0, top=0, right=0, bottom=6),
        shadow=ft.BoxShadow(blur_radius=4, color="#10000000", offset=ft.Offset(0, 1)),
        on_click=on_tap,
        ink=True,
    )


# ══════════════════════════════════════════════
# 화면 4 – 경기 상세 / 선수 통합 조회 (설계서 3.4 Join)
# ══════════════════════════════════════════════

def open_match_detail(page: ft.Page, match_key: str):
    result = query_repo.find_match_with_teams_and_players(match_key)
    if not result or result["match"].empty:
        return

    match_row = result["match"].iloc[0]
    players1  = result["players1"]
    players2  = result["players2"]

    team1  = str(match_row.get("team1", ""))
    team2  = str(match_row.get("team2", ""))
    flag1  = match_row.get("flag1", "🏳️") or "🏳️"
    flag2  = match_row.get("flag2", "🏳️") or "🏳️"
    grp    = match_row.get("group", "")
    rnd    = match_row.get("round", "")
    date   = match_row.get("date", "")
    time_  = str(match_row.get("time", ""))[:5]
    ground = str(match_row.get("ground", ""))
    section = grp if str(grp).startswith("Group") else rnd

    # ── 경기 결과 헤더
    match_header = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Text(f"[ {section} ]", size=12, color=C_SUBTEXT,
                                    weight=ft.FontWeight.W_600,
                                    text_align=ft.TextAlign.CENTER),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Row(
                    [
                        ft.Column(
                            [ft.Text(flag1, size=40), ft.Text(team1, size=12,
                                                               text_align=ft.TextAlign.CENTER,
                                                               weight=ft.FontWeight.W_700)],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Text("VS", size=22, weight=ft.FontWeight.W_900,
                                            color=C_ACCENT),
                            width=64, alignment=ft.Alignment(0, 0),
                        ),
                        ft.Column(
                            [ft.Text(flag2, size=40), ft.Text(team2, size=12,
                                                               text_align=ft.TextAlign.CENTER,
                                                               weight=ft.FontWeight.W_700)],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            expand=True,
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(f"{date}  {time_}", size=12, color=C_SUBTEXT,
                        text_align=ft.TextAlign.CENTER),
                ft.Row(
                    [ft.Icon(ft.Icons.STADIUM_OUTLINED, size=13, color=C_SUBTEXT),
                     ft.Text(ground, size=12, color=C_SUBTEXT)],
                    alignment=ft.MainAxisAlignment.CENTER, spacing=4,
                ),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=C_CARD,
        border_radius=14,
        padding=16,
        margin=ft.Margin(left=12, top=8, right=12, bottom=8),
        shadow=ft.BoxShadow(blur_radius=6, color="#12000000", offset=ft.Offset(0, 2)),
    )

    # ── 양팀 선수 명단 (JOIN 결과)
    def player_table(df: pd.DataFrame, team_name: str) -> ft.Container:
        rows = []
        pos_colors = {"GK": "#FFF3CD", "DF": "#D1FAE5", "MF": "#DBEAFE", "FW": "#FCE7F3"}
        pos_text   = {"GK": "#92400E", "DF": "#065F46", "MF": "#1E40AF", "FW": "#9D174D"}
        if df.empty:
            rows.append(ft.Text("선수 정보 없음", size=12, color=C_SUBTEXT))
        else:
            for _, p in df.iterrows():
                pos = str(p.get("position", ""))[:2]
                pc  = pos_colors.get(pos, "#F3F4F6")
                tc  = pos_text.get(pos, "#374151")
                raw_name = str(p.get("name", ""))
                is_captain = "captain" in raw_name.lower()
                name = raw_name.replace("( captain )", "").replace("(captain)", "").strip()
                name_widgets = [
                    ft.Text(name, size=11, color=C_TEXT,
                            weight=ft.FontWeight.W_500, expand=True),
                ]
                if is_captain:
                    name_widgets.append(
                        ft.Container(
                            content=ft.Text("©", size=9, color="#FFFFFF",
                                            weight=ft.FontWeight.W_700),
                            bgcolor=C_ACCENT,
                            border_radius=10,
                            padding=ft.Padding(left=4, top=1, right=4, bottom=1),
                        )
                    )
                rows.append(
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(pos, size=9, color=tc, weight=ft.FontWeight.W_700),
                                bgcolor=pc, border_radius=4,
                                padding=ft.Padding(left=4, top=1, right=4, bottom=1),
                                width=34, alignment=ft.Alignment(0, 0),
                            ),
                            ft.Text(str(p.get("jersey_number", "")), size=11,
                                    color=C_SUBTEXT, width=22),
                            ft.Row(name_widgets, spacing=4, expand=True,
                                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ],
                        spacing=6,
                    )
                )

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(f"{team_name} 선수명단",
                            size=12, weight=ft.FontWeight.W_700, color=C_PRIMARY),
                    ft.Divider(height=1, color=C_BORDER),
                    *rows,
                ],
                spacing=5,
            ),
            bgcolor=C_CARD,
            border_radius=12,
            padding=12,
            expand=True,
        )

    lineup_section = ft.Container(
        content=ft.Column(
            [
                section_chip("경기 라인업"),
                ft.Row(
                    [
                        player_table(players1, team1),
                        ft.VerticalDivider(width=1, color=C_BORDER),
                        player_table(players2, team2),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    expand=True,
                    spacing=8,
                ),
            ],
            spacing=8,
            expand=True,
        ),
        bgcolor=C_BG,
        padding=ft.Padding(left=12, top=4, right=12, bottom=4),
        expand=True,
    )

    content = ft.Column(
        [
            app_bar(f"{team1} vs {team2}",
                    on_back=lambda e: page.views.pop() or page.update()),
            ft.Container(
                content=ft.Column(
                    [match_header, lineup_section],
                    spacing=0,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
                expand=True,
            ),
        ],
        spacing=0,
        expand=True,
    )

    page.views.append(
        ft.View(
            route="/match",
            controls=[content],
            bgcolor=C_BG,
            padding=0,
        )
    )
    page.update()


# ══════════════════════════════════════════════
# 메인 앱 진입점
# ══════════════════════════════════════════════

def main(page: ft.Page):
    page.title = "GoalLog"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = C_BG
    page.padding = 0
    page.window.width  = 420
    page.window.height = 820
    page.window.resizable = True

    # ── 탭 콘텐츠
    tab_contents = [None, None]  # [matches_tab, teams_tab]

    matches_tab_ctrl = build_matches_tab(page)
    teams_tab_ctrl   = build_teams_tab(page)

    # ── 탭 뷰 컨테이너
    content_area = ft.Container(expand=True)

    def switch_tab(idx: int):
        if idx == 0:
            content_area.content = matches_tab_ctrl
        else:
            content_area.content = teams_tab_ctrl

        page.update()

    nav_buttons = [
        ft.NavigationBarDestination(
            icon=ft.Icons.CALENDAR_MONTH_OUTLINED,
            selected_icon=ft.Icons.CALENDAR_MONTH,
            label="Matches",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.GROUPS_OUTLINED,
            selected_icon=ft.Icons.GROUPS,
            label="Teams",
        ),
    ]

    def on_nav(e):
        switch_tab(e.control.selected_index)

    nav_bar = ft.NavigationBar(
        destinations=nav_buttons,
        selected_index=0,
        bgcolor=C_NAV_BG,
        indicator_color="#E8F0FE",
        shadow_color="#20000000",
        on_change=on_nav,
    )

    # ── 앱바 (최상단)
    top_bar = ft.Container(
        content=ft.Row(
            [
                ft.Text("⚽", size=22),
                ft.Text("GoalLog", size=20, weight=ft.FontWeight.W_800, color=C_PRIMARY),
                ft.Container(expand=True),
                ft.Text("2026 FIFA World Cup™", size=10, color=C_SUBTEXT),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=C_CARD,
        padding=ft.Padding(left=16, top=12, right=16, bottom=12),
        shadow=ft.BoxShadow(blur_radius=4, color="#12000000", offset=ft.Offset(0, 2)),
    )

    # ── 라우팅 (뒤로가기)
    def on_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            page.update()

    page.on_view_pop = on_pop

    page.views.clear()
    page.views.append(
        ft.View(
            route="/",
            controls=[
                ft.Column(
                    [
                        top_bar,
                        ft.Container(content_area, expand=True),
                    ],
                    spacing=0,
                    expand=True,
                )
            ],
            navigation_bar=nav_bar,
            bgcolor=C_BG,
            padding=0,
        )
    )

    switch_tab(0)


if __name__ == "__main__":
    ft.run(main)