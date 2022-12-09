# Football Data Analytics
This repository contains a collection of tools, scripts and projects that focus on analysis and visualisation of football data.

## Contents

<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#project-description"> ➤ Project Description </a></li>
    <li><a href="#folder-structure"> ➤ Folder Structure</a></li>
    <li><a href="#workflow"> ➤ Workflow</a></li>
    <li>
      <a href="#projects"> ➤ Projects</a>
      <ul>
        <li><a href="#01---world-cup-2018-box-to-box-midfielder-analysis">01 - World Cup 2018 Box to Box Midfielder Analysis</a></li>
        <li><a href="#02---transfermarkt-web-scrape-and-analyse">02 - Transfermarkt Web-Scrape and Analyse</a></li>
        <li><a href="#03---expected-goals-modelling">03 - Expected Goals Modelling</a></li>
        <li><a href="#04---automated-match-reporting">04 - Automated Match Reporting</a></li>
        <li><a href="#05---automated-competition-reporting">05 - Automated Competition Reporting</a></li>
      </ul>
    </li>
  </ol>
</details>

## Project Description
This repository contains a collection of projects that aim to generate meaningful insight from football data. Python is used for extraction, processing, analysis and visualisation of event data, aggregated team data, market value data and more. The project is broken down into sub-projects, each of which aims to either perform a specific analysis, generate some specific insight, or introduce automation to football data analytics. Using the contents of this repository, a number of novel & informative visuals and text threads have been created and shared with the football data analytics community via Twitter [(@_JKDS_)](https://twitter.com/_JKDS_).

## Folder Structure

    football-data-analytics
    │
    ├── analysis_tools
    │   ├── __init__.py
    │   ├── get_football_data.py [not included in git repo]
    │   ├── logos_and_badges.py
    │   ├── pitch_zones.py
    │   ├── statsbomb_custom_events.py
    │   ├── statsbomb_data_engineering.py
    │   ├── whoscored_custom_events.py
    │   ├── whoscored_data_engineering.py
    │   ├── wyscout_data_engineering.py   
    │ 
    ├── data_directory
    │   ├── misc_data
    │   │   ├── images
    │   │   │   ├── ___.png
    │   │   ├── log_regression_xg_data.pbz2
    │   │   ├── neural_net_xg_data.pbz2
    │   │   ├── worldcup_2010_to_2018_distcovered.xlsx
    │   ├── statsbomb_data [not included in git repo]
    │   ├── transfermarkt_data
    │   ├── whoscored_data [not included in git repo]
    │   ├── wyscout_data
    │
    ├── projects
    │   ├── 00_misc_work
    │   │   ├── saudi_arabia_argentina_world_cup_def_actions.py 
    │   ├── 01_worldcup_b2b_midfielders
    │   │   ├── import_data_statsbomb.py
    │   │   ├── worldcup_b2b_mids.py
    │   ├── 02_transfermarkt_scrape_and_analyse
    │   │   ├── championship_forward_value_analysis.py
    │   │   ├── premierleague_forward_value_analysis.py
    │   │   ├── scrape_data_transfermarkt.py
    │   ├── 03_xg_model
    │   │   ├── shot_xg_plot.py
    │   │   ├── xg_log_regression_model.py
    │   │   ├── xg_neural_network.py  
    │   ├── 04_match_reports
    │   │   ├── import_data_whoscored.py
    │   │   ├── pass_report_ws.py
    │   │   ├── shot_report_understat.py     
    │   ├── 05_competition_reports
    │   │   ├── player_defensive_contribution.py   
    │   │   ├── player_effective_passers.py
    │   │   ├── player_high_defensive_actions.py    
    │   │   ├── player_penalty_takers.py
    │   │   ├── player_progressive_passers.py
    │   │   ├── team_ball_winning.py
    │   │   ├── team_threat_creation.py
    │   ├── 06_player_reports
    │   │   ├── ws_full_back_report.py
    │ 
    ├── .gitignore 
    │     
    ├── LICENSE 
    │ 
    ├── README.md 

## Workflow

As shown in the folder structure above, the project contains three key folders:
- **data_directory**: Collection of raw football data used for projects.
- **analysis_tools**: Python package containing modules that support football data import, processing, manipulation and visualisation.
- **projects**: Series of sub-projects, that cover various elements of football data analytics. Also contains any template scripts used to import raw data from various football data APIs, websites or data services.

In general, each project follows a number of logical steps:
1. Create a folder within the Projects area to store files associated with the project.
2. Use analysis_tools package > get_football_data module [note this module is not available within the git repo] to import raw data from football data API, website or data service:
    * If imported dataset is large, save to data_directory area in compressed BZ2 format and create a new script for analysis.
    * If imported dataset is small, data import and analysis can be completed in the same script (without saving data).
3. Within data analysis script import required modules from analysis_tools package.
4. Pre-process and format data using data_engineering modules within analysis_tools package.
5. Synthesise additional information using custom_events and pitch_zones modules within analysis_tools package.
6. Create visuals and generate insight for end-consumer using visualisation and logos_and_badges modules within analysis_tools package.

## Projects

Project table of contents: <br>
&nbsp; &nbsp; [01 - World Cup 2018 Box to Box Midfielder Analysis](#01---world-cup-2018-box-to-box-midfielder-analysis) <br>
&nbsp; &nbsp; [02 - Transfermarkt Web-Scrape and Analyse](#02---transfermarkt-web-scrape-and-analyse) <br>
&nbsp; &nbsp; [03 - Expected Goals Modelling](#03---expected-goals-modelling) <br>
&nbsp; &nbsp; [04 - Automated Match Reporting](#04---automated-match-reporting) <br>
&nbsp; &nbsp; [05 - Automated Competition Reporting](#05---automated-competition-reporting)

### 01 - World Cup 2018 Box to Box Midfielder Analysis

**Summary**: Use Statsbomb data to define the most effective box to box midfielders at the 2018 World Cup. Throughout the work a number of custom metrics are used to score central midfielders in ball winning, ball retention & creativity, and mobility. A good box to box midfielder is defined as a central midfielder that excels in each of these areas. Of key interest in this work is the use of convex hulls as a proxy for player mobility / distance covered. The work also includes the development of a number of appealing visuals, as shown below.

<p align="center">
  <img width="29%" src="./data_directory/misc_data/images/top_12_progressive_passers.png"> &nbsp &nbsp 
  <img width="29%" src="./data_directory/misc_data/images/top_12_pressers.png"> &nbsp &nbsp
  <img width="29%" src="./data_directory/misc_data/images/top_12_action_distribution.png">
</p>

### 02 - Transfermarkt Web-Scrape and Analyse

**Summary:** Scrape team and player market value information from transfermarkt.co.uk. This work includes the development of a "scouting tool" that highlights players from a given league that have a favourable combination of Age and Goal Contribution per £m market value. The work also explores the use of statistical models to predict market value based on player performance, as well as identifies teams that under and over-performed (league position) based on squad value.

<p align="center">
  <img width="25%" src="./data_directory/misc_data/images/GB2_player_value_regression.png"> &nbsp &nbsp
  <img width="25%" src="./data_directory/misc_data/images/GB2_player_scouting.png"> &nbsp &nbsp
  <img width="25%" src="./data_directory/misc_data/images/GB2_value_league_table.png">
</p>

### 03 - Expected Goals Modelling

**Summary:** Implementation and testing of basic expected goals probabilistic models. This work includes development and comparison of a logistic regression expected goals model and a neural network expected goals model, each trained off over 40000 shots taken across Europe's 'big five' leagues during the 2017/2018 season. The models are used to calculated expected goals for specific players, clubs and leagues over a specified time period.

<p align="center">
  <img width="35%" src="./data_directory/misc_data/images/xg_log_regression_model.png"> &nbsp &nbsp
  <img width="35%" src="./data_directory/misc_data/images/xg_neural_network.png"> &nbsp &nbsp
</p>
<p align="center">
  <img width="25%" src="./data_directory/misc_data/images/EPL-2017-Salah-Shotmap.png"> &nbsp &nbsp
  <img width="25%" src="./data_directory/misc_data/images/EPL-2017-Liverpool-Shotmap.png"> &nbsp &nbsp
  <img width="25%" src="./data_directory/misc_data/images/Bundesliga-2017-All-Shotmap.png"> &nbsp &nbsp
</p>


### 04 - Automated Match Reporting

**Summary:** Development of automated scripts to produce match reports immediately after a match has concluded. This work includes collection and processing of public-domain match event data, and the production of multiple visuals that together constitute informative and appealing match reports. Visuals currently include shot maps, inter-zone passflows, pass plots and offensive action convex hulls.

<p align="center">
  <img width="35%" src="./data_directory/misc_data/images/EPL-2022-08-06-Tottenham-Southampton.png"> &nbsp &nbsp
  <img width="35%" src="./data_directory/misc_data/images/EPL-2022-08-07-Manchester%20United-Brighton.png"> &nbsp &nbsp
</p>
<p align="center">
  <img width="25%" src="./data_directory/misc_data/images/EPL-1640700-Manchester United-Liverpool-passhulls.png"> &nbsp &nbsp
  <img width="29.55%" src="./data_directory/misc_data/images/EPL-1640709-Liverpool-Bournemouth-passreport_Liverpool.png"> &nbsp &nbsp
</p>

### 05 - Automated Competition Reporting

**Summary:** Development of automated scripts to produce competition reports and multi-match player evaluations at any point throughout a competition. This work includes collection and processing of public-domain match event data, and the production of multiple visuals that generate novel and meaningful insight at a team and player level. Visuals currently include an assessment of progressive passes, defensive actions and penalty placement.

<p align="center">
  <img width="32%" src="./data_directory/misc_data/images/EPL-2021-top-defensive-actions-per-100-opposition-passes-in-that-third.png"> &nbsp &nbsp 
  <img width="32%" src="./data_directory/misc_data/images/europe5-top-pen-takers-2019-2022.png">
</p>
<p align="center">
  <img width="24%" src="./data_directory/misc_data/images/EPL-2022-defensive-contributions-player-variant.png"> &nbsp &nbsp 
  <img width="24%" src="./data_directory/misc_data/images/EPL-2022-opposition-half-passers-player-variant.png">
</p>
