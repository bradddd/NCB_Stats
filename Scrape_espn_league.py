__author__ = 'Ryan'
from bs4 import BeautifulSoup
import pandas as pd
import requests
import pickle
from robobrowser import RoboBrowser
from espn_login import *
import datetime

espn_header = {'1/0': 'H/AB', '1/0': 'H/AB', }

def loginToESPN(leagueID, year):
    link = 'http://games.espn.go.com/flb/leagueoffice?leagueId='+str(leagueID)+'&seasonId='+str(year)
    br = RoboBrowser(history=True)
    br.open(link)
    try:
        form = br.get_form(action="https://r.espn.go.com/espn/memberservices/pc/login")
        username = input('ESPN Username: \n')
        password = input('ESPN Password: \n')
        form['username'].value = username
        form['password'].value = password
        br.submit_form(form)
        print('\nLogging In\n')
    except:
        print('\nNo need to login!\n')

    return br

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def nameToBatPos(d):
    #BatPos = ['Catcher', 'First Base', 'Second Base', 'Third Base', 'Shortstop', 'Left Field', 'Center Field', 'Right Field', 'Designated Hitter']
    s = d.text.format('ascii')
    name = getPlayerName(s)
    s = s[s.find(',')+2:]
    pID = getPlayerID(d)
    team = s[:s.find('\xa0')]
    pos = s[s.find('\xa0')+1:]
    posOut = getBatPositions(pos)
    return [pID, name, team] + posOut


def getPlayerName(s):
    return s[:s.find(',')]


def getPlayerID(d):
    return d.find_all('a')[0]['playerid']


def getBatPositions(s):
    posOut = [None]*9
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

def splitHAB(s):
    hits = s[:s.find('/')]
    ab = s[s.find('/')+1:]
    if is_number(hits):
        hits = float(hits)
    else:
        hits = 0
    if is_number(ab):
        ab = float(ab)
    else:
        ab = 0
    return [hits, ab]

def nameToPitchPos(d):
    #['Starting Pitcher', 'Relief Pitcher']
    s = d.text.format('ascii')
    name = s[:s.find(',')]
    s = str(s[s.find(',')+2:])
    pID = d.find_all('a')[0]['playerid']
    team = s[:s.find('\xa0')]
    pos = s[s.find('\xa0')+1:]
    posOut = getPitchPositions(pos)
    return [pID, name, team] + posOut

def getPitchPositions(s):
    posOut = [None]*2
    if 'SSPD' in s:
        s = s.replace('SSPD', '')
    if 'SP' in s:
        posOut[0] = 1
        s = s.replace('SP', '')
    if 'RP' in s:
        posOut[1] = 1
        s = s.replace('RP', '')
    return posOut

def tableToBatters(table):
    Hitters = pd.DataFrame()
    rows = table.find_all('tr')
    rows = rows[2:]
    for r in rows:
        data = r.find_all('td')
        data = [data[0]] + data[8:20]
        row_data = []
        for i, d in enumerate(data):
            if i == 0:
                row_data = nameToBatPos(d)
            elif '/' in d.text:
                row_data += splitHAB(d.text)
            else:
                if is_number(d.text):
                    row_data.append(float(d.text))
                else:
                    row_data.append(0)
        Hitters = Hitters.append(pd.Series(row_data), ignore_index=True)
    return Hitters

def tableToPitchers(table):
    Pitchers = pd.DataFrame()
    rows = table.find_all('tr')
    rows = rows[2:]
    for r in rows:
        data = r.find_all('td')
        data = [data[0]] + data[8:24]
        row_data = []
        for i, d in enumerate(data):
            if i == 0:
                row_data = nameToPitchPos(d)
            else:
                if is_number(d.text):
                    row_data.append(float(d.text))
                else:
                    row_data.append(0)
        Pitchers = Pitchers.append(pd.Series(row_data), ignore_index=True)
    return Pitchers


