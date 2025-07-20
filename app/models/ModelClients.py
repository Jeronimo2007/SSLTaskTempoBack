from fastapi import HTTPException
from app.database.data import supabase
from app.models.ModelTasks import delete_task
from app.schemas.schemas import clientCreate, clientUpdate


def create_client(data: clientCreate):
    try:
        name = data.name
        permanent = data.permanent
        lawyers = data.lawyers
        nit = data.nit
        phone = data.phone
        city = data.city
        address = data.address
        email = data.email
        international = data.international
        type = data.type

        print(f"Creating client with name: {name} and lawyers: {lawyers}")

        # Insertar cliente
        response = supabase.table('clients').insert({
            'name': name,
            'permanent': permanent,
            'nit': nit,
            'phone': phone,
            'city': city,
            'address': address,
            'email': email,
            'international': international,
            'type': type,

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


def read_clients(user_id: int = None):
    if user_id:
        # Get client IDs associated with the user
        client_user_response = supabase.table('client_user').select('client_id').eq('user_id', user_id).execute()
        
        if client_user_response.data:
            client_ids = [item['client_id'] for item in client_user_response.data]
            # Filter clients based on the retrieved client IDs and active status
            response = supabase.table('clients').select('*').in_('id', client_ids).eq('active', True).execute()
        else:
            return []
    else:
        # If user_id is not provided, return all active clients
        response = supabase.table('clients').select('*').eq('active', True).execute()

    return response.data



def update_client(data: clientUpdate):
    
    name = data.name
    lawyers = data.lawyers
    permanent = data.permanent
    
    nit = data.nit
    phone = data.phone
    city = data.city
    address = data.address
    email = data.email
    client_id = data.id
    international = data.international
    type = data.type
    
    update_data = {}

    if type is not None:
        update_data['type'] = type


    if name is not None:
        update_data['name'] = name

    if permanent is not None:
        update_data['permanent'] = permanent

    if international is not None:
        update_data['international'] = international

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
            if not response.data: # Check if response.data exists and is not empty
                # Consider raising HTTPException or logging the error more robustly
                return {
                    "error": "Error al agregar abogados al cliente",
                    "details": getattr(response, 'error', 'Unknown error') # Safely access error
                }

        if assignments_to_remove:
            # Construct the OR filter string
            or_filter_parts = []
            for assignment in assignments_to_remove:
                cid = assignment['client_id']
                uid = assignment['user_id']
                or_filter_parts.append(f"and(client_id.eq.{cid},user_id.eq.{uid})")
            or_filter_string = ",".join(or_filter_parts)

            response = supabase.table('client_user').delete().or_(or_filter_string).execute()
            # Check if response.data exists and is not empty (delete often returns the deleted rows)
            # Also check for errors explicitly if the library provides them
            if hasattr(response, 'error') and response.error:
                # Consider raising HTTPException or logging the error more robustly
                return {
                    "error": "Error al remover abogados del cliente",
                    "details": response.error
                }
            elif not response.data: # If no error but also no data, it might mean nothing matched or an issue occurred
                # Depending on expected behavior, this might not be an error,
                # but logging it could be useful.
                print(f"Warning: No rows returned after attempting to delete assignments: {or_filter_string}")
    
    
    
    # --- Rest of the function ---
    # The update logic for the 'clients' table starts here
    if not update_data and not lawyers: # Check if there's anything to do at all
         return {"message": "No changes detected for the client."} # Or specific error if needed

    if update_data: # Only update client table if there are changes
        try:
            response = supabase.table('clients')\
                .update(update_data)\
                .eq('id', client_id)\
                .execute()

            if hasattr(response, 'error') and response.error:
                 return {
                    "error": "Error al actualizar el cliente",
                    "details": response.error
                }
            elif response.data:
                # Combine results if both client data and lawyers were updated
                return {
                    "message": "Cliente actualizado exitosamente",
                    "client": response.data[0]
                }
            else: # No error, but no data returned from update
                # This might indicate the client_id didn't match any row
                return {
                    "error": "Error al actualizar el cliente: Cliente no encontrado o sin cambios.",
                    "details": "No data returned from update operation."
                }

        except Exception as e:
            # Log the exception details
            print(f"Exception during client update: {e}")
            raise HTTPException(status_code=500, detail=f"Error interno al actualizar el cliente: {str(e)}")
    elif lawyers is not None: # Only lawyer changes were made
        # If only lawyer assignments changed, return a success message for that
        # We need to fetch the updated client data to return it consistently
        client_response = supabase.table('clients').select('*').eq('id', client_id).maybe_single().execute()
        if client_response.data:
             return {
                "message": "Asignaciones de abogados actualizadas exitosamente.",
                "client": client_response.data
            }
        else:
            # This case should ideally not happen if client_id is valid, but handle defensively
            return {"error": "Cliente no encontrado después de actualizar abogados."}

    # This return should ideally not be reached if logic above is correct
    return {"error": "Estado inesperado al final de la función de actualización."}
    

def remove_client(id: int):
    try:
        # Set client's active status to False
        response_client = supabase.table('clients').update({'active': False}).eq('id', id).execute()

        if response_client:
           
            response_tasks = supabase.table('tasks').select('id').eq('client_id', id).execute()

            if response_tasks.data:
                for task in response_tasks.data:
                    
                    delete_task(task['id'])

            return {
                'message': 'Cliente desactivado y tareas eliminadas correctamente'
            }

    except Exception as e:
        return {
            'error': 'Error al desactivar el cliente',
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

