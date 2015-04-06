__author__ = 'Ryan'
import FBB_League
from Scrape_espn_league import *
import pandas as pd
import pickle
import numpy as np

def main():
    with open('NCB.pickle', 'rb') as handle:
        NCB = pickle.load(handle)
    ARB, ARP = scrapeTeamPlayers('123478', '2015', NCB.getTeams())
    NCB.setBatterRosters(ARB)
    NCB.setPitcherRosters(ARP)
    projections = NCB.projectTeams()
    projections.sort('Zscore', ascending=True, inplace=True)
    projections.to_csv('Data/League_Projections.csv')
    BatterProjections = NCB.getBatterProjections()
    BatterProjections.to_csv('Data/Hitter_Projections.csv')
    PitcherProjections = NCB.getPitcherProjections()
    PitcherProjections.to_csv('Data/Pitcher_Projections.csv')
    with open('NCB.pickle', 'wb') as handle:
        pickle.dump(NCB, handle)

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
    """


main()