from nba_api.stats.static import players 
from nba_api.stats.endpoints import playercareerstats, playergamelog, leaguedashplayerstats
import pandas as pd

# get player ID based on player name
def get_player_id(player_name):
    player_dict = players.get_players()
    for player in player_dict:
        if player['full_name'] == player_name:
            return player['id']
    return None

# fetch player career stats (not needed here but might be useful in the future)
def fetch_player_stats(player_id):
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    career_df = career.get_data_frames()[0]
    return career_df

# fetch player game logs for a specific season
def fetch_player_gamelog(player_id, season):
    game_logs = playergamelog.PlayerGameLog(player_id=player_id, season=season)
    game_logs_df = game_logs.get_data_frames()[0]
    return game_logs_df

# fetch league stats for a specific season
def fetch_league_stats(season):
    league_stats = leaguedashplayerstats.LeagueDashPlayerStats(season=season)
    league_stats_df = league_stats.get_data_frames()[0]
    return league_stats_df

# calculate unadjusted PER for a player in a specific season
def calculate_uPER(stats):
    # check for all columns 
    required_columns = ['PTS', 'FGM', 'FTM', 'FG3M', 'AST', 'REB', 'OREB', 'DREB', 'BLK', 'STL', 'FGA', 'FTA', 'TOV', 'MIN']
    for col in required_columns:
        if col not in stats:
            stats[col] = 0

    uPER = (stats['PTS'] + stats['FGM'] + stats['FTM'] + stats['FG3M'] + stats['AST'] + stats['REB'] + stats['OREB'] + stats['DREB'] + stats['BLK'] + stats['STL']
        - (stats['FGA'] - stats['FGM']) - (stats['FTA'] - stats['FTM']) - stats['TOV']) / stats['MIN']
    return uPER

# adjust PER for pace (pace being the number of possessions per 48 minutes)
def adjust_for_pace(uPER, team_pace, league_pace):
    return uPER * (league_pace / team_pace)

# normalize PER to league average PER
def normalize_PER(uPER, league_avg_PER):
    return uPER * (15 / league_avg_PER)

# calculate PER for a player in a specific season
def calculate_PER(player_name, season):
    # Get player ID
    player_id = get_player_id(player_name)
    if not player_id:
        print(f"Player {player_name} not found")
        return
    
    # Fetch player game logs for the season
    game_logs = fetch_player_gamelog(player_id, season)
    
    # Aggregate the stats from the game logs
    aggregated_stats = game_logs[['PTS', 'FGM', 'FTM', 'FG3M', 'AST', 'REB', 'OREB', 'DREB', 'BLK', 'STL', 'FGA', 'FTA', 'TOV', 'MIN']].sum()
    
    # Calculate unadjusted 
    uPER = calculate_uPER(aggregated_stats)
    print(f"Unadjusted PER (uPER): {uPER}")

    # Fetch league stats for the season
    league_stats = fetch_league_stats(season)

    # Calculate league averages
    if 'PACE' in league_stats.columns:
        league_pace = league_stats['PACE'].mean()
    else:
        # Calculate league pace if not directly available (using formula: league_pace = ((FGA + 0.44 * FTA - OREB + TOV) / MIN).mean() * 48)
        league_pace = ((league_stats['FGA'] + 0.44 * league_stats['FTA'] - league_stats['OREB'] + league_stats['TOV']) / league_stats['MIN']).mean() * 48  # Assuming 48 minutes per game

    if 'PER' in league_stats.columns:
        league_avg_PER = league_stats['PER'].mean()
    else:
        # Calculate league average PER using available data (using formula: league_avg_PER = ((PTS + FGM + FTM + FG3M + AST + REB + OREB + DREB + BLK + STL - (FGA - FGM) - (FTA - FTM) - TOV) / MIN).mean())
        league_avg_PER = ((league_stats['PTS'] + league_stats['FGM'] + league_stats['FTM'] + league_stats['FG3M'] + league_stats['AST'] + league_stats['REB'] + league_stats['OREB'] + league_stats['DREB'] + league_stats['BLK'] + league_stats['STL']
            - (league_stats['FGA'] - league_stats['FGM']) - (league_stats['FTA'] - league_stats['FTM']) - league_stats['TOV']) / league_stats['MIN']).mean()

    print(f"League Pace: {league_pace}, League Avg PER: {league_avg_PER}")

    # Adjust and normalize PER 
    pace_adjusted_PER = adjust_for_pace(uPER, league_pace, league_pace)  
    normalized_PER = normalize_PER(pace_adjusted_PER, league_avg_PER)
    
    print(f"{player_name}'s PER: {normalized_PER}")

    # Save data to CSV files
    game_logs.to_csv(f"{player_name}_game_logs_{season}.csv", index=False)

# Example usage
calculate_PER('Tim Duncan', '2008-09')
calculate_PER('Russell Westbrook', '2016-17')
calculate_PER('Kevin Durant', '2016-17')