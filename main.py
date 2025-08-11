# -*- coding: utf-8 -*-

import flet as ft
import database
import re
from functools import partial

class CrudUI(ft.Container):
    """
    Una clase de UI genérica para manejar las operaciones CRUD para una entidad.
    """
    def __init__(self, page, model, entity_name, main_column, search_field_label, form_fields, column_definitions):
        super().__init__(expand=True)
        self.page = page
        self.model = model
        self.entity_name = entity_name
        self.main_column = main_column
        self.search_field_label = search_field_label
        self.form_fields = form_fields
        self.column_definitions = column_definitions
        
        self.selected_rows = {}

        # --- Componentes de la UI ---
        self.search_field = ft.TextField(
            label=self.search_field_label,
            width=350,
            capitalization=ft.TextCapitalization.CHARACTERS,
            on_submit=self.execute_search
        )
        
        self.main_datatable = ft.DataTable(columns=self.column_definitions, rows=[])
        
        self.results_datatable = ft.DataTable(
            columns=[ft.DataColumn(ft.Text("Seleccionar"))] + self.column_definitions[1:-1], # Excluir ID y Acciones
            rows=[]
        )
        
        self.results_view = ft.Column(
            visible=False,
            controls=[
                ft.Text(f"Resultados de Búsqueda: {self.entity_name}", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(content=self.results_datatable, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=5),
                ft.ElevatedButton("Cancelar", on_click=self.close_results_view)
            ]
        )

        self.main_data_view = ft.Column(
            controls=[
                ft.Text(f"{self.entity_name} Seleccionados", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(content=self.main_datatable, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=5)
            ]
        )

        self.content = ft.Column(
            controls=[
                ft.Row(
                    [
                        self.search_field,
                        ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, on_click=lambda e: self.open_form_dialog(), tooltip=f"Crear Nuevo {self.entity_name}")
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(),
                self.results_view,
                self.main_data_view
            ]
        )

    def execute_search(self, e):
        search_term = self.search_field.value.strip()
        if not search_term:
            return
        
        # Usar el método de búsqueda específico del modelo si existe
        found_results = []
        if hasattr(self.model, 'search') and callable(getattr(self.model, 'search')):
            # Check if the model's search method is the generic BaseModel.search
            # or a specialized one that doesn't need 'column'
            if self.model.search.__qualname__ == 'BaseModel.search':
                found_results = self.model.search(search_term, self.main_column)
            else:
                # Assume specialized search methods don't need 'column'
                found_results = self.model.search(search_term)
        else:
            # Fallback if no search method is found (shouldn't happen with BaseModel)
            self.show_snackbar("Error: No search method found for this entity.", is_error=True)
            return

        if not found_results:
            self.show_snackbar(f"No se encontraron resultados. Puede crear uno nuevo.")
            self.open_form_dialog(search_term_as_value=search_term)
        elif len(found_results) == 1:
            self.add_to_main_table(found_results[0])
        else:
            self.populate_results_table(found_results)
            self.results_view.visible = True
        
        self.search_field.value = ""
        self.update()

    def generic_search(self, search_term):
        return self.model.search(search_term, self.main_column)

    def populate_results_table(self, results):
        self.results_datatable.rows.clear()
        for res in results:
            cells = [ft.DataCell(ft.IconButton(icon=ft.Icons.ADD_TASK, tooltip="Seleccionar", on_click=partial(self.select_from_results, res)))]
            for col in self.column_definitions[1:-1]: # Iterar sobre las columnas de datos
                cells.append(ft.DataCell(ft.Text(res.get(col.label.value.replace('-', '').lower(), ''))))
            self.results_datatable.rows.append(ft.DataRow(cells=cells))

    def select_from_results(self, data, e):
        self.add_to_main_table(data)
        self.close_results_view(e)

    def close_results_view(self, e):
        self.results_view.visible = False
        self.update()

    def add_to_main_table(self, data):
        item_id = str(data['id'])
        if item_id in self.selected_rows:
            self.show_snackbar(f"'{data[self.main_column]}' ya está en la lista.")
            return

        new_row = ft.DataRow(
            cells=[ft.DataCell(ft.Text(str(data.get(col.label.value.replace('-', '').lower(), '')))) for col in self.column_definitions[:-1]] + # Datos
                  [ft.DataCell(ft.Row([ # Acciones
                      ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", on_click=partial(self.open_form_dialog, item_id=item_id)),
                      ft.IconButton(icon=ft.Icons.DELETE, tooltip="Eliminar", on_click=partial(self.remove_from_main_table, item_id)),
                  ]))]
        )
        self.selected_rows[item_id] = new_row
        self.main_datatable.rows.append(new_row)
        self.main_datatable.rows.sort(key=lambda r: r.cells[1].content.value) # Ordenar por la columna principal
        self.update()

    def remove_from_main_table(self, item_id, e):
        if item_id in self.selected_rows:
            row_to_remove = self.selected_rows.pop(item_id)
            self.main_datatable.rows.remove(row_to_remove)
            self.update()
            self.show_snackbar(f"{self.entity_name} eliminado de la vista.")

    def open_form_dialog(self, e=None, item_id=None, search_term_as_value=None):
        is_edit = item_id is not None
        title_text = f"Editar {self.entity_name}" if is_edit else f"Crear Nuevo {self.entity_name}"
        
        form_controls = []
        # initial_data = {} # Removed, as it's not used

        if is_edit:
            # En una app real, aquí se haría una consulta a la DB para obtener los datos frescos
            row = self.selected_rows[item_id]
            for i, field in enumerate(self.form_fields.values()):
                # Ensure the key for data.get() matches the database column name
                # This assumes the order of form_fields matches the order of columns in the row
                # and that the row.cells[0] is ID, row.cells[1] is the first data column
                field.value = row.cells[i+1].content.value
                # initial_data[field.label.lower()] = field.value # Removed, as it's not used
        else:
            for field in self.form_fields.values():
                field.value = ""
            if search_term_as_value:
                main_field = list(self.form_fields.values())[0]
                main_field.value = search_term_as_value.upper()


        for field in self.form_fields.values():
            form_controls.append(field)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(title_text),
            content=ft.Column(controls=form_controls, width=750), # Set width on the content Column
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.close_dialog(dialog)),
                ft.ElevatedButton("Guardar", on_click=lambda e: self.save_form(dialog, item_id)) # Re-added Guardar button
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            
        )
        
        # Add dialog to page.overlay and open it
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def save_form(self, dialog, item_id=None):
        data = {key: field.value.strip() for key, field in self.form_fields.items()}
        
        # --- VALIDACIÓN (Ejemplo simple) ---
        if not data[self.main_column]:
            self.show_snackbar(f"El campo {self.main_column.upper()} no puede estar vacío.", is_error=True)
            return
        
        if self.model.check_exists(self.main_column, data[self.main_column], exclude_id=item_id):
            self.show_snackbar(f"Este valor '{data[self.main_column]}' ya existe.", is_error=True)
            return

        # --- LÓGICA DE GUARDADO ---
        if item_id: # Editar
            result = self.model.update(item_id, data)
        else: # Crear
            result = self.model.insert(data)

        if result:
            if item_id:
                self.update_row_in_main_table(result)
            else:
                self.add_to_main_table(result)
            self.show_snackbar(f"{self.entity_name} guardado con éxito.")
            self.close_dialog(dialog)
        else:
            self.show_snackbar(f"Error al guardar {self.entity_name}.", is_error=True)

    def update_row_in_main_table(self, data):
        item_id = str(data['id'])
        if item_id in self.selected_rows:
            row_to_update = self.selected_rows[item_id]
            for i, col in enumerate(self.column_definitions[:-1]): # Excluir Acciones
                row_to_update.cells[i].content.value = str(data.get(col.label.value.replace('-', '').lower(), ''))
            self.main_datatable.rows.sort(key=lambda r: r.cells[1].content.value)
            self.update()

    def close_dialog(self, dialog):
        dialog.open = False
        self.page.update()

    def show_snackbar(self, message, is_error=False):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_500 if is_error else ft.Colors.GREEN_500,
        )
        self.page.snack_bar.open = True
        self.page.update()


