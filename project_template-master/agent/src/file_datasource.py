from csv import reader
from datetime import datetime

from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.aggregated_data import AggregatedData
from domain.parking import Parking


class FileDatasource:
    """Джерело даних, що циклічно зчитує записи з CSV-файлів.

    Parameters
    ----------
    accelerometer_filename : str
        Шлях до CSV-файлу з даними акселерометра.
    gps_filename : str
        Шлях до CSV-файлу з GPS-координатами.
    parking_filename : str
        Шлях до CSV-файлу з даними паркування.
    user_id : int, optional
        Ідентифікатор користувача, за замовчуванням 1.
    """

    def __init__(
        self,
        accelerometer_filename: str,
        gps_filename: str,
        parking_filename: str,
        user_id: int = 1,
    ) -> None:
        self.accelerometer_filename = accelerometer_filename
        self.gps_filename = gps_filename
        self.parking_filename = parking_filename
        self.user_id = user_id

        self.accel_file = None
        self.gps_file = None
        self.parking_file = None

        self.accel_reader = None
        self.gps_reader = None
        self.parking_reader = None

    def startReading(self, *args, **kwargs):
        """Відкриває CSV-файли та ініціалізує зчитувачі."""
        self.accel_file = open(self.accelerometer_filename, newline="", encoding="utf-8")
        self.gps_file = open(self.gps_filename, newline="", encoding="utf-8")
        self.parking_file = open(self.parking_filename, newline="", encoding="utf-8")

        self.accel_reader = reader(self.accel_file)
        self.gps_reader = reader(self.gps_file)
        self.parking_reader = reader(self.parking_file)

        next(self.accel_reader)
        next(self.gps_reader)
        next(self.parking_reader)

    def _next_accel_row(self):
        """Повертає наступний рядок акселерометра, циклічно перезапускаючи файл."""
        try:
            return next(self.accel_reader)
        except StopIteration:
            self.accel_file.seek(0)
            self.accel_reader = reader(self.accel_file)
            next(self.accel_reader)
            return next(self.accel_reader)

    def _next_gps_row(self):
        """Повертає наступний GPS-рядок, циклічно перезапускаючи файл."""
        try:
            return next(self.gps_reader)
        except StopIteration:
            self.gps_file.seek(0)
            self.gps_reader = reader(self.gps_file)
            next(self.gps_reader)
            return next(self.gps_reader)

    def _next_parking_row(self):
        """Повертає наступний рядок паркування, циклічно перезапускаючи файл."""
        try:
            return next(self.parking_reader)
        except StopIteration:
            self.parking_file.seek(0)
            self.parking_reader = reader(self.parking_file)
            next(self.parking_reader)
            return next(self.parking_reader)

    def read(self) -> AggregatedData:
        """Зчитує один агрегований запис з усіх джерел.

        Returns
        -------
        AggregatedData
            Об'єкт із даними акселерометра, GPS, паркування та часовою міткою.

        Raises
        ------
        RuntimeError
            Якщо зчитувачі не були ініціалізовані.
        """
        if not all([self.accel_reader, self.gps_reader, self.parking_reader]):
            raise RuntimeError("Datasource is not initialized. Call startReading() first.")

        accel_row = self._next_accel_row()
        gps_row = self._next_gps_row()
        parking_row = self._next_parking_row()

        return AggregatedData(
            user_id=self.user_id,
            accelerometer=Accelerometer(
                int(accel_row[0]), int(accel_row[1]), int(accel_row[2])
            ),
            gps=Gps(
                float(gps_row[0]), float(gps_row[1])
            ),
            parking=Parking(
                empty_count=int(parking_row[0]),
                gps=Gps(float(parking_row[2]), float(parking_row[1]))
            ),
            timestamp=datetime.now()
        )

    def stopReading(self, *args, **kwargs):
        """Закриває відкриті файли джерел даних."""
        if self.accel_file:
            self.accel_file.close()
        if self.gps_file:
            self.gps_file.close()
        if self.parking_file:
            self.parking_file.close()