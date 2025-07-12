import json
import requests
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication
from common import WEBHOOK, ROLES


def save_dict_to_file(main_window):
    """プレイヤー情報をファイルに保存する"""
    try:
        file_path, _ = QFileDialog.getSaveFileName(main_window, "プレイヤー情報ファイルを保存", "player_dictionary.json", "JSONファイル (*.json)")
        if not file_path:
            return

        player_data_to_save = {}
        for player in main_window.player_list:
            roles_data = {role: getattr(player, role).isChecked() for role in ROLES}
            ranks_data = {f"{role}_rank": getattr(player, f"{role}_rank_combobox").currentText() for role in ROLES}

            player_data_to_save[player.name] = {
                'tag': player.tag,
                'rank': ranks_data,
                'role': roles_data,
            }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(player_data_to_save, f, indent=4, ensure_ascii=False)
    except Exception as e:
        QMessageBox.warning(main_window, "エラー", f"ファイルの保存中にエラーが発生しました: {e}")


def load_dict_from_file(main_window):
    """ファイルからプレイヤー情報を読み込む"""
    try:
        file_path, _ = QFileDialog.getOpenFileName(main_window, "プレイヤー情報ファイルを開く", "", "JSONファイル (*.json)")
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

                for row in range(1, main_window.player_grid.rowCount()):  # Start from 1 to skip header
                    name_widget_item = main_window.player_grid.itemAtPosition(row, 0)
                    if not name_widget_item:
                        continue
                    player_name = name_widget_item.widget().text()

                    if player_name in data:
                        player_data = data[player_name]

                        # Update roles and role-specific ranks
                        col_offset = 1
                        for role in ROLES:
                            # Role checkbox
                            checkbox = main_window.player_grid.itemAtPosition(row, col_offset).widget()
                            checkbox.setChecked(player_data.get('role', {}).get(role, False))
                            col_offset += 1

                            # Role rank
                            role_rank_combobox = main_window.player_grid.itemAtPosition(row, col_offset).widget()
                            role_rank_combobox.setCurrentText(player_data.get('rank', {}).get(f'{role}_rank', 'UNRANKED'))
                            col_offset += 1

    except Exception as e:
        QMessageBox.warning(main_window, "エラー", f"ファイルの読み込み中にエラーが発生しました: {e}")


def copy_to_clipboard(main_window):
    team1_text = "チーム1----\n"
    for player in main_window.team1_player:
        team1_text += f'{player.role}: {player.name}\n'

    team2_text = "チーム2----\n"
    for player in main_window.team2_player:
        team2_text += f'{player.role}: {player.name}\n'

    # クリップボードにコピー
    QApplication.clipboard().setText(team1_text + "\n" + team2_text)


def copy_to_clipboard_opgg(main_window):
    name1_list = []
    team1_text = "チーム1----\n"
    for player in main_window.team1_player:
        team1_text += f'{player.role}: {player.name}\n'
        name = player.name.replace(' ', '+')
        tag = player.tag
        name1_list.append(f'{name}%23{tag}')
    name1 = '%2C'.join(name1_list)
    team1_text += f'https://www.op.gg/multisearch/jp?summoners={name1}'

    name2_list = []
    team2_text = "チーム2----\n"
    for player in main_window.team2_player:
        team2_text += f'{player.role}: {player.name}\n'
        name = player.name.replace(' ', '+')
        tag = player.tag
        name2_list.append(f'{name}%23{tag}')
    name2 = '%2C'.join(name2_list)
    team2_text += f'https://www.op.gg/multisearch/jp?summoners={name2}'

    # クリップボードにコピー
    QApplication.clipboard().setText(team1_text + "\n" + team2_text)


def webhook_button_clicked(main_window):
    name1_list = []
    team1_text = ""
    for player in main_window.team1_player:
        team1_text += f'{player.role}: {player.name}\n'
        name = player.name.replace(' ', '+')
        tag = player.tag
        name1_list.append(f'{name}%23{tag}')
    name1 = '%2C'.join(name1_list)
    team1_url = f'[OPGG](https://www.op.gg/multisearch/jp?summoners={name1})'

    name2_list = []
    team2_text = ""
    for player in main_window.team2_player:
        team2_text += f'{player.role}: {player.name}\n'
        name = player.name.replace(' ', '+')
        tag = player.tag
        name2_list.append(f'{name}%23{tag}')
    name2 = '%2C'.join(name2_list)
    team2_url = f'[OPGG](https://www.op.gg/multisearch/jp?summoners={name2})'

    payload = {
        "payload_json" : {
            "embeds": [
                {
                    "title"			: "Custom Team",
                    "description"	: "",
                    "url"			: "",
                    "color"			: 5620992,
                    "fields": [
                        {
                            "name"	: "Team 1",
                            "value"	: f"{team1_text}\n {team1_url}",
                            "inline": True,
                        },
                        {
                            "name"	: "Team 2",
                            "value"	: f"{team2_text}\n {team2_url}",
                            "inline": True,
                        },
                    ],
                }
            ]
        }
    }
    payload['payload_json'] = json.dumps(payload['payload_json'], ensure_ascii=False)
    requests.post(WEBHOOK, data=payload)
