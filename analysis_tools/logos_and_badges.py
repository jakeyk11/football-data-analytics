"""Module containing functions to fetch URLs for badges and logos

Functions
---------
get_team_badge(team)
    Get URL of badge image for team of choice

get_league_badge(league)
    Get URL of league badge image
"""


def get_team_badge(team):
    """ Get URL of badge image for team of choice

    Function to return the badge image URL for the team of choice. Also defines a scale factor to ensure that images
    are sized consistently.

    Args:
        team (string): team badge to obtain.

    Returns:
        url (string): website address of team badge image
        scaling (float): scale to apply to image for consistent sizing
    """

    # Initialise returns
    url = None
    scaling = None

    if team in ['Arsenal', 'Arsenal FC']:
        url = "https://logos-world.net/wp-content/uploads/2020/05/Arsenal-Logo.png"
        scaling = 1

    if team in ['Aston Villa', 'Aston Villa FC', 'Villa']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Aston-Villa-Logo-700x394.png"
        scaling = 1

    if team in ['Bournemouth', 'AFC Bournemouth']:
        url = "https://1000logos.net/wp-content/uploads/2018/06/AFC-Bournemouth-Logo-768x432.png"
        scaling = 0.95

    if team in ['Brentford', 'Brentford FC']:
        url = "https://images.racingpost.com/football/teambadges/378.png"
        scaling = 1

    if team in ['Brighton & Hove Albion', 'Brighton']:
        url = "https://1000logos.net/wp-content/uploads/2018/06/Brighton-Hove-Albion-Logo-768x432.png"
        scaling = 0.95

    if team in ['Burnley FC', 'Burnley']:
        pass

    if team in ['Chelsea', 'Chelsea FC']:
        url = "https://logos-world.net/wp-content/uploads/2020/05/Chelsea-Logo.png"
        scaling = 1

    if team in ['Crystal Palace', 'Crystal Palace FC']:
        url = "https://boxtoboxfootball.uk/wp-content/uploads/2017/11/821px-Crystal_Palace_FC_logo.svg_-241x300.png"
        scaling = 0.9

    if team in ['Everton', 'Everton FC']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Everton-Logo-700x394.png"
        scaling = 0.9

    if team in ['Fulham', 'Fulham FC']:
        url = "https://sportslogohistory.com/wp-content/uploads/2020/11/fulham_fc_2001-pres.png"
        scaling = 5/6

    if team in ['Huddersfield Town', 'Huddersfield Town FC', 'Huddersfield']:
        pass

    if team in ['Leeds', 'Leeds United', 'Leeds United FC', 'Leeds Utd']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Leeds-United-Logo-700x394.png"
        scaling = 1

    if team in ['Leicester City', 'Leicester City FC', 'Leicester']:
        url = "https://1000logos.net/wp-content/uploads/2018/06/Leicester-City-Logo.png"
        scaling = 0.95

    if team in ['Liverpool', 'Liverpool FC']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Liverpool-Logo.png"
        scaling = 1

    if team in ['Manchester City', 'Manchested City FC', 'Man City']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Manchester-City-Logo.png"
        scaling = 1

    if team in ['Manchester United', 'Manchester United FC', 'Man United', 'Man Utd', 'Manchested Utd']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Manchester-United-logo-700x394.png"
        scaling = 0.9

    if team in ['Newcastle United', 'Newcastle United FC', 'Newcastle', 'Newcastle Utd']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Newcastle-Logo-700x394.png"
        scaling = 0.9

    if team in ['Nottingham Forest', 'Nottingham Forest FC', 'Notts Forest']:
        url = "https://upload.wikimedia.org/wikipedia/commons/6/61/Nottingham_Forest_logo.png"
        scaling = 1

    if team in ['Southampton', 'Southampton FC']:
        url = "https://1000logos.net/wp-content/uploads/2018/07/Southampton-Logo-640x400.png"
        scaling = 0.9

    if team in ['Stoke City', 'Stoke City FC', 'Stoke']:
        pass

    if team in ['Swansea City', 'Swansea City FC', 'Swansea']:
        pass

    if team in ['Tottenham Hotspur', 'Tottenham Hotspur FC', 'Tottenham', 'Spurs']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Tottenham-Hotspur-Logo-700x394.png"
        scaling = 1

    if team in ['Watford', 'Watford FC']:
        pass

    if team in ['West Bromich Albion', 'West Bromich Albion FC', 'West Brom']:
        pass

    if team in ['West Ham United', 'West Ham United FC', 'West Ham', 'West Ham Utd']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/West-Ham-Logo.png"
        scaling = 0.9

    if team in ['Wolverhampton Wanderers', 'Wolverhampton Wanderers FC', 'Wolves']:
        url = "https://logos-download.com/wp-content/uploads/2018/09/FC_Wolverhampton_Wanderers_Logo-700x606.png"
        scaling = 5/6

    return url, scaling
