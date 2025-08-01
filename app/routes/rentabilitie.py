from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, HTTPException
from fastapi.security import OAuth2PasswordBearer
from ..database.data import supabase

router = APIRouter(prefix="/rentability", tags=["Rentabilidad"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

@router.get("/lawyers/profitability")
def get_lawyers_profitability():
    try:
        today = datetime.now()
        start_of_month = today.replace(day=1).date()
        end_of_month = (today.replace(day=1) + relativedelta(months=1, days=-1)).date()

        users_resp = supabase.table("users").select("id, username, salary, cost, cost_per_hour_client, desvinculado").execute()
        users = [u for u in users_resp.data if not u.get("desvinculado", False)]

        time_resp = supabase.table("time_entries")\
            .select("user_id, duration")\
            .gte("start_time", str(start_of_month))\
            .lte("start_time", str(end_of_month))\
            .execute()
        entries = time_resp.data

        hours_by_user = {}
        for e in entries:
            uid = e["user_id"]
            hours_by_user[uid] = hours_by_user.get(uid, 0) + e["duration"]

        results = []
        for u in users:
            uid = u["id"]
            worked_hours = round(hours_by_user.get(uid, 0), 2)
            salary = u.get("salary", 0) or 0
            cost = u.get("cost", 0) or 0
            rate_client = u.get("cost_per_hour_client", 0) or 0
            ingresos = round(worked_hours * rate_client, 2)
            rentabilidad = round(ingresos - salary, 2)

            results.append({
                "username": u["username"],
                "worked_hours": worked_hours,
                "salary": round(salary, 2),
                "ingresos": ingresos,
                "rentabilidad": rentabilidad
            })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/lawyers/cost-vs-hours")
def get_lawyer_cost_vs_hours():
    try:
        today = datetime.now()
        start_of_month = today.replace(day=1).date()
        end_of_month = (today.replace(day=1) + relativedelta(months=1, days=-1)).date()

        users_resp = supabase.table("users").select("id, username, salary, cost, cost_per_hour_client, desvinculado").execute()
        users = [u for u in users_resp.data if not u.get("desvinculado", False)]

        time_resp = supabase.table("time_entries")\
            .select("user_id, duration")\
            .gte("start_time", str(start_of_month))\
            .lte("start_time", str(end_of_month))\
            .execute()
        entries = time_resp.data

        hours_by_user = {}
        for e in entries:
            uid = e["user_id"]
            duration = e.get("duration", 0) or 0  # Handle None values
            hours_by_user[uid] = hours_by_user.get(uid, 0) + duration

        results = []
        for u in users:
            uid = u["id"]
            hours = round(hours_by_user.get(uid, 0), 2)
            salary = u.get("salary", 0) or 0
            cost = u.get("cost", 0) or 0
            rate_client = u.get("cost_per_hour_client", 0) or 0
            ingresos = round(hours * rate_client, 2)
            utilidad_hora = round(rate_client - cost, 2) if hours > 0 else 0

            results.append({
                "username": u["username"],
                "salary": round(salary, 2),
                "worked_hours": hours,
                "cost_per_hour_firma": round(cost, 2),
                "cost_per_hour_client": round(rate_client, 2),
                "ingresos_generados": ingresos,
                "utilidad_por_hora": utilidad_hora
            })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/lawyers/weekly-workload")
def get_lawyers_weekly_workload():
    try:
        today = datetime.now()
        # Weekly period
        start_of_week = today - timedelta(days=today.weekday())  # Lunes
        end_of_week = start_of_week + timedelta(days=6)          # Domingo
        # Monthly period
        start_of_month = today.replace(day=1).date()
        end_of_month = (today.replace(day=1) + relativedelta(months=1, days=-1)).date()

        users_resp = supabase.table("users").select("id, username, weekly_hours, desvinculado").execute()
        users = [u for u in users_resp.data if not u.get("desvinculado", False)]

        # Get weekly entries
        weekly_time_resp = supabase.table("time_entries")\
            .select("user_id, duration, start_time")\
            .gte("start_time", str(start_of_week.date()))\
            .lte("start_time", str(end_of_week.date()))\
            .execute()
        weekly_entries = weekly_time_resp.data

        # Get monthly entries
        monthly_time_resp = supabase.table("time_entries")\
            .select("user_id, duration, start_time")\
            .gte("start_time", str(start_of_month))\
            .lte("start_time", str(end_of_month))\
            .execute()
        monthly_entries = monthly_time_resp.data

        # Calculate weekly hours
        weekly_hours_by_user = {}
        for e in weekly_entries:
            uid = e["user_id"]
            duration = e.get("duration", 0) or 0  # Handle None values
            weekly_hours_by_user[uid] = weekly_hours_by_user.get(uid, 0) + duration

        # Calculate monthly hours
        monthly_hours_by_user = {}
        for e in monthly_entries:
            uid = e["user_id"]
            duration = e.get("duration", 0) or 0  # Handle None values
            monthly_hours_by_user[uid] = monthly_hours_by_user.get(uid, 0) + duration

        results = []
        for u in users:
            uid = u["id"]
            weekly_worked = round(weekly_hours_by_user.get(uid, 0), 2)
            monthly_worked = round(monthly_hours_by_user.get(uid, 0), 2)
            weekly_hours = u.get("weekly_hours", 0) or 0
            monthly_expected = round(weekly_hours * 4.33, 2)
            
            results.append({
                "username": u["username"],
                "worked_hours_this_week": weekly_worked,
                "weekly_hours_expected": round(weekly_hours, 2),
                "worked_hours_this_month": monthly_worked,
                "monthly_hours_expected": monthly_expected
            })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/clients/contributions")
def get_client_contributions():
    try:
        today = datetime.now()
        # Get current week
        start_of_week = today - timedelta(days=today.weekday())  # Lunes
        end_of_week = start_of_week + timedelta(days=6)          # Domingo
        
        # Obtener tareas y sus clientes
        tasks_resp = supabase.table("tasks").select("id, client_id").execute()
        
        task_map = {}
        client_task_ids = {}
        for t in tasks_resp.data:
            tid = t["id"]
            cid = t["client_id"]
            task_map[tid] = cid
            client_task_ids.setdefault(cid, []).append(tid)

        # Obtener clientes
        clients_resp = supabase.table("clients").select("id, name").execute()
        clients = {c["id"]: c["name"] for c in clients_resp.data}

        # Obtener usuarios
        users_resp = supabase.table("users").select("id, username, desvinculado").execute()
        users = {u["id"]: u["username"] for u in users_resp.data if not u.get("desvinculado", False)}

        # Try to get time entries for the current week
        entries_resp = supabase.table("time_entries")\
            .select("user_id, duration, task_id, start_time")\
            .gte("start_time", str(start_of_week.date()))\
            .lte("start_time", str(end_of_week.date()))\
            .execute()
        
        entries = entries_resp.data

        # If no entries found for current week, try the previous week
        if not entries:
            start_of_week = start_of_week - timedelta(days=7)
            end_of_week = end_of_week - timedelta(days=7)
            
            entries_resp = supabase.table("time_entries")\
                .select("user_id, duration, task_id, start_time")\
                .gte("start_time", str(start_of_week.date()))\
                .lte("start_time", str(end_of_week.date()))\
                .execute()
            
            entries = entries_resp.data

        # If still no entries, try the last 30 days
        if not entries:
            start_date = today - timedelta(days=30)
            
            entries_resp = supabase.table("time_entries")\
                .select("user_id, duration, task_id, start_time")\
                .gte("start_time", str(start_date.date()))\
                .lte("start_time", str(today.date()))\
                .execute()
            
            entries = entries_resp.data

        # Agrupar por cliente y abogado
        client_user_hours = {}
        total_client_hours = {}
        for e in entries:
            tid = e["task_id"]
            uid = e["user_id"]
            dur = e.get("duration", 0) or 0  # Handle None values
            cid = task_map.get(tid)
            if cid and uid in users:  # Only include active users
                total_client_hours[cid] = total_client_hours.get(cid, 0) + dur
                client_user_hours.setdefault(cid, {})
                client_user_hours[cid][uid] = client_user_hours[cid].get(uid, 0) + dur

        # Construir resultados
        results = []
        for cid, user_hours in client_user_hours.items():
            total = total_client_hours[cid]
            contributions = []
            for uid, hours in user_hours.items():
                percentage = round((hours / total) * 100, 2) if total > 0 else 0
                contributions.append({
                    "user_id": uid,
                    "username": users.get(uid, "—"),
                    "worked_hours": round(hours, 2),
                    "porcentaje_contribucion": percentage
                })

            results.append({
                "client_id": cid,
                "client_name": clients.get(cid, "Desconocido"),
                "total_hours": round(total, 2),
                "contributions": contributions
            })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/office/summary")
def get_office_summary():
    try:
        today = datetime.now()
        start_of_month = today.replace(day=1).date()
        end_of_month = (today.replace(day=1) + relativedelta(months=1, days=-1)).date()

        # Obtener usuarios
        users_resp = supabase.table("users").select("id, username, salary, cost_per_hour_client, desvinculado").execute()
        if not users_resp.data:
            raise HTTPException(status_code=404, detail="No users found in the database")
        users = {u["id"]: u for u in users_resp.data if not u.get("desvinculado", False)}

        # Obtener time entries del mes actual
        time_resp = supabase.table("time_entries")\
            .select("user_id, duration")\
            .gte("start_time", str(start_of_month))\
            .lte("start_time", str(end_of_month))\
            .execute()
        if not time_resp.data:
            # If no time entries, return zeros but don't raise an error
            return {
                "total_salarios": 0,
                "total_horas_trabajadas": 0,
                "total_ingresos": 0,
                "rentabilidad_oficina": 0
            }
        entries = time_resp.data

        total_salarios = 0
        total_horas = 0
        total_ingresos = 0

        for u in users.values():
            salary = u.get("salary", 0) or 0
            total_salarios += salary

        for e in entries:
            uid = e["user_id"]
            if uid in users:  # Only include active users
                dur = e.get("duration", 0) or 0  # Handle None values
                rate = users.get(uid, {}).get("cost_per_hour_client", 0) or 0
                total_horas += dur
                total_ingresos += dur * rate

        rentabilidad = round(total_ingresos - total_salarios, 2)

        return {
            "total_salarios": round(total_salarios, 2),
            "total_horas_trabajadas": round(total_horas, 2),
            "total_ingresos": round(total_ingresos, 2),
            "rentabilidad_oficina": rentabilidad
        }

    except Exception as e:
        # Log the full error details
        print(f"Error in get_office_summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating office summary: {str(e)}"
        )