def scrapePlayerProjections(leagueID, year):
    br = loginToESPN(leagueID, year)
    Hitters = pd.DataFrame()
    HitPos = ['Catcher', 'First Base', 'Second Base', 'Third Base', 'Shortstop', 'Left Field', 'Center Field', 'Right Field', 'Designated Hitter']
    Pitchers = pd.DataFrame()
    PitchPos = ['Starting Pitcher', 'Relief Pitcher']
    thead = []
    index = 0
    #get batter values
    br.open('http://games.espn.go.com/flb/freeagency?leagueId='+str(leagueID)+'&teamId=1&seasonId='+str(year)+'&context=freeagency&view=stats&version=projections&startIndex=0&avail=-1&startIndex='+str(index))
    table = br.find_all('table', class_='playerTableTable tableBody')[0]
    rows = table.find_all('tr')

    #get the column headers
    header = rows[1]
    data = header.find_all('td')
    data = [data[0]] + data[8:20]
    for d in data:
        txt = d.text.replace('\xa0', '')
        thead.append(txt.format('ascii'))
    thead[0] = 'PlayerId'
    if 'H/AB' in thead:
        ind = thead.index('H/AB')
        thead[ind] = 'AB'   #AB stored in ind+1
        thead.insert(ind, 'H')  #H stored in ind
    thead.insert(1, 'Team')
    thead.insert(1, 'Name')
    thead = thead[0:3]+HitPos+thead[3:]
    #get player projections
    while index < 250:
        br.open('http://games.espn.go.com/flb/freeagency?leagueId='+str(leagueID)+'&teamId=1&seasonId='+str(year)+'&context=freeagency&view=stats&version=projections&avail=-1&startIndex='+str(index))
        table = br.find_all('table', class_='playerTableTable tableBody')[0]
        Hitters = Hitters.append(tableToBatters(table))
        index += 50
    Hitters.columns = thead
    index = 0


    #get Pitchers
    br.open('http://games.espn.go.com/flb/freeagency?leagueId='+str(leagueID)+'&teamId=1&seasonId='+str(year)+'&context=freeagency&view=stats&version=projections&avail=-1&slotCategoryGroup=2&startIndex='+str(index))
    table = br.find_all('table', class_='playerTableTable tableBody')[0]
    rows = table.find_all('tr')

    #get the column headers
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
    thead = thead[0:3]+PitchPos+thead[3:]
    #get player projections
    while index < 250:
        br.open('http://games.espn.go.com/flb/freeagency?leagueId='+str(leagueID)+'&teamId=1&seasonId='+str(year)+'&context=freeagency&view=stats&version=projections&avail=-1&slotCategoryGroup=2&startIndex='+str(index))
        table = br.find_all('table', class_='playerTableTable tableBody')[0]
        Pitchers = Pitchers.append(tableToPitchers(table))
        index += 50
    Pitchers.columns = thead

    return Hitters, Pitchers


def scrapePlayerSeason(leagueID, year):
    br = loginToESPN(leagueID, year)
    Hitters = pd.DataFrame()
    HitPos = ['Catcher', 'First Base', 'Second Base', 'Third Base', 'Shortstop', 'Left Field', 'Center Field',
              'Right Field', 'Designated Hitter']
    Pitchers = pd.DataFrame()
    PitchPos = ['Starting Pitcher', 'Relief Pitcher']
    thead = []
    index = 0
    # get batter values
    br.open('http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
        year) + '&context=freeagency&view=stats&version=currSeason&startIndex=0&avail=-1&startIndex=' + str(index))
    table = br.find_all('table', class_='playerTableTable tableBody')[0]
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
        br.open('http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
            year) + '&context=freeagency&view=stats&version=currSeason&avail=-1&startIndex=' + str(index))
        table = br.find_all('table', class_='playerTableTable tableBody')[0]
        Hitters = Hitters.append(tableToBatters(table))
        index += 50
    Hitters.columns = thead
    index = 0


    #get Pitchers
    br.open('http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
        year) + '&context=freeagency&view=stats&version=currSeason&avail=-1&slotCategoryGroup=2&startIndex=' + str(
        index))
    table = br.find_all('table', class_='playerTableTable tableBody')[0]
    rows = table.find_all('tr')

    #get the column headers
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
        br.open('http://games.espn.go.com/flb/freeagency?leagueId=' + str(leagueID) + '&teamId=1&seasonId=' + str(
            year) + '&context=freeagency&view=stats&version=currSeason&avail=-1&slotCategoryGroup=2&startIndex=' + str(
            index))
        table = br.find_all('table', class_='playerTableTable tableBody')[0]
        Pitchers = Pitchers.append(tableToPitchers(table))
        index += 50
    Pitchers.columns = thead

    return Hitters, Pitchers


