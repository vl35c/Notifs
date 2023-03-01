from bs4 import BeautifulSoup
import urllib3
import re
import tweepy
import datetime


class TwitterAPI:
    def __init__(self):
        self.client = tweepy.Client(
            'AAAAAAAAAAAAAAAAAAAAAGnglAEAAAAAqLPfJkcEJ2BMGQfTTTFfgzNuVAs%3DyNdQZZLqjWIwsPHoVXS2lXrogV1VCV9LeysNzI2Hr1LsG0Tdnn',
            '4rEhWeemVGnTFa08S3DrQxQBZ',
            'dEGuSbM2fxWlievHB1Vka8sb4ah94905apxhrCMYg9XkZ3DQ2W',
            '1614310861174079497-eOHj4z4y87VjvI7SmQR8PodFPHcN5S',
            'RInaEoX0klQz0qtimhx2EauYTpvVhauFbSuJo0Hz5pXZO'
        )

    def send_message(self, message):
        self.client.create_direct_message(
            participant_id='1547514135151316992',
            text=message
        )


class Analytics:
    def __init__(self, analytics_data):
        self.__data = analytics_data

        self.status = int(re.findall('\"gameStatus\":[0-9]', self.__data)[0][-1])
        self.statusText = re.findall('\"gameStatusText\":\"[A-Za-z]+\"', self.__data)[0].split(':')[1][1:-1]
        self.homeTeamTri = re.findall('\"homeTeam\":.+', self.__data)[0].split(':')[5].split(',')[0][1:-1]
        self.homeTeamScore = re.findall('\"homeTeam\":.+', self.__data)[0].split(':')[9].split(',')[0]

        self.awayTeamTri = re.findall('\"awayTeam\":.+', self.__data)[0].split(':')[5].split(',')[0][1:-1]
        self.awayTeamScore = re.findall('\"awayTeam\":.+', self.__data)[0].split(':')[9].split(',')[0]


class App:
    def __init__(self):
        self.http = urllib3.PoolManager()

        self.today = datetime.date.today()
        self.yesterday = datetime.date.today() - datetime.timedelta(days=1)

        self.games = []
        self.games_to_remove = []

        self.get_games_by_date(self.today)
        self.get_games_by_date(self.yesterday)

        self.adm = TwitterAPI()

        self.updated = False
        self.game_refresh = True

    def run(self):
        now = datetime.datetime.now()

        if now.minute < 59 and not self.updated:
            self.check_finished_games()
            self.updated = True
        elif now.minute == 59:
            self.updated = False  # reset every hour

        if now.hour == 00 and not self.game_refresh:
            self.today = datetime.date.today()
            self.yesterday = datetime.date.today() - datetime.timedelta(days=1)

            self.get_games_by_date(self.today)
            self.get_games_by_date(self.yesterday)

            self.game_refresh = True
        elif now.hour > 00:
            self.game_refresh = False

    def get_games_by_date(self, date):
        self.r = self.http.request('GET', f'https://www.nba.com/games?date={date}')
        self.data = self.r.data.decode()
        self.soup = BeautifulSoup(self.data, 'html.parser')
        self.atags = self.soup.find_all('a')

        self.get_games()

    def get_games(self):
        for tag in self.atags:
            if re.match('.+/game/.+', str(tag)):
                url = re.findall('/game/[a-z]{3}-vs-[a-z]{3}-[0-9]{10}', str(tag))[0]
                if url in self.games:
                    continue
                self.games.append(url)

    def get_analytics(self, index):
        self.r = self.http.request('GET', f'https://www.nba.com{self.games[index]}/boxscore')
        self.data = self.r.data.decode()

        analytics = re.findall('\"analytics\":.+\"statistics\"', self.data)[0]

        return analytics

    def check_finished_games(self):
        for i, current_game in enumerate(self.games):
            analytics = self.get_analytics(i)

            game = Analytics(analytics)
            if game.status == 3:
                msg = f'{game.homeTeamScore} - {game.homeTeamTri} vs {game.awayTeamTri} - {game.awayTeamScore}'
                self.adm.send_message(msg)

                self.games_to_remove.append(current_game)

        for game in self.games_to_remove:
            if game in self.games:
                self.games.remove(game)


if __name__ == '__main__':
    app = App()
