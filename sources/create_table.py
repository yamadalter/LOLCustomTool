# データベース登録
# テーブルが存在しない場合は作成する SQL 文を定義
create_game_table = """
CREATE TABLE IF NOT EXISTS game (
    id INT,
    platform VARCHAR(255),
    mode VARCHAR(255),
    gameCreation BIGINT,
    region VARCHAR(255),
    queue INT,
    seasonId INT,
    endOfGameResult VARCHAR(255),
    gameDuration INT,
    duration TIME,
    creation DATETIME(6),
    version VARCHAR(255),
    gameCreationDate DATETIME(6),
    privateGame BOOLEAN,
    mapId INT,
    type VARCHAR(255),
    PRIMARY KEY (id)
)
"""

create_team_table = """
CREATE TABLE IF NOT EXISTS team (
    gameId INT,
    teamId INT,
    side VARCHAR(255),
    isWinner VARCHAR(255),
    inhibitorKills INT,
    vilemawKills INT,
    firstBloodKiller BOOLEAN,
    firstTowerKiller BOOLEAN,
    firstInhibitorKiller BOOLEAN,
    firstBaronKiller BOOLEAN,
    firstDargon BOOLEAN,
    towerKills INT,
    riftHeraldKills INT,
    hordeKills INT,
    dragonKills INT,
    baronKills INT,
    PRIMARY KEY (gameId, teamId),
    FOREIGN KEY (gameId) REFERENCES game(id),
    INDEX team_game_team_id (gameId, teamId)
)
"""

create_bans_table = """
CREATE TABLE IF NOT EXISTS bans (
    gameId INT,
    teamId INT,
    pickTurn INT,
    championId INT,
    championName VARCHAR(255),
    PRIMARY KEY (gameId, teamId, pickTurn),
    FOREIGN KEY (gameId, teamId) REFERENCES team(gameId, teamId)
)
"""

create_player_table = """
CREATE TABLE IF NOT EXISTS player (
    puuid VARCHAR(255),
    accountId BIGINT,
    currentAccountId BIGINT,
    currentPlatformId VARCHAR(255),
    gameName VARCHAR(255),
    matchHistoryUri VARCHAR(255),
    platformId VARCHAR(255),
    profileIcon INT,
    summonerId BIGINT,
    summonerName VARCHAR(255),
    tagLine VARCHAR(255),
    PRIMARY KEY (puuid)
)
"""

create_participants_table = """
CREATE TABLE IF NOT EXISTS participants (
    participantId INT,
    gameId INT,
    teamId INT,
    puuid VARCHAR(255),
    championId INT,
    position VARCHAR(255),
    championName VARCHAR(255),
    platformId VARCHAR(255),
    spell1Id INT,
    spell2Id INT,
    highestAchievedSeasonTier VARCHAR(255),
    side VARCHAR(255),
    PRIMARY KEY (participantId, gameId),
    FOREIGN KEY (gameId, teamId) REFERENCES team(gameId, teamId),
    FOREIGN KEY (puuid) REFERENCES player(puuid)
)
"""

create_stats_table = """
CREATE TABLE IF NOT EXISTS stats (
    participantId INT,
    gameId INT,
    puuid VARCHAR(255),
    assists INT,
    causedEarlySurrender BOOLEAN,
    champLevel INT,
    combatPlayerScore INT,
    damageDealtToObjectives INT,
    damageDealtToTurrets INT,
    damageSelfMitigated INT,
    deaths INT,
    doubleKills INT,
    earlySurrenderAccomplice BOOLEAN,
    firstBloodAssist BOOLEAN,
    firstBloodKill BOOLEAN,
    firstInhibitorAssist BOOLEAN,
    firstInhibitorKill BOOLEAN,
    firstTowerAssist BOOLEAN,
    firstTowerKill BOOLEAN,
    gameEndedInEarlySurrender BOOLEAN,
    gameEndedInSurrender BOOLEAN,
    goldEarned INT,
    goldSpent INT,
    inhibitorKills INT,
    item0 INT,
    item1 INT,
    item2 INT,
    item3 INT,
    item4 INT,
    item5 INT,
    item6 INT,
    killingSprees INT,
    kills INT,
    largestCriticalStrike INT,
    largestKillingSpree INT,
    largestMultiKill INT,
    longestTimeSpentLiving INT,
    magicDamageDealt INT,
    magicDamageDealtToChampions INT,
    magicalDamageTaken INT,
    neutralMinionsKilled INT,
    neutralMinionsKilledEnemyJungle INT,
    neutralMinionsKilledTeamJungle INT,
    objectivePlayerScore INT,
    pentaKills INT,
    perk0 INT,
    perk0Var1 INT,
    perk0Var2 INT,
    perk0Var3 INT,
    perk1 INT,
    perk1Var1 INT,
    perk1Var2 INT,
    perk1Var3 INT,
    perk2 INT,
    perk2Var1 INT,
    perk2Var2 INT,
    perk2Var3 INT,
    perk3 INT,
    perk3Var1 INT,
    perk3Var2 INT,
    perk3Var3 INT,
    perk4 INT,
    perk4Var1 INT,
    perk4Var2 INT,
    perk4Var3 INT,
    perk5 INT,
    perk5Var1 INT,
    perk5Var2 INT,
    perk5Var3 INT,
    perkPrimaryStyle INT,
    perkSubStyle INT,
    physicalDamageDealt INT,
    physicalDamageDealtToChampions INT,
    physicalDamageTaken INT,
    playerAugment1 INT,
    playerAugment2 INT,
    playerAugment3 INT,
    playerAugment4 INT,
    playerAugment5 INT,
    playerAugment6 INT,
    playerScore0 INT,
    playerScore1 INT,
    playerScore2 INT,
    playerScore3 INT,
    playerScore4 INT,
    playerScore5 INT,
    playerScore6 INT,
    playerScore7 INT,
    playerScore8 INT,
    playerScore9 INT,
    playerSubteamId INT,
    quadraKills INT,
    sightWardsBoughtInGame INT,
    subteamPlacement INT,
    teamEarlySurrendered BOOLEAN,
    timeCCingOthers INT,
    totalDamageDealt INT,
    totalDamageDealtToChampions INT,
    totalDamageTaken INT,
    totalHeal INT,
    totalMinionsKilled INT,
    totalPlayerScore INT,
    totalScoreRank INT,
    totalTimeCrowdControlDealt INT,
    totalUnitsHealed INT,
    tripleKills INT,
    trueDamageDealt INT,
    trueDamageDealtToChampions INT,
    trueDamageTaken INT,
    turretKills INT,
    unrealKills INT,
    visionScore INT,
    visionWardsBoughtInGame INT,
    wardsKilled INT,
    wardsPlaced INT,
    win BOOLEAN,
    PRIMARY KEY (participantId, gameId),
    FOREIGN KEY (gameId) REFERENCES game(id),
    FOREIGN KEY (puuid) REFERENCES player(puuid)
)"""
