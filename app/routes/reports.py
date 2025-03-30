from collections import defaultdict
import os
import tempfile
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.database.data import supabase
from app.schemas.schemas import ClientReportRequest, ClientReportRequestTimeEntries, InvoiceByHoursRequest, InvoiceByPercentageRequest, InvoiceFilterRequest, ReportRequest
from app.services.utils import role_required
import pandas as pd
import io
from fastapi.responses import FileResponse, StreamingResponse
from jinja2 import Environment, FileSystemLoader  
from weasyprint import HTML


env = Environment(loader=FileSystemLoader("app/templates"))

router = APIRouter(prefix="/reports", tags=["Reportes"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def parse_datetime(date_str):
    """Parse a datetime string with or without milliseconds."""
    try:
        # Try parsing with milliseconds
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        # Fallback to parsing without milliseconds
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


@router.post("/hours_by_client/", response_model=List[dict])
async def get_hours_by_client(
    request: ReportRequest,
    user: dict = Depends(role_required(["socio", "senior", "consultor"]))
):
    """get the report of the client between two dates"""
    
    response = supabase.table("time_entries") \
        .select("task_id, duration, start_time, end_time") \
        .gte("start_time", request.start_date.isoformat()) \
        .lte("end_time", request.end_date.isoformat()) \
        .execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="No hay datos en el rango de fechas seleccionado")
   
    task_response = supabase.table("tasks").select("id, client_id, title").execute()
    task_dict = {task["id"]: {"client_id": task["client_id"], "title": task["title"]} for task in task_response.data}

    client_hours = {}
   
    for entry in response.data:
        task_id = entry["task_id"]
        task_info = task_dict.get(task_id, None)
        if task_info:
            client_id = task_info["client_id"]
            task_title = task_info["title"]
            
            if client_id not in client_hours:
                client_hours[client_id] = {"total_hours": 0, "tasks": {}}
            
            client_hours[client_id]["total_hours"] += entry["duration"]
            
            if task_id not in client_hours[client_id]["tasks"]:
                client_hours[client_id]["tasks"][task_id] = {"title": task_title, "hours": 0}
            client_hours[client_id]["tasks"][task_id]["hours"] += entry["duration"]

    client_response = supabase.table("clients").select("id, name").execute()
    client_dict = {client["id"]: client["name"] for client in client_response.data}

    report_data = []
    for client_id, data in client_hours.items():
        client_name = client_dict.get(client_id, "Desconocido")
        total_hours = round(data["total_hours"], 2) 
        
        tasks = [{"task_id": task_id, "Título": task_data["title"], "Horas": round(task_data["hours"], 2)} 
                 for task_id, task_data in data["tasks"].items()]
        
        report_data.append({
            "Cliente": client_name,
            "Total Horas": total_hours,
            "Tareas": tasks
        })

    return report_data

@router.post("/download_report")
async def download_report(
    request: ReportRequest,
    user: dict = Depends(role_required(["socio", "senior", "consultor"]))
):
    """Download the report of clients"""

    # Obtener datos del cliente
    report_data = await get_hours_by_client(request, user)

    # Obtener tareas con las nuevas columnas
    task_response = supabase.table("tasks").select("id, assignment_date, due_date, area").execute()
    task_dict = {task["id"]: task for task in task_response.data}

    # Preparar datos para el archivo Excel
    excel_data = []
    for entry in report_data:
        client_name = entry["Cliente"]
        total_hours = entry["Total Horas"]

        if not entry["Tareas"]:
            excel_data.append({
                "Cliente": client_name,
                "Total Horas": total_hours,
                "Tarea": "",
                "Horas por Tarea": "",
                "Fecha de Asignación": "",
                "Fecha de Vencimiento": "",
                "Área": ""
            })
            continue

        for idx, task in enumerate(entry["Tareas"]):
            # Buscar información de la tarea usando task_id
            task_id = task.get("task_id")
            task_info = task_dict.get(task_id)

            excel_data.append({
                "Cliente": client_name if idx == 0 else "",
                "Total Horas": total_hours if idx == 0 else "",
                "Tarea": task.get("Título", ""),
                "Horas por Tarea": task.get("Horas", ""),
                "Fecha de Asignación": task_info.get("assignment_date", "").split("T")[0] if task_info else "",
                "Fecha de Vencimiento": task_info.get("due_date", "").split("T")[0] if task_info else "",
                "Área": task_info.get("area", "") if task_info else ""
            })

    # Crear archivo Excel
    df = pd.DataFrame(excel_data)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Reporte", index=False, startrow=1)
        workbook = writer.book
        worksheet = writer.sheets["Reporte"]

        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'fg_color': '#D7E4BC',
            'border': 1
        })

        cell_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        # Ajustar el ancho de las columnas
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(1, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 20)

        worksheet.set_column('A:A', 30)  # Ajusta el ancho de la columna "Cliente"
        worksheet.set_column('C:C', 30)  # Ajusta el ancho de la columna "Tarea"
        worksheet.set_column('E:E', 25)  # Ajusta el ancho de la columna "Fecha de Asignación"
        worksheet.set_column('F:F', 25)  # Ajusta el ancho de la columna "Fecha de Vencimiento"
        worksheet.set_column('G:G', 20)  # Ajusta el ancho de la columna "Área"

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })
        worksheet.merge_range('A1:G1', 'Reporte de Horas por Cliente', title_format)

        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iloc[row, col]
                worksheet.write(row + 2, col, value, cell_format)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=reporte_horas_{request.start_date.date()}_{request.end_date.date()}.xlsx"}
    )

