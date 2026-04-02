from collections import deque
import asyncio
from kivy.app import App
from kivy_garden.mapview import MapMarker, MapView
from kivy.clock import Clock
from lineMapLayer import LineMapLayer
from datasource import Datasource

MAX_PATH = 100

class MapViewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.datasource = Datasource(user_id=1)
        self.line_layer = LineMapLayer(color=[0.5, 0, 1, 1], width=6)
        self.car_marker = None
        self.path_points = deque(maxlen=MAX_PATH)
        self.prev_lat, self.prev_lon = 0, 0

        # Keep track of all potholes and bumps to avoid repetition
        self.potholes = set()
        self.bumps = set()

        # Animation
        self.animating = False
        self.animation_speed = 0.6 # car marker shift duration
        self.update_rate = 30
        self.pending_points = [] # wait for animation to stop to draw this path

    def on_start(self):
        """Періодично викликає функцію для оновлення мапи"""
        Clock.schedule_interval(self.update, 1)

    def update(self, *args):
        """Викликається регулярно для читання даних і потенційног оновлення мапи"""
        new_points = list(self.datasource.get_new_points())
        if not new_points:
            return

        new_points.reverse() # oldest to newest

        if self.car_marker is None:
            lat, lon, road_state, _ = new_points[0]
            self.car_marker = MapMarker(lat=lat, lon=lon, source="images/car.png")
            self.mapview.add_widget(self.car_marker)
            self.prev_lat, self.prev_lon = lat, lon

        if not self.animating:
            target_lat, target_lon, _, _ = new_points[-1]
            self.animate_marker_transition((self.prev_lat, self.prev_lon),
                                           (target_lat, target_lon))
            self.prev_lat, self.prev_lon = target_lat, target_lon

        if self.animating:
            self.pending_points.extend(new_points)
        else:
            self.pending_points = new_points.copy()

    def place_road_state_marker(self, lat, lon, road_state, timestamp):
        """Визначення типу нерівності на дорозі"""
        if road_state == "pothole":
            self.set_pothole_marker(lat, lon)
        elif road_state == "bump":
            self.set_bump_marker(lat, lon)
        self.path_points.append((lat, lon, timestamp))

    def update_car_marker(self, lat, lon):
        """
        Оновлює дані маркера машини на мапі.

        Parameters
        ----------
        lat : float
            Широта поточної позиції.
        lon : float
            Довгота поточної позиції.
        """
        self.car_marker.lat = lat
        self.car_marker.lon = lon
        self.mapview.trigger_update(False)

    def animate_marker_transition(self, start, end):
        """Інтерполяція переміщення маркера машини на мапі"""
        self.animating = True
        lat1, lon1 = start
        lat2, lon2 = end
        steps = self.update_rate
        delay = self.animation_speed / self.update_rate

        for i in range(1, steps + 1):
            t = i / steps
            lat = lat1 + (lat2 - lat1) * t
            lon = lon1 + (lon2 - lon1) * t

            Clock.schedule_once(
                lambda dt, latitude=lat, longitude=lon:
                self.update_car_marker(latitude, longitude),
                i * delay,
            )
        Clock.schedule_once(self.stop_animation, steps * delay)

    def stop_animation(self, dt):
        """Сигнал про завершення асинхронного виконання анімації"""
        self.animating = False
        for lat, lon, road_state, timestamp in self.pending_points:
            self.place_road_state_marker(lat, lon, road_state, timestamp)
        self.pending_points.clear()
        self.line_layer.coordinates = [(lat, lon) for lat, lon, _ in self.path_points]

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

        marker = MapMarker(lat=lat, lon=lon, source="images/pothole.png")
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

        marker = MapMarker(lat=lat, lon=lon, source="images/bump.png")
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
