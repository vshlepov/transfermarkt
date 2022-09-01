# Step 1 - SET "start_date" end "end_date" (lines 16-17)
# Step 2 - run "set_initial_inputs" once (line 35) and COMMENT OUT (put # sign before the function)
# Step 3 - UNCOMMENT (remove # sign) "run" function (line 1867) and execute it before completion of all steps.


from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import pandas as pd
import itertools
import matplotlib as mpl
from matplotlib import pyplot as plt
import dateutil


### SET INITIAL INPUTS###
start_date = "2022-07-05"
end_date = "2022-07-06"
def set_initial_inputs(start_date, end_date):
    """
    Writes initial inputs for "step_1" function to JSON file
    :param start_date: str | start date in "yyyy-mm-dd" format
    :param end_date: str | end date (non-inclusive) in "yyyy-mm-dd" format
    :return: None
    """
    year = pd.to_datetime(start_date).year
    years = list(range(year-4, year))

    data = {"start_date": [start_date],
            "end_date": [end_date],
            "start_row": [0],
            "path": [0],
            "step": [0]}
    df = pd.DataFrame(data=data)
    df.to_json("inputs-master.json")
#set_initial_inputs(start_date, end_date)


### SET DIMENSIONS - DO NOT CHANGE ###
# number of seasons, preceding to transfer date, and start/end calendar years
seasons_preceding_num = 3
start_year = int(pd.to_datetime(start_date).year - (seasons_preceding_num + 1))
end_year = int(pd.to_datetime(end_date).year)
# list of seasons, preceding to transfer date
seasons_preceding_global = list(range(0, seasons_preceding_num))
# list of calendar years
seasons_global = list(range(start_year, end_year))
# list of tournaments
tournaments_global = {0: "total",
                  1: "1st league tier", 2: "2nd league tier", 3: "3rd league tier",
                  4: "4th league tier", 5: "5th league tier", 6: "6th league tier",
                  12: "play-offs", 18: "reserve league", 7: "youth league",
                  8: "domestic cup", 9: "domestic super cup", 14: "league cup", 15: "domestic youth cup",
                  21: "further cup", 24: "regional championship",
                  10: "international cup", 13: "international super-cup", 16: "international youth cup"}
# transfer attributes
transfer_attributes = ["name", "left_club", "joined_club", "fee"]
# player attributed
player_attributes = ["date_birth", "height", "citizenship", "position", "foot"]
# player stats
player_stats = ["squad", "appearances", "ppg", "goals", "assists", "own_goals",
                "subs_on", "subs_out", "yellow", "yellow2", "red", "pen_goals", "mp", "points","club_url"]
# player attributes
club_attributes = ["country"]
# club stats in domestic league
club_stats_league = ["league", "w", "d", "l", "+/-", "rank", "goals_made", "goals_taken"] # output stats
# club stats in domestic and international cups
club_stats_cups = ["round_achieved"]
# international cups
cups_international = {"uefa-champions-league": 30, "europa-league": 31, "uefa-europa-conference-league": 32,
                      "uefa-super-cup": 33, "uefa-champions-league-qualifying": 34, "europa-league-qualifying": 35,
                      "uefa-europa-conference-league-qualifiers": 36, "uefa-youth-league": 37,
                      # AMERICA
                      "concacaf-champions-league": 40, "concacaf-league": 41, "copa-libertadores": 42,
                      "u20-copa-libertadores": 43, "campeones-cup": 44, "leagues-cup-showcase": 45,
                      "copa-sudamericana": 46,
                      #AFRICA
                      "caf-champions-league": 50, "caf-confederation-cup": 51, "caf-supercup": 52,
                      # ASIA
                      "afc-champions-league": 60, "afc-cup": 61, "ofc-champions-league": 62}
rounds_global = {"winner": 0, "final": 1, "semi-finals": 2, "quarter_finals": 3, "last_16": 4,
                 "group_stage": 5, "qualifying_round": 6, "intermediate": 7,
                 "6th_round": 8, "5th_round": 9, "4th_round": 10, "3rd_round": 11, "2nd_round": 12, "1st_round": 13}


### GET FUNCTIONS ###
def get_transfer_data(date):
    """
    Return transfer data for a given date. The following set of data is collected:
        player name ("name")
        club left ("left_club")
        club joined ("joined_club")
        transfer fee ("fee"), EUR M
        date of transfer ("date") in yyyy-mm-dd format
        Transfermarkt url for the player ("name_url")
        Transfermarkt url for the club left ("left_club_url")
        Transfermarkt url for the club joined ("joined_club_url")
        Transfermarkt url for the transfer details ("fee_url")
    :param date: str | "yyyy-mm-dd" format
    :return: dataframe
    """

    # set url mask
    url_mask = "https://www.transfermarkt.com/transfers/transfertagedetail/statistik/top/land_id_ab//land_id_zu//leihe/true/datum/{}/plus/1/galerie/0/page/{}"

    # create empty list to store BeautifulSoup objects (pages)
    bs = []

    # url for page ONE for a given date in yyyy-mm-dd format
    url = url_mask.format(date, 1)

    # get BeautifulSoup object
    soup = url_to_BS(url)

    # get the number of pages for a given date
    num_pages = soup.find_all("li", {"class": "tm-pagination__list-item tm-pagination__list-item--icon-last-page"})
    if len(num_pages) > 0:
        num_pages = num_pages[0].find_next()["title"]
        num_pages = int(re.search("\d+", num_pages)[0])
    else:
        num_pages = 1

    # Iterate over pages for a given date (starting with the page ONE)
    # and store BeautifulSoup objects to a list
    for j in range(1, num_pages+1):
        time_start = datetime.now()
        url = url_mask.format(date, j)
        soup = url_to_BS(url)
        bs.append(soup)
        time_diff = datetime.now() - time_start
        print("Day {}, page {}/{} completed in {} seconds".format(date, j, num_pages, time_diff))

    # Extract data from BeautifulSoup objects for a given date to a dataframe
    for i in range(len(bs)):

        # extract data (name, left, joined, fee) from BS object
        data = bs[i].find_all("td", {"class": "hauptlink"})

        # load data into df_tmp
        columns = transfer_attributes
        columns = columns * int(len(data) / 4)
        index_tmp = list(range(len(data)))
        df = pd.DataFrame(data=[data, columns, index_tmp]).transpose()
        df.columns = ["data", "column", "index"]

        # extract urls
        def get_url(row):
            if row.a != None:
                return row.a.get("href")
            else:
                return None
        df["url"] = df["data"].apply(lambda x: get_url(x))

        # convert name, left, joined clubs, and fee into text
        def get_text(row):
            if row.text != None:
                return row.text.strip()
            else:
                return None
        df["data"] = df["data"].apply(lambda x: x.text.strip())

        # add date
        df["date"] = date

        return df
def get_expiry_date(url):
    """
    Returns contract expiry date (if any, if none - returns None) as of the date of transfer for a given fee_url
    :param url: str | fee_url
    :return: string
    """

    # set url mask
    url_mask = "https://www.transfermarkt.com{}"

    # compile url with transfer info
    url = url_mask.format(url)

    # get BeautifulSoup object for url
    soup = url_to_BS(url)

    # get remaining contract
    data = soup.find_all("td", {"class": "zentriert"})
    str = ""
    for i in range(len(data)):
        str = str + data[i].text
    if len(re.findall("\(.+\)", str)) != 0:
        return re.findall("\(.+\)", str)[0].strip("()")
    else:
        return None
