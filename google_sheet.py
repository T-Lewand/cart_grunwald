import google.auth
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError

import pandas as pd
import os
import pickle


class GoogleSheet:
    def __init__(self, congregation_name):
        congregation = pd.read_csv('congragation_list.txt', sep=';')
        congregation.set_index('congregation_name', inplace=True)
        self.sheet_id = congregation.loc[congregation_name, 'cart_sheet_id']
        self.congregation_name = congregation_name

    def get_credentials(self):
        """
        Creates file with credentials to access google sheets and build service access
        :return:
        """
        credentials = None
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                credentials = pickle.load(token)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json', SCOPES)
                credentials = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(credentials, token)

        self.credentials = credentials
        self.service = build('sheets', 'v4', credentials=self.credentials)

    def get_spreadsheet(self):
        """
        Gets spreadsheet for congregation schedule
        :return:
        """

        request = self.service.spreadsheets().get(spreadsheetId=self.sheet_id)
        self.spreadsheet = request.execute()

    def list_sheets(self):
        sheet_list = []
        for sheet in self.spreadsheet['sheets']:
            sheet_list.append(sheet['properties']['title'])

        return sheet_list

    def get_sheet(self, sheet_title: str, range: str):

        request = self.service.spreadsheets().values().get(spreadsheetId=self.sheet_id,
                                                               range=f'{sheet_title}!{range}')
        sheet = request.execute()
        values = sheet.get('values')
        return values

    def init_new_spreadsheet(self, title):
        new_spreadsheet = {'properties': {'title': title}}
        spreadsheet = self.service.spreadsheets().create(body=new_spreadsheet, fields='spreadsheetId').execute()
        print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
        return spreadsheet.get('spreadsheetId')