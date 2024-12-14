from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=100)  # Medicine_Name
    manufacture_date = models.DateField(default='2000-01-01')  # Provide a default date, e.g., '2000-01-01'
    expiry_date = models.DateField(default='2100-01-01')  # Default date in the future for safety
    batch_number = models.CharField(max_length=100, default='Unknown')  # Default value for batch_number
    supplier = models.CharField(max_length=255, default='Unknown')  # Default value for supplier
    temperature = models.FloatField(default=0.0)  # Default for temperature
    humidity = models.FloatField(default=0.0)  # Default for humidity
    ph_level = models.FloatField(default=0.0)  # Default for pH_Level
    contaminant_level = models.FloatField(default=0.0)  # Default for Contaminant_Level
    active_ingredient_purity = models.FloatField(default=0.0)  # Default for Active_Ingredient_Purity
    inspected_by = models.CharField(max_length=255, default='Unknown')  # Default for Inspected_By
    accepted_or_rejected = models.CharField(max_length=50, default='Unknown')  # Default for Accepted_or_Rejected

    def _str_(self):
        return self.name