def get_player_attributes(url):
    """
    Returns player attributes for a given name_url
    :param url: Transfermarkt url for the player ("name_url")
    :return: dictionary of player attributes:
        date of birth (date_birth)
        height, meters
        citizenship (primary, if more than one)
        position (main position, if more than one)
        foot
    """

    # set url mask
    url_mask = "https://www.transfermarkt.com{}"

    # construct url for the page with player attributes
    url = url_mask.format(url)

    # get BeautifulSoup object for url
    soup = url_to_BS(url)

    # get date of birth
    data = soup.find_all("span", {"itemprop": "birthDate"})
    if len(data) > 0:
        date_birth = data[0].text.strip()[:12].strip()
    else:
        date_birth = None

    # get height
    data = soup.find_all("span", {"itemprop": "height"})
    if len(data) > 0:
        height = data[0].text
    else:
        height = None

    # get citizenship
    data = soup.find_all("span", {"itemprop": "nationality"})
    if len(data) > 0:
        citizenship = data[0].text.strip()
    else:
        citizenship = None

    # get main position
    data = soup.find_all("dd", {"class": "detail-position__position"})
    if len(data) > 0:
        position = data[0].text
    else:
        position = None

    # get foot
    dict_tmp = {}
    data = soup.find_all("span", {"class": "info-table__content info-table__content--regular"})
    for i in range(len(data)):
        dict_tmp[data[i].text.strip()] = data[i].find_next().text
    if "Foot:" in dict_tmp.keys():
        foot = dict_tmp["Foot:"]
    else:
        foot = None # kinda bad for the football professional

    # save data to dictionary and return
    dict = {"date_birth":date_birth, "height":height, "citizenship":citizenship, "position":position, "foot":foot}
    return dict
def get_player_stats(url, year, league):
    """
    Parses player statistics for a given url, year and league. In case player changed the club in mid-season,
    all statistics is returned for both clubs within a league type, but club url is returned for the last one.
    :param url: str, Transfermarkt url for the player ("name_url")
    :param year: int
    :param league: int:
    :return: dictionary of player statistics wrapped in list
    """

    # construct url for the page with player statistics
    url = re.sub(pattern="profil", repl="leistungsdatendetails", string=url)
    mask = "/plus/1?saison={}&verein=&liga={}&wettbewerb=&pos=&trainer_id="
    url = "https://www.transfermarkt.com" + url + mask
    url = url.format(year, league)

    # get BeautifulSoup object for url
    soup = url_to_BS(url)

    # get statistics from BeautifulSoup object
    data = soup.find_all("td", {"class": "zentriert"})[0:12]

    # get minutes played data
    mp = soup.find_all("td", {"class": "rechts"})
    if len(mp) > 2: # Parsing item with index 2, need at least 3 items
        mp = mp[2].text
    else:
        mp = None

    # get club_url
    club_url = soup.find_all("td", {"class": "hauptlink no-border-rechts zentriert"})
    if len(club_url) > 0:
        club_url = club_url[0].a["href"]
    else:
        club_url = None

    # save data to dictionary and return
    stats = player_stats[:-3] # last TREE stats (mp, points and club url) are added below
    if len(data) > 11: # check if there's at least 12 items (one per each attribute), otherwise return None

        # check if "squad" is digit, otherwise return None
        if data[0].text.isdigit():
            dict = {}
            for i in range(len(stats)):
                dict[stats[i]] = data[i].text

            # remove dot and apostrophe from mp and add to the dict
            dict["mp"] = re.sub("\.|'", "", mp)

            # cast stats to float
            for stat in dict.keys():
                if pd.isna(dict[stat]) == False:
                    # replace dash and "\xa0" with zero
                    dict[stat] = re.sub("-|\\xa0", "0", dict[stat])
                    # strip the string
                    dict[stat] = dict[stat].strip()
                    # cast to float
                    dict[stat] = float(dict[stat])

            # add points value - ppg times appearances
            if pd.isna(dict["ppg"]) != True:
                if pd.isna(dict["appearances"])  != True:
                    dict["points"] = dict["ppg"] * dict["appearances"]
                else: dict["points"] = None
            else:
                dict["points"] = None

            # add club url to dict
            dict["club_url"] = club_url

            #wrap dict to list and return
            lst = [dict]
            return lst
        else:
            return None
    else:
        return None
def get_club_attributes(url):
    """
    Returns club attributes for a given name_url
    :param url: str | Transfermarkt url for the player ("left_url", "joined_url")
    :return: dictionary of club attributes:
        country
    ### TO BE COMPLETED ###
    """

    # set url mask
    url_mask = "https://www.transfermarkt.com{}"

    # construct url for the page with player attributes
    url = url_mask.format(url)
    url = re.sub(pattern="startseite", repl="datenfakten", string=url)

    # get BeautifulSoup object for url
    soup = url_to_BS(url)

    # get country
    data = soup.find_all("meta", {"name": "keywords"})
    if len(data) > 0:
        country = str(data[0])
        country = re.search("(?<=content=\").*(?=\"\sname)", country)[0]
        country = re.split(",", country)[1]
    else:
        country = None

    dict = {"country": country}

    return [dict]
def get_club_stats_national(url):
    """
    Get club statistics for in the national leagues for a given url.
    :param url: str, Transfermarkt url for the player ("club_url")
    :return: dataframe of stats grouped by (stat, year, league):
        wins ("w")
        draws ("d")
        loses ("l")
        goal difference ("+/-")
        rank (mean rank if multiple rounds for the season)
        goals made ("goals_made")
        goals_taken ("goals_taken")
    """

    # construct url for the page with player statistics
    url_new = re.sub(pattern="startseite", repl="platzierungen", string=url)
    url_new = "https://www.transfermarkt.com{}".format(url_new)

    # get BeautifulSoup object for url
    soup = url_to_BS(url_new)

    # get statistics from BeautifulSoup object
    data = soup.find_all("td", {"class": "zentriert"})
    for i in range(len(data)):
        data[i] = data[i].text

    # change season format from "yy/yy" to "yyyy" (season start)
    for i in range(len(data)):
        if re.match("\d*/\d*", data[i]) != None:
            data[i] = "20" + re.split("/", data[i])[0]

    # list of stats and years, NOTE input stats differ from function output
    stats = ["year", "league_name", "league", "w", "d", "l", "goals", "+/-", "points", "rank"]
    years = seasons_global[:]

    # transform list to array
    df = np.array(data)

    # reshape array
    df = df.reshape([int(len(df) / 10), 10])

    # transform array to dataframe
    df = pd.DataFrame(df, columns=stats).drop(columns=["league_name", "points"])

    # transform goals into separate columns - goals_made and goals_taken
    def split_goals(row):
        row["goals"] = re.split(":", row["goals"])
        row["goals_made"] = row["goals"][0]
        row["goals_taken"] = row["goals"][1]
        return row
    df = df.apply(lambda x: split_goals(x), axis=1).drop(columns=["goals"])

    # transform "league" into integer - 1 for the first tier and 0 for the 2nd tier
    league_tiers = {"First Tier": 1, "Second Tier": 2, "Third Tier": 3, "Fourth Tier": 4,
                    "Fifth Tier": 5, "Sixth Tier": 6, "Youth league": 7, "Play-Offs": 12,
                    "Reserve league": 18}
    df["league"] = df["league"].apply(lambda x: league_tiers[x])

    # cast data to integers
    for column in df.columns:
        df[column] = df[column].apply(lambda x: int(x))

    # drop all years out of the "years_global" range
    mask = (df["year"] >= years[0]) & (df["year"] <= years[-1])
    df = df[mask]

    # reshape dataframe

    # group by years and add "year" as a column (NOT index)
    df["rounds"] = 1
    df = df.groupby(by="year", axis=0).sum()
    df["year"] = df.index
    df.index = range(len(df.index))

    # get mean values for "league" and "rank"
    for label in df.index:
        if pd.isna(label) == False:
            df.at[label, "league"] = df.at[label, "league"] / df.at[label, "rounds"]
            df.at[label, "rank"] = df.at[label, "rank"] / df.at[label, "rounds"]
    df = df.drop(columns="rounds")

    # get a series with index as tuples (stat, year, league)
    df = df.pivot(columns=["year", "league"]).sum()
    df.index = list(df.index)
    df.name = "values"

    # create df_master with full-scope index, merge with df, transpose (to add as a line) and return as a list
    stats = club_stats_league[1:] # EXCEPT for league - it's part of the index
    years = seasons_global[:]
    leagues = list(tournaments_global.keys())[1:10] # tiers 1-6, youth league, play-offs, and reserve league
    index = list(itertools.product(stats, years))
    index = list(itertools.product(index, leagues))
    for i in range(len(index)):
        index[i] = (index[i][0][0], index[i][0][1], index[i][1])
    df_master = pd.DataFrame(index=index)
    df_master = pd.merge(left = df_master, right=df, left_index=True, right_index=True, how="outer")
    return list(df_master["values"])
