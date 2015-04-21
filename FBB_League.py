__author__ = 'Ryan'

import pandas as pd
from Scrape_espn_league import *
from FBB_Team import *
import pickle


class FBB_League:
    def __init__(self, leagueId, year):
        self.leagueId = leagueId
        self.year = year
        # data frame containing
        # [teamID, Name, wins, losses, draws]
        self.teams = pd.DataFrame()
        # data frame containing all of the schedule
        # [weekID, gameID, teamID, H/A]
        self.schedule = pd.DataFrame()
        # data frame containing all of te results for each weeks schedule
        #[weekID, gameID, teamID, H, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG,
        # K, QS, CG, SO, W, L, SV, HD, BAA, ERA, WHIP, K/9, Wins, Losses, Ties]
        self.matchUpResults = pd.DataFrame()
        #data frame containing all of the batters and their year to date stats
        # [playerID, Name, Team, catcher, first base, second base, third base, shortstop,
        # left field, center field, right field, designated hitter
        # H, AB, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG]
        self.batters = pd.DataFrame()
        #data frame containing all of the batters and their projections
        # [playerID, Name, Team, catcher, first base, second base, third base, shortstop,
        # left field, center field, right field, designated hitter
        # H, AB, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG]
        self.batterProjections = pd.DataFrame()
        #data frame containing all of the batters and what FBB team their are on
        # [playerID, TeamID]
        self.batterRosters = pd.DataFrame()
        #data frame containing each batters week as they played for a team
        #[playerID, Name, FBBteamID, H, AB, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG]
        self.matchUpBatters = pd.DataFrame()
        #data frame containing all of the pitchers and their year to data stats
        #[playerID, Name, Team, Starting Pitcher, Relief Pitcher, IP, K, QS, CG, SO, W, L, SV, HD, BAA, ERA, WHIP, K/9]
        self.pitchers = pd.DataFrame()
        #data frame containing all of the pitchers and their projections
        #[playerID, Name, Team, Starting Pitcher, Relief Pitcher, IP, K, QS, CG, SO, W, L, SV, HD, BAA, ERA, WHIP, K/9]
        self.pitcherProjections = pd.DataFrame()
        #data frame containing all of the pitcher and what FBB team their are on
        # [playerID, FBBTeamID]
        self.pitcherRosters = pd.DataFrame()
        #data frame containing each pitchers week as they played for a team
        #[playerID, Name, FBBteamID, gameID, H, AB, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG]
        self.matchUpPitchers = pd.DataFrame()
        #data frame containing all of the teamIDs and their ELO rating
        #[teamID, ELO, Init, week 1 ELO, , week 2 ELO, ... ]
        self.ELO = pd.DataFrame()
        #data frame containing all of the information for how much each roster can hold
        # [Roster Position, Num Starters, Min, Max]
        # note bench and DL will be roster positions
        self.leagueInfo = pd.DataFrame()
        # data frame containing the season stats for each team
        #[Name, teamID, ...Scoring Stats...]
        self.seasonStats = pd.DataFrame()
        # list of team objects
        self.teamObjs = []

    # ############################################################################
    #                                                                           #
    #                                                                           #
    #                           League Functions                                #
    #                NOTE* No Scraping is done by this class                    #
    #                                                                           #
    #############################################################################

    #############################################################################
    #                                                                           #
    #                                 ELO                                       #
    #                                                                           #
    #############################################################################

    def createELO(self):
        teams = list(self.teams['teamID'])
        for t in teams:
            self.ELO = self.ELO.append(pd.Series([t, 1400.0, 1400.0]), ignore_index=True)
        self.ELO.columns = ['teamID', 'ELO', 'Init']

    def updateELO(self, weekID):
        if weekID not in self.ELO.columns:
            games = list(self.schedule[(self.schedule['weekID'] == weekID)]['gameID'])
            for g in games:
                self.calcELO(g)
            self.ELO[weekID] = pd.Series(list(self.ELO['ELO']))

    def calcELO(self, gameID):
        teamsMatch = self.schedule[(self.schedule[gameID] == gameID)]
        weekID = list(teamsMatch['weekID'])[0]
        teams = list(teamsMatch['teamID'])
        teamA = self.ELO[(self.ELO['teamID'] == teams[0])]['ELO']
        teamB = self.ELO[(self.ELO['teamID'] == teams[1])]['ELO']
        teamA_new, teamB_new = self.ELOMath(teamA, teamB)
        self.ELO.loc[self.ELO.teamID == teams[0], 'ELO'] = teamA_new
        self.ELO.loc[self.ELO.teamID == teams[1], 'ELO'] = teamB_new

    def ELOMath(self, teamA, teamB):
        A = 1 / (1 + 10 ** ((teamB - teamA) / 400))
        B = 1 / (1 + 10 ** ((teamA - teamB) / 400))
        return A, B

    #############################################################################
    #                                                                           #
    #                                 Analysis                                  #
    #                                                                           #
    #############################################################################

    def calculateBatterZScores(self, battersIn):
        batters = battersIn.copy()
        cols = list(batters.columns)
        if 'Zscore' not in cols[-1]:
            cols = cols[12:]  # eventually fix to only take the positions used by the league
            new_cols = []
            for col in cols:
                col_zscore = col + '_zscore'
                if batters[col].std(ddof=0) != 0:
                    batters[col_zscore] = (batters[col] - batters[col].mean()) / batters[col].std(ddof=0)
                else:
                    batters[col_zscore] = 0
                new_cols.append(col_zscore)
            batters['Zscore'] = 0
            for col in new_cols:
                batters['Zscore'] += batters[col]
        return batters

    def calculatePitcherZScores(self, pitchersIn):
        pitchers = pitchersIn.copy()
        neg_cats = ['ER', 'BB', 'L', 'BAA', 'ERA', 'WHIP']
        cols = list(pitchers.columns)
        if 'Zscore' not in cols[-1]:
            cols = cols[5:]  # eventually fix to only take the positions used by the league
            new_cols = []
            for col in cols:
                col_zscore = col + '_zscore'
                if pitchers[col].std(ddof=0) != 0:
                    pitchers[col_zscore] = (pitchers[col] - pitchers[col].mean()) / pitchers[col].std(ddof=0)
                else:
                    pitchers[col_zscore] = 0
                new_cols.append(col_zscore)
            pitchers['Zscore'] = 0
            for col in new_cols:
                if col[:col.find('_zscore')] in neg_cats:
                    pitchers['Zscore'] = pitchers['Zscore'] - pitchers[col]
                else:
                    pitchers['Zscore'] = pitchers['Zscore'] + pitchers[col]
        return pitchers


    def buildTeams(self):
        teamIds = list(self.teams['teamId'])
        for t in teamIds:
            teamBatters = self.batterRosters[self.batterRosters['teamId'] == t]
            teamPitchers = self.pitcherRosters[self.pitcherRosters['teamId'] == t]
            teamName = self.teams[self.teams['teamId'] == t].iloc[0]['Name']
            team = FBB_Team(self.leagueID, self.year, t, teamName)
            team.setBatterProjections(
                self.batterProjections[self.batterProjections['PlayerId'].isin(list(teamBatters['playerId']))])
            team.setPitcherProjections(
                self.pitcherProjections[self.pitcherProjections['PlayerId'].isin(list(teamPitchers['playerId']))])
            self.teamObjs.append(team)


    def updateTeams(self):
        for team in self.teamObjs:
            t = team.getTeamId()
            teamBatters = self.batterRosters[self.batterRosters['teamId'] == t]
            teamPitchers = self.pitcherRosters[self.pitcherRosters['teamId'] == t]
            team.setBatters(teamBatters)
            team.setPitchers(teamPitchers)

    def projectTeams(self):
        projections = pd.DataFrame()
        for team in self.teamObjs:
            team.projectTeam()
            team.printOptimalLineup()
            projections = projections.append(pd.Series([team.getTeamId(), team.getTeamName(),
                                                        team.getTeamBattingScore(), team.getTeamPitchingScore(),
                                                        team.getTeamScore()]), ignore_index=True)

        projections.columns = ['TeamId', 'TeamName', 'Batting Score', 'Pitching Score', 'Total Score']
        projections = projections.sort('Total Score', ascending=False)
        print(projections)


    #############################################################################
    #                                                                           #
    #                          End of Week Analysis                             #
    #       team of the week, player of the week, next week predictions         #
    #############################################################################

    def analyizeWeek(self, weekId):
        weekMatchup = self.calculateMatchupZScores(weekId)
        Top10B, Bot10B, Top10P, Bot10P = self.calculatePOTW(weekId)
        TOTW = weekMatchup.head(1)
        WOTW = weekMatchup.tail(1)

        print(
            'Your Team of the Week[/b] is {0} with a score of {1}'.format(TOTW.iloc[0]['Name'], TOTW.iloc[0]['Zscore']))
        print('Your [b]Worst of the Week[/b] is {0} with a score of {1}'.format(WOTW.iloc[0]['Name'],
                                                                                WOTW.iloc[0]['Zscore']))
        print('\nWeek Rankings: ')
        print(weekMatchup.loc[:, ['Name', 'Zscore']])
        print('\nTop 10 Batters of the week:')
        print(Top10B.loc[:, ['Name', 'Zscore']])
        print('\nBottom 10 Batters of the week:')
        print(Bot10B.loc[:, ['Name', 'Zscore']])
        print('\nTop 10 Pitchers of the week:')
        print(Top10P.loc[:, ['Name', 'Zscore']])
        print('\nBottom 10 Pitchers of the week:')
        print(Bot10P.loc[:, ['Name', 'Zscore']])

    def calculateMatchupZScores(self, weekId):
        weekMatchup = self.matchUpResults[self.matchUpResults['weekId'] == weekId].copy()
        neg_cats = ['ER', 'BB', 'L', 'BAA', 'ERA', 'WHIP', ]
        cols = list(weekMatchup.columns)
        if 'Zscore' not in cols[-1]:
            cols = cols[4:-2]  # eventually fix to only take the positions used by the league
            new_cols = []
            for col in cols:
                col_zscore = col + '_zscore'
                if weekMatchup[col].std(ddof=0) != 0:
                    weekMatchup[col_zscore] = (weekMatchup[col] - weekMatchup[col].mean()) / weekMatchup[col].std(
                        ddof=0)
                else:
                    weekMatchup[col_zscore] = 0
                new_cols.append(col_zscore)
            weekMatchup['Zscore'] = 0
            for col in new_cols:
                if col[:col.find('_zscore')] in neg_cats:
                    weekMatchup['Zscore'] = weekMatchup['Zscore'] - weekMatchup[col]
                else:
                    weekMatchup['Zscore'] = weekMatchup['Zscore'] + weekMatchup[col]
        weekMatchup = weekMatchup.sort('Zscore', ascending=False)
        return weekMatchup

    def calculatePOTW(self, weekId):
        weekBatters = self.matchUpBatters[self.matchUpBatters['weekId'] == weekId]
        weekBattersZ = self.calculateBatterZScores(weekBatters)

        weekPitchers = self.matchUpPitchers[self.matchUpPitchers['weekId'] == weekId]
        weekPitchersZ = self.calculatePitcherZScores(weekPitchers)

        weekBattersZ = weekBattersZ.sort('Zscore', ascending=False)
        weekPitchersZ = weekPitchersZ.sort('Zscore', ascending=False)

        Top10B = weekBattersZ.head(10)
        Bot10B = weekBattersZ.tail(10)

        Top10P = weekPitchersZ.head(10)
        Bot10P = weekPitchersZ.tail(10)

        return Top10B, Bot10B, Top10P, Bot10P
    #############################################################################
    #                                                                           #
    #                                                                           #
    #                           GETTERS, SETTERS, UPDATERS                      #
    #                                                                           #
    #                                                                           #
    #############################################################################

    #############################################################################
    #                                                                           #
    #                                 Getters                                   #
    #                                                                           #
    #############################################################################



    def getLeagueId(self):
        return self.leagueId

    def getYear(self):
        return self.year

    def getELO(self):
        return self.ELO

    def getTeams(self):
        return self.teams

    def getSchedule(self):
        return self.schedule

    def getMatchUpResults(self):
        return self.matchUpResults

    def getBatters(self):
        return self.batters

    def getBatterProjections(self):
        return self.batterProjections

    def getBatterRosters(self):
        return self.batterRosters

    def getMatchUpBatters(self):
        return self.matchUpBatters

    def getPitchers(self):
        return self.pitchers

    def getPitcherProjections(self):
        return self.pitcherProjections

    def getPitcherRosters(self):
        return self.pitcherRosters

    def getMatchUpPitchers(self):
        return self.matchUpPitchers

    def getLeagueInfo(self):
        return self.leagueInfo

    def getSeasonStats(self):
        return self.seasonStats

    def getTeamObjs(self):
        return self.teamObjs

    #############################################################################
    #                                                                           #
    #                                 Setters                                   #
    #                                                                           #
    #############################################################################

    def setLeagueId(self, leagueId):
        self.leagueId = leagueId

    def setYear(self, year):
        self.year = year

    def setELO(self, ELO):
        self.ELO = ELO

    def setTeams(self, teams):
        self.teams = teams

    def setSchedule(self, schedule):
        self.schedule = schedule

    def setMatchUpResults(self, matchupresults):
        self.matchUpResults = matchupresults

    def setBatters(self, batters):
        self.batters = batters

    def setBatterProjections(self, batterProjections):
        self.batterProjections = batterProjections

    def setBatterRosters(self, batterRosters):
        self.batterRosters = batterRosters

    def setMatchUpBatters(self, matchUpBatters):
        self.matchUpBatters = matchUpBatters

    def setPitchers(self, pitchers):
        self.pitchers = pitchers

    def setPitcherProjections(self, pitcherProjections):
        self.pitcherProjections = pitcherProjections

    def setPitcherRosters(self, pitcherRosters):
        self.pitcherRosters = pitcherRosters

    def setMatchUpPitchers(self, matchUpPitchers):
        self.matchUpPitchers = matchUpPitchers

    def setLeagueInfo(self, leagueInfo):
        self.leagueInfo = leagueInfo

    def setSeasonStats(self, seasonStats):
        self.seasonStats = seasonStats

    def setTeamObjs(self, teamObjs):
        self.teamObjs = teamObjs

    """
    #############################################################################
    #                                                                           #
    #                                 Updaters                                  #
    #                                                                           #
    #############################################################################

    def updateELO(self, ELO):
        self.ELO = ELO

    def updateTeams(self, teams):
        self.teams = teams

    def updateschedule(self, schedule):
        self.schedule = schedule

    def updateMatchUpResults(self, matchupresults):
        self.matchupresults = matchupresults

    def updateBatters(self, batters):
        self.batters = batters

    def updateBatterProjections(self, batterProjections):
        self.batterProjections = batterProjections

    def updateBatterRosters(self, batterRosters):
        self.batterRosters = batterRosters

    def updateMatchUpBatters(self, matchUpBatters):
        self.matchUpBatters = matchUpBatters

    def updatePitchers(self, pitchers):
        self.pitchers = pitchers

    def updatePitcherProjections(self, pitcherProjections):
        self.pitcherProjections = pitcherProjections

    def updatePitcherRosters(self, pitcherRosters):
        self.pitcherRosters = pitcherRosters

    def updateMatchUpPitchers(self, matchUpPitchers):
        self.matchUpPitchers = matchUpPitchers

    def updateLeagueInfo(self, leagueInfo):
        self.leagueInfo = leagueInfo

    def updateeasonStats(self, seasonStats):
        self.seasonStats = seasonStats

    """