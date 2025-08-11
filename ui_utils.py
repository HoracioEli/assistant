import flet as ft
from functools import partial

class CrudViewManager:
    def __init__(self, page, entity_name, db_module, main_table_rows_dict,
                 search_field_control, form_title_control, form_id_text_control,
                 form_save_button_control, form_edit_button_control, form_view_control,
                 results_datatable_control, results_view_control, main_datatable_control,
                 main_data_view_control, search_bar_control, search_field_container_control,
                 entity_specific_form_fields, validate_function,
                 add_to_main_table_func, update_row_in_main_table_func, delete_from_view_func,
                 populate_results_table_func, select_from_results_func, show_new_form_func,
                 show_edit_form_func):

        self.page = page
        self.entity_name = entity_name
        self.db_module = db_module
        self.main_table_rows_dict = main_table_rows_dict

        # UI Controls
        self.search_field_control = search_field_control
        self.form_title_control = form_title_control
        self.form_id_text_control = form_id_text_control
        self.form_save_button_control = form_save_button_control
        self.form_edit_button_control = form_edit_button_control
        self.form_view_control = form_view_control
        self.results_datatable_control = results_datatable_control
        self.results_view_control = results_view_control
        self.main_datatable_control = main_datatable_control
        self.main_data_view_control = main_data_view_control
        self.search_bar_control = search_bar_control
        self.search_field_container_control = search_field_container_control

        # Entity-specific functions/data
        self.entity_specific_form_fields = entity_specific_form_fields # Dictionary of form fields
        self.validate_function = validate_function
        self.add_to_main_table_func = add_to_main_table_func
        self.update_row_in_main_table_func = update_row_in_main_table_func
        self.delete_from_view_func = delete_from_view_func
        self.populate_results_table_func = populate_results_table_func
        self.select_from_results_func = select_from_results_func
        self.show_new_form_func = show_new_form_func
        self.show_edit_form_func = show_edit_form_func

    def show_view(self, search=False, form=False, results=False, main=False):
        self.search_bar_control.visible = not search
        self.search_field_container_control.visible = search
        self.form_view_control.visible = form
        self.results_view_control.visible = results
        self.main_data_view_control.visible = main
        self.page.update()

    def show_search_field(self, e):
        self.show_view(search=True)
        self.search_field_control.focus()

    def execute_search(self, e):
        search_term = self.search_field_control.value.strip()
        if not search_term:
            self.show_view()
            return

        # Dynamically call the search function from db_module
        search_db_func = getattr(self.db_module, f"search_{self.entity_name.lower()}s")
        found_results = search_db_func(search_term)

        if len(found_results) == 0:
            self.show_new_form_func(search_term)
        elif len(found_results) == 1:
            self.add_to_main_table_func(found_results[0])
            self.show_view(main=True)
        else:
            self.populate_results_table_func(found_results)
            self.show_view(results=True)
        self.search_field_control.value = ""
        self.page.update()

    def save_new_data(self, e):
        # Collect data from form fields dynamically
        data = {field_name: field_control.value.strip() for field_name, field_control in self.entity_specific_form_fields.items()}

        if not self.validate_function(**data): # Pass data to validation function
            return

        # Dynamically call the insert function from db_module
        insert_db_func = getattr(self.db_module, f"insert_{self.entity_name.lower()}")
        new_data = insert_db_func(**data)

        if new_data:
            self.add_to_main_table_func(new_data)
            self.show_view(main=True)
        self.page.update()

    def update_data(self, e):
        entity_id = int(self.form_id_text_control.value)
        data = {field_name: field_control.value.strip() for field_name, field_control in self.entity_specific_form_fields.items()}

        if not self.validate_function(exclude_id=entity_id, **data): # Pass data to validation function
            return

        # Dynamically call the update function from db_module
        update_db_func = getattr(self.db_module, f"update_{self.entity_name.lower()}")
        updated_data = update_db_func(entity_id=entity_id, **data)

        if updated_data:
            self.update_row_in_main_table_func(updated_data)
            self.show_view(main=True)
        self.page.update()

    def close_results_view(self, e):
        self.show_view()
        self.page.update()

    def show_new_form(self, search_term=""):
        self.form_title_control.value = f"Crear Nuevo {self.entity_name}"
        self.form_id_text_control.visible = False
        self.form_save_button_control.visible = True
        self.form_edit_button_control.visible = False

        # Clear and set values for entity-specific form fields
        for field_name, field_control in self.entity_specific_form_fields.items():
            if field_name == self.search_field_control.label.lower().replace(" ", "_"): # Assuming search field label matches a form field
                field_control.value = search_term.upper() if isinstance(field_control, ft.TextField) else search_term
            else:
                field_control.value = ""
            field_control.error_text = ""
            field_control.update()

        self.show_view(form=True)
        self.page.update()

    def show_edit_form(self, data, e):
        self.form_title_control.value = f"Editar {self.entity_name}"
        self.form_id_text_control.value = str(data['id'])
        self.form_id_text_control.visible = True
        self.form_save_button_control.visible = False
        self.form_edit_button_control.visible = True

        # Set values for entity-specific form fields
        for field_name, field_control in self.entity_specific_form_fields.items():
            field_control.value = data.get(field_name.replace("_form_", ""), "") # Adjust key if needed
            field_control.error_text = ""
            field_control.update()

        self.show_view(form=True)
        self.page.update()
