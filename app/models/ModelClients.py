from fastapi import HTTPException
from app.database.data import supabase
from app.models.ModelTasks import delete_task
from app.schemas.schemas import clientCreate, clientUpdate


def create_client(data: clientCreate):
    try:
        name = data.name
        permanent = data.permanent
        limit = data.monthly_limit_hours
        lawyers = data.lawyers
        nit = data.nit
        phone = data.phone
        city = data.city
        address = data.address
        email = data.email

        print(f"Creating client with name: {name} and lawyers: {lawyers}")

        # Insertar cliente
        response = supabase.table('clients').insert({
            'name': name,
            'permanent': permanent,
            'monthly_limit_hours': limit,
            'nit': nit,
            'phone': phone,
            'city': city,
            'address': address,
            'email': email

        }).execute()

        print(f"Response from inserting client: {response}")

       
        if not response or not response.data:
            print("Client creation failed, response data is empty.")
            raise HTTPException(status_code=500, detail="Error creating client: No data returned.")

        client_id = response.data[0]['id']
        print(f"Client created with ID: {client_id}")

        # Crear asignaciones para los abogados
        assignments = [
            {"client_id": client_id, "user_id": lawyer_id}
            for lawyer_id in lawyers
        ]
        print(f"Assignments to be inserted: {assignments}")

        if assignments:
            response = supabase.table("client_user").insert(assignments).execute()
            print(f"Response from inserting assignments: {response}")

            
            if not response or not response.data:
                print("Error inserting assignments: No data returned.")
                raise HTTPException(status_code=500, detail="Error inserting assignments: No data returned.")

        print("Client and assignments created successfully.")
        return {"message": "Cliente creado exitosamente", "client_id": client_id}

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    


def read_client_user():

    try:
        response = supabase.table('client_user').select('*').execute()
        return response.data
    except Exception as e:
        return {
            'error': 'Error al obtener los abogados del cliente',
            'details': str(e)
        }


def read_clients():

    response = supabase.table('clients').select('*').execute()


    return response.data



def update_client(data: clientUpdate):
    
    name = data.name
    lawyers = data.lawyers
    permanent = data.permanent
    limit = data.monthly_limit_hours
    nit = data.nit
    phone = data.phone
    city = data.city
    address = data.address
    email = data.email
    client_id = data.id
    
    update_data = {}
    if name is not None:
        update_data['name'] = name

    if permanent is not None:
        update_data['permanent'] = permanent

    if limit is not None:
        update_data['monthly_limit_hours'] = limit

    if nit is not None:
        update_data['nit'] = nit

    if phone is not None:
        update_data['phone'] = phone

    if city is not None:
        update_data['city'] = city

    if address is not None:
        update_data['address'] = address

    if email is not None:    
        update_data['email'] = email

    if lawyers is not None:
        
        current_lawyers = supabase.table('client_user').select('user_id').eq('client_id', client_id).execute()
        current_lawyers = [lawyer['user_id'] for lawyer in current_lawyers.data]

       
        lawyers_to_add = [lawyer for lawyer in lawyers if lawyer not in current_lawyers]
        lawyers_to_remove = [lawyer for lawyer in current_lawyers if lawyer not in lawyers]

       
        assignments_to_add = [
            {"client_id": client_id, "user_id": lawyer_id}
            for lawyer_id in lawyers_to_add
        ]

        
        assignments_to_remove = [
            {"client_id": client_id, "user_id": lawyer_id}
            for lawyer_id in lawyers_to_remove
        ]

        if assignments_to_add:
            response = supabase.table('client_user').insert(assignments_to_add).execute()
            if not response.data:
                return {
                    "error": "Error al agregar abogados al cliente",
                    "details": response.error
                }

        if assignments_to_remove:
            response = supabase.table('client_user').delete().or_(assignments_to_remove).execute()
            if not response.data:
                return {
                    "error": "Error al remover abogados del cliente",
                    "details": response.error
                }
    
    
    
    if not update_data:
        return {"error": "No se proporcionaron datos para actualizar"}
    
    try:
        response = supabase.table('clients')\
            .update(update_data)\
            .eq('id', client_id)\
            .execute()
        
        if response.data:
            return {
                "message": "Cliente actualizado exitosamente",
                "client": response.data[0]
            }
        else:
            return {
                "error": "Error al actualizar el cliente",
                "details": response.error
            }
        
    except Exception as e:
        return {
            "error": "Error al actualizar el cliente",
            "details": str(e)
        }
    

def remove_client(id: int):
    try:
        
        response_client = supabase.table('clients').delete().eq('id', id).execute()

        if response_client:
           
            response_tasks = supabase.table('tasks').select('id').eq('client_id', id).execute()

            if response_tasks.data:
                for task in response_tasks.data:
                    
                    delete_task(task['id'])

            return {
                'message': 'Cliente y tareas eliminados correctamente'
            }

    except Exception as e:
        return {
            'error': 'Error al eliminar el cliente',
            'details': str(e)
        }



def get_relation_client_user(id: int):
    try:
        response = supabase.table('client_user').select('client_id').eq('user_id', id).execute()
        return response.data
    
    except Exception as e:
        return {
            'error': 'Error al obtener la relación entre clientes y abogados',
            'details': str(e)
        }
