import json
import requests
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication
from common import WEBHOOK, ROLES, RANKS_TAG, RANKS


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

                # Iterate through player objects instead of grid for robustness
                for player in main_window.player_list:
                    if player.name in data:
                        player_data = data[player.name]

                        # Update roles and role-specific ranks from the player object
                        for role in ROLES:
                            # Update checkbox
                            if hasattr(player, role):
                                checkbox = getattr(player, role)
                                checkbox.setChecked(player_data.get('role', {}).get(role, False))

                            # Update combobox
                            if hasattr(player, f"{role}_rank_combobox"):
                                rank_combobox = getattr(player, f"{role}_rank_combobox")
                                rank_tag = player_data.get('rank', {}).get(f'{role}_rank', 'UN')
                                if rank_tag in RANKS_TAG:
                                    rank_combobox.setCurrentText(rank_tag)
                                elif rank_tag in RANKS: # Handle old format
                                    rank_combobox.setCurrentText(RANKS_TAG[RANKS.index(rank_tag)])

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