def get_club_stats_international(url):
    """
    Get club statistics (round achieved) by the club in international cups for a given url.
    :param url: str, Transfermarkt url for the club ("club_url")
    :return: dataframe
    """

    # construct url for the page with player statistics
    url_new = re.sub(pattern="startseite", repl="pokalhistorie", string=url)
    url_new = "https://www.transfermarkt.com{}".format(url_new)

    # get BeautifulSoup object for url
    soup = url_to_BS(url_new)

    # get data from BeautifulSoup object
    data = soup.find_all("td", {"class": "no-border-links zentriert"})
    cups = []
    years = []
    for i in range(len(data)):
        cups.append(data[i].a["href"])
        years.append(data[i].text.strip())
    rounds = soup.find_all("td", {"class": ["", "bg_gelb_20 hauptlink", "bg_gruen_20 hauptlink"]})
    for i in range(len(rounds)):
        rounds[i] = rounds[i].text.strip()

    # transform to dataframe
    data = {"club_url": url,
            "year": years,
            "cup": cups,
            "round": rounds}
    df = pd.DataFrame(data=data)

    return df


### UTILS ###
def get_inputs():
    """
    Return tuple of inputs stored in the last rov of inputs.json
    :return: tuple | (start_date, end_date, start_row, path, step)
    """

    # open inputs.json, read the last row and return as a tuple
    df = pd.read_json("inputs-master.json")
    start_date = df.iloc[-1]["start_date"]
    end_date = df.iloc[-1]["end_date"]
    start_row = df.iloc[-1]["start_row"]
    path = df.iloc[-1]["path"]
    step = df.iloc[-1]["step"]
    return [start_date, end_date, start_row, path, step]
def get_start_date():
    """
    Return start_date stored in the last rov of inputs.json
    :return: str | start_date
    """

    return get_inputs()[0]
def get_end_date():
    """
    Return end_date stored in the last row of inputs.json
    :return: str | start_date
    """

    return get_inputs()[1]
def get_start_row():
    """
    Return end_date stored in the last row of inputs.json
    :return: str | start_row
    """

    return get_inputs()[2]
def get_path():
    """
    Return path stored in the last row of inputs.json
    :return: str | path
    """

    return get_inputs()[3]
def get_step():
    """
    Return step stored in the last row of inputs.json
    :return: str | path
    """

    return get_inputs()[4]
def set_inputs(start_date = None, end_date = None, start_row = None, path = None, step=None):
    """
    Write new set of inputs to the new row of inputs.json
    :param start_date: str | new value of start_date, None = value returned by "get_start_date"
    :param end_date: str | new value of end_date. None = value returned by "get__end_date"
    :param start_row: str or int | new value of start_row, None = value returned by "get_start_row"
    :param path: str | new value of path to JSON file, None = value returned by "get_path"
    :param step: str or int | new value of step, None = value returned by "get_date"
    :return: None
    """
    # get row with new parameters and write to inputs.json
    inputs = [start_date, end_date, start_row, path, step]
    for i in range(len(inputs)):
        if pd.isna(inputs[i]) == True:
            inputs[i] = get_inputs()[i]
    data = {"start_date": [inputs[0]],
            "end_date": [inputs[1]],
            "start_row": [inputs[2]],
            "path": [inputs[3]],
            "step": [inputs[4]]}
    row = pd.DataFrame(data=data)
    df = pd.read_json("inputs-master.json")
    df = pd.concat([df, row], axis=0, ignore_index=True)
    df.to_json("inputs-master.json")
def url_to_BS(url):
    """
    Returns BeautifulSoup object for a given url
    :param url: url
    :return: BeautifulSoup object
    """

    # set browser parameters for requests.get function
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

    # get data from url
    page = requests.get(url=url, headers=headers)

    # create BeautifulSoup object
    soup = BeautifulSoup(page.content, "html.parser")

    return soup
def str_to_tuple(str):
    """
    Casts string with parentheses into a tuple: "(goals, 2010, 1)" to ("goals", 2010, 1)
    :param str: str
    :return: tuple
    """

    # check if given string has an opening and closing parentheses
    if re.search(pattern="\(.+\)(?!_@_)", string=str) != None:

        # if so - get the text inside the parentheses
        str = re.search(pattern="\(.+\)(?!_@_)", string=str)[0]
        str = re.sub("[()]", "", str)

        # split string it into elements (comma followed by the space)
        str = re.split(",\s", str)
        for i in range(len(str)):
            # check if text consists of digits
            if re.match("\d+", str[i]) != None:
                # convert into integer
                str[i] = int(str[i])
            else:
                # remove single quote around the text, if any
                str[i] = str[i].strip("'")
        return tuple(str)
    else:
        return str
def cols_to_tuple(df):
    """
    Casts dataframe column names to tuples
    :param df: DataFrame
    :return: DataFrame
    """

    columns = []
    for column in df.columns:
        column = str_to_tuple(column)
        columns.append(column)
    df.columns = columns
    return df
