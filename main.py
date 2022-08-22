from cart import Cart, FormResults, Month, Schedule
from google_sheet import GoogleSheet
import string


# cart = Cart('Plac Grunwaldzki')
# cart._get_spreadsheet()
# cart.get_schedule()
# cart.get_statistics()
# exit()
file_name = 'formularze.csv'
score = 0.98

response = FormResults(file_name)
response.read_file()
response.clean()
data, weigths = response.get_accessibility()
# print('XXXXXXXXXXXXXXXXX', data)
# print('YYYYYYYYYYYYYYYYY', weigths)
# response.get_accessibility_statistic(data)
schedule = Schedule(data, 8)
schedule.populate(weigths)
schedule.check_completeness()
score = schedule.statistics()


# schedule.schedule_to_gsheet('twoja stara wagowana_best1')
# TODO: format komórek, możliwość powtarzalności dla wybranych

