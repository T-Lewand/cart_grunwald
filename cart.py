import math

import pandas as pd
from datetime import datetime
from calendar import monthrange
import copy
from google_sheet import GoogleSheet
import numpy as np
import utilities as util


class Cart:
    def __init__(self, name):
        self.name = name
        self.group_list = []
        self.congregation_sheet = None
        self.data_filename = f'{self.name}.data'

    def _get_spreadsheet(self):
        congregation_sheet = GoogleSheet(self.name)
        congregation_sheet.get_credentials()
        congregation_sheet.get_spreadsheet()
        print(congregation_sheet.list_sheets())
        self.congregation_sheet = congregation_sheet

    def get_cells(self, range):
        cells = self.congregation_sheet.get_sheet('Arkusz1', range=range)
        print(cells)

    def get_schedule(self):

        time = self.congregation_sheet.get_sheet('Arkusz1', range='B5:B')
        participant_1 = self.congregation_sheet.get_sheet('Arkusz1', range='C5:C')
        participant_2 = self.congregation_sheet.get_sheet('Arkusz1', range='D5:D')
        participant_1 = [participant[0] for participant in participant_1]
        participant_2 = [participant[0] for participant in participant_2]

        schedule = []
        for person_1, person_2, hour in zip(participant_1, participant_2, time):
            duty = {'Time': hour, 'Person_1': person_1, "Person_2": person_2}
            schedule.append(duty)

        self.schedule = schedule

    def get_all_participants(self):
        participants = [duty['Person_1'] for duty in self.schedule]
        participants.extend([duty['Person_2'] for duty in self.schedule])
        return participants

    def get_statistics(self):
        participants = self.get_all_participants()
        unique, count = np.unique(participants, return_counts=True)
        for u, c in zip(unique, count):
            print(u, c)


class Person:
    STATUS = ['Pioneer', 'Elder', 'Gray']

    def __init__(self, firstname, surname):
        self.firstname = firstname
        self.surname = surname
        self.weight = 1
        self.status = None

    def update_status(self, status):
        if status not in self.STATUS:
            raise ValueError
        self.status = status

    def update_weigth(self, value):
        self.weight = value

    def __eq__(self, other):
        return (self.firstname==other.firstname) and (self.surname==other.surname)

    def __lt__(self, other):
        return self.surname<other.surname

    def __repr__(self):
        return f'Person({self.firstname}, {self.surname})'

class Day:
    DAY_LIST = ['Poniedzialek', 'Czwartek', 'Sobota']
    # DAY_DICT = {}
    #
    # for day in DAY_LIST:
    #     day_hours = []
    #     if 'Sobota' in day:
    #         for i in range(7, 15):
    #             day_hours.append(i)
    #     else:
    #         for i in range(7, 20):
    #             day_hours.append(i)
    #     dict = {}
    #     for hour in day_hours:
    #         dict[hour] = []
    #     DAY_DICT[day] = dict

    def __init__(self, name):
        self.name = name
        # self.day_dict = self.DAY_DICT[name]
        DAY_DICT = {}

        for day in self.DAY_LIST:
            day_hours = []
            if 'Sobota' in day:
                for i in range(7, 15):
                    day_hours.append(i)
            else:
                for i in range(7, 20):
                    day_hours.append(i)
            dict = {}
            for hour in day_hours:
                dict[hour] = []
            DAY_DICT[day] = dict
        self.day_dict = DAY_DICT[name]


