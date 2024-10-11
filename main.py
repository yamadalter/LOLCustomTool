import sys
import random
import asyncio
from PyQt5.QtWidgets import (
    QApplication,
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
)
from PyQt5.QtCore import Qt
from common import RANK_VAL, RANKS  # common.py から変数をインポート
from lcu_driver import Connector
import qasync


async def get_lobby_players(connection):
    # ロビー情報を取得
    lobby = await connection.request('get', '/lol-lobby/v2/lobby')
    lobby_data = await lobby.json()

    # プレイヤー情報を読み取る
    players = []
    for member in lobby_data['members']:
        summoner_name = member['summonerName']
        # 必要に応じて、ランクなどの他の情報も取得
        players.append({'name': summoner_name, 'rank': 'ランク情報'})  # ランク情報は適切な方法で取得
    return players


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("LoLチーム分け")

        # LCU APIとの接続を確立
        self.connector = Connector()

        # GUIのレイアウトを構築
        main_layout = QVBoxLayout()

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
        main_layout.addLayout(input_layout)

        # プレイヤー情報表示エリア
        player_group = QGroupBox("プレイヤー")
        player_layout = QVBoxLayout()
        self.player_list = QListWidget()
        self.player_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        player_layout.addWidget(self.player_list)
        player_group.setLayout(player_layout)
        main_layout.addWidget(player_group)

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
        main_layout.addWidget(team_group)

        # 許容ランク誤差入力エリア
        tolerance_layout = QHBoxLayout()
        tolerance_layout.addWidget(QLabel("許容ランク誤差:"))
        self.tolerance_spinbox = QSpinBox()
        self.tolerance_spinbox.setRange(0, 100)  # 許容範囲を設定
        self.tolerance_spinbox.setValue(
            10
        )  # デフォルト値を設定 (必要に応じて変更)
        tolerance_layout.addWidget(self.tolerance_spinbox)
        main_layout.addLayout(tolerance_layout)

        # ロビーからプレイヤーを追加するボタン
        self.add_from_lobby_button = QPushButton("ロビーから追加")
        self.add_from_lobby_button.clicked.connect(self.add_players_from_lobby)  # ensure_open は削除
        input_layout.addWidget(self.add_from_lobby_button)

        # チーム分け実行ボタン
        self.divide_button = QPushButton("チーム分け")
        self.divide_button.clicked.connect(self.divide_teams)
        main_layout.addWidget(self.divide_button)

        self.setLayout(main_layout)

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

        # ランク順にソート
        players.sort(key=lambda x: x["rank_value"], reverse=True)

        # チーム分け
        team1 = []
        team2 = []
        team1_total_rank = 0
        team2_total_rank = 0

        while players:
            player = random.choice(players)
            if team1_total_rank <= team2_total_rank:
                team1.append(player)
                team1_total_rank += player["rank_value"]
            else:
                team2.append(player)
                team2_total_rank += player["rank_value"]
            players.remove(player)

        # ランク差が許容範囲内になるまでチーム分けを繰り返す
        while abs(team1_total_rank - team2_total_rank) > tolerance:
            team1 = []
            team2 = []
            team1_total_rank = 0
            team2_total_rank = 0
            random.shuffle(players)  # プレイヤーの順番をシャッフル

            for player in players:
                if team1_total_rank <= team2_total_rank:
                    team1.append(player)
                    team1_total_rank += player["rank_value"]
                else:
                    team2.append(player)
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

    async def add_players_from_lobby(self):
        await self.connector.ws.ensure_open()
        players = await get_lobby_players(self.connector)
        for player in players:
            item = QListWidgetItem(f"{player['name']} ({player['rank']})")
            item.setData(Qt.UserRole, player)
            self.player_list.addItem(item)

    async def close_connector(self):
        await self.connector.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    # アプリケーション終了時に connector を close
    try:
        sys.exit(loop.run_forever())
    finally:
        loop.run_until_complete(window.close_connector())
        loop.close()