# import csv
# import os
# from datetime import datetime
# from django.core.management.base import BaseCommand
# from api.models import Item

# class Command(BaseCommand):
#     help = 'Import medicine data from a CSV file'

#     def handle(self, *args, **kwargs):
#         file_path = os.path.join('data', 'medicines.csv')  # Path to your CSV file

#         try:
#             with open(file_path, 'r') as file:
#                 reader = csv.DictReader(file)
#                 for row in reader:
#                     # Convert the date format from MM/DD/YYYY to YYYY-MM-DD
#                     manufacture_date = datetime.strptime(row['Manufacture_Date'], '%m/%d/%Y').strftime('%Y-%m-%d')
#                     expiry_date = datetime.strptime(row['Expiry_Date'], '%m/%d/%Y').strftime('%Y-%m-%d')

#                     Item.objects.create(
#                         name=row['Medicine_Name'],
#                         manufacture_date=manufacture_date,
#                         expiry_date=expiry_date,
#                         batch_number=row['Batch_No'],
#                         supplier=row['Supplier'],
#                         temperature=row['Temperature (Â°C)'],
#                         humidity=row['Humidity (%)'],
#                         ph_level=row['pH_Level'],
#                         contaminant_level=row['Contaminant_Level (ppm)'],
#                         active_ingredient_purity=row['Active_Ingredient_Purity (%)'],
#                         inspected_by=row['Inspected_By'],
#                         accepted_or_rejected=row['Accepted_or_Rejected']
#                     )
#             self.stdout.write(self.style.SUCCESS('Successfully imported medicine data!'))
#         except FileNotFoundError:
#             self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
#         except KeyError as e:
#             self.stdout.write(self.style.ERROR(f"Missing expected column: {e}"))
#         except ValueError as e:
#             self.stdout.write(self.style.ERROR(f"Invalid value: {e}"))


import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from api.models import Item

class Command(BaseCommand):
    help = 'Import medicine data from a CSV file'

    def handle(self, *args, **kwargs):
        # Define the path to the CSV file
        file_path = os.path.join('data', 'medicines.csv')  # Update with correct path if needed

        try:
            # Open the CSV file for reading
            with open(file_path, 'r') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    try:
                        # Convert the date format from MM/DD/YYYY to YYYY-MM-DD
                        manufacture_date = datetime.strptime(row['Manufacture_Date'], '%m/%d/%Y').strftime('%Y-%m-%d')
                        expiry_date = datetime.strptime(row['Expiry_Date'], '%m/%d/%Y').strftime('%Y-%m-%d')

                        # Create a new Item object from the CSV row
                        Item.objects.create(
                            name=row['Medicine_Name'],
                            manufacture_date=manufacture_date,
                            expiry_date=expiry_date,
                            batch_number=row['Batch_No'],
                            supplier=row['Supplier'],
                            temperature=row['Temperature (Â°C)'],
                            humidity=row['Humidity (%)'],
                            ph_level=row['pH_Level'],
                            contaminant_level=row['Contaminant_Level (ppm)'],
                            active_ingredient_purity=row['Active_Ingredient_Purity (%)'],
                            inspected_by=row['Inspected_By'],
                            accepted_or_rejected=row['Accepted_or_Rejected']
                        )
                    except KeyError as e:
                        # Handle missing columns gracefully
                        self.stdout.write(self.style.ERROR(f"Missing expected column: {e}"))
                    except ValueError as e:
                        # Handle invalid date or value format
                        self.stdout.write(self.style.ERROR(f"Invalid value in row: {row}. Error: {e}"))

            # Success message after import completes
            self.stdout.write(self.style.SUCCESS('Successfully imported medicine data!'))

        except FileNotFoundError:
            # Handle file not found error
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
        except Exception as e:
            # Handle general exceptions
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))