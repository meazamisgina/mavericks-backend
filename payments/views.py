from django.shortcuts import render
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from .mpesa_api import MpesaAPIClient
from .models import MpesaSTKPush
from .serializers import MpesaSTKPushInitiateSerializer
from datetime import datetime
import logging

# Create your views here.

logger = logging.getLogger(__name__)
mpesa_client = MpesaAPIClient() 

class InitiateSTKPushView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MpesaSTKPushInitiateSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            amount = serializer.validated_data['amount']
            reference = serializer.validated_data.get('reference', f"Order-{request.user.id}-{datetime.now().timestamp()}")
            description = serializer.validated_data.get('description', 'Payment for Goods/Services')

            try:
                mpesa_transaction = MpesaSTKPush.objects.create(
                    user=request.user, # FIX: request.user is the AppUser instance
                    phone_number=phone_number,
                    amount=amount,
                    reference=reference,
                    description=description,
                    status='Pending'
                )
                daraja_response = mpesa_client.initiate_stk_push(
                    phone_number=phone_number,
                    amount=amount,
                    reference=reference,
                    description=description
                )

                mpesa_transaction.merchant_request_id = daraja_response.get('MerchantRequestID')
                mpesa_transaction.checkout_request_id = daraja_response.get('CheckoutRequestID')
                mpesa_transaction.response_code = daraja_response.get('ResponseCode')
                mpesa_transaction.response_description = daraja_response.get('ResponseDescription')
                mpesa_transaction.customer_message = daraja_response.get('CustomerMessage')
                mpesa_transaction.save()

                if daraja_response.get('ResponseCode') == '0':
                    return Response({
                        'message': 'STK Push initiated successfully. Please check your phone.',
                        'checkout_request_id': mpesa_transaction.checkout_request_id,
                        'merchant_request_id': mpesa_transaction.merchant_request_id
                    }, status=status.HTTP_200_OK)
                else:
                    logger.error(f"STK Push initiation failed for {phone_number}. Daraja Response: {daraja_response}")
                    mpesa_transaction.status = 'Failed'
                    mpesa_transaction.save()
                    return Response({
                        'error': 'Failed to initiate STK Push.',
                        'details': daraja_response.get('ResponseDescription', 'Unknown error.')
                    }, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                logger.error(f"An unexpected error occurred during STK Push initiation: {e}", exc_info=True)
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def mpesa_callback(request):

    try:
        data = request.data
        logger.info(f"M-Pesa Callback Received: {data}")

        body = data.get('Body', {})
        stk_callback = body.get('stkCallback', {})

        merchant_request_id = stk_callback.get('MerchantRequestID')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_description = stk_callback.get('ResultDesc')
        callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])

        amount = None
        mpesa_receipt_number = None
        transaction_date_str = None
        phone_number_from_callback = None

        for item in callback_metadata:
            if item.get('Name') == 'Amount':
                amount = item.get('Value')
            elif item.get('Name') == 'MpesaReceiptNumber':
                mpesa_receipt_number = item.get('Value')
            elif item.get('Name') == 'TransactionDate':
                transaction_date_str = item.get('Value')
            elif item.get('Name') == 'PhoneNumber':
                phone_number_from_callback = item.get('Value')

        transaction_date = None
        if transaction_date_str:
            try:
                transaction_date = datetime.strptime(transaction_date_str, '%Y%m%d%H%M%S')
            except ValueError:
                logger.error(f"Invalid TransactionDate format: {transaction_date_str}")

        try:
            mpesa_transaction = MpesaSTKPush.objects.get(checkout_request_id=checkout_request_id)

            if result_code == 0:
                mpesa_transaction.status = 'Completed'
                mpesa_transaction.mpesa_receipt_number = mpesa_receipt_number
                mpesa_transaction.transaction_date = transaction_date
                mpesa_transaction.amount_from_callback = amount
                mpesa_transaction.phone_number_from_callback = phone_number_from_callback
                logger.info(f"Transaction {checkout_request_id} COMPLETED. Receipt: {mpesa_receipt_number}")
            else:
                mpesa_transaction.status = 'Failed'
                logger.warning(f"Transaction {checkout_request_id} FAILED. Result Code: {result_code}, Desc: {result_description}")

            mpesa_transaction.result_code = result_code
            mpesa_transaction.result_description = result_description
            mpesa_transaction.save()

            return Response({"ResultCode": 0, "ResultDesc": "Callback accepted successfully"}, status=status.HTTP_200_OK)

        except MpesaSTKPush.DoesNotExist:
            logger.error(f"No matching MpesaSTKPush record found for CheckoutRequestID: {checkout_request_id}")
            return Response({"ResultCode": 1, "ResultDesc": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        logger.error(f"Error processing M-Pesa callback: {e}", exc_info=True)
        return Response({"ResultCode": 1, "ResultDesc": f"Error processing callback: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
