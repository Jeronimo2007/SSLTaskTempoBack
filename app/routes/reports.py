from collections import defaultdict
import os
import tempfile
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.database.data import supabase
from app.schemas.schemas import ClientReportRequest, ClientReportRequestTimeEntries, InvoiceByHoursRequest, InvoiceByPercentageRequest, InvoiceFilterRequest, ReportRequest, TaskReportRequest
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
        .select("id, client_id, title, assignment_date, billing_type ,due_date, area") \
        .eq("client_id", request.client_id) \
        .execute()
    task_dict = {task["id"]: task for task in task_response.data}

    # Preparar datos para el archivo Excel
    excel_data = []
    for task_id, task_info in task_dict.items():
        # Traducir el tipo de facturación a español
        billing_type = task_info['billing_type']
        billing_type_spanish = "Por Hora" if billing_type == "hourly" else "Por porcentaje"
        
        excel_data.append({
            "Cliente": client_name,
            "Asunto": task_info["title"],
            "Facturacion": billing_type_spanish,
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


@router.post("/download_task_report")
async def download_task_report(
    request: TaskReportRequest,
    user: dict = Depends(role_required(["socio", "senior", "consultor"]))
):
    """Download a detailed report of time entries for a specific task"""

    # Obtener la tarea
    start_date = request.start_date.strftime("%Y-%m-%d")
    end_date = request.end_date.strftime("%Y-%m-%d")
    
    task_response = supabase.table("tasks") \
        .select("id, title, billing_type, percentage_billed") \
        .eq("id", request.task_id) \
        .single() \
        .execute()

    if not task_response.data:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    task = task_response.data
    task_title = task["title"]
    billing_type = task.get("billing_type", "hourly")
    percentage_billed = task.get("percentage_billed", 0)

    # Obtener time entries relacionados
    entries_response = supabase.table("time_entries") \
        .select("description, start_time, duration, facturado") \
        .gte("start_time", start_date) \
        .lte("end_time", end_date) \
        .eq("task_id", request.task_id) \
        .execute()

    entries = entries_response.data
    if not entries:
        raise HTTPException(status_code=404, detail="No hay registros de tiempo para esta tarea")

    # Preparar datos para Excel
    excel_data = []
    for entry in entries:
        if billing_type == "percentage":
            if percentage_billed >= 100:
                estado = "si"
            elif percentage_billed > 0:
                estado = "parcialmente"
            else:
                estado = "no"
        else:
            estado = "si" if entry.get("facturado") else "no"

        excel_data.append({
            "Descripción": entry.get("description", ""),
            "Fecha": entry.get("start_time", "")[:10],
            "Duración (h)": round(entry.get("duration", 0), 2),
            "Facturado": estado
        })

    df = pd.DataFrame(excel_data)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Entradas", index=False, startrow=1)
        workbook = writer.book
        worksheet = writer.sheets["Entradas"]

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
            worksheet.set_column(col_num, col_num, 20)

        worksheet.merge_range('A1:D1', f"Desglose de Tiempos - {task_title}", workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        }))

        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iloc[row, col]
                worksheet.write(row + 2, col, value, cell_format)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=desglose_tarea_{task_title.replace(' ', '_')}.xlsx"}
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
def generate_invoice_by_hours(req: InvoiceByHoursRequest):
    try:
        today = datetime.now()

        if req.currency == "USD" and not req.exchange_rate:
            raise HTTPException(status_code=400, detail="Debe enviar exchange_rate si la moneda es USD")

        # Verificar tarea
        task_resp = supabase.table("tasks").select("id, title, area").eq("id", req.task_id).single().execute()
        if not task_resp or not task_resp.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        task = task_resp.data

        # Obtener cliente
        client_resp = supabase.table("clients").select("*").eq("id", req.client_id).single().execute()
        if not client_resp or not client_resp.data:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        client = client_resp.data

        # Obtener time entries no facturados para la tarea
        time_resp = supabase.table("time_entries")\
            .select("duration, user_id")\
            .eq("task_id", req.task_id)\
            .eq("facturado", "no")\
            .execute()

        if not time_resp or not time_resp.data:
            raise HTTPException(status_code=400, detail="No hay registros de tiempo sin facturar para esta tarea")
        entries = time_resp.data

        # Obtener usuarios relacionados
        user_ids = list(set([e["user_id"] for e in entries]))
        users_resp = supabase.table("users").select("id, username, cost, cost_per_hour_client").in_("id", user_ids).execute()
        if not users_resp or not users_resp.data:
            raise HTTPException(status_code=400, detail="No se encontraron usuarios relacionados")
        user_map = {u["id"]: u for u in users_resp.data}

        # Calcular totales y detalles para PDF
        subtotal = 0
        total_hours = 0
        tasks_details = []
        for e in entries:
            uid = e["user_id"]
            duration = round(e["duration"], 2)
            rate = user_map[uid]["cost_per_hour_client"]
            total = duration * rate

            if req.currency == "USD":
                rate = round(rate / req.exchange_rate, 2)
                total = round(total / req.exchange_rate, 2)

            subtotal += total
            total_hours += duration

            tasks_details.append({
                "username": user_map[uid]["username"],
                "area": task.get("area", "Sin área"),
                "description": task["title"],
                "duration": duration,
                "rate": rate,
                "total": total
            })

        subtotal = round(subtotal, 2)
        tax = round(subtotal * 0.19, 2) if req.include_tax else 0
        total = round(subtotal + tax, 2)

        # Registrar orden de servicio
        invoice_data = {
            "client_id": req.client_id,
            "start_date": str(today.replace(day=1).date()),
            "end_date": str(today.date()),
            "issued_at": today.isoformat(),
            "billing_type": "hourly",
            "total_hours": total_hours,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "currency": req.currency,
            "exchange_rate": req.exchange_rate,
            "include_tax": req.include_tax
        }
        supabase.table("invoices").insert(invoice_data).execute()

        # Actualizar total facturado en la tarea
        new_total = round(task.get("total_billed", 0) + total, 2)
        update_fields = {
            "total_billed": new_total
        }
        supabase.table("tasks").update(update_fields).eq("id", req.task_id).execute()

        # Marcar time_entries como facturados
        supabase.table("time_entries").update({"facturado": "si"}).eq("task_id", req.task_id).eq("facturado", "no").execute()

        # Renderizar HTML para el PDF
        template = env.get_template("invoice_template.html")
        html_out = template.render(
            client=client,
            date=today.strftime("%Y-%m-%d"),
            start_date=today.replace(day=1).date(),
            end_date=today.date(),
            tasks_details=tasks_details,
            subtotal=subtotal,
            tax=tax,
            total=total,
            currency_symbol="$" if req.currency == "COP" else "USD",
            billing_type="hourly"
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
            pdf_path = tmpfile.name
        HTML(string=html_out, base_url=os.getcwd()).write_pdf(pdf_path)

        return FileResponse(
            path=pdf_path,
            filename=f"orden_servicio_{client['name'].replace(' ', '_')}_{today.strftime('%Y-%m-%d')}.pdf",
            media_type="application/pdf"
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    

@router.post("/invoices/by-percentage")
def generate_invoice_by_percentage(req: InvoiceByPercentageRequest):
    try:
        if req.currency == "USD" and not req.exchange_rate:
            raise HTTPException(status_code=400, detail="Debe enviar exchange_rate si la moneda es USD")

        task_resp = supabase.table("tasks").select("*", count="exact").eq("id", req.task_id).single().execute()
        if not task_resp or not task_resp.data:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        task = task_resp.data

        total_case_value = task.get("total_value")
        if total_case_value is None:
            raise HTTPException(status_code=400, detail="La tarea no tiene un valor total definido")

        billed_raw = total_case_value * (req.percentage / 100)
        subtotal = round(billed_raw if req.currency == "COP" else billed_raw / req.exchange_rate, 2)
        tax = round(subtotal * 0.19, 2)
        total = round(subtotal + tax, 2)

        now = datetime.now()
        currency_symbol = "$" if req.currency == "COP" else "USD"

        # Registrar orden de servicio (invoice)
        invoice_data = {
            "client_id": req.client_id,
            "start_date": str(now.replace(day=1).date()),
            "end_date": str(now.date()),
            "issued_at": now.isoformat(),
            "billing_type": "percentage",
            "percentage": req.percentage,
            "subtotal": subtotal,
            "tax": tax,
            "total": total,
            "payment_type": req.payment_type,
            "total_case_value": total_case_value,
            "currency": req.currency,
            "exchange_rate": req.exchange_rate
        }
        supabase.table("invoices").insert(invoice_data).execute()

        # Actualizar progreso de facturación en la tarea
        new_percentage = round(task.get("percentage_billed", 0) + req.percentage, 2)
        new_total = round(task.get("total_billed", 0) + total, 2)

        update_fields = {
            "percentage_billed": new_percentage,
            "total_billed": new_total
        }

        if new_percentage >= 100:
            supabase.table("time_entries").update({"facturado": "si"}).eq("task_id", req.task_id).execute()
        elif new_percentage > 0:
            supabase.table("time_entries").update({"facturado": "parcialmente"}).eq("task_id", req.task_id).execute()

        supabase.table("tasks").update(update_fields).eq("id", req.task_id).execute()

        # Obtener los datos del cliente para el PDF
        client_resp = supabase.table("clients").select("name").eq("id", req.client_id).single().execute()
        client_name = client_resp.data["name"]

        # Obtener los detalles de la tarea
        task_details = {
            "username": "—",
            "area": task["area"],
            "description": task["title"],
            "duration": "—",
            "rate": "—",
            "total": total
        }

        # Preparar el HTML para el PDF
        template = env.get_template("invoice_template.html")
        html_out = template.render(
            client=client_resp.data,
            date=now.strftime("%Y-%m-%d"),
            start_date=now.replace(day=1).date(),
            end_date=now.date(),
            tasks_details=[task_details],
            subtotal=subtotal,
            tax=tax,
            total=total,
            currency_symbol=currency_symbol,
            billing_type="percentage",  # Solo porcentaje aquí
            total_facturado=new_total,
            restante=total_case_value - new_total
        )

        # Crear el PDF
        pdf_path = "/tmp/invoice.pdf"
        HTML(string=html_out).write_pdf(pdf_path)

        return FileResponse(pdf_path, media_type="application/pdf", filename=f"invoice_{client_name}_{now.strftime('%Y-%m-%d')}.pdf")

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

@router.get("/invoices/registry/excel")
async def get_invoice_registry_excel(
    start_date: str = Query(..., description="Fecha inicial en formato YYYY-MM-DD"),
    end_date: str = Query(..., description="Fecha final en formato YYYY-MM-DD")
):
    try:
        # Obtener facturas en el rango
        response = supabase.table("invoices")\
            .select("issued_at, billing_type, subtotal, currency")\
            .gte("issued_at", start_date)\
            .lte("issued_at", end_date)\
            .order("issued_at", desc=True)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="No hay facturas en el rango de fechas seleccionado")

        # Preparar datos para Excel
        excel_data = []
        for invoice in response.data:
            billing_type = "Por Hora" if invoice["billing_type"] == "hourly" else "Por porcentaje"
            currency = "COP" if invoice["currency"] == "COP" else "USD"
            
            excel_data.append({
                "Fecha de Emisión": invoice["issued_at"].split("T")[0],
                "Tipo de Facturación": billing_type,
                "Subtotal": invoice["subtotal"],
                "Moneda": currency
            })

        # Crear archivo Excel
        df = pd.DataFrame(excel_data)
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Registro de Facturas", index=False, startrow=1)
            workbook = writer.book
            worksheet = writer.sheets["Registro de Facturas"]

            # Formato para encabezados
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'vcenter',
                'align': 'center',
                'fg_color': '#D7E4BC',
                'border': 1
            })

            # Formato para celdas
            cell_format = workbook.add_format({
                'border': 1,
                'align': 'center',
                'valign': 'vcenter'
            })

            # Aplicar formatos y ajustar columnas
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(1, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 20)

            # Ajustar el ancho de las columnas específicas
            worksheet.set_column('A:A', 15)  # Fecha de Emisión
            worksheet.set_column('B:B', 20)  # Tipo de Facturación
            worksheet.set_column('C:C', 15)  # Subtotal
            worksheet.set_column('D:D', 10)  # Moneda

            # Título del reporte
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'align': 'center',
                'valign': 'vcenter'
            })
            worksheet.merge_range('A1:D1', 'Registro de Facturas', title_format)

            # Aplicar formato a las celdas de datos
            for row in range(len(df)):
                for col in range(len(df.columns)):
                    value = df.iloc[row, col]
                    worksheet.write(row + 2, col, value, cell_format)

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=registro_facturas_{start_date}_{end_date}.xlsx"}
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")




