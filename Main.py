__author__ = 'Ryan'
import FBB_League
from Scrape_espn_league import *
import pandas as pd


def main():
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


main()