@router.post("/download_client_report")
async def download_client_report(
    request: ClientReportRequest,
    user: dict = Depends(role_required(["socio", "senior", "consultor"]))
):
    """Download the report of a specific client"""

    # Obtener datos del cliente
    client_response = supabase.table("clients") \
        .select("id, name") \
        .eq("id", request.client_id) \
        .execute()
    if not client_response.data:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    client_name = client_response.data[0]["name"]

    # Obtener tareas con las nuevas columnas
    task_response = supabase.table("tasks") \
        .select("id, client_id, title, assignment_date, due_date, area") \
        .eq("client_id", request.client_id) \
        .execute()
    task_dict = {task["id"]: task for task in task_response.data}

    # Preparar datos para el archivo Excel
    excel_data = []
    for task_id, task_info in task_dict.items():
        excel_data.append({
            "Cliente": client_name,
            "Tarea": task_info["title"],
            "Fecha de Asignación": task_info.get("assignment_date", "").split("T")[0],
            "Fecha de Vencimiento": task_info.get("due_date", "").split("T")[0],
            "Área": task_info.get("area", "")
        })

    # Crear archivo Excel
    df = pd.DataFrame(excel_data)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Reporte", index=False, startrow=1)
        workbook = writer.book
        worksheet = writer.sheets["Reporte"]

        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'fg_color': '#D7E4BC',
            'border': 1
        })

        cell_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(1, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)

        worksheet.set_column('A:A', 30)  
        worksheet.set_column('C:C', 30)  

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })
        worksheet.merge_range('A1:E1', f'Reporte de Horas para {client_name}', title_format)

        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iloc[row, col]
                worksheet.write(row + 2, col, value, cell_format)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=reporte_cliente_{client_name}_{request.start_date.date()}_{request.end_date.date()}.xlsx"}
    )


@router.post("/get_time_entries")
async def get_time_entries(data: ClientReportRequestTimeEntries, user: dict = Depends(role_required(["socio", "senior", "consultor"]))):
    """ get the time entries by client """

    try:
        start_date = data.start_date.strftime("%Y-%m-%d")
        end_date = data.end_date.strftime("%Y-%m-%d")

        response = (
            supabase.table("time_entries")
            .select("start_time, end_time, task_id, tasks(client_id, clients(name))")
            .gte("start_time", start_date)
            .lte("start_time", end_date)
            .execute()
        )

        if not response.data:
            return []

        time_entries_by_date = {}

        for entry in response.data:
            start_time = parse_datetime(entry["start_time"])
            end_time = parse_datetime(entry["end_time"])
            duration_hours = (end_time - start_time).total_seconds() / 3600

            date_key = start_time.strftime("%Y-%m-%d")
            client_name = entry["tasks"]["clients"]["name"]

            if date_key not in time_entries_by_date:
                time_entries_by_date[date_key] = {}

            if client_name not in time_entries_by_date[date_key]:
                time_entries_by_date[date_key][client_name] = 0

            time_entries_by_date[date_key][client_name] += duration_hours

        result = [
            {"date": date, "client": client, "hours": hours}
            for date, clients in time_entries_by_date.items()
            for client, hours in clients.items()
        ]

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los registros de tiempo: {str(e)}")
    
