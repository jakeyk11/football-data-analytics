"""Module containing functions to fetch URLs for badges and logos

Functions
---------
get_competition_logo(competition)
    Get URL of competition logo for competition of choice, and format image ready for printing

get_team_badge_and_colour(team, hoa='home' )
    Get team colourmap and get URL of badge image for team of choice, and format image ready for printing.
"""

from PIL import Image, ImageEnhance
import requests
from io import BytesIO
import matplotlib.cm as cm


def get_competition_logo(competition, year=None, logo_brighten=False):
    """ Get URL of competition logo for competition of choice, and format image ready for printing.

    Function to return the image PIL object for the competition of choice. The function ensures that images are
    consistently sized, and adds padding (of user defined colour) where appropriate.

    Args:
        competition (string):  competition logo to obtain.
        year (string, optional): start year of competition, none by default
        logo_brighten (bool, optional): selection of whether to brighten logo. Recommended for dark logos

    Returns:
        PIL Image: Formatted competition badge image.
    """

    # Initialise returns
    url = None

    if competition in ['EPL', 'Premier League', 'GB1']:
        url = "https://www.fifplay.com/img/public/premier-league-2-logo.png"

    if competition in ['EFLC', 'EFL Championship', 'Championship', 'GB2']:
        url = "https://brandlogos.net/wp-content/uploads/2022/07/efl_championship-logo_brandlogos.net_e58ej.png"

    if competition in ['EFL1', 'EFL League One', 'League One', 'GB3']:
        url = "https://a3.espncdn.com/combiner/i?img=%2Fi%2Fleaguelogos%2Fsoccer%2F500%2F25.png"

    if competition in ['EFL2', 'EFL League Two', 'League Two', 'GB4']:
        url = "https://a4.espncdn.com/combiner/i?img=%2Fi%2Fleaguelogos%2Fsoccer%2F500%2F26.png"

    if competition in ['SPL', 'Scottish Premier League', 'Scotland Premier League', 'SC1']:
        url = "https://static.wikia.nocookie.net/logopedia/images/1/16/CinchPremiership.png/"

    if competition in ['La Liga', 'La_Liga', 'La Liga Santander', 'ES1']:
        url = "https://assets.laliga.com/assets/logos/laliga-v/laliga-v-1200x1200.png"

    if competition in ['Bundesliga', 'Fußball-Bundesliga', 'Fußball Bundesliga', '1 Bundesliga', '1. Bundesliga', 'L1']:
        url = "https://1000logos.net/wp-content/uploads/2020/09/Bundesliga-Logo.png"

    if competition in ['Serie A', 'Serie_A', 'Serie A TIM', 'Lega Serie A', 'IT1']:
        url = "https://1000logos.net/wp-content/uploads/2021/10/Italian-Serie-A-logo.png"

    if competition in ['Ligue 1', 'Ligue_1', 'Ligue 1 Uber Eats', 'FR1']:
        url = "https://sportivka.net/wp-content/uploads/2021/10/Ligue_1_logo_PNG1.png"

    if competition in ['World_Cup', 'World Cup', 'FIFA World Cup']:
        if year == '2022':
            url = "https://logodownload.org/wp-content/uploads/2018/07/world-cup-2022-logo-1.png"
        if year == '2018':
            url = "https://purepng.com/public/uploads/large/purepng.com-world-cup-russia-2018-fifa-pocal-logofifawmworld-cupsoccer2018footballfussballpocalsport-31528992075ouo57.png"

    # Get image, and resize
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img = img.crop(img.getbbox())
    width, height = img.size

    if width > height:
        result = Image.new('RGBA', (width, width), color=(255, 0, 0, 0))
        result.paste(img, (0, (width - height) // 2))
    elif height > width:
        result = Image.new('RGBA', (height, height), color=(255, 0, 0, 0))
        result.paste(img, ((height - width) // 2, 0))
    else:
        result = img

    result = result.resize((300, 300))

    if logo_brighten:
        enhancer = ImageEnhance.Brightness(result)
        result = enhancer.enhance(100)

    return result


def get_team_badge_and_colour(team, hoa='home'):
    """ Get team colourmap and get URL of badge image for team of choice, and format image ready for printing.

    Function to return the image PIL object and matplotlib colourmap for the team of choice. The function ensures
    that images are consistently sized, and adds padding (of user defined colour) where appropriate.

    Args:
        team (string): team badge and colour to obtain.
        hoa (string, optional): Selection of home or away colour. Default is 'home'.

    Returns:
        PIL Image: Formatted team badge image.
        matplotlib colormap: Matplotlib colormap object.
    """

    # Initialise returns
    url = None
    cmap = None

    if team in ['AC Milan', 'A.C. Milan']:
        url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Logo_of_AC_Milan.svg/195px-Logo_of_AC_Milan.svg.png"

    if team in ['Unión Deportiva Almería', 'UD Almeria', 'U.D. Almeria', 'Almeria']:
        url = "https://seeklogo.com/images/A/almeria-ud-logo-1AEACC1508-seeklogo.com.png"

    if team in ['Athletic Club Ajaccio', 'AC Ajaccio', 'A.C. Ajaccio', 'Ajaccio']:
        url = "https://tmssl.akamaized.net/images/wappen/head/1147.png"

    if team in ['Angers SCO', 'Angers']:
        url = "https://www.angers-sco.fr/wp-content/themes/sco/images/logo_head.png"

    if team in ['Argentina']:
        url = "https://cdn.countryflags.com/thumbs/argentina/flag-round-250.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['Arsenal', 'Arsenal FC']:
        url = "https://logos-world.net/wp-content/uploads/2020/05/Arsenal-Logo.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Aston Villa', 'Aston Villa FC', 'Villa']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Aston-Villa-Logo-2008-2016.png"
        cmap = cm.get_cmap('BuPu') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Athletic Club', 'Athletic Bilbao', 'Bilbao']:
        url = "https://cdn.athletic-club.eus/imagenes/escudos/Athletic-club.png"

    if team in ['Athletico Madrid', 'Atlético de Madrid', 'Atletico']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/atletico-madrid-Logo-700x394.png"

    if team in ['FC Augsburg', 'Augsburg']:
        url = "https://www.fcaugsburg.de/bundles/exozetfrontend/fca/img/logos/augsburg-logo.png"

    if team in ['Australia']:
        url = "https://cdn.countryflags.com/thumbs/australia/flag-round-250.png"
        cmap = cm.get_cmap('YlOrBr') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Auxerre', 'AJ Auxerre']:
        url = "https://assets.stickpng.com/images/580b57fcd9996e24bc43c4c7.png"

    if team in ['Barcelona', 'FC Barcelona']:
        url = "https://logos-world.net/wp-content/uploads/2020/04/Barcelona-Logo-700x394.png"

    if team in ['Bayer 04 Leverkusen', 'Bayer Leverkusen', 'Leverkusen']:
        url = "https://assets.queue-it.net/bayer04/userdata/B04_L_CMYK.png"

    if team in ['Bayern', 'Bayern Munich', 'FC Bayern Munich', 'FC Bayern München', 'Bayern München']:
        url = "https://www.footballkitarchive.com/static/logos/Re6G2mZRQ8Q0pxb/bayern-munchen-2017-logo.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Belgium']:
        url = "https://cdn.countryflags.com/thumbs/belgium/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Birmingham', 'Birmingham FC', 'Birmingham City', 'Birmingham City FC']:
        url = "https://upload.wikimedia.org/wikipedia/en/thumb/6/68/Birmingham_City_FC_logo.svg/302px-Birmingham_City_FC_logo.svg.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Blackburn', 'Blackburn Rovers', 'Blackburn FC', 'Blackburn Rovers FC']:
        url = "https://seeklogo.com/images/B/blackburn-rovers-logo-410B37A022-seeklogo.com.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Blackpool', 'Blackpool FC']:
        url = "https://upload.wikimedia.org/wikipedia/en/thumb/d/df/Blackpool_FC_logo.svg/1200px-Blackpool_FC_logo.svg.png"
        cmap = cm.get_cmap('YlOrBr') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['VfL Bochum 1848', 'VfL Bochum', 'Bochum']:
        url = "https://brandslogos.com/wp-content/uploads/images/bochum-logo.png"

    if team in ['Bologna', 'Bologna FC', 'Bologna 1909', 'Bologna FC 1909']:
        url = "https://1000logos.net/wp-content/uploads/2021/02/Bologna-logo-768x512.png"

    if team in ['Borussia Dortmund', 'Dortmund']:
        url = "https://1000logos.net/wp-content/uploads/2017/08/BVB-Logo-768x650.png"

    if team in ['Borussia Mönchengladbach', 'Mönchengladbach', 'Borussia M.Gladbach', "Borussia M'Gladbach"]:
        url = "https://assets.sorare.com/club/67715b49-9256-47b3-ade2-444a79131864/picture/b3261021aedc02fc1c0c1145150e5713.png"

    if team in ['Bournemouth', 'AFC Bournemouth']:
        url = "https://1000logos.net/wp-content/uploads/2018/06/AFC-Bournemouth-Logo-768x432.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Bradford', 'Bradford City', 'Bradford City AFC']:
        url = "https://www.aroundthegrounds.org/media/1udayj5x/bradford.png"

    if team in ['Brazil']:
        url = "https://cdn.countryflags.com/thumbs/brazil/flag-round-250.png"
        cmap = cm.get_cmap('YlOrBr') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Brentford', 'Brentford FC']:
        url = "https://images.racingpost.com/football/teambadges/378.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Brighton & Hove Albion', 'Brighton']:
        url = "https://1000logos.net/wp-content/uploads/2018/06/Brighton-Hove-Albion-Logo-768x432.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Bristol City', 'Bristol']:
        url = "https://www.aca-creative.co.uk/wp-content/uploads/2023/02/Bristol-City-980x980.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['Bristol Rovers']:
        url = "https://png2.cleanpng.com/sh/295eb3f6febddd74810600650c8308b2/L0KzQYm4UcE4N6J4jZH0aYP2gLBuTfJzcaR5h942cnB5dcP6TfYua15yfd94cnnkfH76lPFlcaZyRddvbD33grF3iQkubZcyTdRvMHO7RbK3VPFjOmIzUaU8OUS5R4m4VcQzPWE7TaoBMEG8QXB3jvc=/kisspng-bristol-rovers-f-c-memorial-stadium-efl-trophy-ef-5bf0c85a04ab21.9339467815425065860191.png"

    if team in ['Burnley FC', 'Burnley']:
        url = "https://1000logos.net/wp-content/uploads/2018/06/Burnley-logo-768x432.png"
        cmap = cm.get_cmap('BuPu') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Cadiz', 'Cadiz CF', 'Cádiz CF', 'Cádiz']:
        url = "https://upload.wikimedia.org/wikipedia/en/thumb/5/58/C%C3%A1diz_CF_logo.svg/180px-C%C3%A1diz_CF_logo.svg.png"

    if team in ['Cameroon']:
        url = "https://cdn.countryflags.com/thumbs/cameroon/flag-round-250.png"
        cmap = cm.get_cmap('Greens') if hoa == 'home' else cm.get_cmap('Reds')

    if team in ['Canada']:
        url = "https://cdn.countryflags.com/thumbs/canada/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Cardiff City', 'Cardiff', 'Cardiff FC', 'Cardiff City FC']:
        url = "https://cdn.cardiffcityfc.co.uk/icons/team/dark/1x/id/594.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('RdPu')

    if team in ['RC Celta de Vigo', 'RC Celta Vigo', 'Celta Vigo', 'RC Celta']:
        url = "https://img.uefa.com/imgml/TP/teams/logos/100x100/53043.png"

    if team in ['Celtic', 'The Celtic Football Club', 'Celtic FC']:
        url = "https://1000logos.net/wp-content/uploads/2020/09/Celtic-logo.png"

    if team in ['Charlton', 'Charlton Athletic FC', 'Charlton Athletic']:
        url = "https://www.charltonafc.com/themes/custom/charlton/files/charlton@3x.png"

    if team in ['Chelsea', 'Chelsea FC']:
        url = "https://logos-world.net/wp-content/uploads/2020/05/Chelsea-Logo.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('YlOrBr')

    if team in ['Colchester Utd', 'Colchester United FC', 'Colchester', 'Colchester United']:
        url = "https://secure.cache.images.core.optasports.com/soccer/teams/150x150/714.png"

    if team in ['Costa Rica']:
        url = "https://cdn.countryflags.com/thumbs/costa-rica/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Coventry', 'Coventry City', 'Coventry FC', 'Coventry City FC']:
        url = "https://ssl.gstatic.com/onebox/media/sports/logos/KHpmY4tIwqiutl8Cfl0MAw_96x96.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('Purples')

    if team in ['U.S. Cremonese', 'US Cremonese', 'Cremonese']:
        url = "https://www.uscremonese.it/wp-content/themes/uscremonese/images/logo-footer.png"

    if team in ['Croatia']:
        url = "https://cdn.countryflags.com/thumbs/croatia/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Crystal Palace', 'Crystal Palace FC']:
        url = "https://upload.wikimedia.org/wikipedia/hif/c/c1/Crystal_Palace_FC_logo.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Derby', 'Derby County', 'Derby County FC', 'Derby FC']:
        url = "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/374.png"

    if team in ['Denmark']:
        url = "https://cdn.countryflags.com/thumbs/denmark/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Dundee', 'Dundee Utd', 'Dundee United']:
        url = "https://1.bp.blogspot.com/-WldxYkjszRo/X11HMOt_BPI/AAAAAAAAE4g/pv7COcN4ctkBcWKFvlZdf2paYx06KPQIgCLcBGAsYHQ/s1600/Dundee%2BUnited%2BF.%2BC..png"

    if team in ['Ecuador']:
        url = "https://cdn.countryflags.com/thumbs/ecuador/flag-round-250.png"
        cmap = cm.get_cmap('YlOrBr') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Eintracht Frankfurt']:
        url = "https://assets-sports.thescore.com/soccer/team/115/logo.png"

    if team in ['England']:
        url = "https://cdn.countryflags.com/thumbs/england/flag-round-250.png"
        cmap = cm.get_cmap('Greys') if hoa == 'home' else cm.get_cmap('Reds')

    if team in ['Everton', 'Everton FC']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Everton-Logo-700x394.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('RdPu')

    if team in ['Fiorentina', 'ACF Fiorentina']:
        url = "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f2/2022_ACF_Fiorentina_logo.svg/240px-2022_ACF_Fiorentina_logo.svg.png"

    if team in ['Forest Green', 'Forest Green Rovers FC', 'Forest Green Rovers']:
        url = "https://www.fgr.co.uk/static/fgr-logo-244366e93842f383f8a3b515ed76edc3.png"

    if team in ['France']:
        url = "https://cdn.countryflags.com/thumbs/france/flag-round-250.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['SC Freiburg', 'Freiburg']:
        url = "https://www.scfreiburg.com/images/logo-socialshare.png"

    if team in ['Fulham', 'Fulham FC']:
        url = "https://sportslogohistory.com/wp-content/uploads/2020/11/fulham_fc_2001-pres.png"
        cmap = cm.get_cmap('Greys') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['Germany']:
        url = "https://cdn.countryflags.com/thumbs/germany/flag-round-250.png"
        cmap = cm.get_cmap('Greys') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['Getafe Club de Fútbol', 'Getafe CF', 'Getafe']:
        url = "https://www.getafecf.com/Portals/0/logo120.png"

    if team in ['Ghana']:
        url = "https://cdn.countryflags.com/thumbs/ghana/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Girona', 'Girona FC']:
        url = "https://d2zywfiolv4f83.cloudfront.net/img/teams/2783.png"

    if team in ['Hartlepool', 'Hartlepool United FC', 'Hartlepool United']:
        url = "https://static.wikia.nocookie.net/fifa/images/c/c5/Hartlepool_United_FC.png"

    if team in ['Heart of Midlothian FC', 'Heart of Midlothian', 'Hearts', 'Hearts FC']:
        url = "https://cdn.freebiesupply.com/logos/large/2x/hearts-logo-png-transparent.png"

    if team in ['Hellas Verona FC', 'Hellas Verona', 'Verona']:
        url = "https://hellas.hqcdn.it/media?f=2020/09/verona-alt.png"

    if team in ['Hertha BSC', 'Hertha Berlin', 'Herta', 'Hertha BSC Berlin']:
        url = "https://b.fssta.com/uploads/application/soccer/team-logos/hertha-bsc-berlin.vresize.220.220.medium.0.png"

    if team in ['Hibernian FC', 'Hibernian', 'Hibs']:
        url = "https://cdn.freebiesupply.com/logos/large/2x/hibernian-edinburgh-fc-logo-png-transparent.png"

    if team in ['Hoffenheim', 'TSG 1899 Hoffenheim']:
        url = "https://www.tsg-hoffenheim.de/resources/themes/1899relaunch/images/Hoffenheim_Logo.png"

    if team in ['Huddersfield Town', 'Huddersfield Town FC', 'Huddersfield']:
        url = "https://upload.wikimedia.org/wikipedia/en/7/7d/Huddersfield_Town_A.F.C._logo.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Hull', 'Hull City FC', 'Hull City']:
        url = "https://upload.wikimedia.org/wikipedia/en/thumb/5/54/Hull_City_A.F.C._logo.svg/379px-Hull_City_A.F.C._logo.svg.png"
        cmap = cm.get_cmap('Oranges') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Ibiza', 'Unión Deportiva Ibiza', 'UD Ibiza']:
        url = "https://upload.wikimedia.org/wikipedia/en/thumb/a/a8/Shield_of_UD_Ibiza.png/285px-Shield_of_UD_Ibiza.png"

    if team in ['Inter', 'Inter Milan', 'FC Internazionale Milano']:
        url = "https://cdn.resfu.com/img_data/equipos/60505.png"

    if team in ['Ipswich', 'Ipswich Town FC', 'Ipswich Town']:
        url = "https://brandslogos.com/wp-content/uploads/images/large/ipswich-town-fc-logo.png"

    if team in ['IR Iran', 'Iran']:
        url = "https://cdn.countryflags.com/thumbs/iran/flag-round-250.png"
        cmap = cm.get_cmap('gray') if hoa == 'home' else cm.get_cmap('Reds')

    if team in ['Japan']:
        url = "https://cdn.countryflags.com/thumbs/japan/flag-round-250.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Juventus', 'Juventus FC']:
        url = "https://cdn.freebiesupply.com/images/large/2x/juventus-logo-png-transparent.png"

    if team in ['Kilmarnock FC', 'Kilmarnock']:
        url = "https://kilmarnockfc.co.uk/club-crests/crest-t64.png"

    if team in ['1. FC Köln', 'FC Köln', 'Köln', '1. FC Koln', 'FC Koln', 'Koln']:
        url = "http://as01.epimg.net/img/comunes/fotos/fichas/equipos/large/94.png"

    if team in ['SS Lazio', 'S.S. Lazio', 'Lazio']:
        url = "https://proxy-media-sslazio.secure2.footprint.net/VMFS1/FILES/public/images/events/teams/logos/t129.png"

    if team in ['Leeds', 'Leeds United', 'Leeds United FC', 'Leeds Utd']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Leeds-United-Logo-700x394.png"
        cmap = cm.get_cmap('YlOrBr') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Leicester City', 'Leicester City FC', 'Leicester']:
        url = "https://1000logos.net/wp-content/uploads/2018/06/Leicester-City-Logo.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['Lens', 'RC Lens']:
        url = "https://www.rclens.fr/sites/default/files/logo.png"

    if team in ['Levante', 'Levante UD']:
        url = "https://upload.wikimedia.org/wikipedia/en/thumb/7/7b/Levante_Uni%C3%B3n_Deportiva%2C_S.A.D._logo.svg/225px-Levante_Uni%C3%B3n_Deportiva%2C_S.A.D._logo.svg.png"

    if team in ['Liverpool', 'Liverpool FC']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Liverpool-Logo.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('BuPu')

    if team in ['Luton Town', 'Luton', 'Luton Town FC']:
        url = "https://a.espncdn.com/combiner/i?img=/i/teamlogos/soccer/500/301.png"
        cmap = cm.get_cmap('Oranges') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['Olympique Lyonnais', 'Lyon']:
        url = "https://media-olfr-prd.ol.fr/uploads/assets/logo_olympique_lyonnais_8ad2b8da8f.png"

    if team in ['Manchester City', 'Manchester City FC', 'Man City']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Manchester-City-Logo.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['Manchester United', 'Manchester United FC', 'Man United', 'Man Utd', 'Manchester Utd']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Manchester-United-logo-700x394.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['Mansfield', 'Mansfield Town', 'Mansfield Town FC']:
        url = "https://ktckts-cdn.com/76610b61-f709-4947-afe3-124c15ca0c76/34c70326-80ee-40ae-873b-7a6dd5ed08c3.png"

    if team in ['Mexico']:
        url = "https://cdn.countryflags.com/thumbs/mexico/flag-round-250.png"
        cmap = cm.get_cmap('Greens') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Middlesbrough', 'Middlesbrough FC']:
        url = "https://images.webapi.gc.middlesbroughfcservices.co.uk/fit-in/200x200/7af04870-d2d4-11ec-93d3-b732dfcf0a3b.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Millwall', 'Millwall FC']:
        url = "https://www.millwallfc.co.uk/logo.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['Monaco', 'AS Monaco', 'Monaco FC', 'AS Monaco FC']:
        url = "https://www.graphicdesignforum.com/uploads/default/original/2X/5/58e71a95f670ba52bb50bc7ecbfcb89213f8b391.png"

    if team in ['Montpellier Hérault Sport Club', 'Montpellier Hérault SC', 'Montpellier HSC', 'Montpellier']:
        url = "https://static.wikia.nocookie.net/fifa/images/3/3c/HSC_Montpellier_Logo.png"

    if team in ['A.C. Monza', 'AC Monza', 'Monza']:
        url = "https://www.acmonza.com/images/logo/logo.png"

    if team in ['Morocco']:
        url = "https://cdn.countryflags.com/thumbs/morocco/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Nantes', 'FC Nantes']:
        url = "https://nantesport44.com/wp-content/uploads/2020/05/NANTES-128x128.png"

    if team in ['Nice', 'OGC Nice']:
        url = "https://1000logos.net/wp-content/uploads/2020/09/Nice-logo.png"

    if team in ['Napoli', 'SSC Napoli', 'S.S.C. Napoli']:
        url = "https://cdn-assets.sscnapoli.it/uploads/2022/08/loghi_400x400_0007_napoli.png"

    if team in ['Netherlands', 'Holland']:
        url = "https://cdn.countryflags.com/thumbs/netherlands/flag-round-250.png"
        cmap = cm.get_cmap('Oranges') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Newcastle United', 'Newcastle United FC', 'Newcastle', 'Newcastle Utd']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Newcastle-Logo-700x394.png"
        cmap = cm.get_cmap('Greys') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['Norwich', 'Norwich FC', 'Norwich City', 'Norwich City FC']:
        url = "https://assets.stickpng.com/images/580b57fcd9996e24bc43c4e9.png"
        cmap = cm.get_cmap('YlOrBr') if hoa == 'home' else cm.get_cmap('Reds')

    if team in ['Nottingham Forest', 'Nottingham Forest FC', 'Notts Forest']:
        url = "https://d2zywfiolv4f83.cloudfront.net/img/teams/174.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('YlOrBr')

    if team in ['Olympique Marseille', 'Marseille', 'OM']:
        url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Olympique_Marseille_logo.svg/255px-Olympique_Marseille_logo.svg.png"

    if team in ['Osasuna', 'CA Osasuna', 'Club Atlético Osasuna']:
        url = "https://seeklogo.com/images/C/club-atletico-osasuna-logo-3D544C850A-seeklogo.com.png"

    if team in ['Paris Saint-Germain F.C.', 'Paris Saint-Germain', 'PSG']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/PSG-Logo.png"

    if team in ['Plymouth', 'Plymouth Argyle', 'Plymouth Argyle FC']:
        url = "https://www.plymouthonlinedirectory.com/image/964/Plymouth-Argyle-Logo/original.png"

    if team in ['Poland']:
        url = "https://cdn.countryflags.com/thumbs/poland/flag-round-250.png"
        cmap = cm.get_cmap('Greys') if hoa == 'home' else cm.get_cmap('Reds')

    if team in ['Portugal']:
        url = "https://cdn.countryflags.com/thumbs/portugal/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Portsmouth', 'Portsmouth FC']:
        url = "https://img.uefa.com/imgml/TP/teams/logos/140x140/84297.png"

    if team in ['Port Vale', 'Port Vale FC']:
        url = "https://s.yimg.com/cv/apiv2/default/soccer/20181213/500x500/PortVale_wbg.png"

    if team in ['Preston', 'Preston North End', 'Preston FC', 'Preston North End FC', 'PNE', 'PNE FC']:
        url = "https://s27807.pcdn.co/wp-content/uploads/Preston-North-End-LT800-1.png"
        cmap = cm.get_cmap('Greys') if hoa == 'home' else cm.get_cmap('YlOrBr')

    if team in ['Qatar']:
        url = "https://cdn.countryflags.com/thumbs/qatar/flag-round-250.png"
        cmap = cm.get_cmap('Purples') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Queens Park Rangers', 'Queens Park Rangers FC', 'QPR']:
        url = "https://cdn.bleacherreport.net/images/team_logos/328x328/queens_park_rangers.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('BuPu')

    if team in ['Rangers', 'Glasgow Rangers', 'Rangers FC']:
        url = "https://logos-world.net/wp-content/uploads/2020/11/Rangers-Logo.png"

    if team in ['Rayo Vallecano', 'Rayo Vallecano de Madrid']:
        url = "https://seeklogo.com/images/R/Rayo_Vallecano-logo-83EC841FE5-seeklogo.com.png"

    if team in ['Reading', 'Reading FC']:
        url = "https://seeklogo.com/images/R/reading-fc-logo-E95E21532B-seeklogo.com.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Real Betis', 'Real Betis Balompié']:
        url = "https://www.thesportsdb.com/images/media/team/badge/gqmest1663330022.png"

    if team in ['Real Madrid', 'Real Madrid CF']:
        url = "https://seeklogo.com/images/R/real-madrid-c-f-logo-C08F61D801-seeklogo.com.png"

    if team in ['Real Sociedad', 'Real Sociedad SAC', 'Real Sociedad S.A.C']:
        url = "https://logos-world.net/wp-content/uploads/2020/11/Real-Sociedad-Logo.png"

    if team in ['Real Valladolid', 'Real Valladolid CF']:
        url = "https://seeklogo.com/images/R/Real_Valladolid_Club_de_Futbol-logo-E2828971A8-seeklogo.com.png"

    if team in ['RBL', 'Red Bull Leipzig', 'RB Leipzig', 'RasenBallsport Leipzig']:
        url = "https://tickets.rbleipzig.com/light_custom/lightTheme/RBLogo_Shop06.png"

    if team in ['Roma', 'AS Roma', 'A.S. Roma']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Roma-Logo.png"

    if team in ['Rotherham', 'Rotherham United', 'Rotherham FC', 'Rotherham Utd', 'Rotherham United FC']:
        url = "https://seeklogo.com/images/R/rotherham-united-fc-logo-9087864424-seeklogo.com.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('YlOrBr')

    if team in ['AS Saint-Étienne', 'Saint-Etienne', 'Saint-Étienne']:
        url = "https://upload.wikimedia.org/wikipedia/en/thumb/2/25/AS_Saint-%C3%89tienne_logo.svg/225px-AS_Saint-%C3%89tienne_logo.svg.png"

    if team in ['U.C. Sampdoria', 'UC Sampdoria', 'Sampdoria']:
        url = "https://www.sampdoria.it/wp-content/uploads/2021/08/sampdoria-logo-HIGH_01.png"

    if team in ['Saudi Arabia', 'Kingdom of Saudi Arabia', 'KSA']:
        url = "https://cdn.countryflags.com/thumbs/saudi-arabia/flag-round-250.png"
        cmap = cm.get_cmap('Greens') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['U.S. Sassuolo Calcio', 'US Sassuolo Calcio', 'Sassuolo']:
        url = "https://1000logos.net/wp-content/uploads/2018/06/Sassuolo-Logo.png"

    if team in ['Serbia']:
        url = "https://cdn.countryflags.com/thumbs/serbia/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Senegal']:
        url = "https://cdn.countryflags.com/thumbs/senegal/flag-round-250.png"
        cmap = cm.get_cmap('Greens') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Sevilla', 'Sevilla FC']:
        url = "https://upload.wikimedia.org/wikipedia/en/thumb/3/3b/Sevilla_FC_logo.svg/225px-Sevilla_FC_logo.svg.png"

    if team in ['Sheffield United', 'Sheffield United FC', 'Sheffield Utd', 'Sheff Utd']:
        url = "https://upload.wikimedia.org/wikipedia/en/thumb/9/9c/Sheffield_United_FC_logo.svg/1200px-Sheffield_United_FC_logo.svg.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Sheffield Wednesday', 'Sheffield Wednesday FC', 'Sheffield Wed', 'Sheff Wed']:
        url = "https://cdn.pafc.co.uk/icons/team/dark/1x/id/674.png"

    if team in ['Southampton', 'Southampton FC']:
        url = "https://1000logos.net/wp-content/uploads/2018/07/Southampton-Logo-640x400.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('gray')

    if team in ['South Korea']:
        url = "https://cdn.countryflags.com/thumbs/south-korea/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('grey')

    if team in ['Spain']:
        url = "https://cdn.countryflags.com/thumbs/spain/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Spezia Calcio', 'Spezia']:
        url = "https://store.acspezia.com/wp-content/uploads/2021/01/logo-spezia-150x150.png"

    if team in ['Stade Brestois 29', 'Brest']:
        url = "https://logodownload.org/wp-content/uploads/2019/09/stade-brestois-29-logo-1.png"

    if team in ['Stade Rennais FC', 'Stade Rennais', 'Rennais', 'Rennes']:
        url = "https://1000logos.net/wp-content/uploads/2020/09/Rennais-logo.png"

    if team in ['Stoke City', 'Stoke City FC', 'Stoke', 'Stoke FC']:
        url = "https://upload.wikimedia.org/wikipedia/en/thumb/2/29/Stoke_City_FC.svg/415px-Stoke_City_FC.svg.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Strasbourg', 'RC Strasbourg Alsace FC', 'RC Strasbourg']:
        url = "https://ssl.gstatic.com/onebox/media/sports/logos/Eb9xtMpUy8FXQ0RCKvLxcg_96x96.png"

    if team in ['Stockport', 'Stockport County FC', 'Stockport County']:
        url = "https://1.bp.blogspot.com/-mTgOgDlBQkE/XtjebiqdRxI/AAAAAAABAsE/cv05Zge2EMMw-7wLWRlxDyJ7Q31vnhpjwCLcBGAsYHQ/s320/Stockport%2BCounty-ING.png"

    if team in ['Stuttgart', 'VfB Stuttgart', 'VfB Stuttgart 1893']:
        url = "https://www.vfb.de/?proxy=img/vfb_logo.png"

    if team in ['Sunderland', 'Sunderland FC', 'Sunderland AFC']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Sunderland-Logo.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Swansea City', 'Swansea City FC', 'Swansea']:
        url = "https://logos-download.com/wp-content/uploads/2016/05/Swansea_City_AFC_logo_logotype_crest.png"
        cmap = cm.get_cmap('Greys') if hoa == 'home' else cm.get_cmap('Reds')

    if team in ['Switzerland']:
        url = "https://cdn.countryflags.com/thumbs/switzerland/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Tottenham Hotspur', 'Tottenham Hotspur FC', 'Tottenham', 'Spurs']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/Tottenham-Hotspur-Logo-700x394.png"
        cmap = cm.get_cmap('Greys') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Toulouse FC', 'Toulouse']:
        url = "https://www.sportbuzzbusiness.fr/wp-content/uploads/2018/06/Toulouse-FC-nouveau-logo-2018-TFC.png"

    if team in ['ES Troyes AC', 'Troyes AC', 'Troyes']:
        url = "https://cdn.bleacherreport.net/images/team_logos/328x328/troyes_ac.png"

    if team in ['Tunisia']:
        url = "https://cdn.countryflags.com/thumbs/tunisia/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Uruguay']:
        url = "https://cdn.countryflags.com/thumbs/uruguay/flag-round-250.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['USA', 'United States of America']:
        url = "https://cdn.countryflags.com/thumbs/united-states-of-america/flag-round-250.png"
        cmap = cm.get_cmap('Greys') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Valencia', 'Valencia CF']:
        url = "https://valenciacf.azureedge.net/thumbs/2x/vLLXe4oi315XPTDor6oyZW6U27EhvBRByyaCfvvXb4h9Xj0rCBEPcVXht5A4Oanf.png"

    if team in ['Villarreal', 'Villarreal CF']:
        url = "https://cdn.soccerwiki.org/images/logos/clubs/174.png"

    if team in ['Watford', 'Watford FC']:
        url = "https://www.watfordfc.com/img/logo.png"
        cmap = cm.get_cmap('YlOrBr') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['Wales']:
        url = "https://cdn.countryflags.com/thumbs/wales/flag-round-250.png"
        cmap = cm.get_cmap('Reds') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['SV Werder Bremen', 'Werder Bremen', 'Bremen']:
        url = "http://as01.epimg.net/img/comunes/fotos/fichas/equipos/large/303.png"

    if team in ['West Bromwich Albion', 'West Bromwich Albion FC', 'West Brom']:
        url = "https://s.yimg.com/cv/apiv2/default/soccer/20181205/500x500/WestBrom_wbg.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['West Ham United', 'West Ham United FC', 'West Ham', 'West Ham Utd']:
        url = "https://logos-world.net/wp-content/uploads/2020/06/West-Ham-Logo.png"
        cmap = cm.get_cmap('BuPu') if hoa == 'home' else cm.get_cmap('Blues')

    if team in ['AFC Wimbledon', 'Wimbledon']:
        url = "https://cdn.shopify.com/s/files/1/0405/8438/0574/files/AFCWimbledon_Logo_80x.png"

    if team in ['Wigan', 'Wigan Athletic', 'Wigan FC', 'Wigan Athletic FC']:
        url = "https://cdn.freebiesupply.com/logos/large/2x/wigan-athletic-logo-png-transparent.png"
        cmap = cm.get_cmap('Blues') if hoa == 'home' else cm.get_cmap('Greys')

    if team in ['Wolverhampton Wanderers', 'Wolverhampton Wanderers FC', 'Wolves']:
        url = "https://logos-download.com/wp-content/uploads/2018/09/FC_Wolverhampton_Wanderers_Logo-700x606.png"
        cmap = cm.get_cmap('YlOrBr') if hoa == 'home' else cm.get_cmap('YlGnBu')

    # Get image, and resize
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img = img.crop(img.getbbox())
    width, height = img.size

    if width > height:
        result = Image.new('RGBA', (width, width), color=(255, 0, 0, 0))
        result.paste(img, (0, (width - height) // 2))
    elif height > width:
        result = Image.new('RGBA', (height, height), color=(255, 0, 0, 0))
        result.paste(img, ((height - width) // 2, 0))
    else:
        result = img

    result = result.resize((300, 300))

    return result, cmap


