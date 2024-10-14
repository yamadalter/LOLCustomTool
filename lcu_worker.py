import asyncio
from PyQt5.QtCore import QThread, pyqtSignal
from lcu_driver import Connector


class WorkerThread(QThread):
    data_updated = pyqtSignal(list)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        connector = Connector(loop=loop)

        @connector.ready
        async def connect(connection):
            lobby = await connection.request('get', '/lol-lobby/v2/lobby/members')
            lobby_data = await lobby.json()

            players = []
            for member in lobby_data:
                puuid = member['puuid']
                summoner = await connection.request('get', '/lol-summoner/v2/summoners/puuid/%s' % puuid)
                summoner = await summoner.json()
                name = summoner['gameName']
                rank_data = await connection.request('get', '/lol-ranked/v1/ranked-stats/%s' % puuid)
                rank_json = await rank_data.json()
                soloq = rank_json['queueMap']['RANKED_SOLO_5x5']
                tier = soloq['previousSeasonHighestTier']
                div = soloq['previousSeasonHighestDivision']
                rank = f'{tier} {div}' if div != 'NA' else tier
                players.append({'name': name, 'rank': rank})
                rank_json = await rank_data.json()
            
            # match_data = await connection.request('get', '/lol-match-history/v1/products/lol/%s/matches' % puuid)
            # match_json = await match_data.json()
            # games = match_json['games']['games']
            # gameids = []
            # for game in games:
            #     if (game['endOfGameResult'] == 'GameComplete' and
            #         game['gameType'] == 'CUSTOM_GAME' and
            #         game['gameMode'] == 'CLASSIC'):
            #         gameids.append(game['gameId'])

            # gameid = gameids[0]
            # game_data = await connection.request('get', '/lol-match-history/v1/games/%s' % gameid)
            # game_json = await game_data.json()
            # print(game_json)
            self.data_updated.emit(players)

        @connector.close
        async def disconnect(connection):
            print('Finished task')

        try:
            connector.start()
        finally:
            loop.close()
