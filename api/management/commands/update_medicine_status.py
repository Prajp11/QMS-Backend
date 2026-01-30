"""
Management command to update status for all medicines
Automatically sets status to active/expired/quarantine based on conditions
"""
from django.core.management.base import BaseCommand
from api.models import Item

class Command(BaseCommand):
    help = 'Update status for all medicines based on expiry and quality conditions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING('Starting status update...'))
        
        items = Item.objects.all()
        total_count = items.count()
        
        status_changes = {
            'active': 0,
            'expired': 0,
            'quarantine': 0
        }
        
        for i, item in enumerate(items, 1):
            old_status = item.status
            new_status = item.update_status()
            
            if old_status != new_status:
                status_changes[new_status] += 1
                
                if not dry_run:
                    # Use update to avoid triggering save() again
                    Item.objects.filter(pk=item.pk).update(status=new_status)
                
                if options['verbosity'] >= 2:
                    self.stdout.write(
                        f"  {item.name} ({item.batch_number}): {old_status} → {new_status}"
                    )
            
            # Progress indicator
            if i % 100 == 0 or i == total_count:
                self.stdout.write(f"  Processed {i}/{total_count} items...")
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Status update complete!'))
        self.stdout.write(f"   Total items: {total_count}")
        self.stdout.write(f"   Changes made:")
        self.stdout.write(f"     - Set to active: {status_changes['active']}")
        self.stdout.write(f"     - Set to expired: {status_changes['expired']}")
        self.stdout.write(f"     - Set to quarantine: {status_changes['quarantine']}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('   (DRY RUN - no changes saved)'))
        
        # Get final counts
        active = Item.objects.filter(status='active').count()
        expired = Item.objects.filter(status='expired').count()
        quarantine = Item.objects.filter(status='quarantine').count()
        
        self.stdout.write('')
        self.stdout.write('Current status distribution:')
        self.stdout.write(f'  Active: {active} ({round(active/total_count*100, 1)}%)')
        self.stdout.write(f'  Expired: {expired} ({round(expired/total_count*100, 1)}%)')
        self.stdout.write(f'  Quarantine: {quarantine} ({round(quarantine/total_count*100, 1)}%)')