def scrapeTeamPlayers(leagueID, year, teams):
    br = loginToESPN(leagueID, year)

    teamBatters = pd.DataFrame()
    teamPitchers = pd.DataFrame()

    urls = list(teams['Link'])
    for u in urls:
        br.open('http://games.espn.go.com' + u)
        teamId = teams[teams['Link'] == u].iloc[0]['teamId']
        # batters
        Btable = br.find_all('table', class_='playerTableTable tableBody')[0]
        rows = Btable.find_all('tr')
        rows = rows[2:]
        for r in rows:
            d = r.find_all('td')[1]
            if d.find_all('a'):
                pID = int(getPlayerID(d))
                teamBatters = teamBatters.append(pd.Series([teamId, pID]), ignore_index=True)



        #pitchers
        Ptable = br.find_all('table', class_="playerTableTable tableBody playerTableMoreTable")[0]
        rows = Ptable.find_all('tr')
        rows = rows[2:]
        for r in rows:
            d = r.find_all('td')[1]
            if d.find_all('a'):
                pID = int(getPlayerID(d))
                teamPitchers = teamPitchers.append(pd.Series([teamId, pID]), ignore_index=True)

    teamBatters.columns = ['teamId', 'playerId']
    teamPitchers.columns = ['teamId', 'playerId']
    return teamBatters, teamPitchers


# data frame containing all of te results for each weeks matchups
#[weekID, gameID, teamID, H, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG,
# K, QS, CG, SO, W, L, SV, HD, BAA, ERA, WHIP, K/9, Wins, Losses, Ties, H/A]

def scrapeMatchupResults(leagueId, year):
    matchups = pd.DataFrame()
    week = currentWeek()
    weeks = [i for i in range(1, week + 1)]
    for w in weeks:
        matchups.append(scrapeMatchUpWeek(leagueId, year, week))
    return matchups


# data frame containing all of the results for one weeks matchups
# [weekID, gameID, teamID, H, R, 2B, 3B, HR, XBH, RBI, BB, SB, AVG, OBP, SLG,
# K, QS, CG, SO, W, L, SV, HD, BAA, ERA, WHIP, K/9, Wins, Losses, Ties, H/A]
def scrapeMatchUpWeek(leagueId, year, weekId):
    matchupWeek = pd.DataFrame()
    br = loginToESPN(leagueId, year)
    link = 'http://games.espn.go.com/flb/scoreboard?leagueId=' + str(leagueId) + '&seasonId=' + str(
        year) + '&matchupPeriodId=' + str(weekId)
    br.open(link)
    table = br.find_all('table', class_='tableBody')
    table = table[0]
    rows = table.find_all('tr')
    head = rows[1].find_all('th')
    header = [h.text for h in head]
    while '' in header:
        header.remove('')
    header = header[1:-1]
    header.insert(0, 'Name')
    header.insert(0, 'teamId')
    header.append('Wins')
    header.append('Losses')
    header.append('Ties')
    stats = rows[2:]

    for r in stats:
        data_row = []
        teamRow = r.find_all('td', class_='teamName')
        if teamRow:
            name = teamNameToRow(teamRow[0])
            data = r.find_all('td')
            for d in data:
                if is_number(d.text):
                    data_row.append(float(d.text))
            score = scoreToList(data[-1].text)
            out = name[:2] + data_row + score
            matchupWeek = matchupWeek.append(pd.Series(out), ignore_index=True)
    matchupWeek.columns = header
    return matchupWeek