class FormResults:
    def __init__(self, file_path):
        self.file_path = file_path

    def read_file(self):
        """
        Reads raw data from csv file retrieved from google forms
        """
        file = pd.read_csv(self.file_path)
        file.drop(columns=['Sygnatura czasowa', 'Nazwa użytkownika'], inplace=True)
        self.raw_data = file
        self.day_list = file.columns.to_list()[-4:-1]
        # TODO: Nagłówki poprawić bo są dwukropki i znaki polskie

    def check_for_duplicates(self, remove=True):
        """
        Use for cleaned data, removed duplicated accessibility from one person. Leaves data from last send form
        :return:
        """
        duplicate_mask = self.data.duplicated(subset=self.data.columns[0], keep='last')
        if remove:
            self.data = self.data[~duplicate_mask]
            self.data.reset_index(inplace=True, drop=True)

    def clean(self):
        """
        Cleans data, replaces hours to simple form of duty start hour
        """
        data = self.raw_data.copy()
        for day in self.day_list:
            for row in range(data.shape[0]):
                hours = data.loc[row, day]
                if not pd.isna(hours):
                    hours = hours.split(';')
                    clean_hours = []
                    for single_hour in hours:
                        clean_hours.append(int(single_hour.split('.')[0]))
                else:
                    clean_hours = np.NAN
                data.loc[row, day] = clean_hours

        self.data = data
        self.check_for_duplicates()

    def get_accessibility(self, return_weigths=True):
        """
        Gets list of persons available for given day at given hour
        """
        accessibility = {}
        for data_day in self.day_list:
            day = Day(data_day)
            for row in range(self.data.shape[0]):
                name = self.data.loc[row, self.data.columns[0]]
                if pd.isna(name):
                    # print('DUPA - nie podano nazwiska')
                    continue
                available_hours = self.data.loc[row, data_day]
                if available_hours is not np.NAN:
                    for hour in available_hours:
                        day.day_dict[hour].append(name)

            accessibility[data_day] = day.day_dict

        if return_weigths:
            weights = self.get_weights(accessibility)
            return accessibility, weights
        else:
            return accessibility

    def get_weights(self, accessibility_data):
        """
        Calculates weight for each participant baseD on formula =
        ALL PARTICIPANT FOR DAY / NUMBER OF DECLARED HOURS FOR GIVEN PARTICIPANT IN THAT DAY
        :return: dict with weights for each name for each day
        """
        day_weigths = {}
        for day in accessibility_data:
            # print(day)
            day_access = accessibility_data[day]
            hold = []
            for hour in day_access:
                hour_access = day_access[hour]
                hold.extend(hour_access)
            print(hold)
            person, count = np.unique(hold, return_counts=True)
            weights = {}
            for i, a in zip(person, count):
                print('Dupa', i)
                w = len(person)//a
                # print(i, a, f'    waga = {w}')
                weights[i] = w
            day_weigths[day] = weights

        return day_weigths


class Month:
    CART_DAYS = ['Poniedzialek', 'Czwartek', 'Sobota']
    CART_DAYS_DICT = {0: 'Poniedzialek', 3: 'Czwartek', 5: 'Sobota'}
    CART_DAYS_NUMBER = [0, 3, 5]

    def __init__(self, month_number: int, year=datetime.now().year):
        self.month = month_number
        self.year = year
        self.month_days = monthrange(year, month_number)

    def get_cart_dates(self):
        """
        Gets dates of Mondays, Thursdays and Saturdays in given month
        :return: list of dates
        """
        cart_dates = []
        for day in range(self.month_days[0]+1, self.month_days[1]+1):
            date = datetime(year=self.year, month=self.month, day=day).date()
            weekday = date.weekday()
            if weekday in self.CART_DAYS_NUMBER:
                cart_dates.append(date)

        return cart_dates

    def init_schedule(self):
        """
        Creates empty schedule with dates and hours for given month
        """
        cart_dates = self.get_cart_dates()
        empty_schedule = pd.DataFrame(columns=['Date', 'Day', 'Hour'])
        index = 0
        for date in cart_dates:
            day = Day(self.CART_DAYS_DICT[date.weekday()])
            day_hours = list(day.day_dict.keys())
            for hour in day_hours:
                empty_schedule.loc[index, 'Date'] = date
                empty_schedule.loc[index, 'Day'] = day.name
                empty_schedule.loc[index, 'Hour'] = hour
                index += 1

        return empty_schedule


