from .utils import PaymentGateway
from django.http import HttpRequest, HttpResponseRedirect, Http404, HttpResponse
from . import models
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

# Create your views here.


@csrf_exempt
def payment_callback(request: HttpRequest):
    pg = request.GET.get('pg')
    transaction_id = request.GET.get('transaction_id')
    if pg not in ['phonepe', 'razorpay', 'paytm'] and transaction_id is None:
        raise Http404

    # Best-effort authenticity: don't trust query params; fetch status from gateway
    if pg == 'phonepe':
        status = PaymentGateway.PhonePe(
            order_id=transaction_id).get_transaction_status()
    elif pg == 'razorpay':
        status = PaymentGateway.RazorPay(
            order_id=transaction_id).get_transaction_status()
    elif pg == 'paytm':
        status = PaymentGateway.PayTm(
            order_id=transaction_id).get_transaction_status()
    else:
        raise Http404

    payments = models.Payment.objects.filter(
        transaction_id=transaction_id, mode=pg)
    if not payments.exists():
        # Unknown transaction id for this gateway; no-op to avoid leaking info
        return HttpResponse(status=200)

    payment = payments.first()
    # Update payment status idempotently
    new_status = status.get('status')
    new_paid = bool(status.get('paid', False))
    dirty = False
    if payment.status != new_status:
        payment.status = new_status
        dirty = True
    if payment.paid != new_paid:
        payment.paid = new_paid
        dirty = True
    if dirty:
        payment.save(update_fields=['status', 'paid'])

    # If paid, ensure a single 'Paid' OrderStatus and update order.status string
    if payment.paid:
        paid_index = models.STATUS_CHOICES.index(
            'Paid') if 'Paid' in models.STATUS_CHOICES else None
        if paid_index is not None:
            exists_paid = payment.order.statuses.filter(
                status=paid_index).exists()
            if not exists_paid:
                models.OrderStatus.objects.create(
                    status=paid_index, order=payment.order)
        # Update order.status string for quick reference
        if payment.order.status != 'Paid':
            payment.order.status = 'Paid'
            payment.order.save(update_fields=['status'])

    # Optionally, if not paid and desired, we could set order.status = 'Pending'
    # For now, only update when paid as per requirement

    return HttpResponseRedirect(
        f"{settings.FE_SITE}/callback?pg={pg}&transaction_id={transaction_id}")