def main(page: ft.Page):
    
    database.create_tables_if_not_exists()

    page.title = "Gestor de Datos"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_width = 950
    page.window_height = 700
    page.theme = ft.Theme(color_scheme_seed='indigo')

    # --- Definición de las Vistas CRUD ---

    tkt_view = CrudUI(
        page,
        model=database.Ticket(),
        entity_name="Ticket",
        main_column="tkt",
        search_field_label="Buscar por Nro de TKT",
        form_fields={
            "tkt": ft.TextField(label="TKT", capitalization=ft.TextCapitalization.CHARACTERS, width=200),
            "interno": ft.TextField(label="Interno", multiline=True, min_lines=3, max_lines=6, width=750),
            "externo": ft.TextField(label="Externo", multiline=True, min_lines=3, max_lines=6, width=750)
        },
        column_definitions=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("TKT")),
            ft.DataColumn(ft.Text("Interno")),
            ft.DataColumn(ft.Text("Externo")),
            ft.DataColumn(ft.Text("Acciones")),
        ]
    )

    interviniente_view = CrudUI(
        page,
        model=database.Interviniente(),
        entity_name="Interviniente",
        main_column="interviniente",
        search_field_label="Buscar por Nombre de Interviniente",
        form_fields={
            "interviniente": ft.TextField(label="Interviniente", capitalization=ft.TextCapitalization.CHARACTERS, width=750),
            "interno": ft.TextField(label="Interno", multiline=True, min_lines=3, max_lines=6, width=750),
            "externo": ft.TextField(label="Externo", multiline=True, min_lines=3, max_lines=6, width=750)
        },
        column_definitions=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Interviniente")),
            ft.DataColumn(ft.Text("Interno")),
            ft.DataColumn(ft.Text("Externo")),
            ft.DataColumn(ft.Text("Acciones")),
        ]
    )
    
    productor_view = CrudUI(
        page,
        model=database.Productor(),
        entity_name="Productor",
        main_column="codigo",
        search_field_label="Buscar por Código o Nombre",
        form_fields={
            "nombre": ft.TextField(label="Nombre", capitalization=ft.TextCapitalization.CHARACTERS, width=750),
            "codigo": ft.TextField(label="Código", width=200),
            "interno": ft.TextField(label="Interno", multiline=True, min_lines=3, max_lines=6, width=750),
            "externo": ft.TextField(label="Externo", multiline=True, min_lines=3, max_lines=6, width=750)
        },
        column_definitions=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre")),
                        ft.DataColumn(ft.Text("Codigo")), # Changed from "Código" to "Codigo",
            ft.DataColumn(ft.Text("Interno")),
            ft.DataColumn(ft.Text("Externo")),
            ft.DataColumn(ft.Text("Acciones")),
        ]
    )

    tema_estado_view = CrudUI(
        page,
        model=database.TemaEstado(),
        entity_name="Tema-Estado",
        main_column="temaestado",
        search_field_label="Buscar por Tema-Estado",
        form_fields={
            "temaestado": ft.TextField(label="Tema-Estado", capitalization=ft.TextCapitalization.CHARACTERS, width=750),
        },
        column_definitions=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Tema-Estado")),
            ft.DataColumn(ft.Text("Acciones")),
        ]
    )

    localidad_view = CrudUI(
        page,
        model=database.Localidad(),
        entity_name="Localidad",
        main_column="localidad",
        search_field_label="Buscar por Localidad",
        form_fields={
            "localidad": ft.TextField(label="Localidad", capitalization=ft.TextCapitalization.CHARACTERS, width=750),
        },
        column_definitions=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Localidad")),
            ft.DataColumn(ft.Text("Acciones")),
        ]
    )

    # --- Navegación por Pestañas ---
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Tickets", content=tkt_view),
            ft.Tab(text="Intervinientes", content=interviniente_view),
            ft.Tab(text="Productores", content=productor_view),
            ft.Tab(text="Tema-Estado", content=tema_estado_view),
            ft.Tab(text="Localidades", content=localidad_view),
        ],
        expand=1,
    )

    page.add(tabs)
    page.update()


if __name__ == "__main__":
    ft.app(target=main)