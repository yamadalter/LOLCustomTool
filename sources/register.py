import datetime
import pandas as pd
from PyQt6.QtCore import QThread, pyqtSignal
from common import RDS_HOST, RDS_USER, RDS_PASSWORD, RDS_DB
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from pangres import upsert
from create_table import (
    create_game_table,
    create_team_table,
    create_bans_table,
    create_player_table,
    create_stats_table,
    create_participants_table,
)


class MatchDataUploader(QThread):
    # シグナルの定義
    upload_finished = pyqtSignal(bool)  # アップロード完了シグナル
    connected = pyqtSignal(bool)  # 接続完了シグナル

    def __init__(self):
        super().__init__()
        self.engine = None

    def run(self):
        # MySQL 接続 (データベース指定なし)
        self.engine = create_engine(f'mysql+pymysql://{RDS_USER}:{RDS_PASSWORD}@{RDS_HOST}:3306/{RDS_DB}')
        if not database_exists(self.engine.url):
            create_database(self.engine.url)
            # テーブル作成
            with self.engine.connect() as conn:  # コネクションを取得
                try:
                    conn.connection.cursor().execute(create_game_table)
                    conn.connection.cursor().execute(create_team_table)
                    conn.connection.cursor().execute(create_bans_table)
                    conn.connection.cursor().execute(create_player_table)
                    conn.connection.cursor().execute(create_stats_table)
                    conn.connection.cursor().execute(create_participants_table)
                    # 処理が成功したことを通知
                    self.connected.emit(True)
                except Exception as e:
                    print(f"テーブル作成中にエラーが発生しました: {e}")
                    # 処理が失敗したことを通知
                    self.connected.emit(False)
                    return  # テーブル作成エラー発生時は以降の処理を中断
        else:
            print("データベースは既に作成済みです")
        # 処理が成功したことを通知
        self.connected.emit(True)

    def upload_match_data(self, d):

        # 初期化
        df_player = pd.DataFrame([])
        df_participants = pd.DataFrame([])
        df_stats = pd.DataFrame([])
        df_teams = pd.DataFrame([])
        df_bans = pd.DataFrame([])

        # データフレームに変換
        _ = d.pop('participantIdentities', None)
        participants = d.pop('participants', None)
        teams = d.pop('teams', None)

        df_game = pd.json_normalize(d)
        df_game['duration'] = str(d['duration'])
        df_game['creation'] = d['creation'].datetime.strftime('%Y-%m-%d %H:%M:%S.%f')
        df_game['gameCreationDate'] = str(datetime.datetime.strptime(d['gameCreationDate'], '%Y-%m-%dT%H:%M:%S.%fZ'))
        gameId = d['id']

        # teamデータ処理
        for team in teams:
            if 'blue' in str(team['side']):
                side = 'blue'
                teamId = 0
            else:
                side = 'red'
                teamId = 1
            team['side'] = side
            team['teamId'] = teamId
            team['gameId'] = gameId
            bans = team.pop('bans', None)
            _ = team.pop('participants', None)
            df_teams = pd.concat([df_teams, pd.json_normalize(team)])
            for ban in bans:
                ban['teamId'] = teamId
                ban['gameId'] = gameId
                df_bans = pd.concat([df_bans, pd.json_normalize(ban)])

        # participantsデータ処理
        for p in participants:
            if 'blue' in str(p['side']):
                side = 'blue'
                teamId = 0
            else:
                side = 'red'
                teamId = 1
            p['puuid'] = p['player']['puuid']
            p['side'] = side
            p['teamId'] = teamId
            p['gameId'] = gameId
            participantId = p['participantId']
            _ = p.pop('timeline', None)
            stats = p.pop('stats', None)
            stats['participantId'] = participantId
            stats['gameId'] = gameId
            stats['puuid'] = p['puuid']
            player = p.pop('player', None)
            df_participants = pd.concat([df_participants, pd.json_normalize(p)])
            df_player = pd.concat([df_player, pd.json_normalize(player)])
            df_stats = pd.concat([df_stats, pd.json_normalize(stats)])

        # インデックスを設定
        df_game = df_game.set_index('id')
        df_player = df_player.set_index('puuid')
        df_teams = df_teams.set_index(['gameId', 'teamId'])
        df_bans = df_bans.set_index(['gameId', 'teamId', 'pickTurn'])
        df_stats = df_stats.set_index(['participantId', 'gameId'])
        df_participants = df_participants.set_index(['participantId', 'gameId'])

        try:
            # データフレームをデータベースに登録
            upsert(
                con=self.engine, df=df_game,
                table_name='game', if_row_exists='update',
                add_new_columns=True, create_table=False
            )
            upsert(
                con=self.engine, df=df_player,
                table_name='player', if_row_exists='update',
                add_new_columns=True, create_table=False
            )
            upsert(
                con=self.engine, df=df_teams,
                table_name='team', if_row_exists='update',
                add_new_columns=True, create_table=False
            )
            upsert(
                con=self.engine, df=df_bans,
                table_name='bans', if_row_exists='update',
                add_new_columns=True, create_table=False
            )
            upsert(
                con=self.engine, df=df_stats,
                table_name='stats', if_row_exists='update',
                add_new_columns=True, create_table=False
            )
            upsert(
                con=self.engine, df=df_participants,
                table_name='participants', if_row_exists='update',
                add_new_columns=True, create_table=False
            )

            self.upload_finished.emit(True)
        except Exception as e:
            print(f"アップロード中にエラーが発生しました: {e}")
            # 処理が失敗したことを通知
            self.upload_finished.emit(False)
            return
