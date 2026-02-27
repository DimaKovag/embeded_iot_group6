from csv import reader
from datetime import datetime
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.aggregated_data import AggregatedData
from domain.parking import Parking

class FileDatasource:
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
        """Відкриття файлів та ініціалізація читання"""
        self.accel_file = open(self.accelerometer_filename, newline='')
        self.gps_file = open(self.gps_filename, newline='')
        self.parking_file = open(self.parking_filename, newline='')
        
        self.accel_reader = reader(self.accel_file)
        self.gps_reader = reader(self.gps_file)
        self.parking_reader = reader(self.parking_file)

        next(self.accel_reader)
        next(self.gps_reader)
        next(self.parking_reader)

    def read(self) -> AggregatedData:
        """Зчитування наступного набору даних"""
        try:
            accel_row = next(self.accel_reader)
            gps_row = next(self.gps_reader)
            parking_row = next(self.parking_reader)
        except StopIteration:
            self.accel_file.seek(0)
            self.gps_file.seek(0)
            self.parking_file.seek(0)
            
            self.accel_reader = reader(self.accel_file)
            self.gps_reader = reader(self.gps_file)
            self.parking_reader = reader(self.parking_file)
            
            next(self.accel_reader)
            next(self.gps_reader)
            next(self.parking_reader)
            
            accel_row = next(self.accel_reader)
            gps_row = next(self.gps_reader)
            parking_row = next(self.parking_reader)

        return AggregatedData(
            user_id=self.user_id,
            accelerometer=Accelerometer(
                int(accel_row[0]),
                int(accel_row[1]),
                int(accel_row[2])
            ),
            gps=Gps(
                float(gps_row[0]),
                float(gps_row[1])
            ),
            parking=Parking(
                empty_count=int(parking_row[0]),
                gps=Gps(float(parking_row[2]), float(parking_row[1]))
            ),
            timestamp=datetime.now()
        )

    def stopReading(self, *args, **kwargs):
        """Закриття всіх відкритих файлів"""
        if self.accel_file:
            self.accel_file.close()
        if self.gps_file:
            self.gps_file.close()
        if self.parking_file:
            self.parking_file.close()