def run():
    """
    Run next step of data collection and processing.
    :param step:
    :return: path to JSON file
    """

    # get current step
    step = get_step() + 1

    if step == 1:
        print("Step 1: create empty dataframe FIFA ratings")
        return step_01()
    elif step == 2:
        print("Step 2: get FIFA ratings data")
        return step_02()
    elif step == 3:
        print("Step 3: create empty dataframe for transfer data")
        return step_03()
    elif step == 4:
        print("Step 4: get transfer data")
        return step_04()
    elif step == 5:
        print("Step 5: process transfer data")
        return step_05()
    elif step == 6:
        print("Step 6: get contract expiry dates")
        return step_06()
    elif step == 7:
        print("Step 7: process contract expiry dates")
        return step_07()
    elif step == 8:
        print("Step 8: create empty dataframe for player attributes")
        return step_08()
    elif step == 9:
        print("Step 9: get player attributes")
        return step_09()
    elif step == 10:
        print("Step 10: process player attributes")
        return step_10()
    elif step == 11:
        print("Step 11: add columns for player stats")
        return step_11()
    elif step == 12:
        print("Step 12: get player stats")
        return step_12()
    elif step == 13:
        print("Step 13: process player stats")
        return step_13()
    elif step == 14:
        print("Step 14: merge dataframes with transfer and player info and process data")
        return step_14()
    elif step == 15:
        print("Step 15: create empty dataframe for club attributes")
        return step_15()
    elif step == 16:
        print("Step 16: get club attributes")
        return step_16()
    elif step == 17:
        print("Step 17: process club attributes")
        return step_17()
    elif step == 18:
        print("Step 18: create empty dataframe for club stats national")
        return step_18()
    elif step == 19:
        print("Step 19: get club stats national")
        return step_19()
    elif step == 20:
        print("Step 20: create empty dataframe for club stats international")
        return step_20()
    elif step == 21:
        print("Step 21: get club stats international")
        return step_21()
    elif step == 22:
        print("Step 22: process club stats international")
        return step_22()
    elif step == 23:
        print("Step 23: merge club stats national and international")
        return step_23()
    elif step == 24:
        print("Step 24: merge club attributes, stats, and FIFA ratings")
        return step_24()
    else:
        print("Data collection and processing is completed")
    return None
def reset(step):
    """
    Reset parameters in input.json back to a given step
    :param step: inr | step
    :return: None
    """

    inputs = pd.read_json("inputs-master.json")
    inputs = inputs[inputs["step"] <= step]
    inputs.to_json("inputs-master.json")
    print("All data is reset to step {}".format(step))

    return None


### DATA COLLECTION AND PROCESSING ###

# !!! IMPORTANT !!! All parameters are stored in inputs.json file and set by relevant get_{parameter} functions.
# Do not set parameters and (or) or update inputs.json manually.

