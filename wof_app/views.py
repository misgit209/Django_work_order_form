from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from django.db import connections

from .models import (
    FinishedGoodsMaster,
    LineMaster,
    ProductionOperationMaster,
    EmployeeMaster,
    WorkOrder,
)


def index(request):
    return render(request, "wof_app/index.html")


def get_tr_item_codes(request):
    """Return ItemCode values where ItemCategory == 'TR' using ORM."""
    try:
        item_codes = list(FinishedGoodsMaster.objects.filter(ItemCategory='TR').values_list('ItemCode', flat=True))
        print(f"[INFO] Found {len(item_codes)} TR items")
        return JsonResponse(item_codes, safe=False)
    except Exception as e:
        print("[ERROR]", e)
        return JsonResponse([], safe=False)

def get_item_codes(request):
    """Fetch all ItemCodes from FinishedGoodsMaster"""
    try:
        item_codes = list(FinishedGoodsMaster.objects.values_list('ItemCode', flat=True))
        print(f"[INFO] Found {len(item_codes)} item codes")
        return JsonResponse(item_codes, safe=False)
    except Exception as e:
        print("[ERROR]", e)
        return JsonResponse([], safe=False)

def get_line_name(request):
    try:
        line_names = list(LineMaster.objects.filter(Product='TR').values_list('LineName', flat=True))
        return JsonResponse(line_names, safe=False)
    except Exception as e:
        print(f"[ERROR] {e}")
        return JsonResponse([], safe=False)


def get_operation_name(request):
    try:
        operation_names = list(ProductionOperationMaster.objects.values_list('OperationName', flat=True))
        return JsonResponse(operation_names, safe=False)
    except Exception as e:
        print(f"[ERROR] {e}")
        return JsonResponse([], safe=False)


def get_employee_name(request):
    try:
        employees_qs = EmployeeMaster.objects.using('employee').filter(ResignFlag=0).order_by('EmpName').values('EmpName', 'EmpCode')
        employees = list(employees_qs)
        if not employees:
            print("[INFO] get_employee_name: no rows returned")
        return JsonResponse(employees, safe=False)
    except Exception as e:
        print(f"[ERROR] {e}")
        return JsonResponse([], safe=False)


def get_operation_id_by_name(operation_name):
    """Helper to get numeric operationid from tblProductionOperationMaster by OperationName."""
    if not operation_name:
        return None
    try:
        op = ProductionOperationMaster.objects.filter(OperationName=operation_name).first()
        if op:
            print(f"[DEBUG] Found operation: {operation_name} with id={op.id}")
            return op.id
        print(f"[WARN] Operation not found: {operation_name}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to get operation id for {operation_name}: {e}")
        return None


