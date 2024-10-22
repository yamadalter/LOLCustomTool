import random
import cassiopeia as cass
import requests
import datetime
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
    QAbstractItemView,
    QGroupBox,
    QSpinBox,
    QInputDialog,
    QTextEdit,
    QApplication,
    QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from common import RANK_VAL, RANKS
from lcu_worker import WorkerThread  # lcu_worker.py から WorkerThread をインポート
from roleidentification import pull_data
from cassiopeia.core.match import MatchData
from roleidentification.get_roles import get_roles
from io import BytesIO
from PIL import Image
from PIL.ImageQt import ImageQt


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.history = {}
        self.ver = ''
        self.ver = self.get_ver()
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
        self.player_list.players = []
        self.player_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
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
        self.tolerance_spinbox.setValue(10)  # デフォルト値を設定 (必要に応じて変更)
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
        teamsplit_layout.addLayout(button_layout)  # ボタンレイアウトを追加

        # 試合結果取得ボタン
        self.get_game_results_button = QPushButton("試合結果取得")
        self.get_game_results_button.clicked.connect(self.get_game_history)

        # 試合履歴取得用のワーカースレッド
        self.history_worker_thread = WorkerThread()
        self.history_worker_thread.history_updated.connect(self.display_game_history)

        # ゲームID選択用のコンボボックス
        self.game_id_combobox = QComboBox()
        self.game_id_combobox.currentIndexChanged.connect(self.game_id_selected)  # コンボボックスの選択変更時の処理

        # 取得結果表示
        game_results_outer_layout = QVBoxLayout()
        game_results_outer_layout.addWidget(self.get_game_results_button)
        game_results_outer_layout.addWidget(self.game_id_combobox)  # コンボボックスを追加

        # 試合結果表示エリア
        game_results_group = QGroupBox("試合結果")
        self.result_context_layout = QVBoxLayout()
        self.game_result_grid = QGridLayout()
        self.result_context_layout.addLayout(self.game_result_grid)
        game_results_group.setLayout(self.result_context_layout)
        game_results_group.setMinimumSize(500, 500)

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
            data = self.get_game_data(self.history[int(selected_game_id)])
            td = datetime.timedelta(seconds=data.gameDuration)
            self.title_label = QLabel(f"Summoner's Rift ({td})")
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.game_result_grid.addWidget(self.title_label, 0, 0, 1, 11)
            # 勝者と敗者を分けて表示
            for team in data.teams:
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

        # 各プレイヤーの情報を表示
        i = 0
        for position in ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']:
            for player in team.participants:
                if player.position == position:
                    row_offset = row + i + 1
                    self.display_player(grid, row_offset, player)
                    i += 1

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
        rune_images = self.get_rune_image(palyer)
        rune_image1 = QPixmap(rune_images[0])  # 画像パスを指定
        rune_label1.setPixmap(rune_image1)
        grid.addWidget(rune_label1, row, 2)
        rune_label2 = QLabel()
        rune_image2 = QPixmap(rune_images[1])  # 画像パスを指定
        rune_label2.setPixmap(rune_image2)
        grid.addWidget(rune_label2, row, 3)

        # チャンピオン画像を表示
        champion_label = QLabel()
        champ_image = self.get_champ_image(palyer.championName)
        champion_image = QPixmap(champ_image)  # 画像パスを指定
        champion_label.setPixmap(champion_image)
        grid.addWidget(champion_label, row, 4)

        # アイテム画像を表示
        item_images = self.get_item_images(palyer)
        for j, item_image in enumerate(item_images):
            item_label = QLabel()
            item_image = QPixmap(item_image)  # 画像パスを指定
            item_label.setPixmap(item_image)
            grid.addWidget(item_label, row, 5 + j)  # 4列目から開始

    def add_players_to_list(self, players):
        if players:
            for player in players:
                if player not in self.player_list.players:
                    item = QListWidgetItem(f"{player['name']} ({player['rank']})")
                    item.setData(Qt.ItemDataRole.UserRole, player)
                    self.player_list.addItem(item)
                    self.player_list.players.append(player)

    def add_player(self):
        name = self.player_name_input.text()
        rank = self.rank_combobox.currentText()
        if not name:
            QMessageBox.warning(self, "エラー", "プレイヤー名を入力してください。")
            return
        item = QListWidgetItem(f"{name} ({rank})")
        item.setData(Qt.ItemDataRole.UserRole, {"name": name, "rank": rank})
        self.player_list.addItem(item)

    def divide_teams(self):
        players = []
        for i in range(self.player_list.count()):
            item = self.player_list.item(i)
            if item.isSelected():
                players.append(item.data(Qt.ItemDataRole.UserRole))

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
        current_data = item.data(Qt.ItemDataRole.UserRole)

        # 変更内容を入力するためのダイアログを表示
        new_name, ok_pressed = QInputDialog.getText(self, "プレイヤー名変更", "新しいプレイヤー名:", QLineEdit.EchoMode.Normal, current_data["name"])
        if not ok_pressed:
            return
        if current_data["rank"] == '':
            new_rank, ok_pressed = QInputDialog.getItem(self, "ランク変更", "新しいランク:", RANKS, RANKS.index('SILVER IV'), False)
        else:
            new_rank, ok_pressed = QInputDialog.getItem(self, "ランク変更", "新しいランク:", RANKS, RANKS.index(current_data["rank"]), False)
        if not ok_pressed:
            return

        # プレイヤー情報を更新
        item.setText(f"{new_name} ({new_rank})")
        item.setData(Qt.ItemDataRole.UserRole, {"name": new_name, "rank": new_rank})

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
            team1_text += self.team1_list.item(i).text().split(' (')[0] + "\n"

        team2_text = "チーム2----\n"
        for i in range(self.team2_list.count()):
            team2_text += self.team2_list.item(i).text().split(' (')[0] + "\n"

        # クリップボードにコピー
        QApplication.clipboard().setText(team1_text + "\n" + team2_text)

    def set_positions(self, team, positions):
        for participant in team.participants:
            for k, v in positions.items():
                if participant.championId == v:
                    participant.position = k

    def get_ver(self):
        if self.ver == '':
            ver_res = requests.get('https://ddragon.leagueoflegends.com/api/versions.json')
            ver_data = ver_res.json()
            return ver_data[0]
        else:
            return self.ver

    def set_champion_name(self, participants):
        ver = self.get_ver()
        print(f'https://ddragon.leagueoflegends.com/cdn/{ver}/data/ja_JP/champion.json')
        champ_res = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{ver}/data/ja_JP/champion.json')
        champ_data = champ_res.json()
        for participant in participants:
            for champion_name, champion_data in champ_data['data'].items():
                if int(champion_data['key']) == participant.championId:
                    participant.championName = champion_name

    def get_game_data(self, data):
        champion_roles = pull_data()
        data["region"] = 'JP'
        matchdata = MatchData()
        matchdata = matchdata(**data)
        for team in matchdata.teams:
            champions = [participant.championId for participant in team.participants]
            smite = None
            for participant in team.participants:
                if participant.spell1Id == 11 or participant.spell2Id == 11:
                    if smite is None:
                        smite = participant.championId
                    else:
                        smite = None
                for identity in matchdata.participantIdentities:
                    if participant.participantId == identity['participantId']:
                        participant.player = identity['player']
            if smite is None:
                positions = get_roles(champion_roles, champions)
            else:
                positions = get_roles(champion_roles, champions, jungle=smite)
            self.set_positions(team, positions)
        
        self.set_champion_name(matchdata.participants)

        return matchdata
        
    def get_rune_image(self, palyer):
        ver = self.get_ver()
        rune_res = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{ver}/data/ja_JP/runesReforged.json')
        rune_data = rune_res.json()
        rune_paths = ['', '']
        for rune in rune_data:
            if int(rune['id']) == palyer.stats['perkPrimaryStyle']:
                for keystne in rune['slots'][0]['runes']:
                    if int(keystne['id']) == palyer.stats['perk0']:
                        rune_paths[0] = keystne['icon']
            if int(rune['id']) == palyer.stats['perkSubStyle']:
                rune_paths[1] = rune['icon']
        rune_images = []
        for i, path in enumerate(rune_paths):
            rune_res = requests.get(f'https://ddragon.leagueoflegends.com/cdn/img/{path}')
            img = Image.open(BytesIO(rune_res.content))
            img = ImageQt(img)
            pixmap = QPixmap.fromImage(img)
            if i == 0:
                pixmap = pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio)
            else:
                pixmap = pixmap.scaled(15, 15, Qt.AspectRatioMode.KeepAspectRatio)
            rune_images.append(pixmap)
        return rune_images

    def get_champ_image(self, champ):
        ver = self.get_ver()
        response = requests.get(f'http://ddragon.leagueoflegends.com/cdn/{ver}/img/champion/{champ}.png')
        img = Image.open(BytesIO(response.content))
        img = ImageQt(img)
        pixmap = QPixmap.fromImage(img)
        pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)
        return pixmap

    def get_item_images(self, player):
        ver = self.get_ver()
        items = [player.stats[f'item{i}'] for i in range(6)]
        items_images = []
        for item in items:
            if not item == 0:
                response = requests.get(f'http://ddragon.leagueoflegends.com/cdn/{ver}/img/item/{item}.png')
                img = Image.open(BytesIO(response.content))
                img = ImageQt(img)
                pixmap = QPixmap.fromImage(img)
                pixmap = pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio)
                items_images.append(pixmap)
            else:
                pixmap = QPixmap('0.png')
                pixmap = pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio)
                items_images.append(pixmap)
        return items_images
