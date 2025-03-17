from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List
from datetime import datetime
from app.database.data import supabase
from app.schemas.schemas import ClientReportRequest, ClientReportRequestTimeEntries, ReportRequest
from app.services.utils import role_required
import pandas as pd
import io
from fastapi.responses import StreamingResponse

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
            
            if task_title not in client_hours[client_id]["tasks"]:
                client_hours[client_id]["tasks"][task_title] = 0
            client_hours[client_id]["tasks"][task_title] += entry["duration"]

   
    for task in task_response.data:
        client_id = task["client_id"]
        task_title = task["title"]
       
        if client_id in client_hours:
            if task_title not in client_hours[client_id]["tasks"]:
                client_hours[client_id]["tasks"][task_title] = 0

   
    client_response = supabase.table("clients").select("id, name").execute()
    client_dict = {client["id"]: client["name"] for client in client_response.data}

    report_data = []
    for client_id, data in client_hours.items():
        client_name = client_dict.get(client_id, "Desconocido")
        total_hours = round(data["total_hours"], 2) 
        
        tasks = [{"Título": title, "Horas": round(hours, 2)} 
                 for title, hours in data["tasks"].items()]
        
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
    """donwload the report of clients"""
    
    report_data = await get_hours_by_client(request, user)
    
   
    excel_data = []
    for entry in report_data:
        client_name = entry["Cliente"]
        total_hours = entry["Total Horas"]
        
        if not entry["Tareas"]:
            excel_data.append({
                "Cliente": client_name,
                "Total Horas": total_hours,
                "Tarea": "",
                "Horas por Tarea": ""
            })
            continue
        
        for idx, task in enumerate(entry["Tareas"]):
            excel_data.append({
                "Cliente": client_name if idx == 0 else "",
                "Total Horas": total_hours if idx == 0 else "",
                "Tarea": task.get("Título", ""),
                "Horas por Tarea": task.get("Horas", "")
            })

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
        worksheet.merge_range('A1:D1', 'Reporte de Horas por Cliente', title_format)

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
    """ Donwload the report of a sepecific client """

   
    client_response = supabase.table("clients") \
        .select("id, name") \
        .eq("id", request.client_id) \
        .execute()
    if not client_response.data:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    client_name = client_response.data[0]["name"]

   
    time_response = supabase.table("time_entries") \
        .select("task_id, duration, start_time, end_time") \
        .gte("start_time", request.start_date.isoformat()) \
        .lte("end_time", request.end_date.isoformat()) \
        .execute()

    if not time_response.data:
        raise HTTPException(status_code=404, detail="No hay datos en el rango de fechas seleccionado")

   
    task_response = supabase.table("tasks") \
        .select("id, client_id, title") \
        .eq("client_id", request.client_id) \
        .execute()
    if not task_response.data:
        raise HTTPException(status_code=404, detail="No hay tareas registradas para este cliente")
    task_dict = {task["id"]: {"client_id": task["client_id"], "title": task["title"]} for task in task_response.data}

   
    client_hours_data = {"total_hours": 0, "tasks": {}}
    for entry in time_response.data:
        task_id = entry["task_id"]
        if task_id not in task_dict:
            continue
        task_title = task_dict[task_id]["title"]
        client_hours_data["total_hours"] += entry["duration"]
        if task_title not in client_hours_data["tasks"]:
            client_hours_data["tasks"][task_title] = 0
        client_hours_data["tasks"][task_title] += entry["duration"]

    
    for task in task_response.data:
        task_title = task["title"]
        if task_title not in client_hours_data["tasks"]:
            client_hours_data["tasks"][task_title] = 0

    total_hours = round(client_hours_data["total_hours"], 2)
    tasks_list = [{"Título": title, "Horas": round(hours, 2)} for title, hours in client_hours_data["tasks"].items()]

   
    report = [{
        "Cliente": client_name,
        "Total Horas": total_hours,
        "Tareas": tasks_list
    }]

    
    excel_data = []
    for entry in report:
        cname = entry["Cliente"]
        total = entry["Total Horas"]
        if not entry["Tareas"]:
            excel_data.append({
                "Cliente": cname,
                "Total Horas": total,
                "Tarea": "",
                "Horas por Tarea": ""
            })
            continue

        for idx, task in enumerate(entry["Tareas"]):
            excel_data.append({
                "Cliente": cname if idx == 0 else "",
                "Total Horas": total if idx == 0 else "",
                "Tarea": task.get("Título", ""),
                "Horas por Tarea": task.get("Horas", "")
            })

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
        worksheet.merge_range('A1:D1', f'Reporte de Horas para {client_name}', title_format)

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