import random
from itertools import combinations, product
from PyQt6.QtWidgets import QMessageBox, QListWidgetItem
from common import RANK_VAL, ROLES, RANKS, RANKS_TAG


def divide_teams(main_window):
    attend_players = []
    for player in main_window.player_list:
        attend_check = False
        for role in ROLES:
            role_rank = RANKS[RANKS_TAG.index(getattr(player, f"{role}_rank_combobox").currentText())]
            setattr(player, f"{role}_rank", role_rank)

            if getattr(player, role).isChecked():
                if not attend_check:
                    attend_check = True
                    attend_players.append(player)

    if len(attend_players) != 10:
        QMessageBox.warning(main_window, "エラー", "チーム分けには10人のプレイヤーが必要です。")
        return

    # チーム分けを実行
    tolerance = main_window.tolerance_spinbox.value()
    team1, team2 = perform_team_division(main_window, attend_players, tolerance)

    if team1 is not None and team2 is not None:
        # 結果をリストに表示
        main_window.team1_list.clear()
        main_window.team2_list.clear()
        main_window.team1_player = []
        main_window.team2_player = []
        for player, role in zip(team1, ROLES):
            item = QListWidgetItem(f"{role}: {player.name} ({getattr(player, f'{role}_rank')})")
            main_window.team1_list.addItem(item)
            player.role = role  # Add this line
            main_window.team1_player.append(player)
        for player, role in zip(team2, ROLES):
            item = QListWidgetItem(f"{role}: {player.name} ({getattr(player, f'{role}_rank')})")
            main_window.team2_list.addItem(item)
            player.role = role  # Add this line
            main_window.team2_player.append(player)

        # 差分を計算
        show_diff_role_based(main_window, team1, team2)  # 新しい差分表示メソッド
    else:
        QMessageBox.warning(main_window, "エラー", "チーム分けに失敗しました。ロールの組み合わせを確認してください。")


def perform_team_division(main_window, players, tolerance):
    # プレイヤーのロール情報を辞書にまとめる
    roles = {'top': [], 'jg': [], 'mid': [], 'bot': [], 'sup': []}
    for player in players:
        # player.rank_val = RANK_VAL[player.rank]  # ランク値を追加
        for role in roles:
            if getattr(player, role).isChecked():
                roles[role].append(player)

    # 各ロールのプレイヤー数を表示 (デバッグ用)
    for role, player_list in roles.items():
        if len(player_list) < 2:
            QMessageBox.warning(main_window, "エラー", f"{role}のプレイヤー数は2人以上である必要があります")
            return None, None

    valid_teams = create_teams(players)

    if len(valid_teams) > 0:
        for team1, team2 in valid_teams:
            if random.random() < 0.5:  # 50%の確率でチームを入れ替える
                team1, team2 = team2, team1
            
            # ランク差が許容範囲内になるまでチームメンバーを調整
            # ロール割り当てを先に行う
            assignments1 = assign_roles(team1)
            if not assignments1:
                continue
            team1_assigned = random.choice(assignments1)

            assignments2 = assign_roles(team2)
            if not assignments2:
                continue
            team2_assigned = random.choice(assignments2)

            team1_total_rank = sum(RANK_VAL[getattr(player, f"{role}_rank")] for player, role in zip(team1_assigned, ROLES))
            team2_total_rank = sum(RANK_VAL[getattr(player, f"{role}_rank")] for player, role in zip(team2_assigned, ROLES))

            diff = abs(team1_total_rank - team2_total_rank)
            if diff <= tolerance:
                for player, role in zip(team1_assigned, ROLES):
                    player.role = role
                for player, role in zip(team2_assigned, ROLES):
                    player.role = role
                return team1_assigned, team2_assigned

    return None, None


def create_teams(players):
    """
    複数のロールを選択しているプレイヤーを2つのチームに分割する関数

    Args:
    players: 各プレイヤーが選択したロールを表すオブジェクトのリスト。
    各プレイヤーオブジェクトは、選択したロールの属性がTrueになります。
    Returns:
    2つのチームの可能な組み合わせのリスト。各チームは、各ロールのプレイヤーが1人ずつ含まれています。
    """
    n = len(players) // 2
    all_combinations = list(combinations(players, n))
    random.shuffle(all_combinations)
    valid_teams = []
    roles = ROLES
    for team1 in all_combinations:
        team2 = [player for player in players if player not in team1]
        # チーム1がすべてのロールを持っているか確認する
        has_all_roles_team1 = all(any(getattr(player, role).isChecked() for player in team1) for role in roles)
        # チーム2がすべてのロールを持っているか確認する
        has_all_roles_team2 = all(any(getattr(player, role).isChecked() for player in team2) for role in roles)
        if has_all_roles_team1 and has_all_roles_team2:
            valid_teams.append((team1, team2))
    return valid_teams


def assign_roles(team):
    combinations = []
    role_assignments = [[player for player in team if getattr(player, role).isChecked()] for role in ROLES]
    
    # Check if any role has no players
    if not all(role_assignments):
        return []

    for combination in product(*role_assignments):
        # 重複がない組み合わせのみ追加
        if len(set(combination)) == len(combination):
            combinations.append(combination)

    return combinations


def show_diff_role_based(main_window, team1, team2):
    team1_rank = sum(RANK_VAL[getattr(player, f"{role}_rank")] for player, role in zip(team1, ROLES))
    team2_rank = sum(RANK_VAL[getattr(player, f"{role}_rank")] for player, role in zip(team2, ROLES))
    diff = abs(team1_rank - team2_rank)
    # ラベルにランクを表示
    main_window.team1_score.setText(f"Score: {team1_rank}")
    main_window.team2_score.setText(f"Score: {team2_rank}")
    main_window.diff_label.setText(f"チームのランク差: {diff}")
