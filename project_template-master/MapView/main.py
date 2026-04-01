import asyncio
import math

from kivy.app import App
from kivy_garden.mapview import MapMarker, MapView
from kivy.clock import Clock
from lineMapLayer import LineMapLayer
from datasource import Datasource


class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.datasource = Datasource(user_id=1)
        self.line_layer = LineMapLayer(color=[1, 0, 1, 1], width=2)
        self.car_marker = None
        self.pending_points = []
        self.path_points = []  # store (lat, lon) tuples for the car's path
        self.prev_lat, self.prev_lon = 0, 0

        # Keep track of all potholes and bumps to avoid repetition
        self.potholes = set()
        self.bumps = set()

        # Animation
        self.update_rate = 1/30
        self.animating = False
        self.animation_events = []

    def stop_animation(self, dt):
        self.animating = False

    def on_start(self):
        """Встановлює необхідні маркери, викликає функцію для оновлення мапи"""
        Clock.schedule_interval(self.update, self.update_rate)

    def update(self, *args):
        """Викликається регулярно для оновлення мапи"""
        new_points = list(self.datasource.get_new_points())
        new_points.reverse()    # oldest to newest
        self.pending_points.extend(new_points)

        if not self.pending_points:
            return

        if self.car_marker is None:
            lat, lon, road_state = self.pending_points.pop(0)
            self.car_marker = MapMarker(lat=lat, lon=lon, source="images/car.png")
            self.mapview.add_widget(self.car_marker)
            self.place_road_state_marker(lat, lon, road_state)
            self.prev_lat, self.prev_lon = lat, lon
            return

        if not self.animating and len(self.pending_points) > 1:
            self.cancel_animation()
            curr_lat, curr_lon, _ = self.pending_points[-1]
            self.move_car_marker(curr_lat, curr_lon)

            while self.pending_points:
                lat, lon, road_state = self.pending_points.pop(0)
                self.place_road_state_marker(lat, lon, road_state)

        elif not self.animating:
            lat, lon, road_state = self.pending_points.pop(0)
            self.move_car_marker(lat, lon)
            self.place_road_state_marker(lat, lon, road_state)

    def move_car_marker(self, lat, lon):
        self.animate_marker_transition((self.prev_lat, self.prev_lon), (lat, lon))
        self.prev_lat, self.prev_lon = lat, lon

    def place_road_state_marker(self, lat, lon, road_state):
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

    def set_car_marker_pos(self, lat, lon):
        """Оновлює відображення маркера машини на мапі"""
        self.car_marker.lat = lat
        self.car_marker.lon = lon
        self.mapview.trigger_update(False)

    def animate_marker_transition(self, start, end):
        self.animating = True
        lat1, lon1 = start
        lat2, lon2 = end
        steps = math.floor(1 / self.update_rate)

        for i in range(1, steps + 1):
            t = i / steps
            lat = lat1 + (lat2 - lat1) * t
            lon = lon1 + (lon2 - lon1) * t

            event = Clock.schedule_once(
                lambda dt, latitude=lat, longitude=lon:
                self.set_car_marker_pos(latitude, longitude),
                i * self.update_rate,
            )
            self.animation_events.append(event)
        event = Clock.schedule_once(self.stop_animation, steps * self.update_rate)
        self.animation_events.append(event)

    def cancel_animation(self):
        for ev in self.animation_events:
            ev.cancel()
        self.animation_events.clear()
        self.animating = False

    def set_pothole_marker(self, lat, lon):
        """Встановлює маркер для ями"""
        key = (round(lat, 5), round(lon, 5))
        if key in self.potholes:
            return
        self.potholes.add(key)

        marker = MapMarker(lat=lat, lon=lon, source="images/pothole.png")
        self.mapview.add_widget(marker)

    def set_bump_marker(self, lat, lon):
        """Встановлює маркер для лежачого поліцейського"""
        key = (round(lat, 5), round(lon, 5))
        if key in self.bumps:
            return
        self.bumps.add(key)

        marker = MapMarker(lat=lat, lon=lon, source="images/bump.png")
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
