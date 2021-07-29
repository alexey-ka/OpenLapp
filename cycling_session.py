import numpy as np
import config
from yatcxparser import TcxParser
from utils import time_to_seconds


class OpenLappSession:
    def __init__(self, filename, metadata, min_time):
        """
        Class to process a single cycling session
        :param filename: name of the file to be parsed (.tcx)
        :param metadata: metadata = {
                                        name: name of the rider
                                        ftp: current FTP
                                        date: date of the session
                                        }
        :param min_time: min time of the cycling session e.g. '20m', '1h'
        """
        self.lappparser = TcxParser(filename, pre_read=True)
        if self.lappparser.has_powers and self.lappparser.total_time > time_to_seconds(min_time):
            session_year = str(self.lappparser.date.year)
            self.session_data = {'rider': metadata['name'],
                                 'ftp': metadata['ftps'][session_year], 'date': self.lappparser.date}
        else:
            raise Exception('File does not have power measurements or too short')

    @property
    def all_data(self):
        """
        Get all the retrieved data
        :return: dict: cycling session data
        """
        return self.session_data

    def add_mmps(self, mmps, extra=None, extra_label=None, extra_func=None):
        """
        Calculate MMPs
        :param mmps: dict:{'mmp': (time-interval, e.g. '5m', '20m', 'n': (count of MMPs) },
        :param extra: additional data to be calculated simultaneously. E.g. average grade during the 5min MMP
        :param extra_label: label for the additional data
        :param extra_func: aggregation function for the additional data. E.g. numpy.mean
        """
        # process all the given mmps
        for v in mmps:
            # extract time-interval and the required number
            time = v['mmp']
            n = v['n']
            # Process with/out additional data
            if extra is None:
                mmps, extras = self.calculate_mmps({'time': time_to_seconds(time),
                                                    'data': self.lappparser.powers, 'n': 2})
            else:
                # use numpy.mean function as a default aggregator
                if extra_func is None:
                    extra_func = np.mean
                mmps, extras = self.calculate_mmps({'time': time_to_seconds(time),
                                                    'data': self.lappparser.powers, 'n': 2,
                                                    'related_data': extra,
                                                    'related_data_func': extra_func
                                                    })
            # process the calculated values and add it to the internal dataset
            for i in range(n):
                label = 'mmp_{}_{}'.format(time, i)
                self.session_data[label] = mmps[i]
                if extra is not None:
                    ex_label = '{}_{}_{}'.format(extra_label, time, i)
                    self.session_data[ex_label] = extras[i]

    def add_features(self):
        """
        Process the required features
        """

        # Add the mandatory features
        self.session_data['average_speed'] = round(np.mean(self.lappparser.speeds))
        self.session_data['average_power'] = round(np.mean(self.lappparser.powers))
        self.session_data['average_cadence'] = round(np.mean(self.lappparser.cadences))
        self.session_data['average_heart_rate'] = self.lappparser.mean_heart_rate
        self.session_data['average_altitude'] = round(np.mean(self.lappparser.altitudes))
        self.session_data['high_altitude_distance'] = round(self.lappparser.high_altitude_distance)
        self.session_data['high_altitude_time'] = round(self.lappparser.high_altitude_time)
        self.session_data['total_elevation'] = round(self.lappparser.total_elevation)
        self.session_data['total_calories'] = self.lappparser.calories
        self.session_data['total_work'] = round(np.sum(self.lappparser.powers))
        self.session_data['max_altitude'] = round(max(self.lappparser.altitudes))
        self.session_data['bursts_n'] = self.calculate_effort({'time': 5, 'data': self.lappparser.powers,
                                                               'allowed_pause': 5})
        # Add special efforts
        self.session_data['efforts_20m'] = self.calculate_effort(
            {'time': time_to_seconds('20m'), 'data': self.lappparser.powers,
             'allowed_pause': 5})
        self.session_data['tempo_efforts_8m'] = self.calculate_effort(
            {'time': time_to_seconds('8m'), 'data': self.lappparser.powers,
             'allowed_pause': 5, 'tempo': True})

    def calculate_mmp_subset_index(self, data, time):
        """
        Calculate an MMP in the given data subset
        :param data: data subset
        :param time: time-frame in seconds
        :return: index of the MMP in the given subset
        """
        moving_averages = np.convolve(data, np.ones(int(time)) / int(time), 'valid')
        highest_mmp = np.where(moving_averages == np.amax(moving_averages))
        return highest_mmp

    def divide_mmp_subsets(self, main_subsets, subset_index, max_mmp_index, time, allowed_pause):
        """
        Function to exclude the MMP data-frame and divide the rest of the subset into 2 other ones
        :param main_subsets: original data subsets
        :param subset_index: index of the subset in the subsets
        :param max_mmp_index: index of the first position of the time-frame
        :param time: time of the time-frame
        :param allowed_pause: delay between the calculations
        :return: datasets with an excluded MMP frame
        """
        datasets = main_subsets
        # select left and right subsets after slicing
        left_subset = main_subsets[subset_index][0:max_mmp_index - allowed_pause]
        right_subset = main_subsets[subset_index][max_mmp_index + time + allowed_pause:]
        # skip a too short new subset
        if len(left_subset) >= time:
            datasets.append(left_subset)
        if len(right_subset) >= time:
            datasets.append(right_subset)
        # delete the original subset
        del datasets[subset_index]
        return datasets

    def calculate_mmps(self, p):
        """ Calculate MMP and the related data (e.g. mean slope)
        :param p: a dict in a form {'time':5, 'allowed_pause':0, 'n':2, 'data':array,
        'related_data':array, 'related_data_func':agg_function()}"""
        # get the power data, the required time and the number of the MMPs
        powers = p['data']
        time = p['time']
        n = p['n']
        # do not continue if the subset is too small
        if len(powers) < time:
            return np.nan
        # use default delay if not specified
        if 'allowed_pause' not in p:
            allowed_pause = time_to_seconds(config.session_settings['mmp_delay'])
        else:
            allowed_pause = p['allowed_pause']
        # Calculated values
        mmps = []
        extras = []
        # Data subsets. Initially it is the whole population
        main_subsets = [p['data']]
        if 'related_data' in p:
            extra_subsets = [p['related_data']]
        # process all N MMPs
        while n > 0:
            # Values calculated on the current step
            current_mmps = []
            current_indexes = []
            # process the subsets
            for subset in main_subsets:
                # get an index of the
                index = self.calculate_mmp_subset_index(subset, time)
                # process if there is at least 1 index
                if len(index) > 0:
                    # get the first MMP that was found
                    first_index = int(index[0])
                    # Save its index and the calculated value
                    current_indexes.append(first_index)
                    current_mmps.append(np.mean(subset[first_index:first_index + time]))
            # Get the highest MMP from all the subsets
            max_mmp = np.max(current_mmps)
            mmps.append(round(max_mmp))
            subset_index = current_mmps.index(max_mmp)
            max_mmp_index = current_indexes[subset_index]
            # Exclude data from the subset with the found MMP
            main_subsets = self.divide_mmp_subsets(main_subsets, subset_index, max_mmp_index, time, allowed_pause)
            # Do the same with the additional data
            if 'related_data' in p:
                extras.append(
                    round(p['related_data_func'](extra_subsets[subset_index][max_mmp_index:max_mmp_index + time])))
                extra_subsets = self.divide_mmp_subsets(extra_subsets, subset_index, max_mmp_index, time, allowed_pause)
            n -= 1

        return mmps, extras

    def calculate_effort(self, p):
        """ Calculate special effort
        :param p: a dict in a form {'time':5, 'allowed_pause':0, 'tempo':False, 'data':array}"""
        powers = p['data']
        time = p['time']
        if 'allowed_pause' not in p:
            allowed_pause = 0
        else:
            allowed_pause = p['allowed_pause']
        if len(powers) < time:
            return None
        # get FTP from the metadata
        ftp = self.session_data['ftp']
        if 'tempo' in p and p['tempo']:
            ftp *= config['tempo_coef']
        # calculate a moving average
        moving_averages = np.convolve(powers, np.ones(int(time)) / int(time), 'valid')
        # find a special effort
        mask = np.where(moving_averages >= ftp)
        if len(mask[0]) == 0:
            return 0
        first_match = mask[0][0]
        # remove the already considered subset from the dataset
        p['data'] = p['data'][first_match + time + allowed_pause:]
        # repeat until all the matches are found
        return 1 + self.calculate_effort(p)
