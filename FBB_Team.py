__author__ = 'Ryan'
import pandas as pd


class FBB_Team:
    def __init__(self, leagueId, year, teamId, teamName):
        # League ID
        self.leagueId = leagueId
        #League Year
        self.year = year
        #Team ID
        self.teamId = teamId
        #Name of Team
        self.teamName = teamName
        # data frame containing all of the batters and their year to date stats
        # [playerID, Name, Team, catcher, first base, second base, third base, shortstop,
        # left field, center field, right field, designated hitter
        # H, AB, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG]
        self.batters = pd.DataFrame()
        # data frame containing all of the batters and their projections
        # [playerID, Name, Team, catcher, first base, second base, third base, shortstop,
        # left field, center field, right field, designated hitter
        # H, AB, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG]
        self.batterProjections = pd.DataFrame()
        #
        self.pitchers = pd.DataFrame()
        #
        self.HittingPositions = ['Catcher', 'First Base', 'Second Base', 'Shortstop', 'Third Base', 'Left Field',
                                 'Center Field', 'Right Field']
        #
        self.OptimalLineup = {}
        for hp in self.HittingPositions:
            self.OptimalLineup[hp] = pd.DataFrame()
        self.OptimalLineup['Utility'] = pd.DataFrame()
        #
        self.teamScore = 0
        #
        self.schedule = pd.DataFrame()

    #
    def projectTeam(self):
        self.fillOptimalLineup()
        self.calcTeamScore()

    #
    def fillOptimalLineup(self):
        sum = 0
        ids = []
        multipos = pd.DataFrame()
        HitPosNeeded = self.HittingPositions.copy()
        for pos in self.HittingPositions:
            posHitters = self.batterProjections.loc[self.batterProjections[pos] == 1]
            if not posHitters.empty:
                posHitters = posHitters.sort('Zscore', ascending=True)
                topHit = pd.DataFrame()
                while not posHitters.empty:
                    row = posHitters.head(1)
                    posHitters = posHitters.drop(posHitters.index[0])
                    if self.multiplePositions(row):
                        if multipos.empty or not row.iloc[0]['PlayerId'] in list(multipos['PlayerId']):
                            multipos = multipos.append(row)
                    elif topHit.empty:
                        topHit = row
                        HitPosNeeded.remove(pos)
                    elif row.iloc[0]['Zscore'] > topHit.iloc[0]['Zscore']:
                        topHit = row
                self.OptimalLineup[pos] = topHit
        # filled all single position players, time to check multi-position players to see if they are better
        while not multipos.empty:
            row = multipos.head(1)
            multipos = multipos.drop(multipos.index[0])
            pos = self.findPlayerPos(row)
            bestPos = None
            bestDif = 0
            posStarter = pd.DataFrame()
            for p in pos:
                starter = self.OptimalLineup[p]
                if starter.empty:
                    bestPos = p
                    bestDif = row.iloc[0]['Zscore']
                else:
                    dif = row.iloc[0]['Zscore'] - starter.iloc[0]['Zscore']
                    if dif > bestDif:
                        bestDif = dif
                        bestPos = p
                        posStarter = starter
            if not posStarter.empty:

                multipos.append(posStarter)
                self.OptimalLineup[bestPos] = row
            elif bestPos:
                self.OptimalLineup[bestPos] = row
        starters = []
        for p in self.HittingPositions:
            starters.append(self.OptimalLineup[p].iloc[0]['PlayerId'])
        bench = self.batterProjections[~self.batterProjections['PlayerId'].isin(starters)]
        bench = bench.sort('Zscore', ascending=False)
        self.OptimalLineup['Utility'] = bench.head(1)

    #
    def multiplePositions(self, row):
        count = len(self.findPlayerPos(row))
        if count > 1:
            return True
        else:
            return False

    #
    def findPlayerPos(self, row):
        out = []
        for hp in self.HittingPositions:
            if row.iloc[0][hp] == 1:
                out.append(hp)
        return out

    #
    def zscoreStarters(self):
        score = 0
        for k in self.OptimalLineup.keys():
            score += self.OptimalLineup[k].iloc[0]['Zscore']
        return score

    #
    def zscorePitchers(self):
        return self.pitchers['Zscore'].sum()

    #
    def calcTeamScore(self):
        self.teamScore = self.zscoreStarters() + self.zscorePitchers()

    # ############################################################################
    #                                                                           #
    #                                                                           #
    #                           GETTERS, SETTERS, Printers                      #
    #                                                                           #
    #                                                                           #
    #############################################################################

    def printOptimalLineup(self):
        print('\n{0}\t{1}'.format(self.teamId, self.teamName))
        for k in self.HittingPositions:
            if not dict[k].empty:
                print('%-15.15s: %-25.25s %5.5f' % (k, dict[k].iloc[0]['Name'], dict[k].iloc[0]['Zscore']))
            else:
                print('%-15.15s: %-25.25s %5.5f' % (k, 'None', 0))
        k = 'Utility'
        print('%-15.15s: %-25.25s %5.5f' % (k, dict[k].iloc[0]['Name'], dict[k].iloc[0]['Zscore']))


    #############################################################################
    #                                                                           #
    #                                 Getters                                   #
    #                                                                           #
    #############################################################################

    def getLeagueId(self):
        return self.leagueId

    def getYear(self):
        return self.year

    def getTeamId(self):
        return self.teamId

    def getTeamName(self):
        return self.teamName

    def getBatters(self):
        return self.batters

    def getPitchers(self):
        return self.pitchers

    def getCatcher(self):
        return self.batters[self.batters['Catcher'] == 1]

    def getFirstBase(self):
        return self.batters[self.batters['First Base'] == 1]

    def getSecondBase(self):
        return self.batters[self.batters['Second Base'] == 1]

    def getShortstop(self):
        return self.batters[self.batters['Shortstop'] == 1]

    def getThirdBase(self):
        return self.batters[self.batters['Third Base'] == 1]

    def getRightField(self):
        return self.batters[self.batters['Right Field'] == 1]

    def getCenterField(self):
        return self.batters[self.batters['Center Field'] == 1]

    def getLeftField(self):
        return self.batters[self.batters['Left Field'] == 1]

    def getReliefPitchers(self):
        return self.pitchers[self.pitchers['Relief Pitcher'] == 1]

    def getStartingPitchers(self):
        return self.pitchers[self.pitchers['Starting Pitcher'] == 1]

    def getTeamScore(self):
        return self.teamScore

    def getTeamBattingScore(self):
        return self.zscoreStarters()

    def getTeamPitchingScore(self):
        return self.zscorePitchers()

    #############################################################################
    #                                                                           #
    #                                 Setters                                   #
    #                                                                           #
    #############################################################################

    def setLeagueId(self, leagueId):
        self.leagueId = leagueId

    def setYear(self, year):
        self.year = year

    def setTeamId(self, teamId):
        self.teamId = teamId

    def setTeamName(self, teamName):
        self.teamName = teamName

    def setBatters(self, batters):
        self.batters = batters

    def setPitchers(self, pitchers):
        self.pitchers = pitchers

