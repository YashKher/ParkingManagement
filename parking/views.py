from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from decimal import Decimal
from .models import Vehicle, ParkingRecord
from .forms import VehicleEntryForm, VehicleExitForm
import math

TOTAL_SLOTS = 100

def calculate_fee(vehicle_type, total_hours):
    hours = math.ceil(total_hours)
    if hours == 0:
        hours = 1
    fee_rates = {
        'Bike':       (20, 10),
        'Car':        (50, 20),
        'Auto':       (30, 15),
        'Truck':      (100, 50),
        'Bus':        (120, 60),
        'EV':         (40, 15),
        'Military':   (0, 0),
        'Diplomatic': (0, 0),
    }
    first_hour, add_hour = fee_rates.get(vehicle_type, (50, 20))
    return first_hour + max(0, hours - 1) * add_hour


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                return render(request, 'parking/login.html', {'form': form, 'error': 'Invalid username or password.'})
        else:
            return render(request, 'parking/login.html', {'form': form, 'error': 'Invalid credentials entered.'})
    else:
        form = AuthenticationForm()
    return render(request, 'parking/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    active_records = ParkingRecord.objects.filter(status='Active').select_related('vehicle')
    occupied_slots = active_records.count()
    available_slots = TOTAL_SLOTS - occupied_slots
    percent_occupied = int((occupied_slots / TOTAL_SLOTS) * 100) if TOTAL_SLOTS else 0

    today = timezone.now().date()
    todays_entries = ParkingRecord.objects.filter(entry_time__date=today).count()
    todays_revenue = ParkingRecord.objects.filter(
        exit_time__date=today, status='Exited'
    ).aggregate(Sum('parking_fee'))['parking_fee__sum'] or 0

    context = {
        'total_slots': TOTAL_SLOTS,
        'available_slots': available_slots,
        'occupied_slots': occupied_slots,
        'percent_occupied': percent_occupied,
        'todays_entries': todays_entries,
        'todays_revenue': todays_revenue,
        'active_records': active_records,
    }
    return render(request, 'parking/dashboard.html', context)


@login_required(login_url='login')
def vehicle_entry(request):
    if request.method == 'POST':
        form = VehicleEntryForm(request.POST)
        if form.is_valid():
            vehicle_number = form.cleaned_data['vehicle_number']
            owner_name     = form.cleaned_data['owner_name']
            mobile         = form.cleaned_data['mobile']
            vehicle_type   = form.cleaned_data['vehicle_type']
            plate_type     = form.cleaned_data['plate_type']
            state_code     = form.cleaned_data['state_code']

            # Check if vehicle is CURRENTLY parked (active session exists)
            active_record = ParkingRecord.objects.filter(
                vehicle__vehicle_number=vehicle_number, status='Active'
            ).first()
            if active_record:
                return render(request, 'parking/vehicle_entry.html', {
                    'form': form,
                    'error': f'Vehicle {vehicle_number} is already parked in Slot #{active_record.slot_number}. Please check it out first before re-entry.',
                })

            # Get or create vehicle; update details on every entry
            vehicle, created = Vehicle.objects.get_or_create(
                vehicle_number=vehicle_number,
                defaults={
                    'owner_name': owner_name,
                    'mobile': mobile,
                    'vehicle_type': vehicle_type,
                    'plate_type': plate_type,
                    'state_code': state_code,
                }
            )
            if not created:
                vehicle.owner_name  = owner_name
                vehicle.mobile      = mobile
                vehicle.vehicle_type = vehicle_type
                vehicle.plate_type  = plate_type
                vehicle.state_code  = state_code
                vehicle.save()

            # Find next free slot
            occupied_slot_nums = list(
                ParkingRecord.objects.filter(status='Active').values_list('slot_number', flat=True)
            )
            available_slot = next(
                (i for i in range(1, TOTAL_SLOTS + 1) if i not in occupied_slot_nums), None
            )
            if available_slot is None:
                return render(request, 'parking/vehicle_entry.html', {
                    'form': form,
                    'error': 'No parking slots available! All 100 slots are currently occupied.',
                })

            ParkingRecord.objects.create(vehicle=vehicle, slot_number=available_slot)
            return redirect('dashboard')
    else:
        form = VehicleEntryForm()
    return render(request, 'parking/vehicle_entry.html', {'form': form})


@login_required(login_url='login')
def vehicle_exit(request):
    if request.method == 'POST':
        form = VehicleExitForm(request.POST)
        if form.is_valid():
            vehicle_number = form.cleaned_data['vehicle_number']
            try:
                record = ParkingRecord.objects.select_related('vehicle').get(
                    vehicle__vehicle_number=vehicle_number, status='Active'
                )
                record.exit_time   = timezone.now()
                duration           = record.exit_time - record.entry_time
                total_hours        = duration.total_seconds() / 3600
                record.total_hours = total_hours
                record.parking_fee = calculate_fee(record.vehicle.vehicle_type, total_hours)
                record.status      = 'Exited'
                record.save()
                return redirect('receipt', record_id=record.id)
            except ParkingRecord.DoesNotExist:
                # Check if this vehicle exists at all and already exited
                already_exited = ParkingRecord.objects.filter(
                    vehicle__vehicle_number=vehicle_number, status='Exited'
                ).order_by('-exit_time').first()
                if already_exited:
                    return render(request, 'parking/vehicle_exit.html', {
                        'form': form,
                        'error': f'Vehicle {vehicle_number} has already checked out. It is not currently parked.',
                    })
                return render(request, 'parking/vehicle_exit.html', {
                    'form': form,
                    'error': f'Vehicle {vehicle_number} not found in active parking records. Please verify the number.',
                })
    else:
        form = VehicleExitForm()
    return render(request, 'parking/vehicle_exit.html', {'form': form})


@login_required(login_url='login')
def history(request):
    query = request.GET.get('q', '').strip().upper()
    if query:
        records = ParkingRecord.objects.filter(
            vehicle__vehicle_number__icontains=query
        ).order_by('-entry_time').select_related('vehicle')
        if not records.exists():
            records = ParkingRecord.objects.filter(
                vehicle__owner_name__icontains=query
            ).order_by('-entry_time').select_related('vehicle')
    else:
        records = ParkingRecord.objects.all().order_by('-entry_time').select_related('vehicle')
    return render(request, 'parking/history.html', {'records': records, 'query': query})


@login_required(login_url='login')
def receipt(request, record_id):
    record = get_object_or_404(ParkingRecord, id=record_id)
    return render(request, 'parking/receipt.html', {'record': record})


@login_required(login_url='login')
@require_POST
def delete_record(request, record_id):
    record = get_object_or_404(ParkingRecord, id=record_id)
    record.delete()
    next_url = request.POST.get('next', 'history')
    return redirect(next_url)


@login_required(login_url='login')
@require_POST
def clear_history(request):
    # Deletes all records from database
    ParkingRecord.objects.all().delete()
    next_url = request.POST.get('next', 'history')
    return redirect(next_url)
