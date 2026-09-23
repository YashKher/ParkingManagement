from django.db import models

PLATE_TYPES = [
    ('white_black',   'White Plate / Black Text — Private (Non-Commercial)'),
    ('yellow_black',  'Yellow Plate / Black Text — Commercial'),
    ('green_white',   'Green Plate / White Text — EV Private'),
    ('green_yellow',  'Green Plate / Yellow Text — EV Commercial'),
    ('black_yellow',  'Black Plate / Yellow Text — Self-Drive Rental'),
    ('red_white',     'Red Plate / White Text — Temporary Registration'),
    ('blue_white',    'Blue Plate / White Text — Diplomatic'),
    ('red_emblem',    'Red Plate / National Emblem — President / Governor'),
    ('arrow_red',     'Arrow (↑) / Red — Military / Defence'),
    ('bh_series',     'BH Series / Black — Transferable (Pan-India)'),
]

VEHICLE_TYPES = [
    ('Car', 'Car'),
    ('Bike', 'Bike'),
    ('Auto', 'Auto'),
    ('Truck', 'Truck'),
    ('Bus', 'Bus'),
    ('EV', 'Electric Vehicle'),
    ('Military', 'Military / Defence'),
    ('Diplomatic', 'Diplomatic'),
]

class Vehicle(models.Model):
    vehicle_number = models.CharField(max_length=20, unique=True, help_text="e.g. GJ 00 AA 0000 or BH 24 ZA 0001")
    owner_name     = models.CharField(max_length=100)
    mobile         = models.CharField(max_length=15)
    vehicle_type   = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    plate_type     = models.CharField(max_length=20, choices=PLATE_TYPES, default='white_black')
    state_code     = models.CharField(max_length=5, blank=True, help_text="e.g. MH, DL, KA")

    def __str__(self):
        return f"{self.vehicle_number} ({self.owner_name})"

    def get_plate_colors(self):
        """Return (plate_bg_color, text_color, label) for rendering the plate."""
        color_map = {
            'white_black':  ('#FFFFFF', '#000000', 'Private'),
            'yellow_black': ('#FFD700', '#000000', 'Commercial'),
            'green_white':  ('#008000', '#FFFFFF', 'EV Private'),
            'green_yellow': ('#008000', '#FFD700', 'EV Commercial'),
            'black_yellow': ('#1a1a1a', '#FFD700', 'Self-Drive Rental'),
            'red_white':    ('#CC0000', '#FFFFFF', 'Temporary'),
            'blue_white':   ('#003580', '#FFFFFF', 'Diplomatic'),
            'red_emblem':   ('#CC0000', '#FFD700', 'President/Governor'),
            'arrow_red':    ('#1a1a1a', '#CC0000', 'Military'),
            'bh_series':    ('#FFFFFF', '#000000', 'BH Series'),
        }
        return color_map.get(self.plate_type, ('#FFFFFF', '#000000', 'Unknown'))


class ParkingRecord(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Exited', 'Exited'),
    ]

    vehicle     = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    slot_number = models.IntegerField()
    entry_time  = models.DateTimeField(auto_now_add=True)
    exit_time   = models.DateTimeField(null=True, blank=True)
    total_hours = models.FloatField(null=True, blank=True)
    parking_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')

    def __str__(self):
        return f"{self.vehicle.vehicle_number} - Slot {self.slot_number} - {self.status}"
