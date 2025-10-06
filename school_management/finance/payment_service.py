# finance/payment_service.py
import requests
from django.conf import settings
from django.urls import reverse
from .models import Invoice

class PaystackService:
    @staticmethod
    def initialize_payment(request, invoice_id, email):
        """Initialize payment with Paystack"""
        try:
            import uuid
            from django.utils import timezone
            
            invoice = Invoice.objects.get(id=invoice_id)
            amount = int(invoice.total_amount * 100)  # Convert to kobo
            
            # Generate unique reference for each payment attempt
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            unique_ref = f"{invoice.invoice_number}-{timestamp}-{uuid.uuid4().hex[:6]}"
            
            url = settings.PAYSTACK_INITIALIZE_URL
            callback_url = request.build_absolute_uri(
                reverse('verify_payment', args=[invoice.id])
            )
            
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
            }
            
            data = {
                "email": email,
                "amount": amount,
                "reference": unique_ref,  # Use unique reference
                "callback_url": callback_url,
                "metadata": {
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,  # Add this for tracking
                    "student_id": invoice.student.id,
                    "custom_fields": [
                        {
                            "display_name": "Student Name",
                            "variable_name": "student_name",
                            "value": invoice.student.user.get_full_name()
                        },
                        {
                            "display_name": "Class",
                            "variable_name": "class",
                            "value": str(invoice.student.current_class)
                        },
                        {
                            "display_name": "Invoice Number",
                            "variable_name": "invoice_number",
                            "value": invoice.invoice_number
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response_data = response.json()
            
            # Log the response for debugging
            print(f"Paystack Response: {response_data}")
            
            # Check if request was successful
            if response.status_code != 200:
                return {
                    'status': False,
                    'message': response_data.get('message', 'Payment initialization failed')
                }
            
            return response_data
            
        except Invoice.DoesNotExist:
            return {
                'status': False,
                'message': 'Invoice not found'
            }
        except requests.exceptions.RequestException as e:
            print(f"Network error: {str(e)}")
            return {
                'status': False,
                'message': f'Network error: {str(e)}'
            }
        except Exception as e:
            print(f"Error initializing payment: {str(e)}")
            return {
                'status': False,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def verify_payment(reference):
        """Verify payment with Paystack"""
        try:
            url = f"{settings.PAYSTACK_VERIFY_URL}{reference}"
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            }
            response = requests.get(url, headers=headers, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Error verifying payment: {str(e)}")
            return {
                'status': False,
                'message': f'Verification error: {str(e)}'
            }