import asyncio

import pyowm.weatherapi25.weather
from pyowm import OWM
import geocoder
from pyowm.commons.exceptions import NotFoundError

from config import WEATHER_SERVER, HPA_MMHG
from sconfig import API_key
from pyowm.utils.config import get_default_config
from db_Worker import DBWorker

import socket


class WeatherParser:
    def __init__(self):
        try:
            self.weather_server = WEATHER_SERVER
            config_dict = get_default_config()
            config_dict['language'] = 'ru'
            self.owm = OWM(API_key, config_dict)
            self.weather_mgr = self.owm.weather_manager()
            self.city = geocoder.ip('me').city
        except ConnectionError as ce:
            print(ce)
        finally:
            self.db_worker = DBWorker()

    def has_connected(self) -> bool:
        return bool(socket.create_connection((self.weather_server, 80)))

    def weather(self, forecast_type):
        if forecast_type == 'today':
            return self.weather_today()
        if forecast_type == 'days':
            return self.weather_daily()
        return self.weather_hourly()

    def weather_today(self):
        if self.has_connected():
            loc = geocoder.location(self.city)
            today = self.weather_mgr.weather_at_coords(lat=loc.latitude, lon=loc.longitude)
            self.db_worker.write_weather_today(today)
            return today
        return self.db_worker.weather_today()

    def weather_daily(self):
        if self.has_connected():
            days = self.weather_mgr.one_call(*geocoder.location(self.city).latlng).forecast_daily[:3]
            self.db_worker.write_weather_daily(days)
            return days

        a = pyowm.weatherapi25.weather.Weather
        weather_daily = self.db_worker.weather_daily()

        print(weather_daily[0]['weather_icon_name'])

        for weather in weather_daily:
            weather['sunrise'] = weather['sunrise_time']
            weather['sunset'] = weather['sunset_time']
            weather['last'] = {'dt': weather['reference_time']}

        return [a.from_dict(weather) for weather in weather_daily]

    def weather_hourly(self):
        if self.has_connected():
            loc = geocoder.location(self.city) if isinstance(self.city, str) else self.city
            hours = self.weather_mgr.one_call(lat=loc.latitude, lon=loc.longitude).forecast_hourly
            self.db_worker.write_weather_hourly(hours)
            return hours
        return self.db_worker.weather_hourly()

    def get_city(self):
        return self.city

    def check_city(self, city):
        try:
            self.weather_mgr.weather_at_place(city)
            print(self.weather_mgr.weather_at_place(city).location)
            return True
        except NotFoundError:
            return False

    def change_city(self, city):
        if self.check_city(city):
            self.city = city
            return True
        return False

    # noinspection PyPep8Naming
    @staticmethod
    def hPa_to_mmHg(hPa):
        return hPa * HPA_MMHG
