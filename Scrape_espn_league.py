__author__ = 'Ryan'
from bs4 import *
import pandas as pd
import requests
import pickle
from robobrowser import RoboBrowser
from espn_login import *
import datetime
import math


class ESPN_Scrape:
    def __init__(self):
        self.logged_in = False
        self.espn_header = {'1/0': 'H/AB'}
        self.br = RoboBrowser(history=True)

    def loginToESPN(self, leagueID, year):
        if not self.logged_in:
            link = 'http://games.espn.go.com/flb/leagueoffice?leagueId=' + str(leagueID) + '&seasonId=' + str(year)
            self.br = RoboBrowser(history=True)
            self.br.open(link)
            try:
                form = self.br.get_form(action="https://r.espn.go.com/espn/memberservices/pc/login")
                username = input('ESPN Username: \n')
                password = input('ESPN Password: \n')
                form['username'].value = username
                form['password'].value = password
                self.br.submit_form(form)
                self.logged_in = True
                print('\nLogging In\n')
            except:
                print('\nLogin FailedS!\n')


    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def nameToBatPos(self, d):
        # BatPos = ['Catcher', 'First Base', 'Second Base', 'Third Base', 'Shortstop', 'Left Field', 'Center Field', 'Right Field', 'Designated Hitter']
        s = d.text.format('ascii')
        name = self.getPlayerName(s)
        s = s[s.find(',') + 2:]
        pID = self.getPlayerID(d)
        team = s[:s.find('\xa0')]
        pos = s[s.find('\xa0') + 1:]
        posOut = self.getBatPositions(pos)
        return [pID, name, team] + posOut

    def nameToPlayer(self, d):
        s = d.text.format('ascii')
        name = self.getPlayerName(s)
        s = s[s.find(',') + 2:]
        pID = self.getPlayerID(d)
        team = self.getPlayerTeam(s)
        return [pID, name, team]

    def getPlayerName(self, s):
        return s[:s.find(',')]


    def getPlayerID(self, d):
        return d.find_all('a')[0]['playerid']

    def getPlayerTeam(self, s):
        return s[:s.find('\xa0')]


    def getBatPositions(self, s):
        posOut = [None] * 9
        if 'SSPD' in s:
            s = s.replace('SSPD', '')
        if '1B' in s:
            posOut[1] = 1
            s = s.replace('1B', '')
        if '2B' in s:
            posOut[2] = 1
            s = s.replace('2B', '')
        if '3B' in s:
            posOut[3] = 1
            s = s.replace('3B', '')
        if 'SS' in s:
            posOut[4] = 1
            s = s.replace('SS', '')
        if 'LF' in s:
            posOut[5] = 1
            s = s.replace('LF', '')
        if 'CF' in s:
            posOut[6] = 1
            s = s.replace('CF', '')
        if 'RF' in s:
            posOut[7] = 1
            s = s.replace('RF', '')
        if 'DH' in s:
            posOut[8] = 1
            s = s.replace('DH', '')
        if 'C' in s:
            posOut[0] = 1
            s = s.replace('C', '')
        return posOut

    def splitHAB(self, s):
        hits = s[:s.find('/')]
        ab = s[s.find('/') + 1:]
        if self.is_number(hits):
            hits = float(hits)
        else:
            hits = 0
        if self.is_number(ab):
            ab = float(ab)
        else:
            ab = 0
        return [hits, ab]

    def nameToPitchPos(self, d):
        # ['Starting Pitcher', 'Relief Pitcher']
        s = d.text.format('ascii')
        name = s[:s.find(',')]
        s = str(s[s.find(',') + 2:])
        pID = d.find_all('a')[0]['playerid']
        team = s[:s.find('\xa0')]
        pos = s[s.find('\xa0') + 1:]
        posOut = self.getPitchPositions(pos)
        return [pID, name, team] + posOut

    def getPitchPositions(self, s):
        posOut = [None] * 2
        if 'SSPD' in s:
            s = s.replace('SSPD', '')
        if 'SP' in s:
            posOut[0] = 1
            s = s.replace('SP', '')
        if 'RP' in s:
            posOut[1] = 1
            s = s.replace('RP', '')
        return posOut

    def tableToBatters(self, table):
        Hitters = pd.DataFrame()
        rows = table.find_all('tr')
        rows = rows[2:]
        for r in rows:
            data = r.find_all('td')
            data = [data[0]] + data[8:20]
            row_data = []
            for i, d in enumerate(data):
                if i == 0:
                    row_data = self.nameToBatPos(d)
                elif '/' in d.text:
                    row_data += self.splitHAB(d.text)
                else:
                    if self.is_number(d.text):
                        row_data.append(float(d.text))
                    else:
                        row_data.append(0)
            Hitters = Hitters.append(pd.Series(row_data), ignore_index=True)
        return Hitters

    def tableToPitchers(self, table):
        Pitchers = pd.DataFrame()
        rows = table.find_all('tr')
        rows = rows[2:]
        for r in rows:
            data = r.find_all('td')
            data = [data[0]] + data[8:24]
            row_data = []
            for i, d in enumerate(data):
                if i == 0:
                    row_data = self.nameToPitchPos(d)
                else:
                    if self.is_number(d.text):
                        row_data.append(float(d.text))
                    else:
                        row_data.append(0)
            Pitchers = Pitchers.append(pd.Series(row_data), ignore_index=True)
        return Pitchers


    def scrapePlayerProjections(self, leagueID, year):
        self.loginToESPN(leagueID, year)
        Hitters = pd.DataFrame()
        HitPos = ['Catcher', 'First Base', 'Second Base', 'Third Base', 'Shortstop', 'Left Field', 'Center Field',
                  'Right Field', 'Designated Hitter']
        Pitchers = pd.DataFrame()
        PitchPos = ['Starting Pitcher', 'Relief Pitcher']
        thead = []
        index = 0
        # get batter values
        self.br.open('http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
            year) + '&context=freeagency&view=stats&version=projections&startIndex=0&avail=-1&startIndex=' + str(index))
        table = self.br.find_all('table', class_='playerTableTable tableBody')[0]
        rows = table.find_all('tr')

        # get the column headers
        header = rows[1]
        data = header.find_all('td')
        data = [data[0]] + data[8:20]
        for d in data:
            txt = d.text.replace('\xa0', '')
            thead.append(txt.format('ascii'))
        thead[0] = 'PlayerId'
        if 'H/AB' in thead:
            ind = thead.index('H/AB')
            thead[ind] = 'AB'  #AB stored in ind+1
            thead.insert(ind, 'H')  #H stored in ind
        thead.insert(1, 'Team')
        thead.insert(1, 'Name')
        thead = thead[0:3] + HitPos + thead[3:]
        #get player projections
        while index < 250:
            self.br.open(
                'http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
                    year) + '&context=freeagency&view=stats&version=projections&avail=-1&startIndex=' + str(index))
            table = self.br.find_all('table', class_='playerTableTable tableBody')[0]
            Hitters = Hitters.append(self.tableToBatters(table), ignore_index=True)
            index += 50
        Hitters.columns = thead
        index = 0


        # get Pitchers
        self.br.open('http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
            year) + '&context=freeagency&view=stats&version=projections&avail=-1&slotCategoryGroup=2&startIndex=' + str(
            index))
        table = self.br.find_all('table', class_='playerTableTable tableBody')[0]
        rows = table.find_all('tr')

        # get the column headers
        thead = []
        header = rows[1]
        data = header.find_all('td')
        data = [data[0]] + data[8:24]
        for d in data:
            txt = d.text.replace('\xa0', '')
            thead.append(txt.format('ascii'))
        thead[0] = 'PlayerId'
        thead.insert(1, 'Team')
        thead.insert(1, 'Name')
        thead = thead[0:3] + PitchPos + thead[3:]
        #get player projections
        while index < 250:
            self.br.open(
                'http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
                    year) + '&context=freeagency&view=stats&version=projections&avail=-1&slotCategoryGroup=2&startIndex=' + str(
                    index))
            table = self.br.find_all('table', class_='playerTableTable tableBody')[0]
            Pitchers = Pitchers.append(self.tableToPitchers(table), ignore_index=True)
            index += 50
        Pitchers.columns = thead

        return Hitters, Pitchers


    def scrapePlayerSeason(self, leagueID, year):
        self.loginToESPN(leagueID, year)
        Hitters = pd.DataFrame()
        HitPos = ['Catcher', 'First Base', 'Second Base', 'Third Base', 'Shortstop', 'Left Field', 'Center Field',
                  'Right Field', 'Designated Hitter']
        Pitchers = pd.DataFrame()
        PitchPos = ['Starting Pitcher', 'Relief Pitcher']
        thead = []
        index = 0
        # get batter values
        self.br.open('http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
            year) + '&context=freeagency&view=stats&version=currSeason&startIndex=0&avail=-1&startIndex=' + str(index))
        table = self.br.find_all('table', class_='playerTableTable tableBody')[0]
        rows = table.find_all('tr')

        # get the column headers
        header = rows[1]
        data = header.find_all('td')
        data = [data[0]] + data[8:20]
        for d in data:
            txt = d.text.replace('\xa0', '')
            thead.append(txt.format('ascii'))
        thead[0] = 'PlayerId'
        if 'H/AB' in thead:
            ind = thead.index('H/AB')
            thead[ind] = 'AB'  # AB stored in ind+1
            thead.insert(ind, 'H')  # H stored in ind
        thead.insert(1, 'Team')
        thead.insert(1, 'Name')
        thead = thead[0:3] + HitPos + thead[3:]
        # get player projections
        while index < 250:
            self.br.open(
                'http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
                    year) + '&context=freeagency&view=stats&version=currSeason&avail=-1&startIndex=' + str(index))
            table = self.br.find_all('table', class_='playerTableTable tableBody')[0]
            Hitters = Hitters.append(self.tableToBatters(table), ignore_index=True)
            index += 50
        Hitters.columns = thead
        index = 0


        # get Pitchers
        self.br.open('http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
            year) + '&context=freeagency&view=stats&version=currSeason&avail=-1&slotCategoryGroup=2&startIndex=' + str(
            index))
        table = self.br.find_all('table', class_='playerTableTable tableBody')[0]
        rows = table.find_all('tr')

        # get the column headers
        thead = []
        header = rows[1]
        data = header.find_all('td')
        data = [data[0]] + data[8:24]
        for d in data:
            txt = d.text.replace('\xa0', '')
            thead.append(txt.format('ascii'))
        thead[0] = 'PlayerId'
        thead.insert(1, 'Team')
        thead.insert(1, 'Name')
        thead = thead[0:3] + PitchPos + thead[3:]
        #get player projections
        while index < 250:
            self.br.open(
                'http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
                    year) + '&context=freeagency&view=stats&version=currSeason&avail=-1&slotCategoryGroup=2&startIndex=' + str(
                    index))
            table = self.br.find_all('table', class_='playerTableTable tableBody')[0]
            Pitchers = Pitchers.append(self.tableToPitchers(table), ignore_index=True)
            index += 50
        Pitchers.columns = thead

        return Hitters, Pitchers


    def scrapeTeamPlayers(self, leagueID, year, teams):
        self.loginToESPN(leagueID, year)

        teamBatters = pd.DataFrame()
        teamPitchers = pd.DataFrame()

        urls = list(teams['Link'])
        for u in urls:
            self.br.open('http://games.espn.go.com' + u)
            teamId = teams[teams['Link'] == u].iloc[0]['teamId']
            # batters
            Btable = self.br.find_all('table', class_='playerTableTable tableBody')[0]
            rows = Btable.find_all('tr')
            rows = rows[2:]
            for r in rows:
                d = r.find_all('td')[1]
                if d.find_all('a'):
                    pID = int(self.getPlayerID(d))
                    teamBatters = teamBatters.append(pd.Series([teamId, pID]), ignore_index=True)



            # pitchers
            Ptable = self.br.find_all('table', class_="playerTableTable tableBody playerTableMoreTable")[0]
            rows = Ptable.find_all('tr')
            rows = rows[2:]
            for r in rows:
                d = r.find_all('td')[1]
                if d.find_all('a'):
                    pID = int(self.getPlayerID(d))
                    teamPitchers = teamPitchers.append(pd.Series([teamId, pID]), ignore_index=True)

        teamBatters.columns = ['teamId', 'playerId']
        teamPitchers.columns = ['teamId', 'playerId']
        return teamBatters, teamPitchers


    # data frame containing all of te results for each weeks matchups
    # [weekID, gameID, teamID, H, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG,
    # K, QS, CG, SO, W, L, SV, HD, BAA, ERA, WHIP, K/9, Wins, Losses, Ties, H/A]

    def scrapeMatchupResults(self, leagueId, year):
        matchups = pd.DataFrame()
        week = self.currentWeek()
        weeks = [i for i in range(1, week + 1)]
        for w in weeks:
            matchups = matchups.append(self.scrapeMatchUpWeek(leagueId, year, w), ignore_index=True)
        return matchups


    # data frame containing all of the results for one weeks matchups
    # [weekID, gameID, teamID, H, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG,
    # K, QS, CG, SO, W, L, SV, HD, BAA, ERA, WHIP, K/9, Wins, Losses, Ties, H/A]
    def scrapeMatchUpWeek(self, leagueId, year, weekId):
        matchupWeek = pd.DataFrame()
        self.loginToESPN(leagueId, year)
        link = 'http://games.espn.go.com/flb/scoreboard?leagueId=' + str(leagueId) + '&seasonId=' + str(
            year) + '&matchupPeriodId=' + str(weekId)
        self.br.open(link)
        table = self.br.find_all('table', class_='tableBody')
        table = table[0]
        rows = table.find_all('tr')
        head = rows[1].find_all('th')
        header = [h.text for h in head]
        while '' in header:
            header.remove('')
        header = header[1:-1]
        header.insert(0, 'Name')
        header.insert(0, 'teamId')
        header.insert(0, 'gameId')
        header.insert(0, 'weekId')
        header.append('Wins')
        header.append('Losses')
        header.append('Ties')
        header.append('H/A')
        stats = rows[2:]
        count = 0
        for r in stats:
            data_row = []
            teamRow = r.find_all('td', class_='teamName')
            if teamRow:
                name = self.teamNameToRow(teamRow[0])
                data = r.find_all('td')
                for d in data:
                    if self.is_number(d.text):
                        data_row.append(float(d.text))
                score = self.scoreToList(data[-1].text)
                out = [weekId, 6 * (weekId - 1) + math.floor(count / 2)] + name[:2] + data_row + score + [count % 2]
                matchupWeek = matchupWeek.append(pd.Series(out), ignore_index=True)
                count += 1
        matchupWeek.columns = header
        return matchupWeek


    def scoreToList(self, s):
        wins = float(s[:s.find('-')])
        s = s[s.find('-') + 1:]
        losses = float(s[:s.find('-')])
        ties = float(s[s.find('-') + 1:])
        return [wins, losses, ties]


    # takes current date and find the current week
    def currentWeek(self):
        weekIds = pd.read_csv('Data/weekId.csv', index_col=0)
        now = datetime.datetime.now()
        weekEnds = list(weekIds['end'])
        for i, w in enumerate(weekEnds):
            dt = datetime.datetime.strptime(w, '%m/%d/%y')
            if dt > now:
                return i + 1
        return i + 1


    # data frame containing all of the matchups
    # [weekID, gameID, teamID, H/A]
    def scrapeLeagueSchedule(self, leagueId, year):
        schedule = pd.DataFrame()
        self.loginToESPN(leagueId, year)
        weekId = 0
        gameId = 0
        while weekId < 22:
            link = 'http://games.espn.go.com/flb/scoreboard?leagueId=' + str(leagueId) + '&seasonId=' + str(
                year) + '&matchupPeriodId=' + str(weekId)
            self.br.open(link)
            table = self.br.find_all('table', class_='tableBody')
            table = table[0]
            rows = table.find_all('tr')
            count = 0
            for r in rows:
                data = r.find_all('td', class_='teamName')
                for d in data:
                    name_row = self.teamNameToRow(d)
                    homeAway = count % 2
                    schedule = schedule.append(pd.Series([weekId, gameId, name_row[0], homeAway]), ignore_index=True)
                    count += 1
                    if count % 2 == 0:
                        gameId += 1
            weekId += 1
        schedule.columns = ['weekId', 'gameId', 'teamId', 'H/A']
        return schedule


    # return all matchups so far
    def scrapeMatchupPlayers(self, leagueId, year):
        batters = pd.DataFrame()
        pitchers = pd.DataFrame()
        week = self.currentWeek() - 1

        weeks = [i for i in range(1, week + 1)]
        for w in weeks:
            print(w)
            B, P = self.scrapeMatchupPlayersWeek(leagueId, year, w)
            batters = batters.append(B, ignore_index=True)
            pitchers = pitchers.append(P, ignore_index=True)
        return batters, pitchers

    # data frame containing player results for each matchup
    # both hitters and pitchers and their catagories
    def scrapeMatchupPlayersWeek(self, leagueId, year, week):
        matchupBatters = pd.DataFrame()
        matchupPitchers = pd.DataFrame()
        link = 'http://games.espn.go.com/flb/scoreboard?leagueId=' + str(leagueId) + '&seasonId=' + str(
            year) + '&matchupPeriodId=' + str(week)

        base = 'http://games.espn.go.com'
        self.loginToESPN(leagueId, year)
        self.br.open(link)
        links = self.br.find_all('a')
        bscores = []
        for l in links:
            if l.text == 'Full Box Score':
                bscores.append(base + l['href'])
        for bs in bscores:
            self.br.open(bs)
            tables = self.br.find_all('table', class_="playerTableTable tableBody")
            for i, t in enumerate(tables):
                if i % 2:  # Pitchers
                    matchupPitchers = matchupPitchers.append(self.scrapeMatchupPitchers(t), ignore_index=True)

                else:  # Batters
                    matchupBatters = matchupBatters.append(self.scrapeMatchupBatters(t), ignore_index=True)

        matchupBatters['weekId'] = week
        matchupPitchers['weekId'] = week
        return matchupBatters, matchupPitchers

    def scrapeMatchupBatters(self, table):
        batters = pd.DataFrame()
        rows = table.find_all('tr')
        head = rows[2].find_all('td')
        header = [h.text for h in head]
        header = header[2:]
        header[0] = 'PlayerId'
        if 'H/AB' in header:
            ind = header.index('H/AB')
            header[ind] = 'AB'  # AB stored in ind+1
            header.insert(ind, 'H')  # H stored in ind
        header.insert(1, 'Team')
        header.insert(1, 'Name')
        rows = rows[3:-1]
        for r in rows:
            data_row = r.find_all('td')
            data_row = [data_row[0]] + data_row[3:]
            row_data = []
            for i, d in enumerate(data_row):
                if i == 0:
                    row_data = self.nameToPlayer(d)
                elif '/' in d.text:
                    row_data += self.splitHAB(d.text)
                else:
                    if self.is_number(d.text):
                        row_data.append(float(d.text))
                    else:
                        row_data.append(0)
            batters = batters.append(pd.Series(row_data), ignore_index=True)
        batters.columns = header
        return batters

    def scrapeMatchupPitchers(self, table):
        pitchers = pd.DataFrame()
        rows = table.find_all('tr')
        head = rows[1].find_all('td')
        header = [h.text for h in head]
        header = header[2:]
        header[0] = 'PlayerId'
        header.insert(1, 'Team')
        header.insert(1, 'Name')
        rows = rows[3:-1]
        for r in rows:
            data_row = r.find_all('td')
            data_row = [data_row[0]] + data_row[3:]
            row_data = []
            for i, d in enumerate(data_row):
                if i == 0:
                    row_data = self.nameToPlayer(d)
                else:
                    if self.is_number(d.text):
                        row_data.append(float(d.text))
                    else:
                        row_data.append(0)
            pitchers = pitchers.append(pd.Series(row_data), ignore_index=True)
        pitchers.columns = header
        return pitchers

    # returns data frame containing
    # [teamID, teamName, shortName, wins, losses, draws]
    def scrapeLeagueTeams(self, leagueId, year):
        self.loginToESPN(leagueId, year)

        # dataframe will have the following columns:
        # [teamID, teamName, wins, losses, draws]
        teams = pd.DataFrame()

        self.br.open('http://games.espn.go.com/flb/standings?leagueId=' + str(leagueId) + '&seasonId=' + str(year))
        tables = self.br.find_all('table', class_='tableBody')
        tables = tables[:-1]
        for t in tables:
            row = t.find_all('tr')[2:]
            for r in row:
                data = r.find_all('td')
                name = data[0]
                name_row = self.teamNameToRow(name)
                wins = float(data[1].text)
                losses = float(data[2].text)
                draw = float(data[3].text)
                out = name_row + [wins, losses, draw]
                teams = teams.append(pd.Series(out), ignore_index=True)
        teams.columns = ['teamId', 'Name', 'Link', 'W', 'L', 'T']
        return teams


    def teamNameToRow(self, name):
        link = name.find_all('a')[0]['href']
        ID = link.split('&')[1]
        teamID = int(ID[ID.find('=') + 1:])
        teamName = name.text
        if teamName.find(' (') != -1:
            teamName = teamName[:teamName.find(' (')]

        return [teamID, teamName, link]


    def scrapeTeamStats(self, leagueID, year):
        self.loginToESPN(leagueID, year)

        # dataframe will have the following columns:
        # [teamID, teamName, wins, losses, draws]
        teamStats = pd.DataFrame()

        self.br.open('http://games.espn.go.com/flb/standings?leagueId=' + str(leagueID) + '&seasonId=' + str(year))
        tables = self.br.find_all('table', class_='tableBody')
        table = tables[-1]
        rows = table.find_all('tr')
        head = rows[2].find_all('td')
        header = [h.text for h in head]
        while '' in header:
            header.remove('')
        header.insert(0, 'Name')
        header.insert(0, 'teamId')
        stats = rows[3:]

        for r in stats:
            data_row = []
            data = r.find_all('td')
            name = self.teamNameToRow(data[1])
            data = data[2:-2]
            for d in data:
                if self.is_number(d.text):
                    data_row.append(float(d.text))
            out = name[:2] + data_row

            teamStats = teamStats.append(pd.Series(out), ignore_index=True)
        teamStats.columns = header
        return teamStats



"""
Hitters, Pitchers = scrapePlayerProjections('123478', '2015')
Hitters.to_csv('Data/Hitters_projections.csv')
Pitchers.to_csv('Data/Pitchers_projections.csv')
"""
"""
teams = pd.read_csv('NCB_teams.csv', index_col=0)
teamBatters, teamPitchers = scrapeTeamPlayers('123478', '2015', teams)
teamBatters.to_csv('activeRoster_batter.csv')
teamPitchers.to_csv('activeRoster_pitcher.csv')

#print(scrapeMatchupResults('123478', '2015'))
# week = currentWeek()
#print(scrapeMatchUpWeek('123478', '2015', week))
Scrape = ESPN_Scrape()
B, P = Scrape.scrapeMatchupPlayers('123478', '2015', 1)
print(B)

Scrape = ESPN_Scrape()
print(Scrape.currentWeek())
"""
