import random
from PyQt5.QtWidgets import (
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
    QAbstractItemView,
    QGroupBox,
    QSpinBox,
    QInputDialog,
    QTextEdit,
    QApplication,
)
from PyQt5.QtCore import Qt
from common import RANK_VAL, RANKS
from lcu_worker import WorkerThread  # lcu_worker.py から WorkerThread をインポート


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

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

        # プレイヤー情報表示エリア
        player_group = QGroupBox("プレイヤー")
        player_layout = QVBoxLayout()
        self.player_list = QListWidget()
        self.player_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        player_layout.addWidget(self.player_list)
        player_group.setLayout(player_layout)
        teamsplit_layout.addWidget(player_group)

        # プレイヤー情報変更・削除ボタン
        self.change_player_button = QPushButton("変更")
        self.change_player_button.clicked.connect(self.change_player)
        input_layout.addWidget(self.change_player_button)

        self.delete_player_button = QPushButton("削除")
        self.delete_player_button.clicked.connect(self.delete_player)
        input_layout.addWidget(self.delete_player_button)

        # チーム分け結果表示エリア
        team_group = QGroupBox("チーム分け結果")
        team_layout = QVBoxLayout()
        self.team1_list = QListWidget()
        self.team2_list = QListWidget()
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
        self.tolerance_spinbox.setValue(
            10
        )  # デフォルト値を設定 (必要に応じて変更)
        tolerance_layout.addWidget(self.tolerance_spinbox)
        teamsplit_layout.addLayout(tolerance_layout)

        # ロビーからプレイヤーを追加するボタン
        self.add_from_lobby_button = QPushButton("ロビーから追加")
        self.add_from_lobby_button.clicked.connect(self.start_worker)
        self.worker_thread = WorkerThread()
        self.worker_thread.data_updated.connect(self.add_players_to_list)  # シグナルにスロットを接続
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

        teamsplit_layout.addLayout(button_layout)  # ボタンレイアウトを追加

        # 試合結果取得ボタン
        self.get_game_results_button = QPushButton("試合結果取得")
        self.get_game_results_button.clicked.connect(self.get_game_results)

        # 試合結果表示エリア
        self.game_results_label = QLabel("試合結果")
        self.game_results_text = QTextEdit()
        self.game_results_text.setReadOnly(True)
        game_results_layout = QVBoxLayout()
        game_results_layout.addWidget(self.game_results_label)
        game_results_layout.addWidget(self.game_results_text)

        # 試合結果取得ボタンと試合結果表示エリアをまとめる
        game_results_outer_layout = QVBoxLayout()
        game_results_outer_layout.addWidget(self.get_game_results_button)
        game_results_outer_layout.addLayout(game_results_layout)

        # メインレイアウトに試合結果関連のレイアウトを追加
        gameresult_layout.addLayout(game_results_outer_layout)

        main_layout.addLayout(teamsplit_layout)
        main_layout.addLayout(gameresult_layout)

        self.setLayout(main_layout)

    def start_worker(self):
        self.worker_thread.start()

    def get_game_results(delf):
        print('a')

    def add_players_to_list(self, players):
        if players:
            for player in players:
                item = QListWidgetItem(f"{player['name']} ({player['rank']})")
                item.setData(Qt.UserRole, player)
                self.player_list.addItem(item)

    def add_player(self):
        name = self.player_name_input.text()
        rank = self.rank_combobox.currentText()

        if not name:
            QMessageBox.warning(self, "エラー", "プレイヤー名を入力してください。")
            return

        item = QListWidgetItem(f"{name} ({rank})")
        item.setData(Qt.UserRole, {"name": name, "rank": rank})
        self.player_list.addItem(item)

    def divide_teams(self):
        players = []
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            if item.isSelected():
                players.append(item.data(Qt.UserRole))

        if len(players) < 2:
            QMessageBox.warning(self, "エラー", "チーム分けには2人以上のプレイヤーが必要です。")
            return

        if len(players) % 2 != 0:
            QMessageBox.warning(self, "エラー", "チーム分けには偶数人数のプレイヤーが必要です。")
            return

        # チーム分けを実行
        tolerance = self.tolerance_spinbox.value()
        team1, team2 = self.perform_team_division(players, tolerance)

        # 結果をリストに表示
        self.team1_list.clear()
        self.team2_list.clear()
        for player in team1:
            item = QListWidgetItem(f"{player['name']} ({player['rank']})")
            self.team1_list.addItem(item)
        for player in team2:
            item = QListWidgetItem(f"{player['name']} ({player['rank']})")
            self.team2_list.addItem(item)

        # 差分を計算
        self.show_diff(team1, team2)

    def perform_team_division(self, players, tolerance):
        for player in players:
            player["rank_value"] = RANK_VAL[player["rank"]]

        # ランク差が許容範囲内になるまでチーム分けを繰り返す
        team1_total_rank = 9999
        team2_total_rank = 0
        while abs(team1_total_rank - team2_total_rank) > tolerance:
            random.shuffle(players)
            n = len(players) // 2
            
            team1 = players[:n]
            team2 = players[n:]
            team1_total_rank = 0
            team2_total_rank = 0
            for player in team1:
                team1_total_rank += player["rank_value"]

            for player in team2:
                team2_total_rank += player["rank_value"]

        return team1, team2

    def show_diff(self, team1, team2):
        team1_rank = sum(self.rank_to_value(player["rank"]) for player in team1)
        team2_rank = sum(self.rank_to_value(player["rank"]) for player in team2)
        diff = abs(team1_rank - team2_rank)
        # ラベルにランク差を表示
        self.diff_label.setText(f"チームのランク差: {diff}")

    def rank_to_value(self, rank):
        return RANK_VAL[rank]

    def change_player(self):
        selected_items = self.player_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "エラー", "プレイヤーを選択してください。")
            return

        item = selected_items[0]
        current_data = item.data(Qt.UserRole)

        # 変更内容を入力するためのダイアログを表示
        new_name, ok_pressed = QInputDialog.getText(self, "プレイヤー名変更", "新しいプレイヤー名:", QLineEdit.Normal, current_data["name"])
        if not ok_pressed:
            return

        new_rank, ok_pressed = QInputDialog.getItem(self, "ランク変更", "新しいランク:", RANKS, RANKS.index(current_data["rank"]), False)
        if not ok_pressed:
            return

        # プレイヤー情報を更新
        item.setText(f"{new_name} ({new_rank})")
        item.setData(Qt.UserRole, {"name": new_name, "rank": new_rank})

    def delete_player(self):
        selected_items = self.player_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "エラー", "プレイヤーを選択してください。")
            return

        for item in selected_items:
            self.player_list.takeItem(self.player_list.row(item))

    def copy_to_clipboard(self):
        team1_text = "チーム1----\n"
        for i in range(self.team1_list.count()):
            team1_text += self.team1_list.item(i).text() + "\n"

        team2_text = "チーム2----\n"
        for i in range(self.team2_list.count()):
            team2_text += self.team2_list.item(i).text() + "\n"

        # クリップボードにコピー
        QApplication.clipboard().setText(team1_text + "\n" + team2_text)
