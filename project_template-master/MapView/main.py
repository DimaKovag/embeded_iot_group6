import asyncio
from kivy.app import App
from kivy.animation import Animation
from kivy_garden.mapview import MapMarker, MapView
from kivy.clock import Clock
from lineMapLayer import LineMapLayer
from datasource import Datasource


class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.datasource = Datasource(user_id=1)
        self.line_layer = LineMapLayer(color=[0, 0, 1, 0.7], width=2)
        self.car_marker = None
        self.path_points = []  # store (lat, lon) tuples for the car's path

        # Keep track of all potholes and bumps to avoid repetition
        self.potholes = set()
        self.bumps = set()

    def on_start(self):
        """Встановлює необхідні маркери, викликає функцію для оновлення мапи"""
        Clock.schedule_interval(self.update, 1)

    def update(self, *args):
        """Викликається регулярно для оновлення мапи"""
        points = self.datasource.get_new_points()
        for lat, lon, road_state in reversed(points):
            self.update_car_marker(lat, lon)
            if road_state == "pothole":
                self.set_pothole_marker(lat, lon)
            elif road_state == "bump":
                self.set_bump_marker(lat, lon)

            self.path_points.append((lat, lon))

        max_path_length = 10
        if len(self.path_points) > max_path_length:
            self.path_points = self.path_points[-max_path_length:]
        if self.path_points:
            self.line_layer.coordinates = self.path_points

    def update_car_marker(self, lat, lon):
        """Оновлює відображення маркера машини на мапі"""
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
        """Встановлює маркер для ями"""
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
        """Встановлює маркер для лежачого поліцейського"""
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
        """Ініціалізує мапу MapView(zoom, lat, lon)"""
        self.mapview = MapView(zoom=10, lat=50.4501, lon=30.5234)
        self.mapview.add_layer(self.line_layer, mode="scatter")
        return self.mapview


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(MapViewApp().async_run(async_lib="asyncio"))
    loop.close()
