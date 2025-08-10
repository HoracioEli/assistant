# -*- coding: utf-8 -*-

import psycopg2
import os

# === Configuración de la Conexión a la Base de Datos ===
DB_NAME = os.environ.get("DB_NAME", "ASSISTANT")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "admin")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

def get_connection():
    """Establece y devuelve una nueva conexión a la base de datos PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# === Funciones para Tickets ===

def search_tickets(search_term):
    """Busca tickets en la base de datos."""
    conn = get_connection()
    if not conn:
        return []
    results = []
    try:
        with conn.cursor() as cur:
            query = "SELECT id, tkt, interno, externo FROM tickets WHERE tkt ILIKE %s ORDER BY tkt;"
            cur.execute(query, (f"%{search_term}%",))
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Error al buscar tickets: {e}")
    finally:
        if conn:
            conn.close()
    return results

def check_ticket_exists(tkt_number, exclude_id=None):
    """Verifica si un número de TKT ya existe."""
    conn = get_connection()
    if not conn:
        return False
    exists = False
    try:
        with conn.cursor() as cur:
            if exclude_id:
                query = "SELECT EXISTS(SELECT 1 FROM tickets WHERE tkt = %s AND id != %s);"
                cur.execute(query, (tkt_number, exclude_id))
            else:
                query = "SELECT EXISTS(SELECT 1 FROM tickets WHERE tkt = %s);"
                cur.execute(query, (tkt_number,))
            exists = cur.fetchone()[0]
    except psycopg2.Error as e:
        print(f"Error al verificar TKT: {e}")
    finally:
        if conn:
            conn.close()
    return exists

def insert_ticket(tkt, interno, externo):
    """Inserta un nuevo ticket."""
    conn = get_connection()
    if not conn:
        return None
    new_ticket = None
    try:
        with conn.cursor() as cur:
            query = "INSERT INTO tickets (tkt, interno, externo) VALUES (%s, %s, %s) RETURNING id, tkt, interno, externo;"
            cur.execute(query, (tkt, interno, externo))
            new_ticket_tuple = cur.fetchone()
            conn.commit()
            if new_ticket_tuple:
                columns = [desc[0] for desc in cur.description]
                new_ticket = dict(zip(columns, new_ticket_tuple))
    except psycopg2.Error as e:
        print(f"Error al insertar ticket: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
    return new_ticket

def update_ticket(ticket_id, tkt, interno, externo):
    """Actualiza un ticket existente."""
    conn = get_connection()
    if not conn:
        return None
    updated_ticket = None
    try:
        with conn.cursor() as cur:
            query = "UPDATE tickets SET tkt = %s, interno = %s, externo = %s WHERE id = %s RETURNING id, tkt, interno, externo;"
            cur.execute(query, (tkt, interno, externo, ticket_id))
            updated_ticket_tuple = cur.fetchone()
            conn.commit()
            if updated_ticket_tuple:
                columns = [desc[0] for desc in cur.description]
                updated_ticket = dict(zip(columns, updated_ticket_tuple))
    except psycopg2.Error as e:
        print(f"Error al actualizar ticket: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
    return updated_ticket

# === Funciones para Productores ===

def search_productores(search_term):
    """Busca productores por nombre o código, permitiendo búsqueda por múltiples palabras sin importar el orden en el nombre."""
    conn = get_connection()
    if not conn:
        return []
    results = []
    try:
        with conn.cursor() as cur:
            search_words = search_term.strip().split()
            if not search_words:
                return []

            # Construcción de la cláusula WHERE para el nombre
            nombre_where_clauses = []
            params = []
            for word in search_words:
                nombre_where_clauses.append("nombre ILIKE %s")
                params.append(f"%{word}%")
            
            nombre_where_clause_str = " AND ".join(nombre_where_clauses)

            # Búsqueda por código
            codigo_like_term = f"%{search_term}%"
            params.append(codigo_like_term)

            query = f"""
                SELECT id, nombre, codigo, interno, externo 
                FROM productores 
                WHERE ({nombre_where_clause_str}) OR codigo ILIKE %s 
                ORDER BY codigo;
            """
            
            cur.execute(query, tuple(params))
            
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Error al buscar productores: {e}")
    finally:
        if conn:
            conn.close()
    return results

def check_productor_exists(codigo, exclude_id=None):
    """Verifica si un código de productor ya existe."""
    conn = get_connection()
    if not conn:
        return False
    exists = False
    try:
        with conn.cursor() as cur:
            if exclude_id:
                query = "SELECT EXISTS(SELECT 1 FROM productores WHERE codigo = %s AND id != %s);"
                cur.execute(query, (codigo, exclude_id))
            else:
                query = "SELECT EXISTS(SELECT 1 FROM productores WHERE codigo = %s);"
                cur.execute(query, (codigo,))
            exists = cur.fetchone()[0]
    except psycopg2.Error as e:
        print(f"Error al verificar productor: {e}")
    finally:
        if conn:
            conn.close()
    return exists

def insert_productor(nombre, codigo, interno, externo):
    """Inserta un nuevo productor."""
    conn = get_connection()
    if not conn:
        return None
    new_productor = None
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO productores (nombre, codigo, interno, externo) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id, nombre, codigo, interno, externo;
            """
            cur.execute(query, (nombre, codigo, interno, externo))
            new_productor_tuple = cur.fetchone()
            conn.commit()
            if new_productor_tuple:
                columns = [desc[0] for desc in cur.description]
                new_productor = dict(zip(columns, new_productor_tuple))
    except psycopg2.Error as e:
        print(f"Error al insertar productor: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
    return new_productor

def update_productor(productor_id, nombre, codigo, interno, externo):
    """Actualiza un productor existente."""
    conn = get_connection()
    if not conn:
        return None
    updated_productor = None
    try:
        with conn.cursor() as cur:
            query = """
                UPDATE productores 
                SET nombre = %s, codigo = %s, interno = %s, externo = %s 
                WHERE id = %s 
                RETURNING id, nombre, codigo, interno, externo;
            """
            cur.execute(query, (nombre, codigo, interno, externo, productor_id))
            updated_productor_tuple = cur.fetchone()
            conn.commit()
            if updated_productor_tuple:
                columns = [desc[0] for desc in cur.description]
                updated_productor = dict(zip(columns, updated_productor_tuple))
    except psycopg2.Error as e:
        print(f"Error al actualizar productor: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
    return updated_productor

# === Funciones para Tema-Estado ===

def search_tema_estado(search_term):
    """Busca tema_estado en la base de datos, permitiendo búsqueda por múltiples palabras sin importar el orden."""
    conn = get_connection()
    if not conn:
        return []
    results = []
    try:
        with conn.cursor() as cur:
            search_words = search_term.strip().split()
            if not search_words:
                return []

            # Build the WHERE clause dynamically for each word
            where_clauses = []
            params = []
            for word in search_words:
                where_clauses.append("temaEstado ILIKE %s")
                params.append(f"%{word}%")

            where_clause_str = " AND ".join(where_clauses)
            query = f"SELECT id, temaEstado FROM temaEstado WHERE {where_clause_str} ORDER BY temaEstado;"
            
            cur.execute(query, tuple(params))
            
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Error al buscar tema_estado: {e}")
    finally:
        if conn:
            conn.close()
    return results

def check_tema_estado_exists(tema_estado, exclude_id=None):
    """Verifica si un tema_estado ya existe."""
    conn = get_connection()
    if not conn:
        return False
    exists = False
    try:
        with conn.cursor() as cur:
            if exclude_id:
                query = "SELECT EXISTS(SELECT 1 FROM temaEstado WHERE temaEstado = %s AND id != %s);"
                cur.execute(query, (tema_estado, exclude_id))
            else:
                query = "SELECT EXISTS(SELECT 1 FROM temaEstado WHERE temaEstado = %s);"
                cur.execute(query, (tema_estado,))
            exists = cur.fetchone()[0]
    except psycopg2.Error as e:
        print(f"Error al verificar tema_estado: {e}")
    finally:
        if conn:
            conn.close()
    return exists

def insert_tema_estado(tema_estado):
    """Inserta un nuevo tema_estado."""
    conn = get_connection()
    if not conn:
        return None
    new_tema_estado = None
    try:
        with conn.cursor() as cur:
            query = "INSERT INTO temaEstado (temaEstado) VALUES (%s) RETURNING id, temaEstado;"
            cur.execute(query, (tema_estado,))
            new_tema_estado_tuple = cur.fetchone()
            conn.commit()
            if new_tema_estado_tuple:
                columns = [desc[0] for desc in cur.description]
                new_tema_estado = dict(zip(columns, new_tema_estado_tuple))
    except psycopg2.Error as e:
        print(f"Error al insertar tema_estado: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
    return new_tema_estado

def update_tema_estado(tema_estado_id, tema_estado):
    """Actualiza un tema_estado existente."""
    conn = get_connection()
    if not conn:
        return None
    updated_tema_estado = None
    try:
        with conn.cursor() as cur:
            query = "UPDATE temaEstado SET temaEstado = %s WHERE id = %s RETURNING id, temaEstado;"
            cur.execute(query, (tema_estado, tema_estado_id))
            updated_tema_estado_tuple = cur.fetchone()
            conn.commit()
            if updated_tema_estado_tuple:
                columns = [desc[0] for desc in cur.description]
                updated_tema_estado = dict(zip(columns, updated_tema_estado_tuple))
    except psycopg2.Error as e:
        print(f"Error al actualizar tema_estado: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
    return updated_tema_estado

# === Funciones para Intervinientes ===

def search_intervinientes(search_term):
    """Busca intervinientes en la base de datos, permitiendo búsqueda por múltiples palabras sin importar el orden."""
    conn = get_connection()
    if not conn:
        return []
    results = []
    try:
        with conn.cursor() as cur:
            search_words = search_term.strip().split()
            if not search_words:
                return []

            # Build the WHERE clause dynamically for each word
            where_clauses = []
            params = []
            for word in search_words:
                where_clauses.append("interviniente ILIKE %s")
                params.append(f"%{word}%")

            where_clause_str = " AND ".join(where_clauses)
            query = f"SELECT id, interviniente, interno, externo FROM intervinientes WHERE {where_clause_str} ORDER BY interviniente;"
            
            cur.execute(query, tuple(params))
            
            columns = [desc[0] for desc in cur.description]
            results = [dict(zip(columns, row)) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Error al buscar intervinientes: {e}")
    finally:
        if conn:
            conn.close()
    return results

def check_interviniente_exists(interviniente, exclude_id=None):
    """Verifica si un interviniente ya existe."""
    conn = get_connection()
    if not conn:
        return False
    exists = False
    try:
        with conn.cursor() as cur:
            if exclude_id:
                query = "SELECT EXISTS(SELECT 1 FROM intervinientes WHERE interviniente = %s AND id != %s);"
                cur.execute(query, (interviniente, exclude_id))
            else:
                query = "SELECT EXISTS(SELECT 1 FROM intervinientes WHERE interviniente = %s);"
                cur.execute(query, (interviniente,))
            exists = cur.fetchone()[0]
    except psycopg2.Error as e:
        print(f"Error al verificar interviniente: {e}")
    finally:
        if conn:
            conn.close()
    return exists

def insert_interviniente(interviniente, interno, externo):
    """Inserta un nuevo interviniente."""
    conn = get_connection()
    if not conn:
        return None
    new_interviniente = None
    try:
        with conn.cursor() as cur:
            query = "INSERT INTO intervinientes (interviniente, interno, externo) VALUES (%s, %s, %s) RETURNING id, interviniente, interno, externo;"
            cur.execute(query, (interviniente, interno, externo))
            new_interviniente_tuple = cur.fetchone()
            conn.commit()
            if new_interviniente_tuple:
                columns = [desc[0] for desc in cur.description]
                new_interviniente = dict(zip(columns, new_interviniente_tuple))
    except psycopg2.Error as e:
        print(f"Error al insertar interviniente: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
    return new_interviniente

def update_interviniente(interviniente_id, interviniente, interno, externo):
    """Actualiza un interviniente existente."""
    conn = get_connection()
    if not conn:
        return None
    updated_interviniente = None
    try:
        with conn.cursor() as cur:
            query = "UPDATE intervinientes SET interviniente = %s, interno = %s, externo = %s WHERE id = %s RETURNING id, interviniente, interno, externo;"
            cur.execute(query, (interviniente, interno, externo, interviniente_id))
            updated_interviniente_tuple = cur.fetchone()
            conn.commit()
            if updated_interviniente_tuple:
                columns = [desc[0] for desc in cur.description]
                updated_interviniente = dict(zip(columns, updated_interviniente_tuple))
    except psycopg2.Error as e:
        print(f"Error al actualizar interviniente: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()
    return updated_interviniente

# === Creación de Tablas ===

def create_table_if_not_exists():
    """Crea las tablas en la base de datos si no existen."""
    conn = get_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id SERIAL PRIMARY KEY,
                    tkt VARCHAR(10) NOT NULL UNIQUE,
                    interno TEXT,
                    externo TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS intervinientes (
                    id SERIAL PRIMARY KEY,
                    interviniente VARCHAR(100) NOT NULL UNIQUE,
                    interno TEXT,
                    externo TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS productores (
                    id SERIAL PRIMARY KEY,
                    nombre VARCHAR(255) NOT NULL,
                    codigo VARCHAR(10) NOT NULL UNIQUE,
                    interno TEXT,
                    externo TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS temaEstado (
                    id SERIAL PRIMARY KEY,
                    temaEstado TEXT NOT NULL UNIQUE
                );
            """)
            conn.commit()
            print("Tablas verificadas/creadas exitosamente.")
    except psycopg2.Error as e:
        print(f"Error al crear las tablas: {e}")
    finally:
        if conn:
            conn.close()

# --- Bloque de Ejecución Principal ---
if __name__ == '__main__':
    create_table_if_not_exists()
