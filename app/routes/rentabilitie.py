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

        users_resp = supabase.table("users").select("id, username, salary, cost, cost_per_hour_client").execute()
        users = users_resp.data

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

        users_resp = supabase.table("users").select("id, username, salary, cost, cost_per_hour_client").execute()
        users = users_resp.data

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
    """
    Devuelve:
    - username
    - horas trabajadas en la semana actual
    - horas contratadas semanalmente (weekly_hours)
    """
    try:
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Lunes
        end_of_week = start_of_week + timedelta(days=6)          # Domingo

        users_resp = supabase.table("users").select("id, username, weekly_hours").execute()
        users = users_resp.data

        time_resp = supabase.table("time_entries")\
            .select("user_id, duration, start_time")\
            .gte("start_time", str(start_of_week.date()))\
            .lte("start_time", str(end_of_week.date()))\
            .execute()
        entries = time_resp.data

        hours_by_user = {}
        for e in entries:
            uid = e["user_id"]
            hours_by_user[uid] = hours_by_user.get(uid, 0) + e["duration"]

        results = []
        for u in users:
            uid = u["id"]
            worked = round(hours_by_user.get(uid, 0), 2)
            results.append({
                "username": u["username"],
                "worked_hours_this_week": worked,
                "weekly_hours_expected": round(u.get("weekly_hours", 0) or 0, 2)
            })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    


@router.get("/clients/contributions")
def get_client_contributions():
    """
    Devuelve:
    - client_id
    - client_name
    - total_hours (de todas sus tareas)
    - contributions: [
        {
          user_id,
          username,
          worked_hours,
          porcentaje_contribucion
        }
      ]
    """
    try:
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Lunes
        end_of_week = start_of_week + timedelta(days=6)        
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
        users_resp = supabase.table("users").select("id, username").execute()
        users = {u["id"]: u["username"] for u in users_resp.data}

        # Obtener time_entries
        entries_resp = supabase.table("time_entries")\
            .select("user_id, duration, task_id")\
            .gte("start_time", str(start_of_week.date()))\
            .lte("start_time", str(end_of_week.date()))\
            .execute()
        entries = entries_resp.data

        # Agrupar por cliente y abogado
        client_user_hours = {}
        total_client_hours = {}
        for e in entries:
            tid = e["task_id"]
            uid = e["user_id"]
            dur = e["duration"]
            cid = task_map.get(tid)
            if cid:
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
    """
    Devuelve:
    - total_salarios
    - total_ingresos (usando cost_per_hour_client)
    - total_horas_trabajadas
    - rentabilidad_oficina = ingresos - salarios
    """
    try:
        today = datetime.now()
        start_of_month = today.replace(day=1).date()
        end_of_month = (today.replace(day=1) + relativedelta(months=1, days=-1)).date()

        # Obtener usuarios
        users_resp = supabase.table("users").select("id, username, salary, cost_per_hour_client").execute()
        users = {u["id"]: u for u in users_resp.data}

        # Obtener time entries del mes actual
        time_resp = supabase.table("time_entries")\
            .select("user_id, duration")\
            .gte("start_time", str(start_of_month))\
            .lte("start_time", str(end_of_month))\
            .execute()
        entries = time_resp.data

        total_salarios = 0
        total_horas = 0
        total_ingresos = 0

        for u in users.values():
            total_salarios += u.get("salary", 0) or 0

        for e in entries:
            uid = e["user_id"]
            dur = e["duration"]
            rate = users.get(uid, {}).get("cost_per_hour_client", 0)
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
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