@router.post("/invoices/by-hours")
def generate_order_by_hours(req: InvoiceByHoursRequest):
    try:
        today = datetime.now()
        start_of_month = today.replace(day=1).date()
        end_of_month = today.date()

        if req.currency == "USD" and not req.exchange_rate:
            raise HTTPException(status_code=400, detail="Debe enviar exchange_rate si la moneda es USD")

        client_resp = supabase.table("clients").select("*").eq("id", req.client_id).single().execute()
        if not client_resp or not client_resp.data:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        client = client_resp.data

        tasks_resp = supabase.table("tasks").select("id, title, area").eq("client_id", req.client_id).execute()
        if not tasks_resp or not tasks_resp.data:
            raise HTTPException(status_code=400, detail="El cliente no tiene tareas")
        task_map = {t["id"]: {"title": t["title"], "area": t.get("area", "N/A")} for t in tasks_resp.data}

        time_resp = supabase.table("time_entries")\
            .select("id, duration, task_id, user_id, start_time, facturado")\
            .in_("task_id", list(task_map.keys()))\
            .eq("facturado", False)\
            .gte("start_time", str(start_of_month))\
            .lte("start_time", str(end_of_month))\
            .execute()

        if not time_resp or not time_resp.data:
            raise HTTPException(status_code=400, detail="No hay registros de tiempo no facturados este mes")
        entries = time_resp.data

        user_ids = list(set([e["user_id"] for e in entries]))
        users_resp = supabase.table("users").select("id, username, cost").in_("id", user_ids).execute()
        if not users_resp or not users_resp.data:
            raise HTTPException(status_code=400, detail="No se encontraron usuarios relacionados")
        user_map = {u["id"]: u for u in users_resp.data}

        tasks_details = []
        entry_ids_to_update = []

        for e in entries:
            uid = e["user_id"]
            tid = e["task_id"]
            duration = round(e["duration"], 2)
            rate_cop = user_map[uid]["cost"]
            rate = rate_cop
            total = rate_cop * duration
            if req.currency == "USD":
                rate = round(rate_cop / req.exchange_rate, 2)
                total = round(total / req.exchange_rate, 2)

            tasks_details.append({
                "username": user_map[uid]["username"],
                "description": task_map[tid]["title"],
                "area": task_map[tid]["area"],
                "duration": duration,
                "rate": rate,
                "total": total
            })
            entry_ids_to_update.append(e["id"])

        subtotal = round(sum([t["total"] for t in tasks_details]), 2)
        include_tax = getattr(req, "include_tax", True)  # por defecto True si no lo envían
        tax = round(subtotal * 0.19, 2) if include_tax else 0
        total = round(subtotal + tax, 2)
        currency_symbol = "$" if req.currency == "COP" else "USD"

        template = env.get_template("invoice_template.html")
        html_out = template.render(
            client=client,
            date=today.strftime("%Y-%m-%d"),
            start_date=start_of_month,
            end_date=end_of_month,
            tasks_details=tasks_details,
            subtotal=subtotal,
            tax=tax,
            total=total,
            currency_symbol=currency_symbol
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name

        HTML(string=html_out, base_url=os.getcwd()).write_pdf(pdf_path)

        supabase.table("invoices").insert({
            "client_id": req.client_id,
            "start_date": str(start_of_month),
            "end_date": str(end_of_month),
            "billing_type": "hourly",
            "total_hours": sum([t["duration"] for t in tasks_details]),
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "include_tax": include_tax
        }).execute()

        for entry_id in entry_ids_to_update:
            supabase.table("time_entries").update({"facturado": True}).eq("id", entry_id).execute()

        nombre_archivo = f"orden_servicio_{client['name'].replace(' ', '_')}_{today.strftime('%Y-%m-%d')}.pdf"

        return FileResponse(
            path=pdf_path,
            filename=nombre_archivo,
            media_type="application/pdf"
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    

@router.post("/invoices/by-percentage")
def generate_order_by_percentage(req: InvoiceByPercentageRequest):
    try:
        if req.currency == "USD" and not req.exchange_rate:
            raise HTTPException(status_code=400, detail="Debe enviar exchange_rate si la moneda es USD")

        client_resp = supabase.table("clients").select("*").eq("id", req.client_id).single().execute()
        if not client_resp or not client_resp.data:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        client = client_resp.data

        if not req.contract_id:
            raise HTTPException(status_code=400, detail="Debe enviar contract_id")

        contract_resp = supabase.table("contracts").select("*").eq("id", req.contract_id).eq("client_id", req.client_id).single().execute()
        if not contract_resp or not contract_resp.data:
            raise HTTPException(status_code=400, detail="Contrato inválido o no pertenece al cliente")
        contract = contract_resp.data

        # Calcular valores
        raw_subtotal = contract["total_value"] * (req.percentage / 100)
        subtotal = round(raw_subtotal, 2)
        include_tax = getattr(req, "include_tax", True)
        tax = round(subtotal * 0.19, 2) if include_tax else 0
        total = round(subtotal + tax, 2)
        currency_symbol = "$" if req.currency == "COP" else "USD"

        # Buscar facturas anteriores de ese contrato
        all_resp = supabase.table("invoices")\
            .select("total, percentage")\
            .eq("contract_id", req.contract_id)\
            .eq("billing_type", "percentage")\
            .execute()
        total_facturado = sum([r["total"] for r in all_resp.data]) if all_resp.data else 0
        restante = max(0, contract["total_value"] - total_facturado)
        porcentaje_acumulado = sum([r["percentage"] for r in all_resp.data]) if all_resp.data else 0

        formatted_total = format(contract["total_value"], ',.2f')
        description = f"{req.payment_type.capitalize()} del {req.percentage}% sobre un valor de {currency_symbol} {formatted_total}"

        tasks_details = [{
            "username": "—",
            "area": "—",
            "description": description,
            "duration": "—",
            "rate": "—",
            "total": subtotal
        }]

        today = datetime.now()
        start_of_month = today.replace(day=1).date()
        end_of_month = today.date()

        template = env.get_template("invoice_template.html")
        html_out = template.render(
            client=client,
            date=today.strftime("%Y-%m-%d"),
            start_date=start_of_month,
            end_date=end_of_month,
            tasks_details=tasks_details,
            subtotal=subtotal,
            tax=tax,
            total=total,
            currency_symbol=currency_symbol,
            billing_type="percentage",
            total_facturado=total_facturado,
            restante=restante
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name

        HTML(string=html_out, base_url=os.getcwd()).write_pdf(pdf_path)

        # Registrar orden en invoices
        supabase.table("invoices").insert({
            "client_id": req.client_id,
            "contract_id": req.contract_id,
            "start_date": str(start_of_month),
            "end_date": str(end_of_month),
            "billing_type": "percentage",
            "total_case_value": contract["total_value"],
            "percentage": req.percentage,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "payment_type": req.payment_type,
            "include_tax": include_tax
        }).execute()

        # 🟦 ACTUALIZAR CONTRATO
        nuevo_total_pagado = total_facturado + total
        nuevo_porcentaje_pagado = porcentaje_acumulado + req.percentage
        activo = nuevo_total_pagado < contract["total_value"]

        supabase.table("contracts").update({
            "total_pagado": nuevo_total_pagado,
            "porcentaje_pagado": nuevo_porcentaje_pagado,
            "active": activo
        }).eq("id", req.contract_id).execute()

        nombre_archivo = f"orden_servicio_{client['name'].replace(' ', '_')}_{today.strftime('%Y-%m-%d')}.pdf"

        return FileResponse(
            path=pdf_path,
            filename=nombre_archivo,
            media_type="application/pdf"
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    

@router.get("/invoices/registry")
def get_invoice_registry(
    start_date: str = Query(..., description="Fecha inicial en formato YYYY-MM-DD"),
    end_date: str = Query(..., description="Fecha final en formato YYYY-MM-DD")
):
    try:
        # Obtener facturas en el rango
        response = supabase.table("invoices")\
            .select("*, clients(name)")\
            .gte("issued_at", start_date)\
            .lte("issued_at", end_date)\
            .order("issued_at", desc=True)\
            .execute()

        raw_data = response.data or []

        # Transformar resultados
        facturas = []
        for f in raw_data:
            facturas.append({
                "id": f["id"],
                "issued_at": f["issued_at"],
                "billing_type": f["billing_type"],
                "subtotal": f["subtotal"],
                "tax": f["tax"],
                "total": f["total"],
                "percentage": f.get("percentage"),
                "payment_type": f.get("payment_type"),
                "total_hours": f.get("total_hours"),
                "total_case_value": f.get("total_case_value"),
                "client_name": f["clients"]["name"]
            })

        return facturas

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")





