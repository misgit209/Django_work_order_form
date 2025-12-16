from django.db import models


class Member(models.Model):
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)


class FinishedGoodsMaster(models.Model):
    ItemCode = models.CharField(max_length=50, primary_key=True)
    ItemCategory = models.CharField(max_length=10, null=True, blank=True)
    Product = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'tblFinishedGoodsMaster'
        managed = False

    def __str__(self):
        return str(self.ItemCode)


class LineMaster(models.Model):
    LineName = models.CharField(max_length=100, primary_key=True)
    Product = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'tblLineMaster'
        managed = False

    def __str__(self):
        return str(self.LineName)


class ProductionOperationMaster(models.Model):
    id = models.AutoField(primary_key=True, db_column='operationid')
    OperationName = models.CharField(max_length=100)
    Product = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'tblProductionOperationMaster'
        managed = False

    def __str__(self):
        return str(self.OperationName)


class EmployeeMaster(models.Model):
    EmpCode = models.CharField(max_length=50, primary_key=True)
    EmpName = models.CharField(max_length=255)
    ResignFlag = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'tblEmployeeMaster'
        managed = False

    def __str__(self):
        return f"{self.EmpName} ({self.EmpCode})"


class WorkOrder(models.Model):
    id = models.AutoField(primary_key=True)
    WorkOrderDate = models.DateField(null=True, blank=True)
    FgCode = models.CharField(max_length=50, null=True, blank=True)
    LineName = models.CharField(max_length=100, null=True, blank=True)
    BatchQty = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'tblWorkOrder'
        managed = False

    def __str__(self):
        return f"WO {self.id}: {self.FgCode} / {self.LineName}"


class WorkOrderMisNos(models.Model):
    workordertableid = models.IntegerField()
    misslipno = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'tblWorkOrderMISNos'
        managed = False

    def __str__(self):
        return f"MIS {self.misslipno} for WO {self.workordertableid}"


class WorkOrderTransaction(models.Model):
    workordertableid = models.IntegerField()
    operatorid = models.CharField(max_length=50, null=True, blank=True)
    operationid = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'tblWorkOrderTransaction'
        managed = False

    def __str__(self):
        return f"WO {self.workordertableid} - Operator {self.operatorid} - Op {self.operationid}"  
