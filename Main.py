__author__ = 'Ryan'
import FBB_League
from Scrape_espn_league import *
import pandas as pd
import pickle
import numpy as np

def main():
    Scrape = ESPN_Scrape()
    NCB = FBB_League.FBB_League('123478', '2015')
    NCB = updateLeague(NCB)
    NCB.analyizeWeek(2)

    """
    with open('NCB.pickle', 'rb') as handle:
        NCB = pickle.load(handle)
    projections = NCB.projectTeams()
    projections.sort('Zscore', ascending=True, inplace=True)
    print(projections)
    print('\n\n\n')
    with open('NCB.pickle', 'wb') as handle:
        pickle.dump(NCB, handle)
    """
    """
    NCB = FBB_League.FBB_League('123478', '2015')
    hitters = pd.read_csv('Data/Hitters_projections.csv', index_col=0)
    pitchers = pd.read_csv('Data/Pitchers_projections.csv', index_col=0)
    teams = pd.read_csv('Data/NCB_teams.csv', index_col=0)

    NCB.setBatterProjections(hitters)
    NCB.setPitcherProjections(pitchers)
    NCB.setTeams(teams)
    ARB, ARP = scrapeTeamPlayers('123478', '2015', teams)
    NCB.setBatterRosters(ARB)
    NCB.setPitcherRosters(ARP)
    NCB.calculateBatterZScores()
    NCB.calcualtePitcherZScores()
    NCB.getBatterProjections().to_csv('Data/new_Bprojectections.csv')
    NCB.getPitcherProjections().to_csv('Data/new_Pprojectections.csv')

    with open('NCB.pickle', 'wb') as handle:
        pickle.dump(NCB, handle)

    ARB, ARP = scrapeTeamPlayers('123478', '2015', NCB.getTeams())
    NCB.setBatterRosters(ARB)
    NCB.setPitcherRosters(ARP)
    curHitters, curPitchers = scrapePlayerSeason('123478', '2015')
    NCB.setHitters(curHitters)
    NCB.setPitchers(curPitchers)
    projections = NCB.projectTeams()
    projections.sort('Zscore', ascending=True, inplace=True)
    """


def updateLeague(league):
    Scrape = ESPN_Scrape()
    hitters = pd.read_csv('Data/Hitter_projections.csv', index_col=0)
    pitchers = pd.read_csv('Data/Pitcher_projections.csv', index_col=0)
    teams = Scrape.scrapeLeagueTeams(league.getLeagueId(), league.getYear())
    matchups = Scrape.scrapeMatchupResults(league.getLeagueId(), league.getYear())
    ARB, ARP = Scrape.scrapeTeamPlayers(league.getLeagueId(), league.getYear(), teams)
    curHitters, curPitchers = Scrape.scrapePlayerSeason(league.getLeagueId(), league.getYear())
    matchupBatters, matchupPitchers = Scrape.scrapeMatchupPlayers(league.getLeagueId(), league.getYear())

    league.setBatterProjections(hitters)
    league.setPitcherProjections(pitchers)
    league.setTeams(teams)
    league.setBatterRosters(ARB)
    league.setPitcherRosters(ARP)
    league.setBatters(curHitters)
    league.setPitchers(curPitchers)
    league.setMatchUpResults(matchups)
    league.setMatchUpBatters(matchupBatters)
    league.setMatchUpPitchers(matchupPitchers)
    return league
main()