@csrf_exempt
def save_work_order(request):
    """Receive JSON POST and create a WorkOrder record (FgCode, LineName, BatchQty, WorkOrderDate)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        fg = data.get('partNo') or data.get('partNumber') or data.get('FgCode') or ''
        line = data.get('line') or data.get('lineName') or data.get('LineName') or ''
        batch = data.get('batchQty')
        date = data.get('date') or None
        # accept scanned MIS slip number from several possible keys
        mis_slip = data.get('misslipno') or data.get('misSlipNo') or data.get('mis_slip') or data.get('scannedMis') or None
        # accept employee code from several possible keys
        emp_code = data.get('employeeName') or data.get('employeeCode') or data.get('operatorId') or None
        # accept operation name from several possible keys
        operation_name = data.get('operationName') or data.get('operationId') or None
        print(f"[DEBUG] operation_name from request: '{operation_name}'")
        # Look up the numeric operationid from the operation name
        operation_id = get_operation_id_by_name(operation_name)
        print(f"[DEBUG] operation_id retrieved: {operation_id}")

        # Validate/normalize inputs to avoid SQL Server truncation errors
        # Match lengths to actual DB column widths (reduced to be safe)
        MAX_FG_LEN = 30
        MAX_LINE_LEN = 50
        MAX_MIS_LEN = 30

        truncated = []
        if fg and len(fg) > MAX_FG_LEN:
            truncated.append(f"FgCode truncated from {len(fg)} to {MAX_FG_LEN}")
            fg = fg[:MAX_FG_LEN]
            print(f"[WARN] FgCode truncated: {fg}")

        if line and len(line) > MAX_LINE_LEN:
            truncated.append(f"LineName truncated from {len(line)} to {MAX_LINE_LEN}")
            line = line[:MAX_LINE_LEN]
            print(f"[WARN] LineName truncated: {line}")

        if mis_slip and len(mis_slip) > MAX_MIS_LEN:
            truncated.append(f"MIS slip truncated from {len(mis_slip)} to {MAX_MIS_LEN}")
            mis_slip = mis_slip[:MAX_MIS_LEN]
            print(f"[WARN] MIS slip truncated: {mis_slip}")

        # Ensure batch is integer or NULL
        try:
            batch_val = int(batch) if batch not in (None, '') else None
        except Exception:
            batch_val = None
        
        # Log input values for debugging
        print(f"[DEBUG] Input values - FgCode: '{fg}' ({len(fg) if fg else 0} chars), LineName: '{line}' ({len(line) if line else 0} chars), Date: {date}, BatchQty: {batch_val}")

        # Insert using raw SQL and fetch the new id (SCOPE_IDENTITY for SQL Server).
        # If the table does not generate an IDENTITY value (id is NOT an IDENTITY),
        # a normal insert will fail or SCOPE_IDENTITY() will be NULL. In that case
        # fall back to a transactional allocation using MAX(id)+1 with a table lock
        # to avoid race conditions and return the allocated id via OUTPUT.
        conn = connections['default']
        new_id = None
        with conn.cursor() as cursor:
            try:
                cursor.execute(
                    "INSERT INTO tblWorkOrder (WorkOrderDate, FgCode, LineName, BatchQty) VALUES (%s, %s, %s, %s)",
                    [date or None, fg or None, line or None, batch_val]
                )
                cursor.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
                new_id_row = cursor.fetchone()
                new_id = new_id_row[0] if new_id_row else None
                print(f"[INFO] Work order inserted with SCOPE_IDENTITY: {new_id}")
            except Exception as e:
                # Normal insert failed (likely because 'id' disallows NULL and isn't an IDENTITY).
                # Attempt a safe explicit-id insert inside a transaction using TABLOCKX to
                # allocate a unique id = ISNULL(MAX(id),0)+1 and return it with OUTPUT.
                try:
                    alloc_sql = """
                    SET NOCOUNT ON;
                    BEGIN TRANSACTION;
                    DECLARE @newid INT;
                    SELECT @newid = ISNULL(MAX(id), 0) + 1 FROM tblWorkOrder WITH (TABLOCKX);
                    INSERT INTO tblWorkOrder (id, WorkOrderDate, FgCode, LineName, BatchQty)
                    OUTPUT inserted.id
                    VALUES (@newid, %s, %s, %s, %s);
                    COMMIT TRANSACTION;
                    """
                    cursor.execute(alloc_sql, [date or None, fg or None, line or None, batch_val])
                    row = cursor.fetchone()
                    new_id = row[0] if row else None
                    print(f"[INFO] Work order inserted with explicit-id: {new_id}")
                except Exception as e2:
                    # If that also fails, log and propagate the original error
                    print(f"[ERROR] explicit-id insert failed: {e2}")
                    raise

            # If we have a new_id, insert MIS and/or operator records
            if new_id:
                if mis_slip:
                    try:
                        # Use bracketed identifiers to avoid issues with column name casing/keywords
                        cursor.execute(
                            "INSERT INTO tblWorkOrderMisNos ([workordertableid], [misslipno]) VALUES (%s, %s)",
                            [new_id, mis_slip]
                        )
                        print(f"[INFO] MIS record inserted: workordertableid={new_id}, misslipno={mis_slip}")
                    except Exception as e3:
                        print(f"[ERROR] insert into tblWorkOrderMisNos failed: {e3}")
                        # Propagate so caller knows the secondary insert failed
                        raise
                else:
                    print(f"[INFO] No MIS slip provided (mis_slip={mis_slip})")
                
                # Insert operator/employee record if provided
                if emp_code or operation_id:
                    try:
                        # Insert with operatorid and numeric operationid
                        cursor.execute(
                            "INSERT INTO tblWorkOrderTransaction ([workordertableid], [operatorid], [operationid]) VALUES (%s, %s, %s)",
                            [new_id, emp_code or None, operation_id or None]
                        )
                        print(f"[INFO] Operator record inserted: workordertableid={new_id}, operatorid={emp_code}, operationid={operation_id}")
                    except Exception as e4:
                        print(f"[ERROR] insert into tblWorkOrderTransaction failed: {e4}")
                        raise
                else:
                    print(f"[INFO] No employee or operation provided")

        resp = {'success': True, 'id': new_id}
        if truncated:
            resp['warning'] = truncated
        return JsonResponse(resp, status=201)
    except Exception as e:
        print(f"[ERROR] save_work_order: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def check_mis_duplicate(request):
    """Check if a MIS slip number already exists in tblWorkOrderMisNos."""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)
    try:
        mis_slip = request.GET.get('misslipno') or None
        if not mis_slip:
            return JsonResponse({'exists': False})
        
        # Check if this MIS slip exists in tblWorkOrderMisNos
        conn = connections['default']
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM tblWorkOrderMisNos WHERE misslipno = %s",
                [mis_slip]
            )
            row = cursor.fetchone()
            count = row[0] if row else 0
            exists = count > 0
            print(f"[DEBUG] MIS slip '{mis_slip}' exists: {exists}")
            return JsonResponse({'exists': exists, 'count': count})
    except Exception as e:
        print(f"[ERROR] check_mis_duplicate: {e}")
        return JsonResponse({'error': str(e)}, status=500)