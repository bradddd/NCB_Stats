__author__ = 'Ryan'

import pandas as pd
from Scrape_espn_league import *
from FBB_Team import *
import pickle
import scipy
from scipy import stats as st
import datetime


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
        # [weekID, gameID, teamID, H, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG,
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
        # [teamID, Name,ELO, Init, week 1 ELO, , week 2 ELO, ... ]
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
        # current weekId
        self.currentWeekId = 0
        # dataframe of league week dates
        self.leagueScheduleDates = pd.DataFrame()

    # ############################################################################
    # #
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

    #if there is no ELO table, build the table
    def createELO(self):
        if self.ELO.empty:
            teams = list(self.teams['teamId'])
            for t in teams:
                self.ELO = self.ELO.append(pd.Series([t, self.getTeamName(t), 1400.0, 1400.0]), ignore_index=True)
            self.ELO.columns = ['teamId', 'Name', 'ELO', 'Init']
            for w in range(1, self.currentWeekId):
                self.updateELOTable(w)

    # update the ELO for the week if the week has not yet been updated
    def updateELOTable(self, weekId):
        if weekId not in self.ELO.columns:
            games = list(self.matchUpResults[(self.matchUpResults['weekId'] == weekId)]['gameId'])
            for g in games:
                self.calcELO(g)
            self.ELO[weekId] = pd.Series(list(self.ELO['ELO']))
        self.ELO = self.ELO.sort('ELO', ascending=False)

    # calculate the ELO change for a game results
    def calcELO(self, gameId):
        match = self.matchUpResults[(self.matchUpResults['gameId'] == gameId)]
        teamIds = list(match['teamId'])
        Ea, Eb = self.calculateExpectedScore(teamIds[0], teamIds[1])
        Ra = self.getTeamELO(teamIds[0])
        Rb = self.getTeamELO(teamIds[1])
        if self.getMatchupResult(gameId) is None:
            Sa = 0.5
            Sb = 0.5
        elif self.getMatchupResult(gameId) == teamIds[0]:
            Sa = 1
            Sb = 0
        elif self.getMatchupResult(gameId) == teamIds[1]:
            Sa = 0
            Sb = 1
        Ra = self.ELOUpdate(Ra, Sa, Ea)
        Rb = self.ELOUpdate(Rb, Sb, Eb)
        self.ELO.loc[self.ELO['teamId'] == teamIds[0], 'ELO'] = Ra
        self.ELO.loc[self.ELO['teamId'] == teamIds[1], 'ELO'] = Rb

    #ELO Update Rule
    def ELOUpdate(self, Ra, Sa, Ea):
        K = 32
        return Ra + K * (Sa - Ea)

    # Calculate the expected score for a matchup
    def calculateExpectedScore(self, teamA, teamB):
        Qa = self.calculateELOQ(teamA)
        Qb = self.calculateELOQ(teamB)
        Ea = Qa / (Qa + Qb)
        Eb = Qb / (Qa + Qb)
        return Ea, Eb

    # Calculate the ELO Q value
    def calculateELOQ(self, teamId):
        return 10 ** (self.getTeamELO(teamId) / 400)

    #Return a team's ELO
    def getTeamELO(self, teamId):
        return self.ELO[self.ELO['teamId'] == teamId].iloc[0]['ELO']

    #Return the winner teamId of a matchup
    #Returns None if the game is a tie
    def getMatchupResult(self, gameId):
        match = self.matchUpResults[(self.matchUpResults['gameId'] == gameId)]
        teamIds = list(match['teamId'])
        if match[match['teamId'] == teamIds[0]].iloc[0]['Wins'] > match[match['teamId'] == teamIds[1]].iloc[0]['Wins']:
            return teamIds[0]
        elif match[match['teamId'] == teamIds[0]].iloc[0]['Wins'] < match[match['teamId'] == teamIds[1]].iloc[0][
            'Wins']:
            return teamIds[1]
        elif match[match['teamId'] == teamIds[0]].iloc[0]['Wins'] == match[match['teamId'] == teamIds[1]].iloc[0][
            'Wins']:
            return None



    #############################################################################
    #                                                                           #
    #                                 Analysis                                  #
    #                                                                           #
    #############################################################################

    #calculate Zscore for all batters
    def calculateBatterZScores(self, battersIn):
        batters = battersIn.copy()
        cols = list(batters.columns)
        if 'Zscore' not in cols[-1]:
            cols = cols[3:15]  # eventually fix to only take the positions used by the league
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

    #calculate zscores for all pitchers
    def calculatePitcherZScores(self, pitchersIn):

        pitchers = pitchersIn.copy()
        neg_cats = ['ER', 'BB', 'L', 'BAA', 'ERA', 'WHIP']
        cols = list(pitchers.columns)
        if 'Zscore' not in cols[-1]:
            cols = cols[3:-1]  # eventually fix to only take the positions used by the league
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

    #build team objects for optimal lineups
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

    #update teams with current rosters
    def updateTeams(self):
        for team in self.teamObjs:
            t = team.getTeamId()
            teamBatters = self.batterRosters[self.batterRosters['teamId'] == t]
            teamPitchers = self.pitcherRosters[self.pitcherRosters['teamId'] == t]
            team.setBatters(teamBatters)
            team.setPitchers(teamPitchers)

    #project each team based on their starting batters
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

    # print out the players and teams of the week
    def analyizeLastWeek(self):
        weekId = self.currentWeekId - 1
        weekMatchup = self.calculateMatchupZScores(weekId)
        Top10B, Bot10B, Top10P, Bot10P = self.calculatePOTW(weekId)
        roto = self.calculateWeekRoto(weekId)
        TOTW = roto.head(1)
        WOTW = roto.tail(1)
        self.updateELOTable(weekId)
        print(
            'Your Team of the Week[/b] is {0} with a score of {1}'.format(TOTW.iloc[0]['Name'],
                                                                          TOTW.iloc[0]['Total Points']))
        print('Your [b]Worst of the Week[/b] is {0} with a score of {1}'.format(WOTW.iloc[0]['Name'],
                                                                                WOTW.iloc[0]['Total Points']))
        print('\nWeek Rankings: ')
        print('\nZscores: ')
        print(weekMatchup.loc[:, ['Name', 'Zscore']])
        print('\nRoto: ')
        print(roto.loc[:, ['Name', 'Total Points']])
        print('\nELO')
        print(self.ELO.loc[:, ['Name', 'ELO']])
        print('\nTop 10 Batters of the week:')
        print(Top10B.loc[:, ['Name', 'Zscore']])
        print('\nBottom 10 Batters of the week:')
        print(Bot10B.loc[:, ['Name', 'Zscore']])
        print('\nTop 10 Pitchers of the week:')
        print(Top10P.loc[:, ['Name', 'Zscore']])
        print('\nBottom 10 Pitchers of the week:')
        print(Bot10P.loc[:, ['Name', 'Zscore']])

    # calculate roto for last week:
    def calculateWeekRoto(self, weekId):
        neg_cats = ['ER', 'BB', 'L', 'BAA', 'ERA', 'WHIP']
        rankings = list(range(12, 0, -1))
        weekMatchup = self.matchUpResults[self.matchUpResults['weekId'] == weekId].copy()
        cols = list(weekMatchup.columns)
        if 'Total Points' not in cols[-1]:
            cols = cols[4:-4]
            new_cols = []
            for col in cols:
                col_roto = col + 'roto'
                if col not in neg_cats:
                    weekMatchup = weekMatchup.sort(col, ascending=False)
                else:
                    weekMatchup = weekMatchup.sort(col, ascending=True)
                weekMatchup[col_roto] = rankings
                new_cols.append(col_roto)
            weekMatchup['Total Points'] = 0
            for col in new_cols:
                weekMatchup['Total Points'] = weekMatchup['Total Points'] + weekMatchup[col]
        weekMatchup = weekMatchup.sort('Total Points', ascending=False)
        return weekMatchup

    #calculate the Zscore for the teams for the week
    def calculateMatchupZScores(self, weekId):
        weekMatchup = self.matchUpResults[self.matchUpResults['weekId'] == weekId].copy()
        neg_cats = ['ER', 'BB', 'L', 'BAA', 'ERA', 'WHIP']
        cols = list(weekMatchup.columns)
        if 'Zscore' not in cols[-1]:
            cols = cols[4:-4]  # eventually fix to only take the positions used by the league
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

    #calculate the players of the week
    def calculatePOTW(self, weekId):
        weekBatters = self.matchUpBatters[self.matchUpBatters['weekId'] == weekId]
        weekBattersZ = self.calculateBatterZScores(weekBatters)

        weekPitchers = self.matchUpPitchers[self.matchUpPitchers['weekId'] == weekId]
        weekPitchersZ = self.calculatePitcherZScores(weekPitchers)

        weekBattersZ = weekBattersZ.sort('Zscore', ascending=False)
        weekBattersZ.to_csv('week7batters')
        weekPitchersZ = weekPitchersZ.sort('Zscore', ascending=False)

        Top10B = weekBattersZ.head(10)
        Bot10B = weekBattersZ.tail(10)

        Top10P = weekPitchersZ.head(10)
        Bot10P = weekPitchersZ.tail(10)

        return Top10B, Bot10B, Top10P, Bot10P

    # predicts the comming weak by calculating P(X>Y) for each category, and then sums the probabilities to get the
    # total probability of a win vs a loss
    def predictThisWeek(self):
        neg_cats = neg_cats = ['L', 'BAA', 'ERA', 'WHIP']
        matchups = self.schedule[self.schedule['weekId'] == self.currentWeekId]
        mIds = list(set(matchups['gameId']))
        for m in mIds:
            probT1WinCats = {}
            matchup = self.schedule[self.schedule['gameId'] == m]
            t1 = matchup.iloc[0]['teamId']
            t1Name = self.getTeamName(t1)
            t2 = matchup.iloc[1]['teamId']
            t2Name = self.getTeamName(t2)

            avg1, std1 = self.calculateTeamAverages(t1)
            avg2, std2 = self.calculateTeamAverages(t2)
            keys = list(avg1.keys())[4:27]
            for k in keys:
                if k in neg_cats:
                    probT1WinCats[k] = 1 - self.calculateProbabiltyRelationship(avg1[k], avg2[k], std1[k], std2[k])
                else:
                    probT1WinCats[k] = self.calculateProbabiltyRelationship(avg1[k], avg2[k], std1[k], std2[k])
            probT1Win = 0
            for c in self.possibleWins(22):
                probT1WinComb = 1
                for ind, b in enumerate(c):
                    if b == '1':
                        probT1WinComb = probT1WinComb * probT1WinCats[keys[ind]]
                    else:
                        probT1WinComb = probT1WinComb * (1 - probT1WinCats[keys[ind]])
                probT1Win += probT1WinComb
            probT1Win = 100 * probT1Win
            print('Chance for %s to win: %3.5f ' % (t1Name, probT1Win) + '%')
            print('Chance for %s to win: %3.5f ' % (t2Name, 100 - probT1Win) + '%')

    # analyze the rest of this week
    #prints out the expected category values needed to make up each category in a week given the predicted outcomes
    def analyzeThisWeek(self):
        neg_cats = ['L', 'BAA', 'ERA', 'WHIP']
        matchups = self.matchUpResults[self.matchUpResults['weekId'] == self.currentWeekId]
        matchups = self.calculateWeekRates(matchups)
        weekProjections = self.calculateRestOfWeekProjections(matchups)
        mIds = list(set(matchups['gameId']))
        differences = pd.DataFrame()
        for m in mIds:
            matchup = weekProjections[weekProjections['gameId'] == m]
            differences = differences.append(self.calculateMatchUpDifferences(matchup), ignore_index=True)
        for id in list(matchups['teamId']):
            teamName = self.getTeamName(id)
            print('\n' + teamName)
            for c in list(matchup.columns)[4:28]:
                row = differences[differences['teamId'] == id]
                if c in neg_cats:
                    if row.iloc[0][c] < 0:
                        pass
                    else:
                        print('To win {0}, {1} needs to improve {2} by {3} over the course of the week'
                              .format(c, teamName, c, row.iloc[0][c]))
                else:
                    if row.iloc[0][c] > 0:
                        pass
                    else:
                        print('To win {0}, {1} needs to improve {2} by {3} over the course of the week'
                              .format(c, teamName, c, -row.iloc[0][c]))
            print('\n')
        return differences

    # calculate P(X>Y) given avg, std, and correlation of X and Y
    def calculateProbabiltyRelationship(self, avg1, avg2, std1, std2):
        muD = avg2 - avg1
        stdD = std1 ** 2 + std2 ** 2
        if stdD != 0:
            Z = (-1 * muD) / scipy.sqrt(stdD)
            prob = st.norm.cdf(Z)
        else:
            prob = 0.5
        return prob

    #calculate all possible win possibilities (2**22)
    def possibleWins(self, num):
        for i in range(2 ** num):
            b = bin(i)
            if b.count('1') > 11:
                b = b[b.find('b') + 1:]
                while (len(b) < 22):
                    b = '0' + b
                yield b

    #calculate the season average for each catagory for each team
    def calculateTeamAverages(self, teamId):
        teamResults = self.matchUpResults[
            (self.matchUpResults['teamId'] == teamId) & (self.matchUpResults['weekId'] < self.currentWeekId)]
        trDescribe = teamResults.describe()
        avg = trDescribe.loc['mean']
        std = trDescribe.loc['std']

        return avg, std

    #calculate the differences in each catagory between each team and their opponent
    def calculateMatchUpDifferences(self, matchup):
        dif = matchup.copy()
        cols = list(matchup.columns)[4:28]
        inds = list(matchup.index)
        for c in cols:
            dif.loc[inds[0], c] = matchup.loc[inds[0], c] - matchup.loc[inds[1], c]
            dif.loc[inds[1], c] = matchup.loc[inds[1], c] - matchup.loc[inds[0], c]

        return dif

    #calculates predicted values for the end of the week
    def calculateRestOfWeekProjections(self, matchups):
        ratios = ['AVG', 'OBP', 'SLG', 'BAA', 'ERA', 'WHIP', 'K/9']
        daysLeft = self.matchDaysLeft()
        cols = list(matchups.columns)
        info = cols[:4]
        stats = cols[4:28]
        rates = cols[32:]
        projections = matchups.loc[:, info + stats].copy()
        for i, cat in enumerate(stats):
            if cat not in ratios:
                projections[cat] = projections[cat] + matchups[rates[i]] * daysLeft
        return projections

    #calculates the rates for the week so far
    def calculateWeekRates(self, matchups):
        ratios = ['AVG', 'OBP', 'SLG', 'BAA', 'ERA', 'WHIP', 'K/9']
        cols = list(matchups.columns)[4:28]

        daysPassed = self.matchDaysFinished()
        if daysPassed > 0:
            for col in cols:
                col_ratio = col + '_ratio'
                if col in ratios:
                    matchups[col_ratio] = matchups[col]
                else:
                    matchups[col_ratio] = matchups[col] / daysPassed
        return matchups

    #calculate the number of days left in a matchup
    def matchDaysLeft(self):
        now = datetime.datetime.now()
        matchDates = self.leagueScheduleDates[self.leagueScheduleDates['weekId'] == self.currentWeekId]
        endDate = datetime.datetime.strptime(list(matchDates['end'])[0], '%m/%d/%y')
        return int((endDate - now).days) + 1

    #calculate the number of days finished in a matchup
    def matchDaysFinished(self):
        now = datetime.datetime.now()
        matchDates = self.leagueScheduleDates[self.leagueScheduleDates['weekId'] == self.currentWeekId]
        startDate = datetime.datetime.strptime(list(matchDates['start'])[0], '%m/%d/%y')
        return int((now - startDate).days) + 1





    #############################################################################
    #                                                                           #
    #                                                                           #
    #                           GETTERS, SETTERS, UPDATERS                      #
    #                                                                           #
    #                                                                           #
    #############################################################################

    #return a team name
    def getTeamName(self, id):
        return self.teams[self.teams['teamId'] == id].iloc[0]['Name']

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

    def getCurrentWeekId(self):
        return self.currentWeekId

    def getLeagueScheduleDates(self):
        return self.leagueScheduleDates


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

    def setCurrentWeekId(self, weekId):
        self.currentWeekId = weekId

    def setLeagueScheduleDates(self, leagueScheduleDates):
        self.leagueScheduleDates = leagueScheduleDates

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