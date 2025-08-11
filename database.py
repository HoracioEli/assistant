# -*- coding: utf-8 -*-

import psycopg2
import os
import logging

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        logging.error(f"Error al conectar a la base de datos: {e}")
        return None

class BaseModel:
    """Clase base para la interacción con la base de datos."""
    def __init__(self, table_name):
        self.table_name = table_name
        self.conn = get_connection()

    def _execute_query(self, query, params=None, fetch=None):
        """Ejecuta una consulta y maneja la conexión y el cursor."""
        if not self.conn:
            logging.error("No hay conexión a la base de datos.")
            return None
        
        results = None
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                if fetch == 'one':
                    results = cur.fetchone()
                elif fetch == 'all':
                    columns = [desc[0] for desc in cur.description]
                    results = [dict(zip(columns, row)) for row in cur.fetchall()]
                
                if "INSERT" in query or "UPDATE" in query or "DELETE" in query:
                    self.conn.commit()
                    if fetch == 'one' and results: # For RETURNING clauses
                         columns = [desc[0] for desc in cur.description]
                         results = dict(zip(columns, results))

        except psycopg2.Error as e:
            logging.error(f"Error en la consulta a la tabla {self.table_name}: {e}")
            if self.conn:
                self.conn.rollback()
        return results

    def close_connection(self):
        if self.conn:
            self.conn.close()
            
    def search(self, search_term, column):
        """Busca un término en una columna específica."""
        query = f"SELECT * FROM {self.table_name} WHERE {column} ILIKE %s ORDER BY {column};"
        return self._execute_query(query, (f"%{search_term}%",), fetch='all')

    def check_exists(self, column, value, exclude_id=None):
        """Verifica si un valor ya existe en una columna."""
        if exclude_id:
            query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name} WHERE {column} = %s AND id != %s);"
            params = (value, exclude_id)
        else:
            query = f"SELECT EXISTS(SELECT 1 FROM {self.table_name} WHERE {column} = %s);"
            params = (value,)
        
        result = self._execute_query(query, params, fetch='one')
        return result[0] if result else False

    def insert(self, data):
        """Inserta un nuevo registro."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders}) RETURNING *;"
        return self._execute_query(query, tuple(data.values()), fetch='one')

    def update(self, record_id, data):
        """Actualiza un registro existente."""
        set_clause = ", ".join([f"{key} = %s" for key in data.keys()])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = %s RETURNING *;"
        params = tuple(data.values()) + (record_id,)
        return self._execute_query(query, params, fetch='one')


class Ticket(BaseModel):
    def __init__(self):
        super().__init__('tickets')

class Interviniente(BaseModel):
    def __init__(self):
        super().__init__('intervinientes')

class Productor(BaseModel):
    def __init__(self):
        super().__init__('productores')
    
    def search(self, search_term):
        """Busca productores por nombre o código con coincidencia parcial."""
        if not search_term:
            return []

        # Simplified search: look for search_term in both nombre and codigo
        # This will match "MARTIN" with "MARTIN" and "MARTINEZ"
        query = f"""
            SELECT id, nombre, codigo, interno, externo 
            FROM {self.table_name} 
            WHERE nombre ILIKE %s OR codigo ILIKE %s 
            ORDER BY codigo;
        """
        params = (f"%{search_term}%", f"%{search_term}%")
        return self._execute_query(query, params, fetch='all')

class TemaEstado(BaseModel):
    def __init__(self):
        super().__init__('temaEstado')

class Localidad(BaseModel):
    def __init__(self):
        super().__init__('localidades')

def create_tables_if_not_exists():
    """Crea todas las tablas en la base de datos si no existen."""
    conn = get_connection()
    if not conn:
        return
    
    table_definitions = [
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY,
            tkt VARCHAR(10) NOT NULL UNIQUE,
            interno TEXT,
            externo TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS intervinientes (
            id SERIAL PRIMARY KEY,
            interviniente VARCHAR(100) NOT NULL UNIQUE,
            interno TEXT,
            externo TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS productores (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            codigo VARCHAR(10) NOT NULL UNIQUE,
            interno TEXT,
            externo TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS temaEstado (
            id SERIAL PRIMARY KEY,
            temaEstado TEXT NOT NULL UNIQUE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS localidades (
            id SERIAL PRIMARY KEY,
            localidad VARCHAR(255) NOT NULL UNIQUE
        );
        """
    ]
    
    try:
        with conn.cursor() as cur:
            for table in table_definitions:
                cur.execute(table)
        conn.commit()
        logging.info("Tablas verificadas/creadas exitosamente.")
    except psycopg2.Error as e:
        logging.error(f"Error al crear las tablas: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_tables_if_not_exists()