from django import forms
from tracker.models import NutritionLog


class NutritionLogForm(forms.ModelForm):
    class Meta:
        model = NutritionLog
        fields = ['meal_name', 'date', 'calories', 'protein', 'carbs', 'fat']
        widgets = {
            'meal_name': forms.TextInput(attrs={
                'class': 'gymiq-input',
                'placeholder': 'e.g. Chicken & Rice, Protein Shake...'
            }),
            'date': forms.DateInput(attrs={
                'class': 'gymiq-input',
                'type': 'date'
            }),
            'calories': forms.NumberInput(attrs={
                'class': 'gymiq-input',
                'placeholder': 'kcal'
            }),
            'protein': forms.NumberInput(attrs={
                'class': 'gymiq-input',
                'placeholder': 'g',
                'step': '0.1'
            }),
            'carbs': forms.NumberInput(attrs={
                'class': 'gymiq-input',
                'placeholder': 'g',
                'step': '0.1'
            }),
            'fat': forms.NumberInput(attrs={
                'class': 'gymiq-input',
                'placeholder': 'g',
                'step': '0.1'
            }),
        }