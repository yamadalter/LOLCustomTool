import datetime
from PyQt6.QtWidgets import QMessageBox, QLabel, QWidget, QVBoxLayout
from common import POSITION, ROLES
from lcu_worker import PlayerData
from widgets import PlayerRowWidget


def on_connected(flag):
    """データベース接続完了時に呼び出されるスロット"""
    print('データベース接続が完了しました')


def on_uploaded(flag):
    msg_box = QMessageBox()  # QMessageBoxのインスタンスを作成
    if flag:
        msg_box.setText('アップロード完了しました')
    else:
        msg_box.setText('アップロード失敗しました')
    msg_box.exec()


def add_player(main_window):
    name = main_window.player_name_input.text()
    rank = main_window.rank_combobox.currentText()
    row = main_window.player_grid.rowCount()
    if not name:
        QMessageBox.warning(main_window, "エラー", "プレイヤー名を入力してください。")
        return
    player = PlayerData()
    player.name = name
    player.rank = rank
    player.tag = 'JP1'
    player.spectator = False
    main_window.add_player_gui(player, row)


def add_players_to_list(main_window, players):
    for row, player in enumerate(players, start=main_window.player_grid.rowCount()):
        if not any(p.name == player.name for p in main_window.player_list):
            main_window.add_player_gui(player, row)


def game_id_selected(main_window, index):
    selected_game_id = main_window.game_id_combobox.itemText(index)
    if selected_game_id != "選択してください" and selected_game_id != "":  # 初期値の場合は何もしない
        # レイアウト内のすべてのウィジェットを削除
        for i in reversed(range(main_window.game_result_grid.count())):
            main_window.game_result_grid.itemAt(i).widget().setParent(None)
        # タイトルを表示
        main_window.game_data = main_window.handler.get_game_data(main_window.history[int(selected_game_id)])
        td = datetime.timedelta(seconds=main_window.game_data.gameDuration)
        main_window.title_label = QLabel(f"Summoner's Rift ({td})")
        main_window.title_label.setAlignment(main_window.Qt.AlignmentFlag.AlignLeft)
        main_window.game_result_grid.addWidget(main_window.title_label, 0, 0, 1, 11)

        # チームごとのプレイヤーウィジェットを保持するコンテナ
        main_window.team_widgets = {1: QWidget(), 2: QWidget()}
        main_window.team_layouts = {1: QVBoxLayout(main_window.team_widgets[1]), 2: QVBoxLayout(main_window.team_widgets[2])}
        main_window.team_layouts[1].setContentsMargins(0, 0, 0, 0)
        main_window.team_layouts[2].setContentsMargins(0, 0, 0, 0)

        # 勝者と敗者を分けて表示
        for team in main_window.game_data.teams:
            team_id = 1 if team.isWinner == 'Win' else 2
            display_team(main_window, main_window.game_result_grid, team_id, "Winners" if team_id == 1 else "Losers", team)

        main_window.game_result_grid.addWidget(main_window.team_widgets[1], 2, 0, 1, 12)
        main_window.game_result_grid.addWidget(main_window.team_widgets[2], 13, 0, 1, 12)


def display_team(main_window, grid, team_id, title, team):
    # チームタイトルを表示
    kill, death, assi = 0, 0, 0
    for p in team.participants:
        kill += p.stats['kills']
        death += p.stats['deaths']
        assi += p.stats['assists']

    row = 1 if team_id == 1 else 12
    main_window.team_title_label = QLabel(f"{title} ({kill}/{death}/{assi})")
    main_window.team_title_label.setAlignment(main_window.Qt.AlignmentFlag.AlignLeft)
    grid.addWidget(main_window.team_title_label, row, 0, 1, 12)

    # BAN Champを表示
    main_window.ban_title_label = QLabel("BANS:")
    main_window.ban_title_label.setAlignment(main_window.Qt.AlignmentFlag.AlignLeft)
    grid.addWidget(main_window.ban_title_label, row, 4)
    champ_data = main_window.handler.champ_data
    if len(team.bans) > 0:
        for i, champ in enumerate(team.bans):
            for champion_name, champion_data in champ_data['data'].items():
                if int(champion_data['key']) == champ.championId:
                    champ.championName = champion_name
                    pixmap = main_window.handler.get_champ_image(champion_name)
                    pixmap = pixmap.scaled(30, 30, main_window.Qt.AspectRatioMode.KeepAspectRatio)
                    champ_label = QLabel()
                    champ_image = main_window.QPixmap(pixmap)  # 画像パスを指定
                    champ_label.setPixmap(champ_image)
                    grid.addWidget(champ_label, row, 5 + i)

    # 各プレイヤーの情報を表示
    team_layout = main_window.team_layouts[team_id]
    sorted_participants = sorted(team.participants, key=lambda p: POSITION.index(p.position))
    for player in sorted_participants:
        player_widget = PlayerRowWidget(player, main_window.handler, main_window)
        player_widget.setObjectName(player.player['puuid'])
        team_layout.addWidget(player_widget)


def lobby_worker(main_window):
    main_window.lobby_worker_thread.mode = "lobby"
    main_window.lobby_worker_thread.start()


def get_game_history(main_window):
    main_window.history_worker_thread.mode = "history"  # ワーカースレッドにモードを設定
    main_window.history_worker_thread.start()


def display_game_history(main_window, history):
    # history を QTextEdit に表示する処理
    main_window.game_id_combobox.clear()  # コンボボックスをクリア
    if history:
        main_window.history = history
        main_window.game_id_combobox.addItem("選択してください")  # 初期値を追加
        for matchid in main_window.history:
            main_window.game_id_combobox.addItem(str(matchid))  # ゲームIDを文字列に変換して追加
