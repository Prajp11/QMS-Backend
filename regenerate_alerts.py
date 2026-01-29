#!/usr/bin/env python
"""
Script to regenerate alerts for all existing items
Run with: python regenerate_alerts.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from api.models import Item

def regenerate_alerts():
    """Regenerate alerts for all items in the database"""
    items = Item.objects.all()
    count = items.count()
    
    print(f"Regenerating alerts for {count} items...")
    
    for i, item in enumerate(items, 1):
        alerts = item.generate_alerts()
        item.alerts = alerts
        item.save()
        
        if i % 10 == 0 or i == count:
            print(f"  Processed {i}/{count} items...")
    
    # Count alerts
    total_alerts = sum(len(item.alerts) if item.alerts else 0 for item in Item.objects.all())
    items_with_alerts = Item.objects.exclude(alerts=[]).exclude(alerts__isnull=True).count()
    
    print(f"\n✅ Alert generation complete!")
    print(f"   - Total items: {count}")
    print(f"   - Items with alerts: {items_with_alerts}")
    print(f"   - Total alerts: {total_alerts}")

if __name__ == '__main__':
    regenerate_alerts()
