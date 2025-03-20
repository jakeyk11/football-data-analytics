# Football Data Analytics
This repository contains a collection of tools, projects and resources that enable effective analysis and visualisation of football data.

## Contents

<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#introduction"> ➤ Introduction</a></li>
    <li><a href="#folder-structure"> ➤ Folder Structure</a></li>
    <li><a href="#workflow"> ➤ Workflow</a></li>
    <li><a href="#projects"> ➤ Projects</a></li>
  </ol>
</details>

## Introduction
This repository contains a collection of tools, projects and resources that aim to support the generation of meaningful insight from football data. Python is used for extraction, processing, analysis and visualisation of event data, aggregated team data, market value data and more.

The repository is broken down into mutliple projects and sub-projects, each of which aims to either perform a detailed analysis, generate some specific insight, or introduce some level of automation to football data analytics. Using the contents of this repository, a number of novel & informative visuals and text threads have been created and shared with the football data analytics community via Twitter ([@\_JKDS\_](https://twitter.com/_JKDS_)).

To support others who are wishing to develop their data analytics skills within the context of football data, I have produced a [Getting Started Guide](https://github.com/jakeyk11/football-data-analytics/blob/main/Getting%20Started%20with%20Football%20Analytics.md).

## Folder Structure

The tree below (click drop-down to expand) presents the folder structure of this git repository. Note that some individual files are omitted from the diagram for simplicity.

<details>
<summary>Show folder structure</summary>


    football-data-analytics
    │
    ├── analysis_tools
    │   ├── __init__.py
    │   ├── get_football_data.py [not included in git repo]
    │   ├── logos_and_badges.py
    │   ├── models.py    
    │   ├── pitch_zones.py
    │   ├── statsbomb_custom_events.py
    │   ├── statsbomb_data_engineering.py
    │   ├── whoscored_custom_events.py
    │   ├── whoscored_data_engineering.py
    │   ├── wyscout_data_engineering.py   
    │ 
    ├── data_directory
    │   ├── leaguetable_data
    │   ├── misc_data
    │   │   ├── articles
    │   │   ├── images
    │   ├── statsbomb_data [contents not included in git repo]
    │   ├── transfermarkt_data
    │   ├── whoscored_data [contents not included in git repo]
    │   ├── wyscout_data
    │ 
    ├── model_directory
    │   ├── pass_cluster_model
    │   │   ├── PassClusterModel65.joblib
    │   ├── xg_model
    │   │   ├── log_regression_xg_model.joblib
    │
    ├── projects
    │   ├── 00_data_import_and_misc_work
    │   │   ├── download_yt_video.py 
    │   │   ├── import_data_fbref.py
    │   │   ├── import_data_leaguetable.py
    │   │   ├── import_data_whoscored.py
    │   │   ├── scrape_data_transfermarkt.py
    │   │   ├── misc_work
    │   ├── 01_wc2018_box2box_mids
    │   │   ├── worldcup_b2b_mids.py
    │   ├── 02_player_team_valuation
    │   │   ├── team_player_value_analysis.py
    │   ├── 03_model_development_and_implementation
    │   │   ├── pass_cluster_data_collection.py
    │   │   ├── shot_xg_plot.py
    │   │   ├── xg_log_regression_model.py
    │   │   ├── xg_neural_network.py  
    │   ├── 04_match_reports
    │   │   ├── off_def_shape_report_ws.py
    │   │   ├── pass_report_ws.py
    │   │   ├── shot_report_understat.py     
    │   ├── 05_competition_reports_top_players
    │   │   ├── player_defensive_contribution.py
    │   │   ├── player_effective_carriers.py
    │   │   ├── player_effective_passers.py
    │   │   ├── player_high_defensive_actions.py    
    │   │   ├── player_impact_on_team.py    
    │   │   ├── player_penalty_takers.py
    │   │   ├── player_threat_creators.py
    │   │   ├── player_threat_creators_zonal_comparison.py
    │   ├── 06_competition_reports_top_teams
    │   │   ├── team_ball_winning.py
    │   │   ├── team_common_zonal_actions.py
    │   │   ├── team_cross_success.py   
    │   │   ├── team_delta_threat_creation.py
    │   │   ├── team_fullback_combinations.py
    │   │   ├── team_setpiece_shot_concession.py
    │   │   ├── team_threat_creation.py
    │   │   ├── xg_league_table_sb.py    
    │   ├── 07_player_reports
    │   │   ├── advanced_swarm_radar.py
    │   │   ├── player_report_fullback.py
    │   ├── 08_evolution_of_shooting
    │   │   ├── shot_characteristics_trending.py
    │   ├── 09_league_position_metric_correlation
    │   │   ├── team_metric_pts_correlation.py
    │   ├── 10_team_buildup_passes
    │   │   ├── team_pass_tendencies.py
    │   ├── 11_justice_league
    │   │   ├── justice_league.py
    │   ├── 99_private_work
    │
    ├── .gitignore
    │
    ├── Getting Started with Football Analytics.md
    │     
    ├── LICENSE 
    │ 
    ├── README.md 

</details>

## Workflow

As shown in the folder structure above, the repository contains three key folders:
- **data_directory**: Storage of raw football data used for projects.
- **analysis_tools**: Custom python package containing modules that support football data import, processing, manipulation and visualisation.
- **projects**: Series of projects that cover various elements of football data analytics. Also contains any template scripts used to import raw data from various football data APIs, websites or data services.

In general, each project follows a number of logical steps:
1. Use analysis_tools package: get_football_data module [note this module is not available within the git repo] to import required data from football data API, website or data service:
    * Save to data_directory area in compressed BZ2 format
2. Create a folder within the Projects area to store files associated with the project.
3. Create an analysis script within the new folder, and import any required modules from the analysis_tools package.
4. Pre-process and format data using data_engineering modules within the analysis_tools package.
5. Synthesise additional information using custom_events and pitch_zones modules within the analysis_tools package.
6. With data formatted appropriately, create visuals and generate insight for end-consumer. Use logos_and_badges module to bring in team/compeition logos.

## Projects

Projects are numbered based on the numerical identifier of the project folder area in which they have been undertaken and stored. Decimals are used when more than one sub-project/piece of work has been undertaken in the same folder area. For example, sub-project 2.1 and 2.2 are two seperate pieces of work that exist within project 2, which is stored within folder area 02_player_team_valuation_transfermarkt. Select a project title to expand the drop-down and find out more.

### 1 - Targeted Player & Team Performance Analysis

<details>
<summary>1.1 - World Cup 2018 Box to Box Midfielder Analysis</summary>

\
**Data Source:** Statsbomb & FIFA Match Reports

**Project Area:** [01_wc2018_box2box_mids](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/01_wc2018_box2box_mids)

**Code:** [worldcup_b2b_mids.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/01_wc2018_box2box_mids/worldcup_b2b_mids.py)

**Summary and Output:** An investigation of the most effective box to box midfielders at the 2018 World Cup. A number of custom metrics are used to score central midfielders in ball winning, ball retention & creativity, and mobility. A good box to box midfielder is defined as a central midfielder that excels in each of these areas.

<p align="center">
  <img width="45%" src="./data_directory/misc_data/images/example-1-1-1.png"> &nbsp &nbsp 
  <img width="45%" src="./data_directory/misc_data/images/example-1-1-2.png">
</p>
<p align="center">
  <img width="45%" src="./data_directory/misc_data/images/example-1-1-3.png">
</p>

</details>

### 2 - Player and Team Market Value Analysis

<details>
<summary>2.1 - Scouting Players on Goal Contribution per £m Market Value</summary>

\
**Data Source:** Transfermarkt

**Project Area:** [00_data_import_and_misc_work](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/00_data_import_and_misc_work) & [02_player_team_valuation](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/02_player_team_valuation)

**Code:** [scrape_data_transfermarkt.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/00_data_import_and_misc_work/scrape_data_transfermarkt.py) & [team_player_value_analysis.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/02_player_team_valuation/team_player_value_analysis.py)

**Summary and Output:** 
Development of a tool to scrape team and player market value information from transfermarkt.co.uk. Generation of a "scouting visual" that highlights players from a given league with a favourable combination of Age and Goal Contribution per £m market value. The work also explores the use of statistical models to predict market value based on player performance.

<p align="center">
  <img width="30%" src="./data_directory/misc_data/images/example-2-1-1.png"> &nbsp &nbsp
  <img width="30%" src="./data_directory/misc_data/images/example-2-1-2.png">
</p>
<p align="center">
  <img width="30%" src="./data_directory/misc_data/images/example-2-1-3.png"> &nbsp &nbsp
  <img width="30%" src="./data_directory/misc_data/images/example-2-1-4.png">
</p>

</details>

<details>
<summary>2.2 - Team Market Value League Table</summary>

\
**Data Source:** Transfermarkt

**Project Area:** [00_data_import_and_misc_work](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/00_data_import_and_misc_work) & [02_player_team_valuation](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/02_player_team_valuation)

**Code:** [scrape_data_transfermarkt.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/00_data_import_and_misc_work/scrape_data_transfermarkt.py) & [team_player_value_analysis.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/02_player_team_valuation/team_player_value_analysis.py)

**Summary and Output:** 
Development of a tool to scrape team and player market value information from transfermarkt.co.uk. Investigation of team under/over-performance based on league ranking and total squad value ranking.

<p align="center">
  <img width="30%" src="./data_directory/misc_data/images/example-2-2-1.png"> &nbsp &nbsp
  <img width="30%" src="./data_directory/misc_data/images/example-2-2-2.png">
</p>

</details>

### 3 - Model Development and Implementation

<details>
<summary>3.1 - Expected Goals Modelling</summary>

\
**Data Source:** Wyscout

**Project Area:** [model_directory](https://github.com/jakeyk11/football-data-analytics/tree/main/model_directory/xg_model) & [03_model_development_and_implementation](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/03_model_development_and_implementation)

**Code:** [xg_log_regression_model.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/03_model_development_and_implementation/xg_log_regression_model.py), [xg_neural_network.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/03_model_development_and_implementation/xg_neural_network.py) & [shot_xg_plot.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/03_model_development_and_implementation/shot_xg_plot.py)

**Summary and Output:** 
Implementation and testing of basic expected goals probabilistic models. This work includes development and comparison of a logistic regression expected goals model and a neural network expected goals model, each trained off over 40000 shots taken across Europe's 'big five' leagues during the 2017/2018 season. The models are used to calculate expected goals for specific players, clubs and leagues over a defined time period.

<p align="center">
  <img width="40%" src="./data_directory/misc_data/images/example-3-1-1.png"> &nbsp &nbsp
  <img width="40%" src="./data_directory/misc_data/images/example-3-1-2.png">
</p>
<p align="center">
  <img width="30%" src="./data_directory/misc_data/images/example-3-1-3.png"> &nbsp &nbsp
  <img width="30%" src="./data_directory/misc_data/images/example-3-1-4.png"> &nbsp &nbsp
  <img width="30%" src="./data_directory/misc_data/images/example-3-1-5.png">
</p>

</details>

<details>
<summary>3.2 - Pass Cluster Modelling</summary>

\
**Data Source:** Opta

**Project Area:** [model_directory](https://github.com/jakeyk11/football-data-analytics/tree/main/model_directory/pass_cluster_model), [03_model_development_and_implementation](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/03_model_development_and_implementation) & [External Repo: ml_models_collection](https://github.com/jakeyk11/ml-models-collection)

**Code:** [pass_cluster_data_collection.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/03_model_development_and_implementation/pass_cluster_data_collection.py), [models.py](https://github.com/jakeyk11/football-data-analytics/blob/main/analysis_tools/models.py), [External Repo: ml_model.ipynb](https://github.com/jakeyk11/ml-models-collection/blob/main/Football%20Pass%20Clustering/ml_model.ipynb)

**Summary and Output:** 
Using 5,000,000+ passes withn Europe's "Big 5" leagues (Opta data, 2019/20 - 2022/23), I have constructed a clustering model that is able to assign successful passes to one of 65 clusters. This work involves the construction of a machine learning pipeline and testing of a variety of classification algorithms. The chosen model uses a k Means clustering algorithm to assign passes, which I have then packaged up within a clustering function to support many of my football analytics projects.

</details>

<details>
<summary>3.3 - Expected Points Modelling</summary>

\
**Data Source:** Statsbomb

**Project Area:** [analysis_tools](https://github.com/jakeyk11/football-data-analytics/tree/main/analysis_tools/)

**Code:** [models.py](https://github.com/jakeyk11/football-data-analytics/blob/main/analysis_tools/models.py)

**Summary and Output:** 
Implementation of a Monte-Carlo method to model the probability of individual match outcomes based on shot events and their associated expected goals (xG). A large number (10000+) of simulations are run on a given match to approximate win probability for each team, and draw probability. Expected points in a given match is then simply calculated as 3 × win_probability + 1 × draw_proability. The method adopted is reliant on the assumption that xG represents scoring probability, and that individual shot events are independent.

</details>

### 4 - Automated Match Reporting

<details>
<summary>4.1 - Shot Report</summary>

\
**Data Source:** Understat

**Project Area:** [04_match_reports](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/04_match_reports)

**Code:** [shot_report_understat.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/04_match_reports/shot_report_understat.py)

**Summary and Output:** 
Development of a script to extract shot data from understat and generate shot reports for a any selected match.

<p align="center">
  <img width="40%" src="./data_directory/misc_data/images/example-4-1-1.png"> &nbsp &nbsp
  <img width="40%" src="./data_directory/misc_data/images/example-4-1-2.png">
</p>

</details>

<details>
<summary>4.2 - Inter-zone Pass Flow Report</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [04_match_reports](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/04_match_reports)

**Code:** [pass_report_ws.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/04_match_reports/pass_report_ws.py)

**Summary and Output:** 
Design and development of an algorithm that identifies and counts similar passes based on the area of the pitch in which they start and finish. Generation of inter-zone pass flow reports for any selected match. 

<p align="center">
  <img width="30%" src="./data_directory/misc_data/images/example-4-2-1.png"> &nbsp &nbsp
  <img width="30%" src="./data_directory/misc_data/images/example-4-2-2.png"> 
</p>

</details>

<details>
<summary>4.3 - Offensive and Defensive Shape Report</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [04_match_reports](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/04_match_reports)

**Code:** [pass_report_ws.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/04_match_reports/off_def_shape_report_ws.py)

**Summary and Output:** 
Design and development of an algorithm to calculate player territories based on the positions of all in-play actions throughout a match, including removal of outliers. Generation of shape reports for any selected match, including calculation of territory area as a proxy for pitch area covered.

<p align="center">
  <img width="30%" src="./data_directory/misc_data/images/example-4-3-1.png"> &nbsp &nbsp
  <img width="30%" src="./data_directory/misc_data/images/example-4-3-2.png"> 
</p>

</details>

### 5 - Player Ranking over a Competition

<details>
<summary>5.1 - Top Defensive Contributors</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [05_competition_reports_top_players](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/05_competition_reports_top_players)

**Code:** [player_defensive_contribution.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/05_competition_reports_top_players/player_defensive_contribution.py)

**Summary and Output:** 
Assessment of all players' defensive contribution over the duration of a competition, with identification of top players by metrics such as Recoveries and Ball Wins per 100 opposition touches. Work includes implentation of a diamond scatter diagram that can be re-used for any 2D scatter plot.

<p align="center">
  <img width="27.3%" src="./data_directory/misc_data/images/example-5-1-1.png"> &nbsp &nbsp
  <img width="27.3%" src="./data_directory/misc_data/images/example-5-1-2.png"> 
</p>

</details>

<details>
<summary>5.2 - Top Forward Pressers</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [05_competition_reports_top_players](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/05_competition_reports_top_players)

**Code:** [player_defensive_contribution.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/05_competition_reports_top_players/player_defensive_contribution.py)

**Summary and Output:** 
Assessment of the number of defensive actions completed in the opposition third by all players' over the duration of a competition, giving an indication at who has a tendency to defend from the front.

<p align="center">
  <img width="45%" src="./data_directory/misc_data/images/example-5-2-1.png"> &nbsp &nbsp
  <img width="45%" src="./data_directory/misc_data/images/example-5-2-2.png"> 
</p>

</details>

<details>
<summary>5.3 - Top Passers</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [05_competition_reports_top_players](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/05_competition_reports_top_players)

**Code:** [player_effective_passers.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/05_competition_reports_top_players/player_effective_passers.py)

**Summary and Output:** 
Identification of effective passers through assessment of all in-play passes completed over the duration of a competition. Metrics such as progressive passes, cumulative expected threat and passes into opposition box per 90 are used to identify top players. This work involves the implementation of an [expected threat model](https://karun.in/blog/data/open_xt_12x8_v1.json) developed by Karun Singh.

<p align="center">
  <img width="45%" src="./data_directory/misc_data/images/example-5-3-1.png"> &nbsp &nbsp
  <img width="27.3%" src="./data_directory/misc_data/images/example-5-3-3.png">
</p>
<p align="center">
  <img width="45%" src="./data_directory/misc_data/images/example-5-3-2.png"> &nbsp &nbsp
</p>

</details>

<details>
<summary>5.4 - Top Ball Carriers</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [05_competition_reports_top_players](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/05_competition_reports_top_players)

**Code:** [player_effective_carriers.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/05_competition_reports_top_players/player_effective_carriers.py)

**Summary and Output:** 
Identification of effective carriers through assessment of carries completed over the duration of a competition. This work involves the development of a module to infer carry events from opta event data (as carries are not recorded).

<p align="center">
  <img width="45%" src="./data_directory/misc_data/images/example-5-4-1.png"> &nbsp &nbsp
  <img width="45%" src="./data_directory/misc_data/images/example-5-4-2.png">
</p>

</details>

<details>
<summary>5.5 - Top Threat Creators</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [05_competition_reports_top_players](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/05_competition_reports_top_players)

**Code:** [player_effective_carriers.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/05_competition_reports_top_players/player_threat_creators.py)

**Summary and Output:** 
Identification of top threat creators through assessment of various events/actions completed over the duration of a competition within different areas of the pitch. This work involves the implementation of an [expected threat model](https://karun.in/blog/data/open_xt_12x8_v1.json) developed by Karun Singh.

<p align="center">
  <img width="27.3%" src="./data_directory/misc_data/images/example-5-5-1.png"> &nbsp &nbsp
  <img width="27.3%" src="./data_directory/misc_data/images/example-5-5-2.png">
</p>
<p align="center">
  <img width="27.3%" src="./data_directory/misc_data/images/example-5-5-3.png"> &nbsp &nbsp
  <img width="27.3%" src="./data_directory/misc_data/images/example-5-5-4.png">
</p>

</details>

<details>
<summary>5.6 - Top Penalty Takers</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [05_competition_reports_top_players](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/05_competition_reports_top_players)

**Code:** [player_threat_creators.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/05_competition_reports_top_players/player_penalty_takers.py)

**Summary and Output:** 
Identification of top penalty takers across multiple competitions. Penalty quality is assessed my mean distance of on-target penalty from goalkeeper midriff, with off-target penalties assigned a distance of zero. This work includes implementation of "3D projections" within 2D subplots.

<p align="center">
  <img width="45%" src="./data_directory/misc_data/images/example-5-6-1.png"> &nbsp &nbsp
  <img width="45%" src="./data_directory/misc_data/images/example-5-6-2.png">
</p>

</details>

<details>
<summary>5.7 - Player Impact on their Team</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [05_competition_reports_top_players](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/05_competition_reports_top_players)

**Code:** [player_impact_on_team.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/05_competition_reports_top_players/player_impact_on_team.py)

**Summary and Output:** 
Determination of how a team's aggregrated metrics (team expected threat, team expected threat conceded, team expected threat difference, etc) vary when a specific player is on the pitch vs. when they are not playing

<p align="center">
  <img width="45%" src="./data_directory/misc_data/images/example-5-7-1.png"> &nbsp &nbsp
  <img width="45%" src="./data_directory/misc_data/images/example-5-7-2.png">
</p>

</details>

### 6 - Team Ranking over a Competition

<details>
<summary>6.1 - Zones of Threat Creation</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [06_competition_reports_top_teams](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/06_competition_reports_top_teams)

**Code:** [team_threat_creation.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/06_competition_reports_top_teams/team_threat_creation.py)

**Summary and Output:** 
Ranking of teams by total threat created through in-play passes and carries per 90, including identification of the zones in which each team generates threat.

<p align="center">
  <img width="37%" src="./data_directory/misc_data/images/example-6-1-1.png"> &nbsp &nbsp
  <img width="37%" src="./data_directory/misc_data/images/example-6-1-2.png">
</p>

</details>

<details>
<summary>6.2 - Zones of Possession Gain</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [06_competition_reports_top_teams](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/06_competition_reports_top_teams)

**Code:** [team_ball_winning.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/06_competition_reports_top_teams/team_ball_winning.py)

**Summary and Output:** 
Ranking of teams by the mean height up the pitch that they win the ball back, including identification of the zones in which they gain possession of the ball from the opposition.

<p align="center">
  <img width="37%" src="./data_directory/misc_data/images/example-6-2-1.png"> &nbsp &nbsp
  <img width="37%" src="./data_directory/misc_data/images/example-6-2-2.png">
</p>
  
</details>

<details>
<summary>6.3 - Effective Crossing Teams</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [06_competition_reports_top_teams](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/06_competition_reports_top_teams)

**Code:** [team_cross_success.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/06_competition_reports_top_teams/team_cross_success.py)

**Summary and Output:** 
Ranking of teams by in-play cross success rate. This work includes a custom definition of an effective (or successful) cross, where an effective cross is one that is followed by either a shot or key pass within 5 seconds of play (irrespective of the inital cross outcome).

<p align="center">
  <img width="37%" src="./data_directory/misc_data/images/example-6-3-1.png">
</p>
  
</details>

<details>
<summary>6.4 - Full-back Combinations</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [06_competition_reports_top_teams](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/06_competition_reports_top_teams)

**Code:** [team_fullback_combinations.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/06_competition_reports_top_teams/team_fullback_combinations.py)

**Summary and Output:** 
Ranking of teams by the frequency in which their full backs combine. Passes between full-backs of each team are identified and highlighted based on whether the pass leads to a shot on goal.
  
<p align="center">
  <img width="37%" src="./data_directory/misc_data/images/example-6-4-1.png">
</p>
  
</details>

<details>
<summary>6.5 - Change in Threat Creation by Zone</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [06_competition_reports_top_teams](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/06_competition_reports_top_teams)

**Code:** [team_delta_threat_creation.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/06_competition_reports_top_teams/team_delta_threat_creation.py)

**Summary and Output:** 
Ranking of teams by improvement in total threat created through in-play passes and carries per 90 - current season vs. last season. Includes accounting for teams that were in division above or below in previous year. Change in threat creation is also broken down by pitch zone
  
<p align="center">
  <img width="37%" src="./data_directory/misc_data/images/example-6-5-1.png"> &nbsp &nbsp
  <img width="37%" src="./data_directory/misc_data/images/example-6-5-2.png">
</p>
  
</details>

<details>
<summary>6.6 - Set-piece Chance Concession</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [06_competition_reports_top_teams](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/06_competition_reports_top_teams)

**Code:** [team_setpiece_shot_concession.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/06_competition_reports_top_teams/team_setpiece_shot_concession.py)

**Summary and Output:** 
Investigation of team's ability to defend set-pieces through aggregating chances conceded within 5 seconds of an opposition "indirect" set-piece. "Indirect" set-pieces refer to corner and free-kicks where the ball remains in play after the set-piece is taken, therefore off-target free-kicks and direct goals from set-pieces are excluded from the analysis.
  
<p align="center">
  <img width="30%" src="./data_directory/misc_data/images/example-6-6-1.png"> &nbsp &nbsp
  <img width="30%" src="./data_directory/misc_data/images/example-6-6-2.png">
</p>
  
</details>

<details>
<summary>6.7 - Expected Goals League Table</summary>

\
**Data Source:** Statsbomb

**Project Area:** [06_competition_reports_top_teams](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/06_competition_reports_top_teams)

**Code:** [xg_league_table_sb.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/06_competition_reports_top_teams/xg_league_table_sb.py)

**Summary and Output:** 
Generation of various league table rankings based on team's xG, xG performance, xG/xT ratio and various other metrics.
  
<p align="center">
  <img width="50%" src="./data_directory/misc_data/images/example-6-7-1.png">
</p>
  
</details>

### 7 - Automated Player Reports

<details>
<summary>7.1 - Full-back Reports</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [07_player_reports](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/07_player_reports)

**Code:** [player_report_fullback.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/07_player_reports/player_report_fullback.py)

**Summary and Output:** 
Player report specific to full-backs, including development of a flexible/robust mechanism to compare the report subject to similar players, and then rank the set of players against all full-backs within a chosen league.
  
<p align="center">
  <img width="45%" src="./data_directory/misc_data/images/example-7-1-1.png"> &nbsp &nbsp
  <img width="45%" src="./data_directory/misc_data/images/example-7-1-2.png">
</p>
  
</details>

<details>
  
<summary>7.2 - Swarm Radars</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [07_player_reports](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/07_player_reports)

**Code:** [advanced_swarm_radar.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/07_player_reports/advanced_swarm_radar.py)

**Summary and Output:** 
Development of a novel and innovative means of visualising player performance. The "swarm" radar can quickly profile, assess and compare players but also gives a deeper context through displauomg the distributions of metric scores amongst a pool of comparison players.

<p align="center">
  <img width="30%" src="./data_directory/misc_data/images/example-7-2-1.png"> &nbsp &nbsp
  <img width="30%" src="./data_directory/misc_data/images/example-7-2-2.png">
</p>
  
</details>

### 8 - Evolution of Shooting

<details>

<summary>8.1 - Evolution of Shooting in the Premier League</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [08_evolution_of_shooting](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/08_evolution_of_shooting)

**Code:** [shot_characteristics_trending.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/08_evolution_of_shooting/shot_characteristics_trending.py)

**Summary and Output:** 
A piece of work contracted by the Association of Professional Football Analysis (APFA), exploring how the art of shooting is changing in football and providing an insight into the evolution of shooting in the Premier League. 

[APFA - The Evolution of Shooting in the Premier League Web Article](https://apfa.io/the-evolution-of-shooting-in-the-premier-league/)

[APFA - The Evolution of Shooting in the Premier League.pdf](https://github.com/jakeyk11/football-data-analytics/blob/main/data_directory/misc_data/articles/The%20Evolution%20of%20Shooting%20in%20the%20Premier%20League.pdf)

</details>

### 9 - League Position and Metrics Correlation

<details>

<summary>9.1 - Team Metrics vs. Points</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [09_league_position_metric_correlation](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/09_league_position_metric_correlation)

**Code:** [team_metrics_pts_correlation.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/09_league_position_metric_correlation/team_metrics_pts_correlation.py)

**Summary and Output:** 
Exploratory work to identify the characteristics of successful teams in specific leagues. Investigation of how strongly a range of team metrics correlate with points accumulated in a season, using data from 5+ seasons. Output from this project was included in a [Tifo Video - Why Everton are better than you think](https://www.youtube.com/watch?v=Zcn5HyoBafw&ab_channel=TifoIRL).

<p align="center">
  <img width="38%" src="./data_directory/misc_data/images/example-9-1-2.png"> &nbsp &nbsp
  <img width="46%" src="./data_directory/misc_data/images/example-9-1-1.png">
</p>

</details>

### 10 - Team Build-up Passes

<details>

<summary>10.1 - Team Passing Tendencies at start of Build-up</summary>

\
**Data Source:** Opta/Whoscored

**Project Area:** [10_team_buildup_passes](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/10_team_buildup_passes)

**Code:** [team_pass_tendencies.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/10_team_buildup_passes/team_pass_tendencies.py)

**Summary and Output:** 
Exploitation of previous work on pass clustering to identify passing tendencies of teams in build-up. This inolves looking at common pass clusters for the first 6 passes that a team makes in various areas of the pitch.

<p align="center">
  <img width="40%" src="./data_directory/misc_data/images/example-10-1-1.png"> &nbsp &nbsp
  <img width="40%" src="./data_directory/misc_data/images/example-10-1-2.png">
</p>

</details>

### 11 - The Justice League

<details>

<summary>11.1 - Justice League Table</summary>

\
**Data Source:** Statsbomb

**Project Area:** [11_justice_league](https://github.com/jakeyk11/football-data-analytics/tree/main/projects/11_justice_league)

**Code:** [justice_league.py](https://github.com/jakeyk11/football-data-analytics/blob/main/projects/11_justice_league/justice_league.py)

**Summary and Output:** 
Exploitation of previous work on points modelling to simulate a full season of matches and re-produce league table standings based on probablistic match outcomes (or expected points).

<p align="center">
  <img width="50%" src="./data_directory/misc_data/images/example-11-1-1.png"> &nbsp &nbsp
</p>

</details>
