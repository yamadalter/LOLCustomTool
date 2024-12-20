import asyncio
from PyQt6.QtCore import QThread, pyqtSignal
from lcu_driver import Connector
from common import RANK_VAL


class PlayerData():
    pass


class WorkerThread(QThread):
    data_updated = pyqtSignal(list)
    history_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.mode = "lobby"  # デフォルトのモードを設定

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        connector = Connector(loop=loop)

        @connector.ready
        async def connect(connection):

            # lobby情報の取得
            if self.mode == "lobby":
                lobby = await connection.request('get', '/lol-lobby/v2/lobby')
                lobby_data = await lobby.json()
                players = []
                if 'message' not in lobby_data:
                    members = lobby_data['members']
                    players += await self._set_player_list(connection, members, spectator=False)
                    spectators = lobby_data['gameConfig']['customSpectators']
                    players += await self._set_player_list(connection, spectators, spectator=True)

                self.data_updated.emit(players)

            # 試合結果履歴の取得
            elif self.mode == "history":
                summoner = await connection.request('get', '/lol-summoner/v1/current-summoner/')
                summoner = await summoner.json()
                puuid = summoner['puuid']
                match_data = await connection.request('get', '/lol-match-history/v1/products/lol/%s/matches' % puuid)
                match_json = await match_data.json()
                games = match_json['games']['games']
                game_dict = {}
                for game in games:
                    if (game['endOfGameResult'] == 'GameComplete' and
                        game['gameType'] == 'CUSTOM_GAME' and
                        game['gameMode'] == 'CLASSIC'):
                        game_data = await connection.request('get', '/lol-match-history/v1/games/%s' % game['gameId'])
                        game_json = await game_data.json()
                        game_dict[game['gameId']] = game_json
                if len(game_dict) > 0:
                    self.history_updated.emit(game_dict)

        @connector.close
        async def disconnect(connection):
            print('Finished task')

        try:
            connector.start()
        finally:
            loop.close()

    async def _set_player_list(self, connection, members, spectator=False):
        players = []
        for member in members:
            puuid = member['puuid']
            summoner = await connection.request('get', '/lol-summoner/v2/summoners/puuid/%s' % puuid)
            summoner = await summoner.json()
            if 'gameName' in summoner:
                name = summoner['gameName']
                tag = summoner['tagLine']
                rank_data = await connection.request('get', '/lol-ranked/v1/ranked-stats/%s' % puuid)
                rank_json = await rank_data.json()
                soloq = rank_json['queueMap']['RANKED_SOLO_5x5']
                pre_tier = soloq['previousSeasonHighestTier']
                pre_div = soloq['previousSeasonHighestDivision']
                tier = soloq['highestTier']
                div = soloq['highestDivision']
                rank = f'{tier} {div}' if div != 'NA' else tier
                pre_rank = f'{pre_tier} {pre_div}' if pre_div != 'NA' else pre_tier
                player = PlayerData()
                player.name = name
                player.rank = rank if RANK_VAL.get(rank, 0) >= RANK_VAL.get(pre_rank, 0) else pre_rank
                player.tag = tag
                if spectator:
                    player.spectator = True
                else:
                    player.spectator = False
                players.append(player)
        return players