# COUNTRIES - EMPTY DF
def step_01(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Create an empty dataframe for FIFA ratings and save to JSON file
    """

    # path to JSON file
    path = "data({}-to-{})_01.json".format(start_date, end_date)

    # increment step value by one
    step += 1

    # create empty dataframe
    df = pd.DataFrame()

    # write dataframe to NEW JSON, update inputs.json and return path
    path = path
    df.to_json(path)
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# COUNTRIES - GET FIFA RATINGS
def step_02(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Get FIFA world ratings and UPDATE JSON file
    """

    # increment step value by one
    step += 1

    # read JSON file AND convert column names to tuples
    df = pd.read_json(path, convert_dates=False)

    # url mask
    url = "https://www.transfermarkt.com/statistik/weltrangliste"
    url_page_1 = "https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/plus/0/galerie/0?datum={}"
    url_mask = "https://www.transfermarkt.com/statistik/weltrangliste/statistik/stat/datum/{}/plus/0/galerie/0/page/{}"

    # get list of all dates
    soup = url_to_BS(url)
    data = soup.find_all("option")
    dates = []
    for date in data[:-1]: # EXCEPT for the last date - have different format
        date = pd.to_datetime(date.text)
        if  date >= pd.to_datetime("{}-01-01".format(start_year)):
            if date <= pd.to_datetime(end_date):
                dates.append(date)

    # iterate over dates
    for date in dates[start_row:]:

        #convert date into "yyyy-mm-dd" format
        date_tmp = pd.to_datetime(date).strftime("%Y-%m-%d")

        #get data from the 1st page and add to lists
        time_start = datetime.now()
        countries = []
        uefa_poins = []
        url = url_page_1.format(date_tmp)
        soup = url_to_BS(url)
        data = soup.find_all("tr", {"class": ["odd", "even"]})
        for line in data:
            items = []
            for item in line:
                items.append(item.text)
            countries.append(items[2])
            uefa_poins.append(items[-1])

        # get list of pages for given date
        pages = []
        data = soup.find_all("li", {"class": "tm-pagination__list-item"})
        for page in data:
            page = page.text.strip()
            if page != "":
                pages.append(page)

        # print status
        time_diff = datetime.now() - time_start
        pages_total = len(pages)
        print("{}, page {}/{} completed in {} seconds".format(date_tmp, 1, pages_total, time_diff))

        #iterate over pages and add data to [countries] and [uefa_points]
        i=2
        for page in pages[1:]: #except for the first page
            time_start_page = datetime.now()
            url = url_mask.format(date_tmp, page)
            soup = url_to_BS(url)
            data = soup.find_all("tr", {"class": ["odd", "even"]})
            for line in data:
                items = []
                for item in line:
                    items.append(item.text)
                countries.append(items[2])
                uefa_poins.append(items[-1])
            time_diff = datetime.now() - time_start_page
            print("{}, page {}/{} completed in {} seconds".format(date_tmp, i, pages_total, time_diff))
            i +=1

        # save lists to df_tmp (index=country, data=uefa_points) and merge with df
        data = {date: uefa_poins,
                "country": countries}
        df_tmp = pd.DataFrame(data=data)
        df_tmp = df_tmp.drop_duplicates(subset=["country"], keep="first")
        df_tmp.index = df_tmp["country"]
        df_tmp = df_tmp.drop(columns=["country"])
        df = pd.merge(left=df, right=df_tmp, left_index=True, right_index=True, how="outer")

        # update json file
        df.to_json(path)
        time_diff = datetime.now() - time_start

        # print status and write new row to csv
        left = len(dates) - start_row - 1
        print("{} updated in {} seconds, {} days left to update.".format(date, time_diff, left))
        if start_row < len(dates) - 1:
            # update start_row value
            set_inputs(start_row=start_row + 1)
            start_row += 1
        else:
            # reset start_row to zero and update step value
            set_inputs(start_row=0, step=step)

    return path


# TRANSFERS - EMPTY DATAFRAME
def step_03(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Create an empty dataframe and write to JSON file
    """

    # increment step value by one
    step += 1

    # create empty dataframe
    df = pd.DataFrame(columns=["data", "column", "url", "date"])

    # write df to JSON
    path = path[:-7] + "03.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# TRANSFERS - GET TRANSFER DATA
def step_04(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Open JSON file and UPDATE it (i.e. write directly to input JSON file)
    with transfer data.
    """

    # increment step value by one
    step += 1

    # read JSON file
    df = pd.read_json(path)

    # get range of days as str in "yyyy-mm-dd" format
    dates = [date.strftime("%Y-%m-%d") for date in pd.date_range(start=start_date, end=end_date, freq="D", inclusive="left")]

    # iterate over dates
    n = 0
    for i in range(len(dates)):

        # get start time
        time_start = datetime.now()

        # get date from the list of dates
        date = dates[i]

        # get transfer data for a given day
        df_tmp = get_transfer_data(date)

        # concatenate df_tmp with df
        df = pd.concat(objs=[df, df_tmp], axis=0, ignore_index=True)

        # write df to transfer data for the given day
        df.to_json(path)
        time_diff = datetime.now() - time_start

        # print status and write new date to inputs.json
        left = len(dates) - 1 - n
        print("{} completed in {} seconds, {} days left.".format(date, time_diff, left))
        if i < len(dates) - 1:
            # update date value
            set_inputs(start_date=dates[i + 1])
            n += 1
        else:
            # reset date to initial value and update step value
            set_inputs(start_date=start_date, step=step)

    # return path
    return path


# TRANSFERS - PROCESS TRANSFERS AND ADD COLUMN FOR CONTRACT EXPIRY DATE
def step_05(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Read JSON file as created with "step_04" function, reshape dataframe,
    filter/process data and write to NEW JSON file
    """

    # increment step value by one
    step += 1

    # read JSON file
    df = pd.read_json(path)

    # reshape table
    df["index"] = range(len(df))
    df["index"] = df["index"]//4
    df = df.pivot(index=["index", "date"], columns="column", values=["data", "url"])
    df.columns = ["fee", "joined_club", "left_club", "name", "fee_url", "joined_club_url", "left_club_url", "name_url"]
    df["date"] = df.apply(lambda x: x.name[1], axis=1)
    df = df.droplevel(1, axis=0)
    df = df[["name", "left_club", "joined_club", "fee", "date", "name_url", "left_club_url", "joined_club_url", "fee_url"]]

    # drop NaN
    df = df.dropna()

    # cast transfer fee data to float (million EUR) and replace "free transfer" with zero
    def fee_to_float(row):
        fee_m = re.findall("(?<=€)\d+.\d+(?=m)", row)
        fee_th = re.findall("\d+(?=Th.)", row)
        fee_eur = re.findall("(?<=€)\d+", row)
        if len(fee_m) > 0:
            return float(fee_m[0])
        elif len(fee_th) >0:
            return float(fee_th[0])/1000
        elif len(fee_eur) >0:
            return float(fee_eur[0])/1000000
        elif row == "free transfer": ### FREE TRANSFERS COULD HELP TO CALIBRATE THE MODEL - THEY HAVE STATS TOO ###
            return 0
        else:
            return row
    df["fee"] = df["fee"].apply(lambda x: fee_to_float(x))

    # sort out transfers with no transfer fee info
    #df = df[df["fee"].apply(lambda x: type(x) == float)].dropna()

    # cast "date" to datetime
    df["date"] = df["date"].apply(lambda x: pd.to_datetime(x))

    # add column for contract expiry date (will be used at step 3)
    df["expiry_date"] = None

    # write to JSON file
    path = path[:-7] + "05.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# TRANSFERS - GET CONTRACT EXPIRY DATE
def step_06(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Open JSON file and UPDATE it (i.e. write directly to input JSON file)
    with contract expiry date information in "yyyy-mm-dd" format.
    """

    # increment step value by one
    step += 1

    # read JSON file
    df = pd.read_json(path)

    # get contract expiry date and write to csv file
    index = df.index
    for label in index[start_row:]:
        time_start = datetime.now()
        df.at[label, "expiry_date"] = get_expiry_date(df.loc[label, "fee_url"])
        df.to_json(path)
        time_diff = datetime.now() - time_start

        # print status and write new row to csv
        left = len(index) - start_row - 1
        print("Row {} updated in {} seconds, {} rows left to update.".format(start_row, time_diff, left))
        if start_row < len(index) - 1:
            # update start_row value
            set_inputs(start_row=start_row+1)
            start_row += 1
        else:
            # reset value of start_row to zero and update step value
            set_inputs(start_row=0, step=step)

    print(df.shape)
    print(df.iloc[0])

    return path


# TRANSFERS - PROCESS CONTRACT EXPIRY DATE
def step_07(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Cast transfer expiry date to datetime and write to a NEW JSON file
    """

    # increment step value by one
    step += 1

    # read JSON file
    df = pd.read_json(path)

    # drop empty rows - will save time on step 5 - and write to JSON
    df = df.dropna()

    # cast "expiry date" to datetime
    for label in df.index:
        try:
            df.at[label, "expiry_date"] = pd.to_datetime(df.at[label, "expiry_date"])
        except dateutil.parser._parser.ParserError:
            df = df.drop(labels=label)
            continue
        except pd._libs.tslibs.np_datetime.OutOfBoundsDatetime:
            df = df.drop(labels=label)
            continue
        except ValueError:
            df = df.drop(labels=label)
            continue

    # write to NEW JSON file
    path = path[:-7] + "07.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# PLAYERS - EMPTY DATAFRAME
def step_08(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Create an empty dataframe: index = unique name_url's, columns = "attributes" and save to JSON file
    """

    # increment step value by one
    step += 1

    # read csv file
    df = pd.read_json(path)

    # get list of unique name_url's
    name_url = df["name_url"].unique()

    # create dataframe to store attributes
    df = pd.DataFrame(index=name_url, columns=["attributes"])

    # write dataframe to NEW JSON
    path = path[:-7] + "08.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# PLAYERS - GET ATTRIBUTES
def step_09(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Open JSON file and UPDATE it (i.e. write directly to input JSON file)
    with player attributes
    """

    # increment step value by one
    step += 1

    # read JSON file
    df = pd.read_json(path)

    # get dict with player attributes and write to JSON file
    index = df.index
    for label in index[start_row:]:
        time_start = datetime.now()
        df.at[label, "attributes"] = [get_player_attributes(label)]
        df.to_json(path)
        time_diff = datetime.now() - time_start

        # print status and write new row to csv
        left = len(index) - start_row - 1
        print("Row {} updated in {} seconds, {} rows left to update.".format(start_row, time_diff, left))
        if start_row < len(index) - 1:
            # update start_row value
            set_inputs(start_row=start_row+1)
            start_row += 1
        else:
            # reset start_row to zero and update step value
            set_inputs(start_row=0, step=step)

    return path


# PLAYERS - PROCESS ATTRIBUTES
def step_10(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Read JSON file, unpack attributes from dictionary to dataframe,
    filter and process data and write to a NEW JSON file
    """

    # increment step value by one
    step += 1

    # read JSON file
    df = pd.read_json(path)

    # drop labels with no attributes
    df = df.dropna()

    # unpack player attributes from dictionary to dataframe, drop NaN and "attributes" column
    def unpack_attr(row):
        for attr in row["attributes"][0].keys():
            row[attr] = row["attributes"][0][attr]
        return row
    df = df.apply(lambda x: unpack_attr(x), axis=1).drop(columns=["attributes"]).dropna()

    # convert height to float and filter height > 1 meter
    df["height"] = df["height"].apply(lambda x: re.search("\d,\d*", x)).dropna(). \
        apply(lambda x: x[0]).dropna().apply(lambda x: re.sub(",", ".", x)). \
        apply(lambda x: float(re.sub("\'", "", x)))
    df = df[df["height"] > 1]

    # convert date of birth to datetime
    for label in df.index:
        try:
            df.at[label, "date_birth"] = pd.to_datetime(df.at[label, "date_birth"])
        except dateutil.parser._parser.ParserError:
            df = df.drop(labels=label)
            continue
        except pd._libs.tslibs.np_datetime.OutOfBoundsDatetime:
            df = df.drop(labels=label)
            continue
        except ValueError:
            df = df.drop(labels=label)
            continue

    # filter out goalkeepers (nothing personal, they just have a different set of stats),
    # sorry guys, we'll miss you
    df = df[df["position"] != "Goalkeeper"]
    print(df.shape)

    # drop labels with "N/A" foot - it's kinda strange for professional football player
    df = df[df["foot"] != "N/A"]
    print(df.shape)

    # write dataframe to JSON
    path = path[:-7] + "10.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# PLAYERS - ADD COLUMNS FOR PLAYER STATS
def step_11(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Open JSON file, join it with new empty dataframe: index = name_url,
    columns = product of "seasons_global" and "tournaments_global" and write to NEW JSON file.
    """

    # increment step value by one
    step += 1

    # read JSON file
    df = pd.read_json(path)

    # create empty dataframe (columns = product of year & league type) and merge with df
    years = seasons_global[:]
    leagues = tournaments_global.keys()
    columns = list(itertools.product(years, leagues))
    df_tmp = pd.DataFrame(index=df.index, columns=columns)
    df = df.join(df_tmp)

    # write dataframe to NEW JSON file
    path = path[:-7] + "11.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# PLAYERS - GET STATS
def step_12(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Open JSON file function and UPDATE it (i.e. write directly to input JSON file)
    with player statistics (see "get_player_stats" function for details).
    """

    # increment step value by one
    step += 1

    # read JSON file AND convert column names to tuples
    df = pd.read_json(path)
    df = cols_to_tuple(df)

    # set years and leagues to parse
    years = seasons_global[:]
    leagues = tournaments_global.keys()
    cells_num = len(years) * len(leagues)
    # iterate over names, years and leagues and get [dictionary] with statistics for each "cell"
    index = df.index
    for label in index[start_row:]:
        time_start = datetime.now()
        i=1
        for year in years:
            for league in leagues:
                time_start_year = datetime.now()
                df.at[label, "({}, {})".format(year, league)] = get_player_stats(label, year, league)
                time_diff_year = datetime.now() - time_start_year
                print("Row {}, cell {}/{} completed in {} seconds".format(start_row, i, cells_num, time_diff_year))
                i += 1

        # update json file
        df.to_json(path)
        time_diff = datetime.now() - time_start

        # print status and write new row to csv
        left = len(index) - start_row - 1
        print("Row {} updated in {} seconds, {} rows left to update.".format(start_row, time_diff, left))
        if start_row < len(index) - 1:
            # update start_row value
            set_inputs(start_row=start_row + 1)
            start_row += 1
        else:
            # reset start_row to zero and update step value
            set_inputs(start_row=0, step=step)

    return path


# PLAYERS - PROCESS STATS
def step_13(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Read JSON file, unpack player stats from dictionary to dataframe,
    filter and process data and write to a NEW JSON file.
    """

    # increment step value by one
    step += 1

    # read JSON file AND convert column names to tuples
    df = pd.read_json(path)
    df = cols_to_tuple(df)

    # column index to iterate, avoid shallow copies
    stats = player_stats[:]
    years = seasons_global[:]
    leagues = tournaments_global.keys()

    # make list of column names (year, league, stat), assign it to empty DataFrame and join it with df
    columns = list(itertools.product(stats, years))
    columns = list(itertools.product(columns, leagues))
    for i in range(len(columns)):
        columns[i] = (columns[i][0][0], columns[i][0][1], columns[i][1])
    df = df.join(pd.DataFrame(index=df.index, columns=columns))

    # unpack statistics from dictionaries to df columns
    def unpack_stat(row):
        for stat in stats:
            for year in years:
                for league in leagues:
                    if pd.isna(row[(year, league)]) == False:
                        row[(stat, year, league)] = row[(year, league)][0][stat]
        return row
    df = df.apply(lambda x: unpack_stat(x), axis=1)

    # transform club_url to uniform format (drop seasons from url) amd filter unique club_url's
    def club_url_to_mask(url):
        if pd.isna(url) != True:
            url = re.sub("/saison_id/\d+", "", url)
        return url
    for year in years:
        for league in leagues:
            df[("club_url", year, league)] = df[("club_url", year, league)].apply(lambda x: club_url_to_mask(x))

    # drop unnecessary columns (year, league)
    for year in years:
        for league in leagues:
            df = df.drop(columns=[(year, league)])

    # write dataframe to JSON
    path = path[:-7] + "13.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# TRANSFERS & PLAYERS - MERGE AND PROCESS DATA
def step_14(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Merge transfers and players into single dataframe, process data,
    add non-numeric attributes to columns in binary format (e.g. right_foot: 1 for yes and 0 for no)
    and write dataframe into NEW JSON file
    """

    # increment step value by one
    step += 1

    # read transfers dataframe
    filename = 'data({}-to-{})_07.json'.format(start_date, end_date)
    df_transfers = pd.read_json(filename)

    # read players dataframe
    df_players = pd.read_json(path)

    # inner merge of dataframes
    df = pd.merge(left = df_transfers, right=df_players, left_on="name_url", right_index=True, how="inner")

    # cast column names to tuple
    df = cols_to_tuple(df)

    # cast "expiry_date" and "date_birth" to datetime from timestamp
    df[["expiry_date", "date_birth"]] = df[["expiry_date", "date_birth"]].apply(lambda x: pd.to_datetime(x, unit="ms"))

    # age as of the transfer date, days
    df["age"] = df["date"] - df["date_birth"]

    # days to expiry of contract
    df["days_to_expiry"] = df["expiry_date"] - df["date"]

    # month of birth
    df["month_birth"] = df["date_birth"].apply(lambda x: x.month)

    # Season preceding to transfer date (season = starting year of the season, e.g. 2021 for 2021/2022 season).
    # For the transfers, that took place in pre-season window (from Jun 1st to Oct 1st, non-inclusive)
    # season equals to year of transfer date minus 1.
    # For the transfers, that took place in mid-season window (Oct 1st to Jan 1st, non-inclusive)
    # season might equal to  year of transfer minus 1 (Oct 1st to Jan 1st) or 2 (Jan 1st to Jun 1st).

    # get date of pre-season transfer window start
    def window_start(row):
        """
        Returns start date of pre-season transfer window during the calendar year, for a date
        Example: for any date in 2020 function returns 2020-06-01
        :param row: datetime | date
        :return: datetime year
        """
        return pd.to_datetime(str(row.year)+"06"+"01")
    df["window_start"] = df["date"].apply(lambda x: window_start(x))

    # get starting year of 1st preceding season
    def year_0(row):
        if row["date"] > row["window_start"]:
            return row["date"].year - 1
        else:
            return row["date"].year - 2
    df["year_0"] = df.apply(lambda x: year_0(x), axis=1)


    # get all player statistics for preceding seasons

    # create set of columns = product of "stats", "years_preceding" & "leagues"
    stats = player_stats[:]
    years_preceding = seasons_preceding_global[:]
    leagues = tournaments_global.keys()
    columns = list(itertools.product(stats, years_preceding))
    columns = list(itertools.product(columns, leagues))
    for i in range(len(columns)):
        columns[i] = (columns[i][0][0], columns[i][0][1], columns[i][1])

    # create empty df_tmp with columns=columns  and merge with df
    df_tmp = pd.DataFrame(index=df.index, columns=columns)
    df = df.join(df_tmp)

    # get stats AND club_url for EACH of preceding seasons
    years = seasons_global[:]
    def stats_preceding(row):
        for stat in stats:
            for year in years:
                for league in leagues:
                    for year_preceding in years_preceding:
                        if year == row["year_0"] - year_preceding:
                            row[(stat, year_preceding, league)] = row[(stat, year, league)]
        return row
    df = df.apply(lambda x: stats_preceding(x), axis=1)

    # Drop unnecessary data, keep:
    #   transfer info
    #   player attributes
    #   stats for preceding seasons

    # ALL player stats, ALL years, ALL leagues
    def clean_df(df):
        for stat in stats:
            for year in years:
                for league in leagues:
                    df = df.drop(columns=[(stat, year, league)])
        return df
    df = clean_df(df)

    # drop some columns manually
    df = df.drop(columns=["expiry_date", "date_birth", "window_start"])

    # add non-numeric attributes to columns in binary format
    # (e.g. right_foot: 1 for yes and 0 for no)
    def non_num_to_cols(df):
        # list of non-numeric columns
        non_numerics = ["left_club_url", "joined_club_url", "citizenship", "position", "foot"]
        for non_numeric in non_numerics:
            # get list of unique items for a given attribute
            columns = df[non_numeric].unique()
            for i in range(len(columns)):
                columns[i] = "{}_@_{}".format(non_numeric, columns[i])

            # create empty df_tmp with columns=columns  and merge with df
            df_tmp = pd.DataFrame(index=df.index, columns=columns)
            df = df.join(df_tmp)

            # fill new columns with binary values
            def bin_val(row):
                for column in columns:
                    attribute = re.split("_@_", column)[1]
                    if row[non_numeric] == attribute:
                        row[column] = 1
                    else:
                        row[column] = 0
                return row
            df = df.apply(lambda x: bin_val(x), axis=1)
        return df
    df = non_num_to_cols(df)

    # write dataframe to JSON
    path = path[:-7] + "14.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return df


# CLUBS - EMPTY DATAFRAME
def step_15(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Create an empty dataframe for club's attributes: index = unique left and joined urls combined,
    columns = "attributes" and save to JSON file
    """

    # increment step value by one
    step += 1

    # read JSON file AND convert column names to tuples
    df = pd.read_json(path)
    df = cols_to_tuple(df)

    # get list of columns to collect "club_urls" from
    columns = ["left_club_url", "joined_club_url"]
    years_preceding = seasons_preceding_global[:]
    leagues = tournaments_global.keys()
    for year_preceding in years_preceding:
        for league in leagues:
            columns.append(("club_url", year_preceding, league))

    # export all club_url's in df and filter out None/NaN
    club_url = []
    for column in columns:
        if len(df) > 0:
            club_url += list(df[column])
    data = {"club_url": club_url}
    df = pd.DataFrame(data).dropna()

    # list of unique club_url's
    club_url = df["club_url"].unique()

    # create dataframe to store club attributes
    df = pd.DataFrame(index=club_url, columns=["attributes"])

    # write dataframe to NEW JSON
    path = path[:-7] + "15.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# CLUBS - GET CLUB ATTRIBUTES
def step_16(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Open JSON file and UPDATE it (i.e. write directly to input JSON file)
    with club attributes
    """

    # increment step value by one
    step += 1

    # read JSON file AND convert column names to tuples
    df = pd.read_json(path)
    df = cols_to_tuple(df)

    # get dict with club attributes and write to JSON file
    index = df.index
    for label in index[start_row:]:
        time_start = datetime.now()
        df.at[label, "attributes"] = get_club_attributes(label)
        df.to_json(path)
        time_diff = datetime.now() - time_start

        # print status and write new row to csv
        left = len(index) - start_row - 1
        print("Row {} updated in {} seconds, {} rows left to update.".format(start_row, time_diff, left))
        if start_row < len(index) - 1:
            # update start_row value
            set_inputs(start_row=start_row+1)
            start_row += 1
        else:
            # reset start_row to zero and update step value
            set_inputs(start_row=0, step=step)

    return path


# CLUBS - UNPACK CLUB ATTRIBUTES AND PROCESS DATA
def step_17(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Read JSON file, unpack attributes from dictionary to dataframe,
    filter and process data and write to a NEW JSON file
    """

    # increment step value by one
    step += 1

    # read JSON file AND convert column names to tuples
    df = pd.read_json(path)
    df = cols_to_tuple(df)

    # unpack player attributes from dictionary to dataframe, drop NaN and "attributes" column
    def unpack_attr(row):
        for attr in row["attributes"][0].keys():
            row[attr] = row["attributes"][0][attr]
        return row
    df = df.apply(lambda x: unpack_attr(x), axis=1).drop(columns=["attributes"]).dropna()

    # write dataframe to JSON
    path = path[:-7] + "17.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# CLUBS - EMPTY DATAFRAME FOR STATS NATIONAL
def step_18(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Create an empty dataframe: index = club_url's, columns = product of ("club_stats_national", "seasons" and "stats")
     and save to JSON file
    """

    # increment step value by one
    step += 1

    # read JSON file AND convert column names to tuples
    df = pd.read_json(path)
    df = cols_to_tuple(df)

    # create dataframe to store stats
    stats = club_stats_league[1:] # EXCEPT for the league - it's part of the tuple
    years = seasons_global[:]
    league_tiers = list(tournaments_global.keys())[1:10] # tiers 1-6, play-offs, reserve league and youth league
    columns = list(itertools.product(stats, years))
    columns = list(itertools.product(columns, league_tiers))
    for i in range(len(columns)):
        columns[i] = (columns[i][0][0], columns[i][0][1], columns[i][1])
    df = pd.DataFrame(index=df.index, columns=columns)

    # write dataframe to NEW JSON
    path = path[:-7] + "18.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# CLUBS - GET STATS NATIONAL
def step_19(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Open JSON file and UPDATE it (i.e. write directly to input JSON file)
    with clab national stats (see "get_club_stats_national" function for details).
    """

    # increment step value by one
    step += 1

    # read JSON file AND convert column names to tuples
    df = pd.read_json(path)
    df = cols_to_tuple(df)

    # get dict with club attributes and write to JSON file
    index = df.index
    for label in index[start_row:]:
        time_start = datetime.now()
        df.loc[label] = get_club_stats_national(label)
        df.to_json(path)
        time_diff = datetime.now() - time_start

        # print status and write new row to csv
        left = len(index) - start_row - 1
        print("Row {} updated in {} seconds, {} rows left to update.".format(start_row, time_diff, left))
        if start_row < len(index) - 1:
            # update start_row value
            set_inputs(start_row=start_row+1)
            start_row += 1
        #else:
            # reset start_row to zero and update step value
            set_inputs(start_row=0, step=step)

    return path


# CLUBS - EMPTY DATAFRAME FOR STATS INTERNATIONAL
def step_20(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Create an empty dataframe: columns = ["cup_international", "season", "round", "club_url] and save to JSON file
    """

    # increment step value by one
    step += 1

    # read JSON file AND convert column names to tuples
    df = pd.read_json(path)

    # create empty dataframe
    index = df.index
    df = pd.DataFrame(columns=["club_url", "year", "cup", "round"])

    # write dataframe to NEW JSON
    path = path[:-7] + "20.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# CLUBS - GET STATS INTERNATIONAL
def step_21(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Open JSON file and UPDATE it (i.e. write directly to input JSON file)
    with club stats international (see "get_club_stats_international" function for details).
    """

    # increment step value by one
    step += 1

    # get list of club_url's
    filename = 'data({}-to-{})_18.json'.format(start_date, end_date)
    df = pd.read_json(filename)
    club_urls = df.index

    # read JSON file as created at STEP_19
    df = pd.read_json(path)

    # get club stats international, update (concat) dataframe and write to JSON
    for club_url in club_urls[start_row:]:
        time_start = datetime.now()
        df_tmp = get_club_stats_international(club_url)
        df = pd.concat([df, df_tmp], ignore_index=True)
        df.to_json(path)
        time_diff = datetime.now() - time_start

        # print status and write new row to csv
        left = len(club_urls) - start_row - 1
        print("Row {} updated in {} seconds, {} rows left to update.".format(start_row, time_diff, left))
        if start_row < len(club_urls) - 1:
            # update start_row value
            set_inputs(start_row=start_row+1)
            start_row += 1
        else:
            # reset start_row to zero and update step value
            set_inputs(start_row=0, step=step)

    return path


# CLUBS - PROCESS STATS INTERNATIONAL
def step_22(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Read JSON file process data and write to a NEW JSON file.
    """

    # increment step value by one
    step += 1

    # read JSON file
    df = pd.read_json(path)

    # change season format from "yy/yy" to "yyyy" (season start)
    # and drop all years out of the "years_global" range
    years = seasons_global[:]
    def yy_to_yyyy(row):
        if re.match("\d*/\d*", row["year"]) != None:
            year = "20" + re.split("/", row["year"])[0]
            row["year"] = int(year)
            return row
    df = df.apply(lambda x: yy_to_yyyy(x), axis=1)
    mask = (df["year"] >= years[0]) & (df["year"] <= years[-1])
    df = df[mask]

    # clean round names
    round_names = {"Round of 16": "last_16","Second Round": "2nd_round",  "First Round": "1st_round",
                   "Third Round": "3rd_round", "Quarter-Finals": "quarter_finals", "Semi-Finals": "semi-finals",
                   "Group Stage": "group_stage", "last 16": "last_16", "Qualifying Round": "qualifying_round",
                   "Final": "final", "final": "final", "Fourth Round": "4th_round", "intermediate stage": "intermediate",
                   "Winner": "winner", "Fifth Round": "5th_round", "5th round": "5th_round",
                   "group stage": "group_stage", "3rd round": "3rd_round", "Sixth Round": "6th_round",
                   "relegation round": "relegation", "4th round": "4th_round", "quarter-finals": "quarter_finals"}
    df["round"] = df["round"].apply(lambda x: round_names[x])

    # get cup names from cup_urls
    df["cup"] = df["cup"].apply(lambda x: re.split("/", x)[1])

    # filter international cups and replace cup names as per "cups_international" dict
    cups = list(cups_international.keys())
    df = df[df["cup"].isin(cups)]
    df["cup"] = df["cup"].apply(lambda x: cups_international[x])
    ### CONTROL CHECK - IF ALL STAGES ARE IN DICT ###
    # replace round names as per "rounds_global" dict
    #df["round"] = df["round"].apply(lambda x: rounds_global[x])

    # reshape dataframe: index = "club_url's, column = ("season", "cup")
    df = df.pivot(index="club_url", columns=["year", "cup"], values="round")
    df.columns = df.columns.values

    #extend dataframe
    for year in years:
        for cup in cups_international.values():
            if (year, cup) not in df.columns:
                df[(year, cup)] = 0

    # add non-numeric attributes (round) to columns in binary format

    # columns = product (round, year, cup)
    rounds = list(rounds_global.keys())
    cups = list(cups_international.values())
    columns = list(itertools.product(rounds, years))
    columns = list(itertools.product(columns, cups))
    for i in range(len(columns)):
        columns[i] = (columns[i][0][0], columns[i][0][1], columns[i][1])

    # create empty df_tmp with columns=columns  and merge with df
    df_tmp = pd.DataFrame(index=df.index, columns=columns)
    df = df.join(df_tmp)

    # fill new columns with binary values
    def bin_val(row):
        for round in rounds:
            for year in years:
                for cup in cups:
                    if pd.isna(row[(year, cup)]) != True:
                        if row[(year, cup)] == round:
                            row[(round, year, cup)] = 1
                        else:
                            row[(round, year, cup)] = 0
                    else: row[(year, cup)] = 0
        return row
    df = df.apply(lambda x: bin_val(x), axis=1)

    # drop unused columns and replace NaN's
    for year in years:
        for cup in cups_international.values():
            df = df.drop(columns=[(year, cup)])
    df = df.fillna(0)

    # write dataframe to JSON
    path = path[:-7] + "22.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return path


# CLUBS - MERGE STATS NATIONAL AND STATS INTERNATIONAL
def step_23(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Merge club stats national and club stats international into single dataframe
    and write dataframe into NEW JSON file
    """

    # increment step value by one
    step += 1

    # read club stats national dataframe
    filename = 'data({}-to-{})_18.json'.format(start_date, end_date)
    df_national = pd.read_json(filename)

    # read club stats international dataframe
    df_international = pd.read_json(path)

    # merge of dataframes - OUTER merge as some clubs do not have cup records (e.g. len left >= len right)
    df = pd.merge(left = df_national, right=df_international, left_index=True, right_index=True, how="outer")

    # cast column names to tuple
    df = cols_to_tuple(df)

    # write dataframe to JSON
    path = path[:-7] + "23.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return df


# COUNTRIES - MERGE CLUBS ATTRIBUTES, STATS
def step_24(start_date=get_start_date(), end_date=get_end_date(), start_row=get_start_row(), path=get_path(), step=get_step()):
    """
    Merge club attributes, stats [and FIFA ratings] into single dataframe, process data,
    add non-numeric attributes to columns in binary format (e.g. country: 1 for yes and 0 for no)
    and write dataframe into NEW JSON file
    """

    # increment step value by one
    step += 1

    # club attributes dataframe
    filename = 'data({}-to-{})_17.json'.format(start_date, end_date)
    df_attributes = pd.read_json(filename)

    # club stats dataframe
    df_stats = pd.read_json(path)

    # fifa ratings dataframe - read and clean
    filename = 'data({}-to-{})_01.json'.format(start_date, end_date)
    df_fifa = pd.read_json(filename)

    # merge of attributes and stats - OUTER may have no stats for some clubs (e.g. len left >= len right)
    df = pd.merge(left=df_attributes, right=df_stats, left_index=True, right_index=True, how="outer")

    # add non-numeric attributes (country) to columns in binary format

    # add columns to dataframe and fill with zero's
    countries = df["country"].unique()
    df_tmp = pd.DataFrame(index=df.index, columns=countries)
    df = df.join(df_tmp)
    for country in countries:
        df[country] = 0

    # fill new columns with binary values
    def bin_val(row):
        for country in countries:
            if row["country"] == country:
                row[country] = 1
            else:
                row[country] = 0
        return row
    df = df.apply(lambda x: bin_val(x), axis=1)
    df = df.drop(columns = "country")

    # cast column names to tuple
    df = cols_to_tuple(df)

    # write dataframe to JSON
    path = path[:-7] + "24.json"
    df.to_json(path)

    # update inputs.json and return path
    set_inputs(start_date, end_date, start_row, path, step)
    return df


### EXECUTION

run()
