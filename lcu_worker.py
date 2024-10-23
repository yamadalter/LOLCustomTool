import asyncio
from PyQt6.QtCore import QThread, pyqtSignal
from lcu_driver import Connector


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
                lobby = await connection.request('get', '/lol-lobby/v2/lobby/members')
                lobby_data = await lobby.json()

                players = []
                for member in lobby_data:
                    puuid = member['puuid']
                    summoner = await connection.request('get', '/lol-summoner/v2/summoners/puuid/%s' % puuid)
                    summoner = await summoner.json()
                    name = summoner['gameName']
                    tag = summoner['tagLine']
                    rank_data = await connection.request('get', '/lol-ranked/v1/ranked-stats/%s' % puuid)
                    rank_json = await rank_data.json()
                    soloq = rank_json['queueMap']['RANKED_SOLO_5x5']
                    tier = soloq['previousSeasonHighestTier']
                    div = soloq['previousSeasonHighestDivision']
                    rank = f'{tier} {div}' if div != 'NA' else tier
                    players.append({'name': name, 'rank': rank, 'tag': tag})
                    rank_json = await rank_data.json()

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
