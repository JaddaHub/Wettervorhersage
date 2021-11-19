import os
import shutil
import urllib.request
from datetime import datetime
import sys

import pyowm.weatherapi25.weather
from PyQt5 import uic
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtGui import QPainter, QColor, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QStyle, QDialog,
    QInputDialog, QTabWidget
    )
from change_city_UI import Ui_Dialog

from config import WIDTH, WEATHER_SERVER, HEIGHT
from main_window_ui import Ui_MainWindow
from weather import WeatherParser

stylesheet = open('style.css', 'r').read()


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # uic.loadUi('main_window_ui.ui', self)
        self.setupUi(self)
        self.initUI()

        self.weather = WeatherParser()
        self.tabs = ['today', 'days', 'hours']
        self.current_tab_index = 0

        self.load_widget(0)

    # noinspection PyAttributeOutsideInit,PyPep8Naming
    def initUI(self):
        self.change_city_dialog = ChangeCityDialog(self)
        self.change_city_btn.triggered.connect(self.change_city)
        self.tabWidget.tabBarClicked.connect(self.load_widget)

    def load_widget(self, index):
        self.current_tab_index = index
        if not index:
            return self.load_widget_today()
        if index == 1:
            return self.load_widget_days()
        return self.load_widget_hours()

    def change_city(self):
        self.change_city_dialog.show()

    def load_widget_today(self):
        try:
            weather: pyowm.weatherapi25.weather.Weather = self.get_weather().weather

            self.statusEdit_label.setText(weather.detailed_status.title())
            self.statusEdit_label.setGeometry(
                QRect((WIDTH - self.statusEdit_label.sizeHint().width()) // 2,
                      HEIGHT // 2 - self.statusEdit_label.height(),
                      self.statusEdit_label.sizeHint().width(),
                      self.statusEdit_label.sizeHint().height()))

            pixmap = QPixmap('sources/circle.png')

            # self.temperatureEdit_label.setText(str(weather.temperature('celsius').get('temp')))
            # self.feelsLikeEdit_label.setText(str(weather.temperature('celsius').get('feels_like')))
            self.temperatureEdit_label.setPixmap(pixmap)
            self.feelsLikeEdit_label.setPixmap(pixmap)

            # self.tempText_label.setText(str(weather.temperature('celsius').get('temp')))
            # self.feelsText_label.setText(str(weather.temperature('celsius').get('feels_like')))

            self.set_label(self.tempText_label, weather.temperature('celsius').get('temp'))
            self.set_label(self.feelsText_label, weather.temperature('celsius').get('feels_like'))

            timezone = datetime.now() - datetime.utcnow()

            time = weather.sunrise_time('date') + timezone
            self.set_label(self.sunriseEdit_label,
                           f'{time.hour:02d}:{time.minute:02d}:{time.second:02d}')

            time = weather.sunset_time('date') + timezone
            self.set_label(self.sunsetEdit_label,
                           f'{time.hour:02d}:{time.minute:02d}:{time.second:02d}')

            self.set_label(self.humidityEdit_label, f'{weather.humidity}%')
            if weather.precipitation_probability is not None:
                self.set_label(self.precipitationProbabilityEdit_label,
                               f'{weather.precipitation_probability}%')
                self.precipitationProbability_label.show()
            else:
                self.precipitationProbability_label.hide()
                x = self.humidity_label.width()
                self.humidityEdit_label.setGeometry(QRect(self.humidity_label.x() + x + x // 2,
                                                          self.humidityEdit_label.y(),
                                                          self.humidityEdit_label.width(),
                                                          self.humidityEdit_label.height()))
            if weather.humidex is not None:
                self.set_label(self.humidexEdit_label, weather.humidex)
                self.humidex_label.show()
            else:
                self.humidex_label.hide()

            self.download_img(weather)
            pixmap = QPixmap(f'images/{weather.weather_icon_name}')
            self.status_img.setPixmap(pixmap)
            self.status_img.resize(self.status_img.sizeHint().width(),
                                   self.status_img.sizeHint().height())
        except Exception as e:
            print(e)

    def get_weather_ico(self, weather):
        return weather.weather_icon_url("2x")

    def load_widget_days(self):
        weather = self.get_weather()

    def set_label(self, label, text=None):
        if text is not None:
            label.setText(str(text))
        label.setGeometry(label.x(), label.y(), label.sizeHint().width(), label.sizeHint().height())

    def load_widget_hours(self):
        weather = self.get_weather()

    def get_weather(self):
        return self.weather.weather(self.tabs[self.current_tab_index])

    def download_img(self, weather):
        res = urllib.request.urlopen(self.get_weather_ico(weather))
        out = open(f'images/{weather.weather_icon_name}', 'wb')
        out.write(res.read())
        out.close()

    def closeEvent(self, event):
        shutil.rmtree('images')
        os.mkdir('images')


class ChangeCityDialog(QDialog, Ui_Dialog):
    def __init__(self, first_form: MainWindow):
        super().__init__()
        self.setupUi(self)
        # uic.loadUi('change_city_UI.ui', self)
        self.ok_btn.clicked.connect(self.ok)
        self.cancel_btn.clicked.connect(self.cancel)
        self.not_found_error_label: QLabel
        self.not_found_error_label.setText('')
        self.first_form = first_form

    def ok(self):
        city = self.city_edit.text().strip()
        if not city:
            return self.not_found_error_label.setText('Введите название города')
        answer = self.first_form.weather.change_city(city)
        if answer:
            self.first_form.load_widget(0)
            self.close()
        else:
            self.not_found_error_label.setText('Город не найден')

    def cancel(self):
        self.city_edit.setText('')
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec())
