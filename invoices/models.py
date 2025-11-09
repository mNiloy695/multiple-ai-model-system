from django.db import models
from plan.models import PlanModel
from django.contrib.auth import get_user_model
User=get_user_model()
# Create your models here.
STATUS=(
    ('paid','paid'),
    ('unpaid','unpaid'),
)
class InvoiceModel(models.Model):
    invoice_id=models.CharField(max_length=100,unique=True)
    plan=models.ForeignKey(PlanModel,on_delete=models.SET_NULL,null=True,related_name='invoice_plan')
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='invoices',null=True)
    date=models.DateTimeField(auto_now_add=True)
    payment_status=models.CharField(choices=STATUS,max_length=6,default="paid")
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"invoice id is {self.invoice_id}  user email is {self.user.email} amount is {self.amount}"

