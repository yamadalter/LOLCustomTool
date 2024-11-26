import requests
from roleidentification import pull_data
from cassiopeia.core.match import MatchData
# from roleidentification.get_roles import get_roles
from io import BytesIO
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
import itertools
import copy
from typing import List


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
            sup = None
            for participant in team.participants:
                if participant.spell1Id == 11 or participant.spell2Id == 11:
                    if smite is None:
                        smite = participant.championId
                    else:
                        smite = None
                for i in range(7):
                    if 3865 <= int(participant.stats[f'item{i}']) <= 3877:
                        sup = participant.championId
                for identity in matchdata.participantIdentities:
                    if participant.participantId == identity['participantId']:
                        participant.player = identity['player']
            if smite is None:
                if sup is None:
                    positions = get_roles(champion_roles, champions)
                else:
                    positions = get_roles(champion_roles, champions, utility=sup)
            else:
                if sup is None:
                    positions = get_roles(champion_roles, champions, jungle=smite)
                else:
                    positions = get_roles(champion_roles, champions, jungle=smite, utility=sup)
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


def highest_possible_playrate(champion_positions):
    maxes = {"TOP": 0.0, "JUNGLE": 0.0, "MIDDLE": 0.0, "BOTTOM": 0.0, "UTILITY": 0.0}
    for champion, rates in champion_positions.items():
        for position, rate in rates.items():
            if rate > maxes[position]:
                maxes[position] = rate
    return sum(maxes.values()) / len(maxes)


def calculate_metric(champion_positions, champions_by_position):
    return sum(champion_positions[champion][position] for position, champion in champions_by_position.items()) / len(champions_by_position)


def calculate_confidence(best_metric, second_best_metric):
    confidence = (best_metric - second_best_metric) / best_metric * 100
    return confidence


def get_positions(champion_positions, composition: List[int], top=None, jungle=None, middle=None, bottom=None, utility=None):
    # Check the types in `composition` and the other input types
    for i, champion in enumerate(composition):
        if not isinstance(champion, int):
            raise ValueError("The composition must be a list of champion IDs.")
    if (top is not None and not isinstance(top, int)) or \
            (jungle is not None and not isinstance(jungle, int)) or \
            (middle is not None and not isinstance(middle, int)) or \
            (bottom is not None and not isinstance(bottom, int)) or \
            (utility is not None and not isinstance(utility, int)):
        raise ValueError("The composition must be a list of champion IDs.")

    if None not in (top, jungle, middle, bottom, utility):
        raise ValueError("The composition was predefined by the kwargs.")

    # Set the initial guess to be the champion in the composition, order doesn't matter
    best_positions = {
        "TOP": composition[0],
        "JUNGLE": composition[1],
        "MIDDLE": composition[2],
        "BOTTOM": composition[3],
        "UTILITY": composition[4]
    }
    best_metric = -float('inf')
    second_best_metric = -float('inf')
    second_best_positions = None

    # Figure out which champions and positions we need to fill
    known_champions = [assigned for assigned in (top, jungle, middle, bottom, utility) if assigned is not None]
    unknown_champions = list(set(composition) - set(known_champions))
    unknown_positions = [position for position, assigned in zip(
        ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"),
        (top, jungle, middle, bottom, utility)
    ) if assigned is None]
    test_composition = {
        "TOP": top,
        "JUNGLE": jungle,
        "MIDDLE": middle,
        "BOTTOM": bottom,
        "UTILITY": utility
    }
    # Iterate over the positions we need to fill and record how well each composition "performs"
    for champs in itertools.permutations(unknown_champions, len(unknown_positions)):
        for i, position in enumerate(unknown_positions):
            test_composition[position] = champs[i]

        metric = calculate_metric(champion_positions, test_composition)
        if metric > best_metric:
            second_best_metric = best_metric
            second_best_positions = best_positions
            best_metric = metric
            best_positions = copy.deepcopy(test_composition)

        if best_metric > metric > second_best_metric:
            second_best_metric = metric
            second_best_positions = copy.deepcopy(test_composition)

    best_play_percents = {champion: champion_positions[champion][position] for position, champion in best_positions.items()}
    if second_best_positions is not None:
        second_best_play_percents = {champion: champion_positions[champion][position] for position, champion in second_best_positions.items()}
    else:
        second_best_play_percents = None

    if second_best_positions == best_positions:
        second_best_positions = None
        second_best_play_percents = None
        second_best_metric = -float('inf')
    count_bad_assignments = 0
    for value in best_play_percents.values():
        if value < 0:
            count_bad_assignments += 1

    found_acceptable_alternative = (second_best_play_percents is not None)

    if found_acceptable_alternative:
        confidence = calculate_confidence(best_metric, second_best_metric)
    else:
        confidence = 0.0

    return best_positions, best_metric, confidence, second_best_positions


def get_roles(champion_positions, composition: List[int], top=None, jungle=None, middle=None, bottom=None, utility=None):
    # Check the types in `composition` and the other input types
    for i, champion in enumerate(composition):
        if not isinstance(champion, int):
            raise ValueError("The composition must be a list of champion IDs.")
    if (top is not None and not isinstance(top, int)) or \
            (jungle is not None and not isinstance(jungle, int)) or \
            (middle is not None and not isinstance(middle, int)) or \
            (bottom is not None and not isinstance(bottom, int)) or \
            (utility is not None and not isinstance(utility, int)):
        raise ValueError("The composition must be a list of champion IDs.")

    identified = {}
    if top is not None:
        identified["TOP"] = top
    if jungle is not None:
        identified["JUNGLE"] = jungle
    if middle is not None:
        identified["MIDDLE"] = middle
    if bottom is not None:
        identified["BOTTOM"] = bottom
    if utility is not None:
        identified["UTILITY"] = utility

    if len(identified) >= len(composition):
        raise ValueError("The composition was predefined by the kwargs.")

    secondary_positions = None
    secondary_metric = -float('inf')
    while len(identified) < len(composition) - 1:
        kwargs = {position.lower(): champion for position, champion in identified.items()}
        positions, metric, confidence, sbp = get_positions(champion_positions, composition, **kwargs)
        if sbp is not None:
            _metric = calculate_metric(champion_positions, {position: champion for position, champion in sbp.items()})

            if secondary_positions is None:
                secondary_positions = sbp
                secondary_metric = _metric
            elif metric > _metric > secondary_metric:
                secondary_metric = _metric
                secondary_positions = sbp

        # Done! Grab the results.
        best = sorted([(position, champion) for position, champion in positions.items() if position not in identified],
                      key=lambda t: champion_positions[t[1]][t[0]], reverse=True)[0]
        identified[best[0]] = best[1]
        confidence = calculate_confidence(metric, secondary_metric)

    return positions
