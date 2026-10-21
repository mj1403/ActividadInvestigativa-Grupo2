from database.conexion import inicializar_db
from interfaz.app_metas import iniciar
 
 
def main():
    inicializar_db()
    iniciar()
 
 
if __name__ == "__main__":
    main()