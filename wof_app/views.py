from django.shortcuts import render
from django.http import JsonResponse
from .db_connection import get_connection
import pyodbc


def index(request):
    return render(request, "wof_app/index.html")


def get_tr_item_codes(request):
    conn = None
    try:
        conn = get_connection()
        if not conn:
            print("[ERROR] No database connection")
            return JsonResponse([], safe=False)

        cursor = conn.cursor()
        query = "SELECT ItemCode FROM tblFinishedGoodsMaster WHERE ItemCategory = 'TR'"
        print(f"[DEBUG] Executing query: {query}")
        cursor.execute(query)

        results = cursor.fetchall()
        item_codes = [row.ItemCode for row in results]

        print(f"[INFO] Found {len(item_codes)} TR items")
        return JsonResponse(item_codes, safe=False)

    except pyodbc.Error as e:
        print(f"[ERROR] Database query failed: {e}")
        return JsonResponse([], safe=False)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return JsonResponse([], safe=False)
    finally:
        if conn:
            conn.close()
            print("[INFO] Database connection closed")


def get_line_name(request):
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return JsonResponse([], safe=False)

        cursor = conn.cursor()
        query = "SELECT LineName FROM tblLineMaster WHERE Product = 'TR'"
        cursor.execute(query)

        results = cursor.fetchall()
        line_names = [row.LineName for row in results]

        return JsonResponse(line_names, safe=False)

    except Exception as e:
        print(f"[ERROR] {e}")
        return JsonResponse([], safe=False)
    finally:
        if conn:
            conn.close()


def get_operation_name(request):
    conn = None
    try:
        conn = get_connection()
        if not conn:
            return JsonResponse([], safe=False)

        cursor = conn.cursor()
        query = "SELECT OperationName FROM tblProductionOperationMaster"
        cursor.execute(query)

        results = cursor.fetchall()
        operation_names = [row.OperationName for row in results]

        return JsonResponse(operation_names, safe=False)

    except Exception as e:
        print(f"[ERROR] {e}")
        return JsonResponse([], safe=False)
    finally:
        if conn:
            conn.close()


def get_employee_name(request):
    conn = None
    try:
        conn = get_connection(database="sel2_personnel1516")
        if not conn:
            return JsonResponse([], safe=False)

        cursor = conn.cursor()
        query = "SELECT EmpName, EmpCode FROM tblEmployeeMaster"
        cursor.execute(query)

        results = cursor.fetchall()
        employees = [{"EmpName": row.EmpName, "EmpCode": row.EmpCode} for row in results]

        return JsonResponse(employees, safe=False)

    except Exception as e:
        print(f"[ERROR] {e}")
        return JsonResponse([], safe=False)
    finally:
        if conn:
            conn.close()