class Schedule(Month):
    def __init__(self, accessibility_data, month_number, year=datetime.now().year):
        super().__init__(month_number, year)
        self.accessibility_data = accessibility_data
        self.schedule = self.init_schedule()

    def _generate_index(self, accessibility_for_day, weigths=None):
        """
        Generates pairs of participant for hours on given day based on accessibility data
        :param accessibility_for_day: accessibility for single day
        :return: dictionary with pairs for each hour in a single given day
        """
        duty_dict = {}
        for i in accessibility_for_day:
            people_list = accessibility_for_day[i].copy()
            people_list.sort()
            # print(people_list)

            if weigths is not None:
                # print(weigths)
                weighted_people_list = []
                for person in people_list:
                    for j in range(weigths[person]):
                        weighted_people_list.append(person)
                # print(weighted_people_list)
                people_list = weighted_people_list


            # Control if participant already occurs in schedule for day
            if i > 7:
                for duty_hour in duty_dict:
                    person_1_prev = duty_dict[duty_hour]['Person_1']
                    person_2_prev = duty_dict[duty_hour]['Person_2']
                    if person_1_prev in people_list:
                        # people_list.remove(person_1_prev)
                        util.remove_duplicate_in_list(people_list, person_1_prev)

                    if person_2_prev in people_list:
                        # people_list.remove(person_2_prev)
                        util.remove_duplicate_in_list(people_list, person_2_prev)

            people_number = len(people_list)
            # Get first participant
            index_1 = np.random.randint(0, people_number)
            # person_1 = people_list.pop(index_1)
            person_1 = util.pop_and_remove(people_list, index_1)
            people_number = len(people_list)
            # Get second participant
            index_2 = np.random.randint(0, people_number)
            # person_2 = people_list.pop(index_2)
            person_2 = util.pop_and_remove(people_list, index_2)
            # Control if first and second participant is the same person
            while person_1 == person_2:
                print('Dupa')
                index_2 = np.random.randint(0, people_number)
                person_2 = people_list[index_2]

            duty_dict[i] = {'Person_1': person_1, 'Person_2': person_2}
            duty_dict_df = pd.DataFrame.from_dict(duty_dict, orient='index')

            unique_person, count_person = np.unique(duty_dict_df, return_counts=True)

        return duty_dict

    def populate(self, weigths=None):
        """
        Populates empty schedule with participants
        :param weigths:
        :return:
        """
        row = 0
        _check = 0
        penalty = None
        for date in self.schedule['Date'].unique():
            _check = 0
            # print(self.schedule)
            while _check < 1:
                weekday = self.CART_DAYS_DICT[date.weekday()]
                try:
                    data = self.accessibility_data[weekday]
                    day_weights = weigths[weekday]
                    if 'Person 1' in self.schedule.columns:
                        day_weights = self._weigth_penalty(day_weights)

                    duty = self._generate_index(data, day_weights)

                    _check += 1
                except ValueError:
                    # print('Nie wypełniono, kolejne podejście')
                    continue

                for i in duty:
                    self.schedule.loc[row, 'Person 1'] = duty[i]['Person_1']
                    self.schedule.loc[row, 'Person 2'] = duty[i]['Person_2']
                    row += 1

            # print(weekday, day_weights)


        # print(self.schedule)

    def _weigth_penalty(self, day_weight):
        day_weight = day_weight.copy()

        person, count = np.unique(self.schedule.loc[~self.schedule['Person 1'].isna(), ['Person 1', 'Person 2']],
                                  return_counts=True)
        penalty = {}
        for per, c in zip(person, count):
            penalty[per] = c

        for per in day_weight:
            if per in penalty:
                for occurance in range(penalty[per]):
                    day_weight[per] = int(day_weight[per] / 1.1)
                    if day_weight[per] == 0:
                        day_weight[per] = 1

        return day_weight

    def statistics(self):
        schedule_participants, occurences = np.unique(self.schedule.loc[:, ['Person 1', 'Person 2']],
                                                      return_counts=True)
        occurences_sum = occurences.sum()
        # print(occurences_sum)
        entropy_l = []
        for person, count in zip(schedule_participants, occurences):
            print(person, count)

        print('-' * 30)
        number, number_count = np.unique(occurences, return_counts=True)
        entropy_list = []
        for n in number_count:
            p = n/sum(number_count)
            entropy = p * math.log2(p)
            entropy_list.append(entropy)
        max_entropy = math.log2(len(number_count))
        entropy = -sum(entropy_list)
        score = -(sum(entropy_list)/max_entropy)
        # print(-sum(entropy_list))
        print(len(number_count))
        print(score)
        return score

    def check_completeness(self):
        """
        Checks if everyone who declered accessibility is taken into account in schedule. Prints warning if not.
        """
        schedule_participants = np.unique(self.schedule.loc[:, ['Person 1', 'Person 2']])
        declared_participants = []

        for day in self.accessibility_data:
            for hour in self.accessibility_data[day]:
                declared_participants.extend(self.accessibility_data[day][hour])
        declared_participants = list(set(declared_participants))

        flag = 0
        for participant in declared_participants:
            if participant not in schedule_participants:
                flag += 1
        if flag > 0:
            print("Nie wszyscy zadeklarowani dostali wpis do grafiku!")

    def to_export_form(self):
        """
        Formats data form schedule DataFrame to form accessible for Google Sheet API
        :return: lists of values to populate sheet
        """

        hours_values = [[f'{hour}:00 - {hour+1}:00'] for hour in self.schedule['Hour']]
        person_values = [[person_1, person_2] for person_1, person_2 in zip(self.schedule['Person 1'],
                                                                            self.schedule['Person 2'])]
        date_values = [[f'{date.day:02}.{date.month:02} - {self.CART_DAYS_DICT[date.weekday()]}'] for date in self.schedule['Date']]
        return date_values, hours_values, person_values

    def schedule_to_gsheet(self, sheet_title):
        gsheet = GoogleSheet('Plac Grunwaldzki')
        dates, hours, people = self.to_export_form()

        gsheet.get_credentials()
        sheet_id = gsheet.init_new_spreadsheet(sheet_title)
        values = [['Dzień', 'Godziny', 'Rondo Reagana']]
        body = {'values': values}
        gsheet.service.spreadsheets().values().update(spreadsheetId=sheet_id, range='A1:C1',
                                       valueInputOption='USER_ENTERED', body=body).execute()

        # TODO: This shit below needs to go to seperate file
        data = [{
            'range': 'A3:A',
            'values': dates
        },
            {
            'range': 'B3:B',
            'values': hours
        },
            {
                'range': 'C3:D',
                'values': people
            }]
        requests = [{'autoResizeDimensions': {'dimensions': {'sheetId': 0, 'dimension': "COLUMNS", 'startIndex': 0}}},
                    {'mergeCells': {'range': {"sheetId": 0,
                                              "startRowIndex": 0,
                                              "endRowIndex": 2,
                                              "startColumnIndex": 2,
                                              "endColumnIndex": 4}, 'mergeType': 'MERGE_ALL'}},
                    {'mergeCells': {'range': {"sheetId": 0,
                                              "startRowIndex": 0,
                                              "endRowIndex": 2,
                                              "startColumnIndex": 0,
                                              "endColumnIndex": 1}, 'mergeType': 'MERGE_ALL'}},
                    {'mergeCells': {'range': {"sheetId": 0,
                                              "startRowIndex": 0,
                                              "endRowIndex": 2,
                                              "startColumnIndex": 1,
                                              "endColumnIndex": 2}, 'mergeType': 'MERGE_ALL'}},
                    {'repeatCell': {
                        'range': {"sheetId": 0,
                                  "startRowIndex": 0,
                                  "startColumnIndex": 0},
                        'cell': {'userEnteredFormat': {'horizontalAlignment': 'CENTER'}},
                        'fields': "userEnteredFormat(horizontalAlignment)"
                    }},
                    {'repeatCell': {
                        'range': {"sheetId": 0,
                                  "startRowIndex": 2,
                                  "startColumnIndex": 2,
                                  "endRowIndex": 151, # TODO: Zrobić to automatyczne, bo z palca jest teraz
                                  "endColumnIndex": 4 },
                        'cell': {'userEnteredFormat': {'backgroundColor': {'red': 252/255, 'green': 242/255, 'blue': 203/255}}},
                        'fields': "userEnteredFormat(backgroundColor)"
                    }},
                    {'repeatCell': {
                        'range': {"sheetId": 0,
                                  "startRowIndex": 0,
                                  "startColumnIndex": 2,
                                  "endRowIndex": 2,
                                  "endColumnIndex": 4},
                        'cell': {'userEnteredFormat': {
                            'backgroundColor': {'red': 235 / 255, 'green': 178 / 255, 'blue': 106 / 255}}},
                        'fields': "userEnteredFormat(backgroundColor)"
                    }},
                    {'repeatCell': {
                        'range': {"sheetId": 0,
                                  "startRowIndex": 0,
                                  "startColumnIndex": 0,
                                  "endRowIndex": 2,
                                  "endColumnIndex": 2},
                        'cell': {'userEnteredFormat': {
                            'backgroundColor': {'red': 183 / 255, 'green': 183 / 255, 'blue': 183 / 255}}},
                        'fields': "userEnteredFormat(backgroundColor)"
                    }}
                    ]

        body = {'valueInputOption': 'USER_ENTERED', 'data': data}
        gsheet.service.spreadsheets().values().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
        body = {'requests': requests}
        gsheet.service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=body).execute()

