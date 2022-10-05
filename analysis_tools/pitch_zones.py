"""Module containing functions to group events into pitch zones and plot pitch zones.

Functions
---------

identify_zone(single_event, pitch_dims=(100, 100), zone_type='custom', get_centers=False)):
    Identify pitch zone in which a WhoScored-style event started and finished.

add_pitch_zones(pitch)
    Draw pitch zones on a mplsoccer style pitch

get_key_zones(zone_type='jdp_custom', halfspace=True, zone_14=True, cross_areas=False, split_lr=False):
    Return zone numbers for key zones of pitch.
"""

import numpy as np


def identify_zone(single_event,  zone_type='jdp_custom', get_centers=False, source='WhoScored'):
    """ Identify pitch zone in which a WhoScored-style event started and finished.

    Function to identify the pitch zone in which an event started and finished. The function takes in a single event and
    returns the numerical identifier of the start and finish pitch zones. This function is best used with the dataframe apply method.

    Args:
        single_event (pandas.Series): series corresponding to a single event (row) from WhoScored-style event dataframe.
        zone_type (string, optional): Type of zoning to apply. Options are jdp_custom, jdp_custom2, jdp_sparse, jdp_dense and grid. jdp_custom by default.
        get_centers (bool, optional): Select whether to return central co-ordinate of start/end zone. False by default.
        source (string, optional): Select source of input data. WhoScored by default.

    Returns:
        int: Pitch zone corresponding to event start position. None if not applicable.
        tuple: Co-ordinates of start zone centre. None if not applicable
        int: Pitch zone corresponding to event end position. None if not applicable.
        tuple: Co-ordinates of end zone centre. None if not applicable

    """
    # Statsbomb
    if source == 'Statsbomb':
        pitch_dims = (120, 80)
        pitch_length_x = pitch_dims[0]
        pitch_width_y = pitch_dims[1]
        x_startpos = (single_event['location'][0]
                      if single_event['location'] == single_event['location']
                      else single_event['location'])
        y_startpos = (single_event['location'][1]
                      if single_event['location'] == single_event['location']
                      else single_event['location'])
        if single_event['type'] == 'Pass':
            x_endpos = (single_event['pass_end_location'][0]
                        if single_event['pass_end_location'] == single_event['pass_end_location']
                        else single_event['pass_end_location'])
            y_endpos = (single_event['pass_end_location'][1]
                        if single_event['pass_end_location'] == single_event['pass_end_location']
                        else single_event['pass_end_location'])
        elif single_event['type'] == 'Carry':
            x_endpos = (single_event['carry_end_location'][0]
                        if single_event['carry_end_location'] == single_event['carry_end_location']
                        else single_event['carry_end_location'])
            y_endpos = (single_event['carry_end_location'][1]
                        if single_event['carry_end_location'] == single_event['carry_end_location']
                        else single_event['carry_end_location'])
        else:
            x_endpos = np.nan
            y_endpos = np.nan

    # Whoscored & other
    else:
        pitch_dims = (100, 100)
        pitch_length_x = pitch_dims[0]
        pitch_width_y = pitch_dims[1]
        x_startpos = pitch_length_x * single_event['x'] / pitch_length_x
        y_startpos = pitch_width_y * single_event['y'] / pitch_width_y
        x_endpos = pitch_length_x * single_event['endX'] / pitch_length_x
        y_endpos = pitch_width_y * single_event['endY'] / pitch_width_y

    # Initialise outputs
    zone = [0] * 2
    zone_center = [0] * 2

    # Determine event zones and one centers for first custom jdp
    if zone_type == 'jdp_custom':
        for idx, [x_pos, y_pos] in enumerate([[x_startpos, y_startpos], [x_endpos, y_endpos]]):
            if (x_pos == 0 and y_pos == 0) or x_pos != x_pos or y_pos != y_pos:
                zone[idx] = np.nan
                zone_center[idx] = np.nan
            elif x_pos <= 0.17 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(2)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(1)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, (0.79 + 0.21) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(0)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
            elif 0.17 * pitch_length_x < x_pos <= 0.5 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(7)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(6)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(5)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.3675 + 0.6325) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(4)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.79 + 0.6325) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(3)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.79 + 1) * pitch_width_y / 2)
            elif 0.5 * pitch_length_x < x_pos < (2/3) * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(10)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(12)
                    zone_center[idx] = ((0.83 + 0.5) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(9)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, (0.6325 + 0.3675) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(11)
                    zone_center[idx] = ((0.83 + 0.5) * pitch_length_x / 2, (0.6325 + 0.79) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(8)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
            elif (2/3) * pitch_length_x <= x_pos < 0.83 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(15)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(12)
                    zone_center[idx] = ((0.83 + 0.5) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(14)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, (0.6325 + 0.3675) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(11)
                    zone_center[idx] = ((0.83 + 0.5) * pitch_length_x / 2, (0.6325 + 0.79) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(13)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
            elif x_pos >= 0.83 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(18)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(17)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, (0.21 + 0.79) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(16)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)

    # Determine event zones and one centers for second custom jdp
    if zone_type == 'jdp_custom2':
        for idx, [x_pos, y_pos] in enumerate([[x_startpos, y_startpos], [x_endpos, y_endpos]]):
            if (x_pos == 0 and y_pos == 0) or x_pos != x_pos or y_pos != y_pos:
                zone[idx] = np.nan
                zone_center[idx] = np.nan
            elif x_pos <= 0.17 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(2)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(1)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, (0.79 + 0.21) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(0)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
            elif 0.17 * pitch_length_x < x_pos <= 0.5 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(7)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(6)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(5)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.3675 + 0.6325) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(4)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.79 + 0.6325) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(3)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.79 + 1) * pitch_width_y / 2)
            elif 0.5 * pitch_length_x < x_pos < (2/3) * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(12)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(11)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(10)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, (0.6325 + 0.3675) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(9)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, (0.6325 + 0.79) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(8)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
            elif (2/3) * pitch_length_x <= x_pos < 0.83 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(17)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(16)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(15)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, (0.6325 + 0.3675) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(14)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, (0.6325 + 0.79) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(13)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
            elif x_pos >= 0.83 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(20)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(19)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, (0.21 + 0.79) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(18)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)

    # Determine event zones and zone centers for dense jdp
    elif zone_type == 'jdp_dense':
        for idx, [x_pos, y_pos] in enumerate([[x_startpos, y_startpos], [x_endpos, y_endpos]]):
            if (x_pos == 0 and y_pos == 0) or x_pos != x_pos or y_pos != y_pos:
                zone[idx] = np.nan
                zone_center[idx] = np.nan
            elif x_pos <= 0.17 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(2)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(1)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, (0.79 + 0.21) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(0)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
            elif 0.17 * pitch_length_x < x_pos <= (1/3) * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(7)
                    zone_center[idx] = ((0.17 + (1/3)) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(6)
                    zone_center[idx] = ((0.17 + (1/3)) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(5)
                    zone_center[idx] = ((0.17 + (1/3)) * pitch_length_x / 2, (0.3675 + 0.6325) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(4)
                    zone_center[idx] = ((0.17 + (1/3)) * pitch_length_x / 2, (0.79 + 0.6325) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(3)
                    zone_center[idx] = ((0.17 + (1/3)) * pitch_length_x / 2, (0.79 + 1) * pitch_width_y / 2)
            elif (1/3) * pitch_length_x < x_pos <= 0.5 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(12)
                    zone_center[idx] = (((1/3) + 0.5) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(11)
                    zone_center[idx] = (((1/3) + 0.5) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(10)
                    zone_center[idx] = (((1/3) + 0.5) * pitch_length_x / 2, (0.3675 + 0.6325) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(9)
                    zone_center[idx] = (((1/3) + 0.5) * pitch_length_x / 2, (0.79 + 0.6325) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(8)
                    zone_center[idx] = (((1/3) + 0.5) * pitch_length_x / 2, (0.79 + 1) * pitch_width_y / 2)
            elif 0.5 * pitch_length_x < x_pos < (2/3) * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(17)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(16)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(15)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, (0.6325 + 0.3675) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(14)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, (0.6325 + 0.79) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(13)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
            elif (2/3) * pitch_length_x <= x_pos < 0.83 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(22)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(21)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(20)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, (0.6325 + 0.3675) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(19)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, (0.6325 + 0.79) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(18)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
            elif x_pos >= 0.83 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(25)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(24)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, (0.21 + 0.79) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(23)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)

    # Determine event zones and zone centers for sparse jdp
    elif zone_type == 'jdp_sparse':
        for idx, [x_pos, y_pos] in enumerate([[x_startpos, y_startpos], [x_endpos, y_endpos]]):
            if (x_pos == 0 and y_pos == 0) or x_pos != x_pos or y_pos != y_pos:
                zone[idx] = np.nan
                zone_center[idx] = np.nan
            elif x_pos <= 0.17 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(2)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(1)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, (0.79 + 0.21) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(0)
                    zone_center[idx] = (0.17 * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
            elif 0.17 * pitch_length_x < x_pos <= (1/3) * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(4)
                    zone_center[idx] = ((0.17 + (1/3)) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(3)
                    zone_center[idx] = ((0.17 + (1/3)) * pitch_length_x / 2, (0.79 + 1) * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(7)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(6)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.3675 + 0.6325) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(5)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.79 + 0.6325) * pitch_width_y / 2)
            elif (1/3) * pitch_length_x < x_pos <= 0.5 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(9)
                    zone_center[idx] = (((1/3) + 0.5) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(8)
                    zone_center[idx] = (((1/3) + 0.5) * pitch_length_x / 2, (0.79 + 1) * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(7)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(6)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.3675 + 0.6325) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(5)
                    zone_center[idx] = ((0.17 + 0.5) * pitch_length_x / 2, (0.79 + 0.6325) * pitch_width_y / 2)
            elif 0.5 * pitch_length_x < x_pos < (2/3) * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(11)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(10)
                    zone_center[idx] = (((2/3) + 0.5) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(14)
                    zone_center[idx] = ((0.83 + 0.5) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(13)
                    zone_center[idx] = ((0.83 + 0.5) * pitch_length_x / 2, (0.6325 + 0.3675) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(12)
                    zone_center[idx] = ((0.83 + 0.5) * pitch_length_x / 2, (0.6325 + 0.79) * pitch_width_y / 2)
            elif (2/3) * pitch_length_x <= x_pos < 0.83 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(16)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(15)
                    zone_center[idx] = (((2/3) + 0.83) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos < 0.3675 * pitch_width_y:
                    zone[idx] = int(14)
                    zone_center[idx] = ((0.83 + 0.5) * pitch_length_x / 2, (0.3675 + 0.21) * pitch_width_y / 2)
                elif 0.3675 * pitch_width_y <= y_pos <= 0.6325 * pitch_width_y:
                    zone[idx] = int(13)
                    zone_center[idx] = ((0.83 + 0.5) * pitch_length_x / 2, (0.6325 + 0.3675) * pitch_width_y / 2)
                elif 0.6325 * pitch_width_y < y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(12)
                    zone_center[idx] = ((0.83 + 0.5) * pitch_length_x / 2, (0.6325 + 0.79) * pitch_width_y / 2)
            elif x_pos >= 0.83 * pitch_length_x:
                if y_pos < 0.21 * pitch_width_y:
                    zone[idx] = int(19)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, 0.21 * pitch_width_y / 2)
                elif 0.21 * pitch_width_y <= y_pos <= 0.79 * pitch_width_y:
                    zone[idx] = int(18)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, (0.21 + 0.79) * pitch_width_y / 2)
                elif y_pos > 0.79 * pitch_width_y:
                    zone[idx] = int(17)
                    zone_center[idx] = ((1 + 0.83) * pitch_length_x / 2, (1 + 0.79) * pitch_width_y / 2)

    start_zone = zone[0]
    start_zone_center = zone_center[0]
    end_zone = zone[1]
    end_zone_center = zone_center[1]

    if get_centers:
        return start_zone, start_zone_center, end_zone, end_zone_center
    else:
        return start_zone, end_zone


def add_pitch_zones(pitch, pitch_dims=(100, 100), zone_type='jdp_custom', pitch_orientation='vertical', show_zone_numbers=False, line_colour='grey', text_colour = 'w'):
    """ Draw pitch zones on a mplsoccer style pitch.

    Draw a series of dashed lines on a mplsoccer style pitch to break it up into a series of zones. Takes in a
    zone_type argument to enable specification of zones to be drawn.

    Args:
        pitch (axes object): Mplsoccer pitch axis to plot on.
        pitch_dims (tuple, optional): Pitch dimensions, formatted as (length, width). (100, 100) by default.
        zone_type (string, optional): Type of zoning to apply. Options are jdp_custom, jdp_custom2, jdp_sparse, jdp_dense and grid. jdp_custom by default.
        pitch_orientation (string, optional): Orientation of pitch (horizontal or vertical). vertical by default.
        show_zone_numbers (bool, optional): Selection of whether to show zone numbers on pitch. False by default.
        line_colour (string, optional): Colour of zone lines. 'grey' by default.
        text_colour (string, optional): Colour of zone number text. 'w' by default.

    Returns:
        None
        """

    ls = '--'
    lw = 0.5

    pitch_length_x = pitch_dims[0]
    pitch_width_y = pitch_dims[1]

    # Vertical pitch orientation
    if pitch_orientation == 'vertical':

        # Plot lines for dense jdp
        if zone_type == 'jdp_dense':
            pitch.plot([0.21 * pitch_width_y, 0.21 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.21 * pitch_width_y, 0.21 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.79 * pitch_width_y, 0.79 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.79 * pitch_width_y, 0.79 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.3675 * pitch_width_y, 0.3675 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.3675 * pitch_width_y, 0.3675 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.6325 * pitch_width_y, 0.6325 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.6325 * pitch_width_y, 0.6235 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.209 * pitch_width_y], [0.17 * pitch_length_x, 0.17 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.791 * pitch_width_y, 0.999 * pitch_width_y], [0.17 * pitch_length_x, 0.17 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.209 * pitch_width_y], [0.83 * pitch_length_x, 0.83 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.791 * pitch_width_y, 0.999 * pitch_width_y], [0.83 * pitch_length_x, 0.83 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.999 * pitch_width_y], [(1/3) * pitch_length_x, (1/3) * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.999 * pitch_width_y], [(2/3) * pitch_length_x, (2/3) * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)

            # Show zone numbers for dense jdp
            if show_zone_numbers:
                pitch.text((1 + 0.79) * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 0,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.79 + 0.21) * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 1,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 2,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, (0.17 + (1/3)) * pitch_length_x / 2, 3,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.79 + 0.6325) * pitch_width_y / 2, (0.17 + (1/3)) * pitch_length_x / 2, 4,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.21 + 0.79) * pitch_width_y / 2, (0.17 + (1/3)) * pitch_length_x / 2, 5,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.21) * pitch_width_y / 2, (0.17 + (1/3)) * pitch_length_x / 2, 6,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, (0.17 + (1/3)) * pitch_length_x / 2, 7,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.79 + 1) * pitch_width_y / 2, ((1 / 3) + 0.5) * pitch_length_x / 2, 8,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.79 + 0.6325) * pitch_width_y / 2, ((1/3) + 0.5) * pitch_length_x / 2, 9,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.6325) * pitch_width_y / 2, ((1/3) + 0.5) * pitch_length_x / 2, 10,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.21) * pitch_width_y / 2, ((1/3) + 0.5) * pitch_length_x / 2, 11,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, ((1 / 3) + 0.5) * pitch_length_x / 2, 12,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, ((2/3) + 0.5) * pitch_length_x / 2, 13,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.79) * pitch_width_y / 2, ((2/3) + 0.5) * pitch_length_x / 2, 14,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.3675) * pitch_width_y / 2, ((2/3) + 0.5) * pitch_length_x / 2, 15,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.21) * pitch_width_y / 2, ((2/3) + 0.5) * pitch_length_x / 2, 16,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, ((2/3) + 0.5) * pitch_length_x / 2, 17,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, ((2/3) + 0.83) * pitch_length_x / 2, 18,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.79) * pitch_width_y / 2, ((2/3) + 0.83) * pitch_length_x / 2, 19,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.3675) * pitch_width_y / 2, ((2/3) + 0.83) * pitch_length_x / 2, 20,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.21) * pitch_width_y / 2, ((2/3) + 0.83) * pitch_length_x / 2, 21,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, ((2/3) + 0.83) * pitch_length_x / 2, 22,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 23,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.21 + 0.79) * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 24,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 25,
                           ha="center", va="center", c=text_colour)

        # Plot lines for sparse jdp
        if zone_type == 'jdp_sparse':
            pitch.plot([0.21 * pitch_width_y, 0.21 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.21 * pitch_width_y, 0.21 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.79 * pitch_width_y, 0.79 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.79 * pitch_width_y, 0.79 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.3675 * pitch_width_y, 0.3675 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.3675 * pitch_width_y, 0.3675 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.6325 * pitch_width_y, 0.6325 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.6325 * pitch_width_y, 0.6235 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.209 * pitch_width_y], [0.17 * pitch_length_x, 0.17 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.791 * pitch_width_y, 0.999 * pitch_width_y], [0.17 * pitch_length_x, 0.17 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.209 * pitch_width_y], [0.83 * pitch_length_x, 0.83 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.791 * pitch_width_y, 0.999 * pitch_width_y], [0.83 * pitch_length_x, 0.83 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.209 * pitch_width_y], [(1/3) * pitch_length_x, (1/3) * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.999 * pitch_width_y, 0.791 * pitch_width_y], [(1/3) * pitch_length_x, (1/3) * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.209 * pitch_width_y], [(2/3) * pitch_length_x, (2/3) * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.999 * pitch_width_y, 0.791 * pitch_width_y], [(2/3) * pitch_length_x, (2/3) * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)

            # Show zone numbers for sparse jdp
            if show_zone_numbers:
                pitch.text((1 + 0.79) * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 0,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.79 + 0.21) * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 1,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 2,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, (0.17 + (1/3)) * pitch_length_x / 2, 3,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, (0.17 + (1/3)) * pitch_length_x / 2, 4,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.79 + 0.6325) * pitch_width_y / 2, (1/3) * pitch_length_x, 5,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.21 + 0.79) * pitch_width_y / 2, (1/3) * pitch_length_x, 6,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.21) * pitch_width_y / 2, (1/3) * pitch_length_x, 7,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.79 + 1) * pitch_width_y / 2, ((1 / 3) + 0.5) * pitch_length_x / 2, 8,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, ((1 / 3) + 0.5) * pitch_length_x / 2, 9,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, ((2/3) + 0.5) * pitch_length_x / 2, 10,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, ((2/3) + 0.5) * pitch_length_x / 2, 11,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.79) * pitch_width_y / 2, (2/3) * pitch_length_x, 12,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.3675) * pitch_width_y / 2, (2/3) * pitch_length_x, 13,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.21) * pitch_width_y / 2, (2/3) * pitch_length_x, 14,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, ((2/3) + 0.83) * pitch_length_x / 2, 15,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, ((2/3) + 0.83) * pitch_length_x / 2, 16,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 17,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.21 + 0.79) * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 18,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 19,
                           ha="center", va="center", c=text_colour)

        # Plot lines for first variant of custom jdp
        if zone_type == 'jdp_custom':
            pitch.plot([0.21 * pitch_width_y, 0.21 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.21 * pitch_width_y, 0.21 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.79 * pitch_width_y, 0.79 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.79 * pitch_width_y, 0.79 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.3675 * pitch_width_y, 0.3675 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.3675 * pitch_width_y, 0.3675 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.6325 * pitch_width_y, 0.6325 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.6325 * pitch_width_y, 0.6235 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.209 * pitch_width_y], [0.17 * pitch_length_x, 0.17 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.791 * pitch_width_y, 0.999 * pitch_width_y], [0.17 * pitch_length_x, 0.17 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.209 * pitch_width_y], [0.83 * pitch_length_x, 0.83 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.791 * pitch_width_y, 0.999 * pitch_width_y], [0.83 * pitch_length_x, 0.83 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.209 * pitch_width_y], [(2/3) * pitch_length_x, (2/3) * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.3675 * pitch_width_y, 0.6235 * pitch_width_y], [(2/3) * pitch_length_x, (2/3) * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.999 * pitch_width_y, 0.791 * pitch_width_y], [(2/3) * pitch_length_x, (2/3) * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)

            # Show zone numbers for first variant of custom jdp
            if show_zone_numbers:
                pitch.text((1 + 0.79) * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 0,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.79 + 0.21) * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 1,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 2,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, (1 / 3) * pitch_length_x, 3,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, (1 / 3) * pitch_length_x, 4,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.79 + 0.6325) * pitch_width_y / 2, (1 / 3) * pitch_length_x, 5,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.21 + 0.79) * pitch_width_y / 2, (1 / 3) * pitch_length_x, 6,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.21) * pitch_width_y / 2, (1 / 3) * pitch_length_x, 7,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, ((2 / 3) + 0.5) * pitch_length_x / 2, 8,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.79) * pitch_width_y / 2, (2 / 3) * pitch_length_x, 11,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.3675) * pitch_width_y / 2, ((2 / 3) + 0.5) * pitch_length_x / 2, 9,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.21) * pitch_width_y / 2, (2 / 3) * pitch_length_x, 12,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, ((2 / 3) + 0.5) * pitch_length_x / 2, 10,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, ((2 / 3) + 0.83) * pitch_length_x / 2, 13,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.3675) * pitch_width_y / 2, ((2 / 3) + 0.83) * pitch_length_x / 2, 14,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, ((2 / 3) + 0.83) * pitch_length_x / 2, 15,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 16,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.21 + 0.79) * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 17,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 18,
                           ha="center", va="center", c=text_colour)

        # Plot lines for second variant of custom jdp
        if zone_type == 'jdp_custom2':
            pitch.plot([0.21 * pitch_width_y, 0.21 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.21 * pitch_width_y, 0.21 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.79 * pitch_width_y, 0.79 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.79 * pitch_width_y, 0.79 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.3675 * pitch_width_y, 0.3675 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.3675 * pitch_width_y, 0.3675 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.6325 * pitch_width_y, 0.6325 * pitch_width_y], [0.171 * pitch_length_x, 0.499 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.6325 * pitch_width_y, 0.6235 * pitch_width_y], [0.501 * pitch_length_x, 0.829 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.209 * pitch_width_y], [0.17 * pitch_length_x, 0.17 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.791 * pitch_width_y, 0.999 * pitch_width_y], [0.17 * pitch_length_x, 0.17 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.209 * pitch_width_y], [0.83 * pitch_length_x, 0.83 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.791 * pitch_width_y, 0.999 * pitch_width_y], [0.83 * pitch_length_x, 0.83 * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)
            pitch.plot([0.001 * pitch_width_y, 0.999 * pitch_width_y], [(2/3) * pitch_length_x, (2/3) * pitch_length_x],
                       c=line_colour, linestyle=ls, linewidth=lw)

            # Show zone numbers for second variant of custom jdp
            if show_zone_numbers:
                pitch.text((1 + 0.79) * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 0,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.79 + 0.21) * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 1,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, 0.17 * pitch_length_x / 2, 2,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, (1 / 3) * pitch_length_x, 3,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.79 + 0.6325) * pitch_width_y / 2, (1 / 3) * pitch_length_x, 4,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.21 + 0.79) * pitch_width_y / 2, (1 / 3) * pitch_length_x, 5,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.21) * pitch_width_y / 2, (1 / 3) * pitch_length_x, 6,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, (1 / 3) * pitch_length_x, 7,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, ((2 / 3) + 0.5) * pitch_length_x / 2, 8,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.79) * pitch_width_y / 2, ((2 / 3) + 0.5) * pitch_length_x / 2, 9,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.3675) * pitch_width_y / 2, ((2 / 3) + 0.5) * pitch_length_x / 2, 10,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.21) * pitch_width_y / 2, ((2 / 3) + 0.5) * pitch_length_x / 2, 11,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, ((2 / 3) + 0.5) * pitch_length_x / 2, 12,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, ((2 / 3) + 0.83) * pitch_length_x / 2, 13,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.79) * pitch_width_y / 2, ((2 / 3) + 0.83) * pitch_length_x / 2, 14,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.6325 + 0.3675) * pitch_width_y / 2, ((2 / 3) + 0.83) * pitch_length_x / 2, 15,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.3675 + 0.21) * pitch_width_y / 2, ((2 / 3) + 0.83) * pitch_length_x / 2, 16,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, ((2 / 3) + 0.83) * pitch_length_x / 2, 17,
                           ha="center", va="center", c=text_colour)
                pitch.text((1 + 0.79) * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 18,
                           ha="center", va="center", c=text_colour)
                pitch.text((0.21 + 0.79) * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 19,
                           ha="center", va="center", c=text_colour)
                pitch.text(0.21 * pitch_width_y / 2, (1 + 0.83) * pitch_length_x / 2, 20,
                           ha="center", va="center", c=text_colour)