def scoreToList(s):
    wins = int(s[:s.find('-')])
    s = s[s.find('-') + 1:]
    losses = int(s[:s.find('-')])
    ties = int(s[s.find('-') + 1:])
    return [wins, losses, ties]


# takes current date and find the current week
def currentWeek():
    weekIds = pd.read_csv('Data/weekId.csv', index_col=0)
    now = datetime.datetime.now()
    weekEnds = list(weekIds['end'])
    for i, w in enumerate(weekEnds):
        dt = datetime.datetime.strptime(w, '%m/%d/%y')
        if now > dt:
            return i + 1
    return i + 1


# data frame containing all of the matchups
# [weekID, gameID, teamID, H/A]
def scrapeLeagueSchedule(leagueId, year):
    schedule = pd.DataFrame()
    br = loginToESPN(leagueId, year)
    weekId = 0
    gameId = 0
    while weekId < 22:
        link = 'http://games.espn.go.com/flb/scoreboard?leagueId=' + str(leagueId) + '&seasonId=' + str(
            year) + '&matchupPeriodId=' + str(weekId)
        br.open(link)
        table = br.find_all('table', class_='tableBody')
        table = table[0]
        rows = table.find_all('tr')
        count = 0
        for r in rows:
            data = r.find_all('td', class_='teamName')
            for d in data:
                name_row = teamNameToRow(d)
                homeAway = count % 2
                schedule = schedule.append(pd.Series([weekId, gameId, name_row[0], homeAway]), ignore_index=True)
                count += 1
                if count % 2:
                    gameId += 1
        weekId += 1
    return schedule


# return all matchups so far


# data frame containing player results for each matchup
#both hitters and pitchers and their catagories
def scrapeMatchupPlayers(leagueId, year, week):
    pass

# returns data frame containing
# [teamID, teamName, shortName, wins, losses, draws]
def scrapeLeagueTeams(leagueID, year):
    br = loginToESPN(leagueID, year)

    # dataframe will have the following columns:
    #[teamID, teamName, wins, losses, draws]
    teams = pd.DataFrame()

    br.open('http://games.espn.go.com/flb/standings?leagueId=' + str(leagueID) + '&seasonId=' + str(year))
    tables = br.find_all('table', class_='tableBody')
    tables = tables[:-1]
    for t in tables:
        print('\nTABLE\n')
        row = t.find_all('tr')[2:]
        for r in row:
            data = r.find_all('td')
            name = data[0]
            name_row = teamNameToRow(name)
            wins = float(data[1].text)
            losses = float(data[2].text)
            draw = float(data[3].text)
            out = name_row + [wins, losses, draw]
            teams = teams.append(pd.Series(out), ignore_index=True)
    teams.columns = ['teamId', 'Name', 'Link', 'W', 'L', 'T']
    return teams


def teamNameToRow(name):
    link = name.find_all('a')[0]['href']
    ID = link.split('&')[1]
    teamID = int(ID[ID.find('=') + 1:])
    teamName = name.text
    teamName = teamName[:teamName.find(' (')]

    return [teamID, teamName, link]


def scrapeTeamStats(leagueID, year):
    br = loginToESPN(leagueID, year)

    # dataframe will have the following columns:
    #[teamID, teamName, wins, losses, draws]
    teamStats = pd.DataFrame()

    br.open('http://games.espn.go.com/flb/standings?leagueId=' + str(leagueID) + '&seasonId=' + str(year))
    tables = br.find_all('table', class_='tableBody')
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
        name = teamNameToRow(data[1])
        data = data[2:-2]
        for d in data:
            if is_number(d.text):
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
"""
scrapeMatchupPlayers('123478', '2015')
# week = currentWeek()
#print(scrapeMatchUpWeek('123478', '2015', week))