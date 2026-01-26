from django.core.management.base import BaseCommand
from api.models import Item
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Create sample medicine data for testing expiry tracking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of sample medicines to create (default: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new samples'
        )

    def handle(self, *args, **options):
        if options['clear']:
            Item.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Cleared all existing medicine data')
            )

        count = options['count']
        
        # Sample medicine data
        medicines_data = [
            # Expired medicines
            {
                'name': 'Paracetamol 500mg',
                'batch_number': 'PAR001',
                'manufacture_date': datetime.now().date() - timedelta(days=400),
                'expiry_date': datetime.now().date() - timedelta(days=10),  # Expired
                'quantity': 100,
                'manufacturer': 'PharmaCorp',
                'category': 'Pain Relief',
                'price': 25.50,
                'supplier': 'MedSupply Ltd',
                'temperature': 25.0,
                'humidity': 60.0,
                'ph_level': 7.2,
                'contaminant_level': 0.01,
                'active_ingredient_purity': 99.5,
                'inspected_by': 'Dr. Smith',
                'accepted_or_rejected': 'Expired'
            },
            {
                'name': 'Ibuprofen 400mg',
                'batch_number': 'IBU002',
                'manufacture_date': datetime.now().date() - timedelta(days=350),
                'expiry_date': datetime.now().date() - timedelta(days=5),  # Expired
                'quantity': 75,
                'manufacturer': 'HealthPharma',
                'category': 'Pain Relief',
                'price': 30.00,
                'supplier': 'Global Meds',
                'temperature': 24.5,
                'humidity': 55.0,
                'ph_level': 7.0,
                'contaminant_level': 0.02,
                'active_ingredient_purity': 98.8,
                'inspected_by': 'Dr. Johnson',
                'accepted_or_rejected': 'Expired'
            },
            # Urgent medicines (expiring in 1-7 days)
            {
                'name': 'Amoxicillin 250mg',
                'batch_number': 'AMX003',
                'manufacture_date': datetime.now().date() - timedelta(days=300),
                'expiry_date': datetime.now().date() + timedelta(days=3),  # Urgent
                'quantity': 50,
                'manufacturer': 'MediLabs',
                'category': 'Antibiotic',
                'price': 45.00,
                'supplier': 'MedSupply Ltd',
                'temperature': 23.0,
                'humidity': 50.0,
                'ph_level': 6.8,
                'contaminant_level': 0.005,
                'active_ingredient_purity': 99.2,
                'inspected_by': 'Dr. Brown',
                'accepted_or_rejected': 'Accepted'
            },
            {
                'name': 'Aspirin 100mg',
                'batch_number': 'ASP004',
                'manufacture_date': datetime.now().date() - timedelta(days=280),
                'expiry_date': datetime.now().date() + timedelta(days=6),  # Urgent
                'quantity': 120,
                'manufacturer': 'CardioMed',
                'category': 'Cardiovascular',
                'price': 20.75,
                'supplier': 'HeartCare Supplies',
                'temperature': 22.5,
                'humidity': 45.0,
                'ph_level': 7.1,
                'contaminant_level': 0.008,
                'active_ingredient_purity': 99.0,
                'inspected_by': 'Dr. Wilson',
                'accepted_or_rejected': 'Accepted'
            },
            # Warning medicines (expiring in 8-30 days)
            {
                'name': 'Metformin 500mg',
                'batch_number': 'MET005',
                'manufacture_date': datetime.now().date() - timedelta(days=250),
                'expiry_date': datetime.now().date() + timedelta(days=15),  # Warning
                'quantity': 200,
                'manufacturer': 'DiabetesCare',
                'category': 'Diabetes',
                'price': 35.50,
                'supplier': 'EndoSupplies',
                'temperature': 25.5,
                'humidity': 52.0,
                'ph_level': 6.9,
                'contaminant_level': 0.003,
                'active_ingredient_purity': 99.8,
                'inspected_by': 'Dr. Davis',
                'accepted_or_rejected': 'Accepted'
            },
            {
                'name': 'Cetirizine 10mg',
                'batch_number': 'CET006',
                'manufacture_date': datetime.now().date() - timedelta(days=200),
                'expiry_date': datetime.now().date() + timedelta(days=25),  # Warning
                'quantity': 80,
                'manufacturer': 'AllergyRelief',
                'category': 'Antihistamine',
                'price': 18.25,
                'supplier': 'AllerCare Ltd',
                'temperature': 24.0,
                'humidity': 48.0,
                'ph_level': 7.3,
                'contaminant_level': 0.006,
                'active_ingredient_purity': 98.5,
                'inspected_by': 'Dr. Miller',
                'accepted_or_rejected': 'Accepted'
            },
            # Safe medicines (expiring in 30+ days)
            {
                'name': 'Vitamin D3 1000IU',
                'batch_number': 'VIT007',
                'manufacture_date': datetime.now().date() - timedelta(days=150),
                'expiry_date': datetime.now().date() + timedelta(days=90),  # Safe
                'quantity': 300,
                'manufacturer': 'HealthPlus',
                'category': 'Supplement',
                'price': 15.75,
                'supplier': 'VitaSupply',
                'temperature': 23.5,
                'humidity': 40.0,
                'ph_level': 7.0,
                'contaminant_level': 0.001,
                'active_ingredient_purity': 100.0,
                'inspected_by': 'Dr. Taylor',
                'accepted_or_rejected': 'Accepted'
            },
            {
                'name': 'Omeprazole 20mg',
                'batch_number': 'OME008',
                'manufacture_date': datetime.now().date() - timedelta(days=100),
                'expiry_date': datetime.now().date() + timedelta(days=120),  # Safe
                'quantity': 150,
                'manufacturer': 'GastroMed',
                'category': 'Gastrointestinal',
                'price': 42.00,
                'supplier': 'DigestCare',
                'temperature': 22.0,
                'humidity': 44.0,
                'ph_level': 6.7,
                'contaminant_level': 0.004,
                'active_ingredient_purity': 99.3,
                'inspected_by': 'Dr. Anderson',
                'accepted_or_rejected': 'Accepted'
            }
        ]

        # Create additional random medicines if count is higher than base samples
        base_count = len(medicines_data)
        created_count = 0

        # First create the base samples
        for med_data in medicines_data[:min(count, base_count)]:
            try:
                Item.objects.get_or_create(
                    batch_number=med_data['batch_number'],
                    defaults=med_data
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating {med_data["name"]}: {str(e)}')
                )

        # Generate additional random medicines if needed
        if count > base_count:
            additional_count = count - base_count
            categories = ['Pain Relief', 'Antibiotic', 'Cardiovascular', 'Diabetes', 'Supplement']
            manufacturers = ['PharmaCorp', 'MediLabs', 'HealthPlus', 'CardioMed', 'DiabetesCare']
            suppliers = ['MedSupply Ltd', 'Global Meds', 'VitaSupply', 'EndoSupplies']
            inspectors = ['Dr. Smith', 'Dr. Johnson', 'Dr. Brown', 'Dr. Wilson', 'Dr. Davis']

            for i in range(additional_count):
                batch_num = f'RND{str(i+100).zfill(3)}'
                
                # Randomly assign expiry status
                status_choice = random.choice(['expired', 'urgent', 'warning', 'safe'])
                
                if status_choice == 'expired':
                    expiry_days = random.randint(-30, -1)
                elif status_choice == 'urgent':
                    expiry_days = random.randint(1, 7)
                elif status_choice == 'warning':
                    expiry_days = random.randint(8, 30)
                else:  # safe
                    expiry_days = random.randint(31, 365)

                random_med = {
                    'name': f'Medicine {i+1}',
                    'batch_number': batch_num,
                    'manufacture_date': datetime.now().date() - timedelta(days=random.randint(100, 400)),
                    'expiry_date': datetime.now().date() + timedelta(days=expiry_days),
                    'quantity': random.randint(20, 300),
                    'manufacturer': random.choice(manufacturers),
                    'category': random.choice(categories),
                    'price': round(random.uniform(10.0, 100.0), 2),
                    'supplier': random.choice(suppliers),
                    'temperature': round(random.uniform(20.0, 30.0), 1),
                    'humidity': round(random.uniform(35.0, 65.0), 1),
                    'ph_level': round(random.uniform(6.5, 7.5), 1),
                    'contaminant_level': round(random.uniform(0.001, 0.02), 3),
                    'active_ingredient_purity': round(random.uniform(98.0, 100.0), 1),
                    'inspected_by': random.choice(inspectors),
                    'accepted_or_rejected': 'Accepted' if status_choice != 'expired' else 'Expired'
                }

                try:
                    Item.objects.get_or_create(
                        batch_number=batch_num,
                        defaults=random_med
                    )
                    created_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating random medicine {i+1}: {str(e)}')
                    )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample medicines')
        )

        # Display statistics
        total_items = Item.objects.count()
        today = datetime.now().date()
        
        expired = Item.objects.filter(expiry_date__lt=today).count()
        urgent = Item.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=7)
        ).count()
        warning = Item.objects.filter(
            expiry_date__gt=today + timedelta(days=7),
            expiry_date__lte=today + timedelta(days=30)
        ).count()
        safe = Item.objects.filter(
            expiry_date__gt=today + timedelta(days=30)
        ).count()

        self.stdout.write(f'\nDatabase Statistics:')
        self.stdout.write(f'Total medicines: {total_items}')
        self.stdout.write(self.style.ERROR(f'Expired: {expired}'))
        self.stdout.write(self.style.WARNING(f'Urgent (1-7 days): {urgent}'))
        self.stdout.write(self.style.HTTP_INFO(f'Warning (8-30 days): {warning}'))
        self.stdout.write(self.style.SUCCESS(f'Safe (30+ days): {safe}'))