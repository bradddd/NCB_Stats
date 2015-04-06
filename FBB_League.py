__author__ = 'Ryan'

import pandas as pd
from Scrape_espn_league import *
import pickle


class FBB_League:
    def __init__(self, leagueID, year):
        self.leagueID = leagueID
        self.year = year
        # data frame containing
        # [teamID, teamName, wins, losses, draws]
        self.teams = pd.DataFrame()
        # data frame containing all of the matchups
        # [weekID, gameID, teamID, H/A]
        self.matchups = pd.DataFrame()
        #data frame containing all of te results for each weeks matchups
        #[weekID, gameID, teamID, H, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG,
        # K, QS, CG, SO, W, L, SV, HD, BAA, ERA, WHIP, K/9, Wins, Losses, Ties, H/A]
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
            self.ELO = self.ELO.append(pd.Series([t, 1500.0, 1500.0]), ignore_index=True)
        self.ELO.columns = ['teamID', 'ELO', 'Init']

    def updateELO(self, weekID):
        if weekID not in self.ELO.columns:
            games = list(self.matchups[(self.matchups['weekID'] == weekID)]['gameID'])
            for g in games:
                self.calcELO(g)
            self.ELO[weekID] = pd.Series(list(self.ELO['ELO']))

    def calcELO(self, gameID):
        teamsMatch = self.matchups[(self.matchups[gameID] == gameID)]
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

    def calculateBatterZScores(self):
        cols = list(self.batterProjections.columns)
        if 'Zscore' not in cols[-1]:
            cols = cols[12:]  # eventually fix to only take the positions used by the league
            new_cols = []
            for col in cols:
                col_zscore = col + '_zscore'
                self.batterProjections[col_zscore] = (self.batterProjections[col] - self.batterProjections[col].mean()) \
                                                     / self.batterProjections[col].std(ddof=0)
                new_cols.append(col_zscore)
            self.batterProjections['Zscore'] = 0
            for col in new_cols:
                print()
                self.batterProjections['Zscore'] += self.batterProjections[col]


    def calcualtePitcherZScores(self):
        neg_cats = ['ER', 'BB', 'L', 'BAA', 'ERA', 'WHIP']
        cols = list(self.pitcherProjections.columns)
        if 'Zscore' not in cols[-1]:
            cols = cols[4:]  # eventually fix to only take the positions used by the league
            new_cols = []
            for col in cols:
                col_zscore = col + '_zscore'
                self.pitcherProjections[col_zscore] = (self.pitcherProjections[col] - self.pitcherProjections[
                    col].mean()) \
                                                      / self.pitcherProjections[col].std(ddof=0)
                new_cols.append(col_zscore)
            self.pitcherProjections['Zscore'] = 0
            for col in new_cols:
                if col[:col.find('_zscore')] in neg_cats:
                    self.pitcherProjections['Zscore'] -= self.pitcherProjections[col]
                else:
                    self.pitcherProjections['Zscore'] += self.pitcherProjections[col]


    def projectTeams(self):
        pass

    def calculateTeamZscore(self, teamId):
        pass

    def calculateTeamTotals(self, teamId):
        pass


    #############################################################################
    #                                                                           #
    #                          End of Week Analysis                             #
    #       team of the week, player of the week, next week predictions         #
    #############################################################################




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



    def getLeagueID(self):
        return self.leagueID

    def getYear(self):
        return self.year

    def getELO(self):
        return self.ELO

    def getTeams(self):
        return self.teams

    def getMatchups(self):
        return self.matchups

    def getMatchUpResults(self):
        return self.matchupresults

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

    #############################################################################
    #                                                                           #
    #                                 Setters                                   #
    #                                                                           #
    #############################################################################

    def setLeagueID(self, leagueID):
        self.leagueID = leagueID

    def setYear(self, year):
        self.year = year

    def setELO(self, ELO):
        self.ELO = ELO

    def setTeams(self, teams):
        self.teams = teams

    def setMatchups(self, matchups):
        self.matchups = matchups

    def setMatchUpResults(self, matchupresults):
        self.matchupresults = matchupresults

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

    def updateMatchups(self, matchups):
        self.matchups = matchups

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