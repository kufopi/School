from django.core.management.base import BaseCommand
from students.models import StudentHealthRecord
from decimal import Decimal, InvalidOperation

class Command(BaseCommand):
    help = 'Cleans invalid BMI values in StudentHealthRecord'

    def handle(self, *args, **kwargs):
        invalid_records = []
        for record in StudentHealthRecord.objects.all():
            try:
                if record.bmi is not None:
                    Decimal(str(record.bmi))  # Test conversion to Decimal
            except (ValueError, InvalidOperation, TypeError):
                invalid_records.append(record)
                self.stdout.write(self.style.WARNING(f"Invalid BMI in record ID {record.id}: {record.bmi}"))

        if invalid_records:
            self.stdout.write(self.style.WARNING(f"Found {len(invalid_records)} invalid BMI records"))
            for record in invalid_records:
                try:
                    # Recalculate BMI if possible
                    if record.height and record.weight and float(record.height) > 0 and float(record.weight) > 0:
                        height_in_meters = float(record.height) / 100
                        bmi_value = float(record.weight) / (height_in_meters ** 2)
                        record.bmi = Decimal(str(round(bmi_value, 1)))
                    else:
                        record.bmi = None
                    record.save()
                    self.stdout.write(self.style.SUCCESS(f"Fixed record ID {record.id}: BMI set to {record.bmi}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to fix record ID {record.id}: {e}"))
        else:
            self.stdout.write(self.style.SUCCESS("No invalid BMI records found"))