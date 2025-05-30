from .utils import PaymentGateway
from django.http import HttpRequest, HttpResponseRedirect, Http404, HttpResponse
from . import models
from django.views.decorators.csrf import csrf_exempt

# Create your views here.


@csrf_exempt
def payment_callback(request: HttpRequest):
    SITE = 'http://127.0.0.1:3000'
    pg = request.GET.get('pg')
    transaction_id = request.GET.get('transaction_id')
    if pg not in ['phonepe', 'razorpay', 'paytm'] and transaction_id is None:
        raise Http404
    if pg == 'phonepe':
        status = PaymentGateway.PhonePe(
            order_id=transaction_id).get_transaction_status()
    if pg == 'razorpay':
        status = PaymentGateway.RazorPay(
            order_id=transaction_id).get_transaction_status()
    if pg == 'paytm':
        status = PaymentGateway.PayTm(
            order_id=transaction_id).get_transaction_status()
    print(status)
    payments = models.Payment.objects.filter(
        transaction_id=transaction_id, mode=pg)
    if payments.exists():
        payment = payments.first()
        payment.status = status['status']
        payment.paid = status['paid']
        payment.save()
        models.OrderStatus.objects.create(
            status=models.STATUS_CHOICES.index('Paid'), order=payment.order)
        return HttpResponseRedirect(
            f"{SITE}/callback?pg={pg}&transaction_id={transaction_id}")
    return HttpResponse(status=200)