def get_key_zones(zone_type='jdp_custom', halfspace=True, zone_14=True, cross_areas=False, split_lr=False):
    """ Return zone numbers for key zones of pitch.

    Return a list of zone numbers corresponding to key areas of the pitch, based on the type of zoning used.

    Args:
        zone_type (string, optional): Type of zoning to used.
        halfspace (bool, optional): Select whether to return half-space zone numbers. True by default.
        zone_14 (bool, optional): Select whether to return zone_14 zone number. True by default.
        cross_areas (bool, optional): Select whether to return crossing area zone numbers. False by default
        split_lr (bool, optional): Determine whether to split zone lists into left/right.
    Returns:
        dict: Zone numbers corresponding to user specified zones.
        """

    # Initialise output
    zone_numbers = dict()

    if halfspace:
        if zone_type == 'jdp_custom':
            zone_numbers['halfspace'] = [11, 12]
            if split_lr:
                zone_numbers['l_halfspace'] = [11]
                zone_numbers['r_halfspace'] = [12]
        elif zone_type == 'jdp_custom2':
            zone_numbers['halfspace'] = [9, 14, 11, 16]
            if split_lr:
                zone_numbers['l_halfspace'] = [9, 14]
                zone_numbers['r_halfspace'] = [11, 16]
        elif zone_type == 'jdp_sparse':
            zone_numbers['halfspace'] = [10, 15, 11, 16]
            if split_lr:
                zone_numbers['l_halfspace'] = [10, 15]
                zone_numbers['r_halfspace'] = [11, 16]
        elif zone_type == 'jdp_dense':
            zone_numbers['halfspace'] = [14, 19, 16, 21]
            if split_lr:
                zone_numbers['l_halfspace'] = [14, 19]
                zone_numbers['r_halfspace'] = [16, 21]

    if zone_14:
        if zone_type == 'jdp_custom':
            zone_numbers['zone_14'] = [14]
        elif zone_type == 'jdp_custom2':
            zone_numbers['zone_14'] = [15]
        elif zone_type == 'jdp_sparse':
            zone_numbers['zone_14'] = [13]
        elif zone_type == 'jdp_dense':
            zone_numbers['zone_14'] = [20]

    if cross_areas:
        if zone_type == 'jdp_custom':
            zone_numbers['cross_area'] = [13, 16, 15, 18]
            if split_lr:
                zone_numbers['l_cross_area'] = [13, 16]
                zone_numbers['r_cross_area'] = [15, 18]
        elif zone_type == 'jdp_custom2':
            zone_numbers['cross_area'] = [13, 18, 17, 20]
            if split_lr:
                zone_numbers['l_cross_area'] = [13, 18]
                zone_numbers['r_cross_area'] = [17, 20]
        elif zone_type == 'jdp_sparse':
            zone_numbers['cross_area'] = [15, 17, 16, 19]
            if split_lr:
                zone_numbers['l_cross_area'] = [15, 17]
                zone_numbers['r_cross_area'] = [16, 19]
        elif zone_type == 'jdp_dense':
            zone_numbers['cross_area'] = [18, 23, 22, 25]
            if split_lr:
                zone_numbers['l_cross_area'] = [18, 23]
                zone_numbers['r_cross_area'] = [22, 25]

    return zone_numbers
