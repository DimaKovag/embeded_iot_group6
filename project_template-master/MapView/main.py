from collections import deque
import asyncio
from kivy.app import App
from kiv import App
from kivy_garden.mapview import MapMarker, MapView
from kivy.clock import Clock
from lineMapLayer import LineMapLayer
from datasource import Datasource

MAX_PATH_LENGTH = 300


class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.datasource = Datasource(user_id=1)
        self.line_layer = LineMapLayer(color=[0, 0, 1, 0.7], width=2)
        self.car_marker = None
        self.path_points = deque(maxlen=MAX_PATH_LENGTH)
        self.potholes = set()
        self.bumps = set()

    def on_start(self):
        Clock.schedule_interval(self.update, 1)

    def update(self, *args):
        points = self.datasource.get_new_points()

        for lon, lat, road_state in reversed(points):
            self.update_car_marker(lat, lon)

            if road_state == "pothole":
                self.set_pothole_marker(lat, lon)
            elif road_state == "bump":
                self.set_bump_marker(lat, lon)

            self.path_points.append((lat, lon))

        if self.path_points:
            self.line_layer.coordinates = list(self.path_points)

    def update_car_marker(self, lat, lon):
        """
        Оновлює відображення маркера машини на мапі.

        Parameters
        ----------
        lat : float
            Широта поточної позиції.
        lon : float
            Довгота поточної позиції.
        """
        if self.car_marker is None:
            self.car_marker = MapMarker(
                lat=lat,
                lon=lon,
                source="images/car.png"
            )
            self.mapview.add_widget(self.car_marker)
        else:
            self.mapview.remove_widget(self.car_marker)
            self.car_marker.lat = lat
            self.car_marker.lon = lon
            self.mapview.add_widget(self.car_marker)

    def move_car_marker(self, lat, lon, duration=0.1):
        if self.car_marker:
            Animation(lat=lat, lon=lon, duration=duration).start(self.car_marker)

    def set_pothole_marker(self, lat, lon):
        """
        Встановлює маркер для ями.

        Parameters
        ----------
        lat : float
            Широта позиції ями.
        lon : float
            Довгота позиції ями.
        """
        key = (round(lat, 5), round(lon, 5))
        if key in self.potholes:
            return
        self.potholes.add(key)

        marker = MapMarker(
            lat=lat,
            lon=lon,
            source="images/pothole.png"
        )
        self.mapview.add_widget(marker)

    def set_bump_marker(self, lat, lon):
        """
        Встановлює маркер для лежачого поліцейського.

        Parameters
        ----------
        lat : float
            Широта позиції нерівності.
        lon : float
            Довгота позиції нерівності.
        """
        key = (round(lat, 5), round(lon, 5))
        if key in self.bumps:
            return
        self.bumps.add(key)

        marker = MapMarker(
            lat=lat,
            lon=lon,
            source="images/bump.png"
        )
        self.mapview.add_widget(marker)

    def build(self):
        """
        Ініціалізує мапу.

        Returns
        -------
        MapView
            Ініціалізований об'єкт мапи.
        """
        self.mapview = MapView(zoom=10, lat=50.4501, lon=30.5234)
        self.mapview.add_layer(self.line_layer, mode="scatter")
        return self.mapview


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MapViewApp().async_run(async_lib="asyncio"))
    loop.close()