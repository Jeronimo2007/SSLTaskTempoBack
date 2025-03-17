from app.database.data import supabase
from app.models.ModelTasks import delete_task



def create_client(name: str, color: str):
    
    response = supabase.table('clients').insert({
        'name': name,
        'color': color
    }).execute()

    if response.data:
        return {"message": "Usuario creado exitosamente", "user": response.data}
    else:
        return {"error": "Error al crear el usuario", "details": response.error}
    


def read_clients():

    response = supabase.table('clients').select('*').execute()


    return response.data



def update_client(client_id: int, name: str = None, color: str = None):
    
    
    update_data = {}
    if name is not None:
        update_data['name'] = name


    if color is not None:
        update_data['color'] = color
    
    
    
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

