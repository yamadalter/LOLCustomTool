from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QListWidget,
    QMessageBox,
    QGroupBox,
    QSpinBox,
    QInputDialog,
    QGridLayout,
    QCheckBox,
    QMenu
)
from PyQt6.QtCore import Qt, QPoint
from common import VERSION, RANKS, RANKS_TAG, ROLES, RANK_COLORS
from datahandler import LoLDataHandler
from lcu_worker import WorkerThread
from register import MatchDataUploader
from team_balancer import divide_teams
import actions
import callbacks


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # initial
        self.history = {}
        self.handler = LoLDataHandler()
        self.uploader = MatchDataUploader()
        self.uploader.connected.connect(callbacks.on_connected)  # 接続完了シグナルにスロットを接続
        self.uploader.upload_finished.connect(callbacks.on_uploaded)  # 接続完了シグナルにスロットを接続
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
        self.add_player_button.clicked.connect(lambda: callbacks.add_player(self))
        input_layout.addWidget(self.add_player_button)
        teamsplit_layout.addLayout(input_layout)

        # プレイヤー辞書エリア
        dict_layout = QHBoxLayout()
        dict_layout.addWidget(QLabel("Player info:"))
        self.save_dict_button = QPushButton("SAVE")
        self.save_dict_button.clicked.connect(lambda: actions.save_dict_to_file(self))
        dict_layout.addWidget(self.save_dict_button)
        self.load_dict_button = QPushButton("LOAD")
        self.load_dict_button.clicked.connect(lambda: actions.load_dict_from_file(self))
        dict_layout.addWidget(self.load_dict_button)
        dict_layout.addSpacing(300)
        teamsplit_layout.addLayout(dict_layout)

        # プレイヤー情報表示エリア
        player_group = QGroupBox("プレイヤー")
        player_group.setMinimumSize(100, 50)
        player_group.setAlignment(Qt.AlignmentFlag.AlignTop)
        player_group.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # Apply to parent
        player_group.customContextMenuRequested.connect(self.show_context_menu)  # Connect to parent
        
        # 新しい QVBoxLayout を作成し、グリッドとストレッチを追加
        player_group_layout = QVBoxLayout()
        self.player_grid = QGridLayout()
        self.player_grid_init()
        player_group_layout.addLayout(self.player_grid)
        player_group_layout.addStretch(1)  # このストレッチがグリッドを上に押し上げる

        self.player_list = []
        player_group.setLayout(player_group_layout)  # 新しいレイアウトをセット
        
        teamsplit_layout.addWidget(player_group, 4)

        # チーム分け結果表示エリア
        team_group = QGroupBox("チーム分け結果")
        team_layout = QHBoxLayout()
        team1_layout = QVBoxLayout()
        team2_layout = QVBoxLayout()
        self.team1_list = QListWidget()
        self.team2_list = QListWidget()
        self.team1_player = []
        self.team2_player = []
        self.team1_score = QLabel()
        self.team2_score = QLabel()
        team1_layout.addWidget(self.team1_score)
        team2_layout.addWidget(self.team2_score)
        team1_layout.addWidget(self.team1_list)
        team2_layout.addWidget(self.team2_list)
        team_layout.addLayout(team1_layout)
        team_layout.addLayout(team2_layout)
        team_group.setLayout(team_layout)
        teamsplit_layout.addWidget(team_group, 2)

        # チームのランク差を表示するラベル
        self.diff_label = QLabel()
        teamsplit_layout.addWidget(self.diff_label)

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
        self.add_from_lobby_button.clicked.connect(lambda: callbacks.lobby_worker(self))
        self.lobby_worker_thread = WorkerThread()
        self.lobby_worker_thread.data_updated.connect(lambda players: callbacks.add_players_to_list(self, players))  # シグナルにスロットを接続
        input_layout.addWidget(self.add_from_lobby_button)

        # チーム分け実行ボタン
        button_layout = QHBoxLayout()  # ボタンを横並びにするためのレイアウト
        self.divide_button = QPushButton("チーム分け")
        self.divide_button.clicked.connect(lambda: divide_teams(self))
        button_layout.addWidget(self.divide_button)

        # クリップボードにコピーするボタン
        self.copy_button = QPushButton("結果コピー")
        self.copy_button.clicked.connect(lambda: actions.copy_to_clipboard(self))
        button_layout.addWidget(self.copy_button)
        self.copy_button_opgg = QPushButton("結果コピー(opgg)")
        self.copy_button_opgg.clicked.connect(lambda: actions.copy_to_clipboard_opgg(self))
        button_layout.addWidget(self.copy_button_opgg)
        self.webhook_button = QPushButton("結果出力(Discord)")
        self.webhook_button.clicked.connect(lambda: actions.webhook_button_clicked(self))
        button_layout.addWidget(self.webhook_button)
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
        self.get_game_results_button.clicked.connect(lambda: callbacks.get_game_history(self))
        result_button_layout.addWidget(self.get_game_results_button)

        # 試合履歴取得用のワーカースレッド
        self.history_worker_thread = WorkerThread()
        self.history_worker_thread.history_updated.connect(lambda history: callbacks.display_game_history(self, history))

        # ゲームID選択用のコンボボックス
        self.game_id_combobox = QComboBox()
        self.game_id_combobox.currentIndexChanged.connect(lambda index: callbacks.game_id_selected(self, index))  # コンボボックスの選択変更時の処理
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
        game_results_group.setMinimumSize(500, 800)

        # 試合結果取得ボタンと試合結果表示エリアをまとめる
        game_results_outer_layout.addWidget(game_results_group)

        # メインレイアウトに試合結果関連のレイアウトを追加
        gameresult_layout.addLayout(game_results_outer_layout)

        main_layout.addLayout(teamsplit_layout)
        main_layout.addLayout(gameresult_layout)

        self.setLayout(main_layout)

        # 試合履歴取得用のワーカースレッド
        self.history_worker_thread = WorkerThread()
        self.history_worker_thread.history_updated.connect(lambda history: callbacks.display_game_history(self, history))

    def player_grid_init(self):
        labels = ["NAME"] + [role.upper() for role in ROLES]
        for col, label_text in enumerate(labels):
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
        if 0 < row <= len(self.player_list):
            player = self.player_list[row - 1]  # Adjust for header row
            for role in ROLES:
                checkbox = getattr(player, role)
                checkbox.setChecked(True)

    def update_rank_color(self, combo_box: QComboBox):
        """コンボボックスの色をランクに応じて変更する"""
        try:
            rank_tag = combo_box.currentText()
            index = RANKS_TAG.index(rank_tag)
            rank_name = RANKS[index]
            tier = rank_name.split(" ")[0]
            color = RANK_COLORS.get(tier, "#FFFFFF")
            combo_box.setStyleSheet(f"background-color: {color}; color: #000000;")
        except (ValueError, IndexError):
            combo_box.setStyleSheet("background-color: #FFFFFF; color: #000000;") # Default color

    def add_player_gui(self, player, row):
        # 以前の alignment 指定は不要
        self.player_grid.addWidget(QLabel(f"{player.name}"), row, 0)

        for col_offset, role in enumerate(ROLES, 1):
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.setContentsMargins(2, 2, 2, 2)

            checkbox = QCheckBox('')
            setattr(player, role, checkbox)
            cell_layout.addWidget(checkbox)

            rank_combobox = QComboBox()
            rank_combobox.addItems(RANKS_TAG)
            if hasattr(player, "rank"):
                role_rank = getattr(player, "rank")
                if role_rank == '' or role_rank not in RANKS:
                    role_rank = 'UNRANKED'
                rank_combobox.setCurrentText(RANKS_TAG[RANKS.index(role_rank)])
            else:
                rank_combobox.setCurrentText("UN")
            setattr(player, f"{role}_rank_combobox", rank_combobox)
            
            # 色の更新とシグナル接続
            self.update_rank_color(rank_combobox)
            rank_combobox.currentTextChanged.connect(lambda text, cb=rank_combobox: self.update_rank_color(cb))
            
            cell_layout.addWidget(rank_combobox)
            # 以前の alignment 指定は不要
            self.player_grid.addWidget(cell_widget, row, col_offset)

        self.player_list.append(player)

    def change_player(self):
        selected_items = self.player_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "エラー", "プレイヤーを選択してください。")
            return

        item = selected_items[0]
        current_data = item.data(Qt.ItemDataRole.UserRole)

        if current_data.rank == '':
            new_rank, ok_pressed = QInputDialog.getItem(self, "ランク変更", "新しいランク:", RANKS, RANKS.index('SILVER IV'), False)
        else:
            new_rank, ok_pressed = QInputDialog.getItem(self, "ランク変更", "新しいランク:", RANKS, RANKS.index(current_data.rank), False)
        if not ok_pressed:
            return

        item.setText(f"{current_data.rank} ({new_rank})")
        item.setData(Qt.ItemDataRole.UserRole, {"name": current_data.name, "rank": new_rank, "tag": current_data.tag})

    def output_result(self):
        d = self.game_data.to_dict()
        self.uploader.upload_match_data(d)