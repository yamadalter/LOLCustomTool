import random
import json
import datetime
from common import VERSION, RANK_VAL, RANKS, ROLES
from datahandler import LoLDataHandler
from lcu_worker import WorkerThread, PlayerData  # lcu_worker.py から WorkerThread をインポート
from register import MatchDataUploader
from datetime import timedelta
from itertools import combinations, product
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QGroupBox,
    QSpinBox,
    QInputDialog,
    QApplication,
    QGridLayout,
    QCheckBox,
    QFileDialog,
    QMenu
)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap
from cassiopeia.data import Side


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):  # Arrowオブジェクトはisoformat()メソッドを持つ
            return obj.isoformat()
        elif isinstance(obj, timedelta):
            return str(obj)  # 文字列に変換
        elif isinstance(obj, Side):  # Sideオブジェクトを処理
            return obj.name  # Sideオブジェクトのname属性を返す
        return super().default(obj)  # その他のオブジェクトはデフォルトの処理


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # initial
        self.history = {}
        self.handler = LoLDataHandler()
        self.uploader = MatchDataUploader()
        self.uploader.connected.connect(self.on_connected)  # 接続完了シグナルにスロットを接続
        self.uploader.upload_finished.connect(self.on_uploaded)  # 接続完了シグナルにスロットを接続
        self.uploader.start()  # スレッドを開始

        # ウィンドウの設定
        self.setWindowTitle("LoLチーム分け")

        # GUIのレイアウトを構築
        main_layout = QHBoxLayout()
        teamsplit_layout = QVBoxLayout()
        gameresult_layout = QVBoxLayout()

        # プレイヤー情報入力エリア
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("プレイヤー名:"))
        self.player_name_input = QLineEdit()
        input_layout.addWidget(self.player_name_input)
        input_layout.addWidget(QLabel("ランク:"))
        self.rank_combobox = QComboBox()
        self.rank_combobox.addItems(RANKS)
        input_layout.addWidget(self.rank_combobox)
        self.add_player_button = QPushButton("追加")
        self.add_player_button.clicked.connect(self.add_player)
        input_layout.addWidget(self.add_player_button)
        teamsplit_layout.addLayout(input_layout)

        # プレイヤー辞書エリア
        dict_layout = QHBoxLayout()
        dict_layout.addWidget(QLabel("Player info:"))
        self.save_dict_button = QPushButton("SAVE")
        self.save_dict_button.clicked.connect(self.save_dict_to_file)
        dict_layout.addWidget(self.save_dict_button)
        self.load_dict_button = QPushButton("LOAD")
        self.load_dict_button.clicked.connect(self.load_dict_from_file)
        dict_layout.addWidget(self.load_dict_button)
        dict_layout.addSpacing(300)
        teamsplit_layout.addLayout(dict_layout)

        # プレイヤー情報表示エリア
        player_group = QGroupBox("プレイヤー")
        player_group.setMinimumSize(100, 50)
        player_group.setAlignment(Qt.AlignmentFlag.AlignTop)
        player_group.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # Apply to parent
        player_group.customContextMenuRequested.connect(self.show_context_menu)  # Connect to parent
        self.player_grid = QGridLayout()
        self.player_grid_init()
        self.player_list = []
        player_group.setLayout(self.player_grid)
        teamsplit_layout.addWidget(player_group)

        # チーム分け結果表示エリア
        team_group = QGroupBox("チーム分け結果")
        team_layout = QHBoxLayout()
        self.team1_list = QListWidget()
        self.team2_list = QListWidget()
        self.team1_player = []
        self.team2_player = []
        team_layout.addWidget(self.team1_list)
        team_layout.addWidget(self.team2_list)

        # チームのランク差を表示するラベル
        self.diff_label = QLabel()
        team_layout.addWidget(self.diff_label)
        team_group.setLayout(team_layout)
        teamsplit_layout.addWidget(team_group)

        # 許容ランク誤差入力エリア
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("許容ランク誤差:"))
        self.tolerance_spinbox = QSpinBox()
        self.tolerance_spinbox.setRange(0, 100)  # 許容範囲を設定
        self.tolerance_spinbox.setValue(5)  # デフォルト値を設定 (必要に応じて変更)
        tolerance_layout.addWidget(self.tolerance_spinbox)
        teamsplit_layout.addLayout(tolerance_layout)

        # ロビーからプレイヤーを追加するボタン
        self.add_from_lobby_button = QPushButton("ロビーから追加")
        self.add_from_lobby_button.clicked.connect(self.lobby_worker)
        self.lobby_worker_thread = WorkerThread()
        self.lobby_worker_thread.data_updated.connect(self.add_players_to_list)  # シグナルにスロットを接続
        input_layout.addWidget(self.add_from_lobby_button)

        # チーム分け実行ボタン
        button_layout = QHBoxLayout()  # ボタンを横並びにするためのレイアウト
        self.divide_button = QPushButton("チーム分け")
        self.divide_button.clicked.connect(self.divide_teams)
        button_layout.addWidget(self.divide_button)

        # クリップボードにコピーするボタン
        self.copy_button = QPushButton("結果コピー")
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(self.copy_button)
        self.copy_button_opgg = QPushButton("結果コピー(opgg)")
        self.copy_button_opgg.clicked.connect(self.copy_to_clipboard_opgg)
        button_layout.addWidget(self.copy_button_opgg)
        teamsplit_layout.addLayout(button_layout)  # ボタンレイアウトを追加

        # 署名欄
        signature_layout = QHBoxLayout()
        signature_layout.addWidget(QLabel(f"version:{VERSION}"))
        signature_layout.addStretch(1)
        signature_layout.addWidget(QLabel("Produced by yamadalter"))
        x_label = QLabel("<a href='https://x.com/yamadalter'><img src='material/logo-black.png'></a>")
        x_label.setOpenExternalLinks(True)
        x_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        git_label = QLabel("<a href='https://github.com/yamadalter/LOLCustomTool'><img src='material/github-mark.png'></a>")
        git_label.setOpenExternalLinks(True)
        git_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        signature_layout.addWidget(x_label)
        signature_layout.addWidget(git_label)
        teamsplit_layout.addLayout(signature_layout)

        # 試合結果取得ボタン
        result_button_layout = QHBoxLayout()
        self.get_game_results_button = QPushButton("試合結果取得")
        self.get_game_results_button.clicked.connect(self.get_game_history)
        result_button_layout.addWidget(self.get_game_results_button)

        # 試合履歴取得用のワーカースレッド
        self.history_worker_thread = WorkerThread()
        self.history_worker_thread.history_updated.connect(self.display_game_history)

        # ゲームID選択用のコンボボックス
        self.game_id_combobox = QComboBox()
        self.game_id_combobox.currentIndexChanged.connect(self.game_id_selected)  # コンボボックスの選択変更時の処理
        result_button_layout.addWidget(self.game_id_combobox)

        # 試合結果を出力するボタン
        self.result_output_button = QPushButton("結果アップロード")
        self.result_output_button.clicked.connect(self.output_result)
        result_button_layout.addWidget(self.result_output_button)

        # 取得結果表示
        game_results_outer_layout = QVBoxLayout()
        game_results_outer_layout.addLayout(result_button_layout)

        # 試合結果表示エリア
        game_results_group = QGroupBox("試合結果")
        self.result_context_layout = QVBoxLayout()
        self.game_result_grid = QGridLayout()
        self.result_context_layout.addLayout(self.game_result_grid)
        game_results_group.setLayout(self.result_context_layout)
        game_results_group.setMinimumSize(500, 600)

        # 試合結果取得ボタンと試合結果表示エリアをまとめる
        game_results_outer_layout.addWidget(game_results_group)

        # メインレイアウトに試合結果関連のレイアウトを追加
        gameresult_layout.addLayout(game_results_outer_layout)

        main_layout.addLayout(teamsplit_layout)
        main_layout.addLayout(gameresult_layout)

        self.setLayout(main_layout)

        # 試合履歴取得用のワーカースレッド
        self.history_worker_thread = WorkerThread()
        self.history_worker_thread.history_updated.connect(self.display_game_history)

    def player_grid_init(self):
        for col, label_text in enumerate(("参加", "NAME", "RANK", "TOP", "JG", "MID", "BOT", "SUP")):
            self.player_grid.addWidget(QLabel(label_text), 0, col)
            self.player_grid.setColumnStretch(col, 1)

    def show_context_menu(self, pos: QPoint):
        """プレイヤー情報表示エリアの右クリックメニューを表示"""
        global_pos = self.player_grid.parentWidget().mapToGlobal(pos)
        menu = QMenu(self)
        delete_action = menu.addAction("削除")
        roll_action = menu.addAction("全選択")
        action = menu.exec(global_pos)
        for row in range(self.player_grid.rowCount()):
            for col in range(self.player_grid.columnCount()):
                item = self.player_grid.itemAtPosition(row, col)
                if item is not None:
                    widget = item.widget()
                    if widget.geometry().contains(pos):
                        if action == delete_action:
                            self.delete_row(row)  # Delete the row
                        elif action == roll_action:
                            self.check_all_roles(row)  # Delete the row
                        return  # Stop searching after deleting

    def show_diff(self, team1, team2):
        team1_rank = sum(self.rank_to_value(player.rank) for player in team1)
        team2_rank = sum(self.rank_to_value(player.rank) for player in team2)
        diff = abs(team1_rank - team2_rank)
        # ラベルにランク差を表示
        self.diff_label.setText(f"チームのランク差: {diff}")

    def delete_row(self, row):
        """指定された行を削除"""
        if 0 <= row < self.player_grid.rowCount():
            # グリッドレイアウトからプレイヤー名を取得
            item = self.player_grid.itemAtPosition(row, 1)  # 1列目はプレイヤー名
            if item:
                player_name_widget = item.widget()
                player_name = player_name_widget.text()

                # player_list から対応するプレイヤーを削除
                self.player_list = [player for player in self.player_list if player.name != player_name]

            # グリッドレイアウトからウィジェットを削除
            for col in range(self.player_grid.columnCount()):
                item = self.player_grid.itemAtPosition(row, col)
                if item:
                    widget = item.widget()
                    self.player_grid.removeWidget(widget)
                    widget.deleteLater()

            # グリッドレイアウトの行数を調整
            self.player_grid.setRowStretch(self.player_grid.rowCount() - 1, 0)

    def check_all_roles(self, row):
        """指定された行のロールを選択状態にする"""
        if 0 <= row < self.player_grid.rowCount():
            for col in range(3, self.player_grid.columnCount()):
                item = self.player_grid.itemAtPosition(row, col)
                if item:
                    widget = item.widget()
                    widget.setChecked(True)

    def lobby_worker(self):
        self.lobby_worker_thread.mode = "lobby"
        self.lobby_worker_thread.start()

    def get_game_history(self):
        self.history_worker_thread.mode = "history"  # ワーカースレッドにモードを設定
        self.history_worker_thread.start()

    def display_game_history(self, history):
        # history を QTextEdit に表示する処理
        self.game_id_combobox.clear()  # コンボボックスをクリア
        if history:
            self.history = history
            self.game_id_combobox.addItem("選択してください")  # 初期値を追加
            for matchid in self.history:
                self.game_id_combobox.addItem(str(matchid))  # ゲームIDを文字列に変換して追加

    def game_id_selected(self, index):
        selected_game_id = self.game_id_combobox.itemText(index)
        if selected_game_id != "選択してください":  # 初期値の場合は何もしない
            # レイアウト内のすべてのウィジェットを削除
            for i in reversed(range(self.game_result_grid.count())):
                self.game_result_grid.itemAt(i).widget().setParent(None)
            # タイトルを表示
            self.game_data = self.handler.get_game_data(self.history[int(selected_game_id)])
            td = datetime.timedelta(seconds=self.game_data.gameDuration)
            self.title_label = QLabel(f"Summoner's Rift ({td})")
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.game_result_grid.addWidget(self.title_label, 0, 0, 1, 11)
            # 勝者と敗者を分けて表示
            for team in self.game_data.teams:
                if team.isWinner == 'Win':
                    self.display_team(self.game_result_grid, 1, "Winners", team)  # 2行目から開始
                else:
                    self.display_team(self.game_result_grid, 12, "Losers", team)  # 13行目から開始

    def display_team(self, grid, row, title, team):
        # チームタイトルを表示
        kill, death, assi = 0, 0, 0
        for p in team.participants:
            kill += p.stats['kills']
            death += p.stats['deaths']
            assi += p.stats['assists']

        self.team_title_label = QLabel(f"{title} ({kill}/{death}/{assi})")
        self.team_title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self.team_title_label, row, 0, 1, 12)

        # BAN Champを表示
        self.ban_title_label = QLabel("BANS:")
        self.ban_title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self.ban_title_label, row, 4)
        champ_data = self.handler.champ_data
        for i, champ in enumerate(team.bans):
            for champion_name, champion_data in champ_data['data'].items():
                if int(champion_data['key']) == champ.championId:
                    champ.championName = champion_name
                    pixmap = self.handler.get_champ_image(champion_name)
                    pixmap = pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio)
                    champ_label = QLabel()
                    champ_image = QPixmap(pixmap)  # 画像パスを指定
                    champ_label.setPixmap(champ_image)
                    grid.addWidget(champ_label, row, 5 + i)  # 3列目から開始

        # 各プレイヤーの情報を表示
        j = 0
        for position in ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']:
            for player in team.participants:
                if player.position == position:
                    row_offset = row + j + 1
                    self.display_player(grid, row_offset, player)
                    j += 1

    def display_player(self, grid, row, palyer):

        # サモナー名を表示
        summoner_name_label = QLabel(palyer.player['gameName'])
        grid.addWidget(summoner_name_label, row, 0)

        # KDAを表示
        self.kda_label = QLabel(f"{palyer.stats['kills']}/{palyer.stats['deaths']}/{palyer.stats['assists']}")
        # self.kda_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(self.kda_label, row, 1)

        # ルーン画像を表示
        rune_label1 = QLabel()
        rune_images = self.handler.get_rune_image(palyer)
        rune_image1 = QPixmap(rune_images[0])  # 画像パスを指定
        rune_label1.setPixmap(rune_image1)
        grid.addWidget(rune_label1, row, 2)
        rune_label2 = QLabel()
        rune_image2 = QPixmap(rune_images[1])  # 画像パスを指定
        rune_label2.setPixmap(rune_image2)
        grid.addWidget(rune_label2, row, 3)

        # チャンピオン画像を表示
        champion_label = QLabel()
        champ_image = self.handler.get_champ_image(palyer.championName)
        champ_image = champ_image.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)
        champion_image = QPixmap(champ_image)  # 画像パスを指定
        champion_label.setPixmap(champion_image)
        grid.addWidget(champion_label, row, 4)

        # アイテム画像を表示
        item_images = self.handler.get_item_images(palyer)
        for j, item_image in enumerate(item_images):
            item_label = QLabel()
            item_image = QPixmap(item_image)  # 画像パスを指定
            item_label.setPixmap(item_image)
            grid.addWidget(item_label, row, 5 + j)  # 4列目から開始

    def add_player_gui(self, player, row):

        player.attend_check = QCheckBox('')
        if player.spectator:
            player.attend_check.setChecked(False)
        else:
            player.attend_check.setChecked(True)
        self.player_grid.addWidget(player.attend_check, row, 0)
        self.player_grid.addWidget(QLabel(f"{player.name}"), row, 1)

        player.rank_combobox = QComboBox()
        player.rank_combobox.addItems(RANKS)
        player.rank_combobox.setCurrentText(player.rank)
        self.player_grid.addWidget(player.rank_combobox, row, 2)

        for col, role in enumerate(ROLES, start=3):
            setattr(player, role, QCheckBox(''))
            self.player_grid.addWidget(getattr(player, role), row, col)

        self.player_list.append(player)

    def add_players_to_list(self, players):
        for row, player in enumerate(players, start=self.player_grid.rowCount()):
            if not any(p.name == player.name for p in self.player_list):
                self.add_player_gui(player, row)

    def add_player(self):
        name = self.player_name_input.text()
        rank = self.rank_combobox.currentText()
        row = self.player_grid.rowCount()
        if not name:
            QMessageBox.warning(self, "エラー", "プレイヤー名を入力してください。")
            return
        player = PlayerData()
        player.name = name
        player.rank = rank
        player.tag = 'JP1'
        self.add_player_gui(player, row)

    def delete_player(self):
        selected_items = self.player_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "エラー", "プレイヤーを選択してください。")
            return

        for item in selected_items:
            self.player_list.takeItem(self.player_list.row(item))

    def copy_to_clipboard(self):
        team1_text = "チーム1----\n"
        for player in self.team1_player:
            team1_text += f'{player.role}: {player.name}\n'

        team2_text = "チーム2----\n"
        for player in self.team2_player:
            team2_text += f'{player.role}: {player.name}\n'

        # クリップボードにコピー
        QApplication.clipboard().setText(team1_text + "\n" + team2_text)

    def copy_to_clipboard_opgg(self):
        name1_list = []
        team1_text = "チーム1----\n"
        for player in self.team1_player:
            team1_text += f'{player.role}: {player.name}\n'
            name = player.name.replace(' ', '+')
            tag = player.tag
            name1_list.append(f'{name}%23{tag}')
        name1 = '%2C'.join(name1_list)
        team1_text += f'https://www.op.gg/multisearch/jp?summoners={name1}'

        name2_list = []
        team2_text = "チーム2----\n"
        for player in self.team2_player:
            team2_text += f'{player.role}: {player.name}\n'
            name = player.name.replace(' ', '+')
            tag = player.tag
            name2_list.append(f'{name}%23{tag}')
        name2 = '%2C'.join(name2_list)
        team2_text += f'https://www.op.gg/multisearch/jp?summoners={name2}'

        # クリップボードにコピー
        QApplication.clipboard().setText(team1_text + "\n" + team2_text)

    def divide_teams(self):
        attend_players = []
        for player in self.player_list:
            player.rank = player.rank_combobox.currentText()
            if player.attend_check.isChecked():
                attend_players.append(player)

        if len(attend_players) != 10:
            QMessageBox.warning(self, "エラー", "チーム分けには10人のプレイヤーが必要です。")
            return

        # チーム分けを実行
        tolerance = self.tolerance_spinbox.value()
        team1, team2 = self.perform_team_division(attend_players, tolerance)

        if team1 is not None or team2 is not None:
            # 結果をリストに表示
            self.team1_list.clear()
            self.team2_list.clear()
            self.team1_player = []
            self.team2_player = []
            for player, role in zip(team1, ROLES):
                item = QListWidgetItem(f"{role}: {player.name} ({player.rank})")
                self.team1_list.addItem(item)
                self.team1_player.append(player)
            for player, role in zip(team2, ROLES):
                item = QListWidgetItem(f"{role}: {player.name} ({player.rank})")
                self.team2_list.addItem(item)
                self.team2_player.append(player)

            # 差分を計算
            self.show_diff(team1, team2)

    def perform_team_division(self, players, tolerance):
        # プレイヤーのロール情報を辞書にまとめる
        roles = {'top': [], 'jg': [], 'mid': [], 'bot': [], 'sup': []}
        for player in players:
            player.rank_val = RANK_VAL[player.rank]  # ランク値を追加
            for role in roles:
                if getattr(player, role).isChecked():
                    roles[role].append(player)

        # 各ロールのプレイヤー数を表示 (デバッグ用)
        for role, player_list in roles.items():
            if len(player_list) < 2:
                QMessageBox.warning(self, "エラー", f"{role}のプレイヤー数は2人以上である必要があります")
                return None, None

        valid_teams = self.create_teams(players)

        if len(valid_teams) > 0:
            for team1, team2 in valid_teams:
                # ランク差が許容範囲内になるまでチームメンバーを調整
                team1_total_rank = sum(player.rank_val for player in team1)
                team2_total_rank = sum(player.rank_val for player in team2)
                diff = abs(team1_total_rank - team2_total_rank)
                if diff <= tolerance:
                    assignments = self.assign_roles(team1)
                    team1 = random.choice(assignments)
                    for player, role in zip(team1, ROLES):
                        player.role = role
                    assignments = self.assign_roles(team2)
                    team2 = random.choice(assignments)
                    for player, role in zip(team2, ROLES):
                        player.role = role
                    return team1, team2

        return None, None

    def create_teams(self, players):
        """
        複数のロールを選択しているプレイヤーを2つのチームに分割する関数

        Args:
        players: 各プレイヤーが選択したロールを表すオブジェクトのリスト。
        各プレイヤーオブジェクトは、選択したロールの属性がTrueになります。
        Returns:
        2つのチームの可能な組み合わせのリスト。各チームは、各ロールのプレイヤーが1人ずつ含まれています。
        """
        n = len(players) // 2
        all_combinations = combinations(players, n)
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

    def assign_roles(self, team):
        combinations = []
        role_assignments = [[player for player in team if getattr(player, role).isChecked()] for role in ROLES]
        for combination in product(*role_assignments):
            # 重複がない組み合わせのみ追加
            if len(set(combination)) == len(combination):
                combinations.append(combination)

        return combinations

    def rank_to_value(self, rank):
        return RANK_VAL[rank]

    def change_player(self):
        selected_items = self.player_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "エラー", "プレイヤーを選択してください。")
            return

        item = selected_items[0]
        current_data = item.data(Qt.ItemDataRole.UserRole)

        # 変更内容を入力するためのダイアログを表示
        if current_data.rank == '':
            new_rank, ok_pressed = QInputDialog.getItem(self, "ランク変更", "新しいランク:", RANKS, RANKS.index('SILVER IV'), False)
        else:
            new_rank, ok_pressed = QInputDialog.getItem(self, "ランク変更", "新しいランク:", RANKS, RANKS.index(current_data.rank), False)
        if not ok_pressed:
            return

        # プレイヤー情報を更新
        item.setText(f"{current_data.rank} ({new_rank})")
        item.setData(Qt.ItemDataRole.UserRole, {"name": current_data.name, "rank": new_rank, "tag": current_data.tag})

    def load_dict_from_file(self):
        """ファイルからプレイヤー情報を読み込む"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "プレイヤー情報ファイルを開く", "", "JSONファイル (*.json)")
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.player_list = []

                    for row in range(self.player_grid.rowCount()):
                        name_widget = self.player_grid.itemAtPosition(row, 1).widget()
                        player_name = name_widget.text()
                        rank_widget = self.player_grid.itemAtPosition(row, 2).widget()

                        if player_name in data:
                            player_data = data[player_name]
                            rank_widget.setCurrentText(player_data['rank'])
                            for col, role in enumerate(ROLES, start=3):
                                checkbox = self.player_grid.itemAtPosition(row, col).widget()
                                checkbox.setChecked(player_data['role'].get(role, False))
        except FileNotFoundError:
            QMessageBox.warning(self, "エラー", "ファイルが見つかりません。")

    def save_dict_to_file(self):
        """プレイヤー情報をファイルに保存する"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "プレイヤー情報ファイルを保存", "player_dictionary.json", "JSONファイル (*.json)")
            d = {player.name: {'tag': player.tag, 'rank': player.rank, 'role': {role: getattr(player, role).isChecked() for role in ROLES}} for player in self.player_list}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(d, f, indent=4, ensure_ascii=False)
        except FileNotFoundError:
            QMessageBox.warning(self, "エラー", "ファイルが見つかりません。")

    def output_result(self):
        d = self.game_data.to_dict()
        self.uploader.upload_match_data(d)

    def on_connected(self, flag):
        """データベース接続完了時に呼び出されるスロット"""
        print('データベース接続が完了しました')

    def on_uploaded(self, flag):
        msg_box = QMessageBox()  # QMessageBoxのインスタンスを作成
        if flag:
            msg_box.setText('アップロード完了しました')
        else:
            msg_box.setText('アップロード失敗しました')
        msg_box.exec()
        return
