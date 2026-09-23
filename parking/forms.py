from django import forms
from .models import Vehicle, PLATE_TYPES, VEHICLE_TYPES


class VehicleEntryForm(forms.Form):
    vehicle_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'GJ 00 AA 0000',
            'style': 'text-transform:uppercase;font-family:"JetBrains Mono",monospace;letter-spacing:2px;font-size:16px;',
            'id': 'id_vehicle_number',
        })
    )
    owner_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'FULL NAME',
            'style': 'text-transform:uppercase;',
        })
    )
    mobile = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '9876543210',
            'maxlength': '10',
            'inputmode': 'numeric',
            'id': 'id_mobile',
        })
    )
    vehicle_type = forms.ChoiceField(
        choices=VEHICLE_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    plate_type = forms.ChoiceField(
        choices=PLATE_TYPES,
        initial='white_black',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    state_code = forms.CharField(
        max_length=5,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MH',
            'maxlength': '5',
            'style': 'text-transform:uppercase;font-family:"JetBrains Mono",monospace;letter-spacing:3px;font-size:18px;font-weight:700;',
            'id': 'id_state_code',
        })
    )

    def clean_vehicle_number(self):
        return self.cleaned_data['vehicle_number'].strip().upper()

    def clean_state_code(self):
        return self.cleaned_data['state_code'].strip().upper()

    def clean_owner_name(self):
        return self.cleaned_data['owner_name'].strip().upper()

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile'].strip()
        if mobile.startswith('+91'):
            mobile = mobile[3:].strip()
        elif mobile.startswith('91') and len(mobile) == 12:
            mobile = mobile[2:].strip()
        mobile = mobile.replace(' ', '').replace('-', '')
        if not mobile.isdigit():
            raise forms.ValidationError('Mobile number must contain only digits.')
        if len(mobile) != 10:
            raise forms.ValidationError('Mobile number must be exactly 10 digits (without +91 prefix).')
        if mobile[0] not in '6789':
            raise forms.ValidationError('Mobile number must start with 6, 7, 8, or 9.')
        return mobile

    def clean(self):
        cleaned = super().clean()
        vnum  = cleaned.get('vehicle_number', '').upper()
        state = cleaned.get('state_code', '').upper()
        if vnum and state and len(vnum) >= 2 and len(state) >= 2:
            if vnum[:2] != state[:2]:
                raise forms.ValidationError(
                    f"Vehicle number prefix '{vnum[:2]}' does not match "
                    f"state code '{state[:2]}'. Both must start with the same letters (e.g. MH)."
                )
        return cleaned


class VehicleExitForm(forms.Form):
    vehicle_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'GJ 00 AA 0000',
            'style': 'text-transform:uppercase;font-family:"JetBrains Mono",monospace;letter-spacing:2px;font-size:18px;font-weight:600;',
            'id': 'id_exit_vehicle_number',
        })
    )

    def clean_vehicle_number(self):
        return self.cleaned_data['vehicle_number'].strip().upper()
