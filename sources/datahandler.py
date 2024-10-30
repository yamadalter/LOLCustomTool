import requests
from roleidentification import pull_data
from cassiopeia.core.match import MatchData
from roleidentification.get_roles import get_roles
from io import BytesIO
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class LoLDataHandler():
    def __init__(self):
        ver_res = requests.get('https://ddragon.leagueoflegends.com/api/versions.json')
        ver_data = ver_res.json()
        self.ver = ver_data[0]

        res = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{self.ver}/data/ja_JP/champion.json')
        self.champ_data = res.json()

        res = requests.get(f'https://ddragon.leagueoflegends.com/cdn/{self.ver}/data/ja_JP/runesReforged.json')
        self.rune_data = res.json()

    def set_champion_name(self, participants):
        for participant in participants:
            for champion_name, champion_data in self.champ_data['data'].items():
                if int(champion_data['key']) == participant.championId:
                    participant.championName = champion_name

    def set_positions(self, team, positions):
        for participant in team.participants:
            for k, v in positions.items():
                if participant.championId == v:
                    participant.position = k

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
        rune_paths = ['', '']
        for rune in self.rune_data:
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
        response = requests.get(f'http://ddragon.leagueoflegends.com/cdn/{self.ver}/img/champion/{champ}.png')
        img = Image.open(BytesIO(response.content))
        img = ImageQt(img)
        pixmap = QPixmap.fromImage(img)
        return pixmap

    def get_item_images(self, player):
        items = [player.stats[f'item{i}'] for i in range(6)]
        items_images = []
        for item in items:
            if not item == 0:
                response = requests.get(f'http://ddragon.leagueoflegends.com/cdn/{self.ver}/img/item/{item}.png')
                img = Image.open(BytesIO(response.content))
                img = ImageQt(img)
                pixmap = QPixmap.fromImage(img)
                pixmap = pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio)
                items_images.append(pixmap)
            else:
                pixmap = QPixmap('material/0.png')
                pixmap = pixmap.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio)
                items_images.append(pixmap)
        return items_images
