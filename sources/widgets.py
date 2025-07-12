from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QPixmap, QDrag
from common import POSITION


class PlayerRowWidget(QWidget):
    def __init__(self, player, handler, main_window):
        super().__init__()
        self.player = player
        self.handler = handler
        self.main_window = main_window
        self.setAcceptDrops(True)
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setColumnStretch(0, 3)
        self.display_player()

    def display_player(self):
        # サモナー名を表示
        summoner_name_label = QLabel(self.player.player['gameName'])
        self.layout.addWidget(summoner_name_label, 0, 0, 1, 10)

        # KDAを表示
        self.kda_label = QLabel(f"{self.player.stats['kills']}/{self.player.stats['deaths']}/{self.player.stats['assists']}")
        self.layout.addWidget(self.kda_label, 0, 1)

        # ルーン画像を表示
        rune_label1 = QLabel()
        rune_images = self.handler.get_rune_image(self.player)
        rune_image1 = QPixmap(rune_images[0])
        rune_label1.setPixmap(rune_image1)
        self.layout.addWidget(rune_label1, 0, 2)
        rune_label2 = QLabel()
        rune_image2 = QPixmap(rune_images[1])
        rune_label2.setPixmap(rune_image2)
        self.layout.addWidget(rune_label2, 0, 3)

        # チャンピオン画像を表示
        champion_label = QLabel()
        champ_image = self.handler.get_champ_image(self.player.championName)
        champ_image = champ_image.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio)
        champion_label.setPixmap(champ_image)
        self.layout.addWidget(champion_label, 0, 4)

        # アイテム画像を表示
        item_images = self.handler.get_item_images(self.player)
        for i, item_image in enumerate(item_images):
            item_label = QLabel()
            item_label.setPixmap(item_image)
            self.layout.addWidget(item_label, 0, 5 + i)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(self.player.player['puuid'])
            drag.setMimeData(mime_data)
            drag.setPixmap(self.grab())
            drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        source_puuid = event.mimeData().text()
        source_widget = self.main_window.findChild(PlayerRowWidget, source_puuid)

        if source_widget and source_widget != self and self.player.side == source_widget.player.side:
            # プレイヤーが所属するチームを特定
            team = None
            for t in self.main_window.game_data.teams:
                puuids = [p.player['puuid'] for p in t.participants]
                if self.player.player['puuid'] in puuids and source_puuid in puuids:
                    team = t
                    break

            if team:
                layout = self.parentWidget().layout()
                source_index = layout.indexOf(source_widget)
                target_index = layout.indexOf(self)

                # レイアウト内でウィジェットを入れ替え
                layout.insertWidget(target_index, layout.takeAt(source_index).widget())

                # UIの順序に基づいて新しいロールの辞書を作成
                new_positions = {}
                for i in range(layout.count()):
                    widget = layout.itemAt(i).widget()
                    if isinstance(widget, PlayerRowWidget):
                        # ウィジェットのレイアウト上の位置に基づいて新しいロールを割り当てる
                        new_positions[POSITION[i]] = widget.player.championId

                # datahandlerのset_positionsを呼び出して、データ内のロールを更新
                self.handler.set_positions(team, new_positions)
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()