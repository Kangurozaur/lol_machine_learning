import cassiopeia as cass
import datetime
import pandas as pd
import sys


def print_newest_match(name: str,  region: str):

    summoner = cass.Summoner(name=name, region=region)

    match_history = summoner.match_history(queues={cass.Queue.ranked_solo_fives})
    match = match_history[0]
    print("Match ID:", match.id)

    print("Frame interval:", match.timeline.frame_interval)

    # The cumulative timeline property allows you to get some info about participants during the match.
    #  You access the cumulative timeline by providing the duration into the game that you want the info for.
    #  In this case, we're accessing the game at 15 minutes and 30 seconds.
    #  Some data is only available every one minute.
    for p in match.participants:
        p_state = p.cumulative_timeline[datetime.timedelta(minutes=15, seconds=30)]
        # You can also use a string instead of datetime.timedelta
        items = p_state.items
        wards_placed = 0
        for temp_event in p_state._processed_events:
            if temp_event.type == "WARD_PLACED":
                wards_placed += 1
        items = [item.name for item in items]
        skills = p_state.skills
        print("Player:", p.summoner.name)
        print("Champion:", p.champion.name)
        print("Items:", items)
        print("Skills:", skills)
        print("Kills:", p_state.kills)
        print("Deaths:", p_state.deaths)
        print("Assists:", p_state.assists)
        print("KDA:", p_state.kda)
        print("Level:", p_state.level)
        print("Position:", p_state.position)
        print("Exp:", p_state.experience)
        print("Number of objectives assisted in:", p_state.objectives)
        print("Wards placed:", wards_placed)
        print("Gold earned:", p_state.gold_earned)
        print("Current gold:", p_state.current_gold)
        print("CS:", p_state.creep_score)
        print("CS in jungle:", p_state.neutral_minions_killed)


def get_team_data(match, team, gameDuration, color, region):
    match.properties["blueFirstBlood"] = team.first_blood

    # Metrics to collect

    blueKills = 0
    blueDeaths = 0
    blueAssists = 0
    blueEliteMonsters = 0
    blueDragons = 0
    blueHeralds = 0
    blueBarons = 0
    blueTowersDestroyed = 0
    blueTotalGold = 0
    blueAvgLevel = 0
    blueTotalExperience = 0
    blueTotalMinionsKilled = 0
    blueTotalJungleMinionsKilled = 0
    blueGoldDiff = 0
    blueExperienceDiff = 0
    blueCSPerMin = 0
    blueGoldPerMin = 0
    wards_placed = 0
    wards_destroyed = 0
    buildings_destroyed = 0

    # Temporary variables
    totalLevel = 0
    totalCS = 0
    totalMastery = 0

    for p in team.participants:
        p_state = p.cumulative_timeline[gameDuration]
        summ = p.summoner
        totalMastery += cass.get_champion_mastery(champion=p.champion, summoner=summ, region=region).points
        for temp_event in p_state._processed_events:
            if temp_event.type == "WARD_PLACED":
                 wards_placed += 1
            elif temp_event.type == "WARD_KILL":
                 wards_destroyed += 1
            elif temp_event.type == "BUILDING_KILL":
                buildings_destroyed += 1
            elif temp_event.type == "ELITE_MONSTER_KILL":
                blueEliteMonsters += 1
                if temp_event.monster_type == "DRAGON":
                    blueDragons += 1
                elif temp_event.monster_type == "BARON_NASHOR":
                    blueBarons += 1
                else:
                    blueHeralds += 1
        wards_destroyed += 1
        blueKills += p_state.kills
        blueDeaths += p_state.deaths
        blueAssists += p_state.assists
        totalLevel += p_state.level
        blueTotalExperience += p_state.experience
        blueTotalGold += p_state.gold_earned
        totalCS += p_state.creep_score
        totalCS += p_state.neutral_minions_killed
    blueCSPerMin = float(totalCS)/float(gameDuration.total_seconds()/60)
    blueGoldPerMin = blueTotalGold/float(gameDuration.total_seconds()/60)
    blueAvgLevel = float(totalLevel)/5

    match.properties[color+"Kills"] = blueKills
    match.properties[color+"Deaths"] = blueDeaths
    match.properties[color+"Assists"] = blueAssists
    match.properties[color+"AvgLevel"] = blueAvgLevel
    match.properties[color+"TotalExperience"] = blueTotalExperience
    match.properties[color+"CSPerMin"] = blueCSPerMin
    match.properties[color+"GoldPerMin"] = blueGoldPerMin
    match.properties[color+"WardsPlaced"] = wards_placed
    match.properties[color+"WardsDestroyed"] = wards_destroyed
    match.properties[color+"dragons"] = blueDragons
    match.properties[color+"EliteMonsters"] = blueEliteMonsters
    match.properties[color+"Heralds"] = blueHeralds
    match.properties[color+"Barons"] = blueBarons
    match.properties[color+"TotalMastery"] = totalMastery


def get_match_data(gameId: str, region: str, gameDuration):
    match = cass.get_match(gameId, region)
    match_object = Match
    match_object.properties["gameId"] = gameId
    match_object.properties["blueWins"] = match.blue_team.win

    #Get data for blue team
    get_team_data(match_object, match.blue_team, gameDuration, "blue", region)
    get_team_data(match_object, match.red_team, gameDuration, "red", region)

    return match_object

class Match:
    properties={}

    def csvHeader(self):
        csvString = ""
        i = 0
        for k in self.properties:
            csvString += str(k)
            if i+1 < len(self.properties):
                csvString += ","
            i += 1
        return csvString

    def csvEntry(self):
        csvString = ""
        i = 0
        for v in self.properties.values():
            csvString += str(float(v))
            if i+1 < len(self.properties):
                csvString += ","
            i += 1
        return csvString


if __name__ == '__main__':

    if len(sys.argv) > 1:
        api_key = str(sys.argv[0])
    else:
        api_key = "RGAPI-e4ca6150-7968-4e37-a95a-2ee4e9a422d7"

    cass.set_riot_api_key(api_key)  # This overrides the value set in your configuration/settings.
    cass.set_default_region("EUW")

    try:
        f = open('ranked_games.csv', "tx")
        f.close()
    except:
        print("File exists")

    data = pd.read_csv('high_diamond_ranked_10min.csv')

    print("Type game index to continue with or type \"new\" to start over:")

    selection = input()
    startIndex = 0
    if selection == "new":
        headerPrinted = False
    else:
        startIndex = selection
        headerPrinted = True
    for gameId in data['gameId'][(int(startIndex)-1):]:
        try:
            match = get_match_data(gameId, "EUW", datetime.timedelta(minutes=15, seconds=0))
            if not headerPrinted:
                f = open('ranked_games.csv', "wt")
                f.write(match.csvHeader(match))
                headerPrinted = True
                f.close()
            f = open('ranked_games.csv', "at")
            f.write("\n"+match.csvEntry(match))
            f.close()
        except:
            print("Omitting a game - exception thrown")
