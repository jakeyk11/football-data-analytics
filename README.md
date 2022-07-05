# Football-Data
This repository contains a collection of tools, scripts and projects that focus on analysis and visualisation of football data.

## Folders / Workflow
- **data_directory**: Contains a collection of raw football data used for projects. Also contains any template scripts used to import raw data from various football data APIs or services.
- **analysis_tools**: Package containing modules that support football data pre-processing, manipulation and visualisation.
- **projects**: Series of personal projects, as previewed below, that cover various elements of football data analytics.

In general, each project follows a number of logical steps:
1. Within data_directory, use template data import scripts to save data in compressed BZ2 format.
2. Create a new scipt(s) - referred to here as the main script(s) - in the project folder, and import analysis_tools modules.
3. Within main script, import required compressed BZ2 data as pandas dataframe.
4. Pre-processes and format data using relevant data_engineering module, within analysis_tools.
5. Syntehsise additional information using relevant custom_events module, within analysis_tools.
6. After completing further project work, create visualisations using relevant data_vis module, within analysis_tools.

## Projects

### 01 - World Cup 2018 Box to Box Midfielder Analysis

**Summary**: Using Statsbomb data to define the most effective box to box midfielders at the 2018 World Cup. Throughout the work, a number of custom metrics are used to quantify midfielder ability in ball winning, ball retention & creativity, and mobility. A good box to box midfielder is defined as a central midfielder that excels in each of these areas. Of key interest in this work, is the use of convex hulls as a proxy for distance covered and player mobility. The work also includes development of a number of appealing visuals, as shown below.
