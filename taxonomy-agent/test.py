import re
import readline

class EletrobrasGCPValidator:
    """
    Validates GCP resource names based on the Eletrobras taxonomy document.
    """

    def __init__(self):
        # A dictionary mapping prefixes to their validation methods and resource types
        self.prefix_map = {
            'elet-': (self.validate_project, "Project"),
            'ds_': (self.validate_bigquery_dataset, "BigQuery Dataset"),
            'tb_': (self.validate_bigquery_table, "BigQuery Table (Generic)"),
            'dm_': (self.validate_bigquery_table, "BigQuery Table (Dimension)"),
            'ft_': (self.validate_bigquery_table, "BigQuery Table (Fact)"),
            'vw_': (self.validate_bigquery_view, "BigQuery View"),
            'cs_': (self.validate_cloud_storage_bucket, "Cloud Storage Bucket"),
            'fd_': (self.validate_cloud_storage_folder, "Cloud Storage Folder"),
            'cf_': (self.validate_cloud_function, "Cloud Function"),
            'cr_': (self.validate_cloud_run, "Cloud Run"),
            'df_': (self.validate_dataform_repository, "Dataform Repository"),
            'ws_': (self.validate_dataform_workspace, "Dataform Workspace"),
            'cc_': (self.validate_cloud_composer, "Cloud Composer"),
            'dc_': (self.validate_data_catalog, "Data Catalog / Dataplex"),
            'wf_': (self.validate_cloud_workflow, "Cloud Workflow"),
            'ps_': (self.validate_pubsub, "Pub/Sub Topic/Subscription"),
            'sql_': (self.validate_cloud_sql, "Cloud SQL Instance"),
            'sch_': (self.validate_cloud_scheduler, "Cloud Scheduler Job"),
            'fs_': (self.validate_firestore, "Cloud Firestore Collection"),
            'bt_': (self.validate_bigtable, "Cloud Bigtable Table"),
            'lb_': (self.validate_load_balancer, "Load Balancer"),
            'int_': (self.validate_interconnect, "Cloud Interconnect"),
            'log_': (self.validate_logging, "Cloud Logging"),
            'mon_': (self.validate_monitoring, "Cloud Monitoring"),
            'nb_': (self.validate_ai_notebook, "AI Notebook"),
            'ml_': (self.validate_ai_model, "AI Model"),
            'ais_': (self.validate_ai_service, "AI Service"),
            'tag_': (self.validate_iam_tag, "IAM Tag"),
            'pol_tag_': (self.validate_policy_tag, "IAM Policy Tag"),
            'sa-': (self.validate_service_account, "Service Account"),
        }
        # Prefixes for BigQuery columns
        self.column_prefixes = [
            "id_", "cd_", "dt_", "dh_", "tm_", "nm_", "sg_", "nr_", "ds_",
            "fl_", "vl_", "qn_", "st_", "pr_", "tp", "tx", "bl_", "cr_"
        ]

    def validate(self, resource_name):
        """
        Dynamically selects the correct validation method based on the resource name's prefix.
        """
        # Special check for columns as they don't have a globally unique prefix
        if self._is_column_name(resource_name):
            return self.validate_bigquery_column(resource_name)

        for prefix, (validator_func, resource_type) in self.prefix_map.items():
            if resource_name.startswith(prefix):
                is_valid, message = validator_func(resource_name)
                return is_valid, f"[{resource_type}] {message}"

        return False, "Unknown resource type. The name does not match any known GCP resource prefix from the Eletrobras taxonomy document."

    def _is_column_name(self, name):
        """
        Heuristically determines if a name is a column name.
        It's a column if it starts with a column prefix and does not match any other resource prefix.
        """
        return any(name.startswith(p) for p in self.column_prefixes) and not any(name.startswith(p) for p in self.prefix_map.keys())


    # --- Validation Methods per GCP Service ---

    def validate_project(self, name):
        # Pattern: elet-<núcleo>-<ambiente>
        # Example: elet-comercializacao-dev
        pattern = r"^elet-([a-z0-9\-]+)-(prd|qld|dev)$"
        if re.match(pattern, name):
            return True, "Valid Project name."
        return False, "Invalid Project name. Expected format: elet-<núcleo>-<ambiente>"

    def validate_bigquery_dataset(self, name):
        # Pattern: ds_elet_<núcleo>_<camada>_<domínio>
        # Or: ds_elet_stg_<fonte_de_dados>
        # Or: ds_elet_<núcleo>_governance
        # Examples: ds_elet_comercializacao_raw_marketing, ds_elet_stg_sap
        pattern_nucleo = r"^ds_elet_[a-z0-9_]+_(raw|trusted|refined)_[a-z0-9_]+$"
        pattern_staging = r"^ds_elet_stg_[a-z0-9_]+$"
        pattern_governance = r"^ds_elet_[a-z0-9_]+_governance$"

        if re.match(pattern_nucleo, name) or re.match(pattern_staging, name) or re.match(pattern_governance, name):
            return True, "Valid BigQuery Dataset name."
        return False, "Invalid BigQuery Dataset name. Expected format: ds_elet_<núcleo>_<camada>_<domínio> OR ds_elet_stg_<fonte> OR ds_elet_<núcleo>_governance"

    def validate_bigquery_table(self, name):
        # Pattern: <tb|dm|ft>_<núcleo>_<camada>_<domínio>_<nome_da_tabela>
        # Example: tb_comercializacao_raw_marketing_pld
        pattern = r"^(tb|dm|ft)_[a-z0-9_]+_(raw|trusted|refined|governance)_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid BigQuery Table/Dimension/Fact name."
        return False, "Invalid BigQuery Table name. Expected format: <tb|dm|ft>_<núcleo>_<camada>_<domínio>_<nome>"

    def validate_bigquery_view(self, name):
        # Pattern: vw_<nome_da_view>
        # Example: vw_clientes_ativos
        pattern = r"^vw_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid BigQuery View name."
        return False, "Invalid BigQuery View name. Expected format: vw_<nome_da_view>"

    def validate_bigquery_column(self, name):
        # Pattern: <prefixo>_<nome>
        # Example: dt_nascimento, cd_cadastro
        if not any(name.startswith(p) for p in self.column_prefixes):
            return False, f"Invalid Column name. Must start with one of the standard prefixes: {self.column_prefixes}"

        if not re.match(r"^[a-z0-9_]{6,70}$", name):
             return False, "Invalid Column name. Must be between 6 and 70 characters, lowercase, numbers, and underscores only."

        # Check for redundant information
        prefix = name.split('_')[0] + '_'
        if len(name.split('_')) > 1:
            rest_of_name = name[len(prefix):]
            if prefix[:-1] in rest_of_name:
                 return False, f"Invalid Column name. Do not repeat the prefix '{prefix[:-1]}' in the name itself."

        return True, "Valid BigQuery Column name."

    def validate_cloud_storage_bucket(self, name):
        # Pattern: cs_elet_<...>
        # Example: cs_elet_comercializacao_marketing_setorial
        if not name.startswith("cs_elet_"):
            return False, "Invalid Cloud Storage Bucket name. Must start with 'cs_elet_'."
        if not re.match(r"^[a-z0-9_.-]{3,63}$", name) or name.endswith('.') or name.endswith('-'):
            return False, "Invalid Cloud Storage Bucket name. Must be 3-63 characters, lowercase, numbers, '_', '-', '.' and cannot end with a dot or dash."
        if not (name.endswith("_publico") or name.endswith("_interno") or name.endswith("_setorial") or name.endswith("_confidencial") or any(f"_{freq}" in name for freq in ["hot", "near", "cold", "arch"])):
             return False, "Invalid Cloud Storage Bucket name. Must end with a confidentiality suffix (e.g., _publico, _interno, _setorial, _confidencial) or an optional frequency suffix."
        return True, "Valid Cloud Storage Bucket name."

    def validate_cloud_storage_folder(self, name):
        # Pattern: fd_<prod. dados>
        # Example: fd_analitico
        pattern = r"^fd_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Cloud Storage Folder name."
        return False, "Invalid Cloud Storage Folder name. Expected format: fd_<produto_de_dados>"

    def validate_cloud_function(self, name):
        # Pattern: cf_elet_<núcleo>_<função_específica>
        # Example: cf_elet_comercializacao_processar_fatura
        pattern = r"^cf_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Cloud Function name."
        return False, "Invalid Cloud Function name. Expected format: cf_elet_<núcleo>_<função_específica>"

    def validate_cloud_run(self, name):
        # Pattern: cr_elet_<núcleo>_<serviço_específico>
        # Example: cr_elet_marketing_gerar_relatorio
        pattern = r"^cr_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Cloud Run service name."
        return False, "Invalid Cloud Run service name. Expected format: cr_elet_<núcleo>_<serviço_específico>"

    def validate_dataform_repository(self, name):
        # Pattern: df_elet_<núcleo>_<camada>
        # Example: df_elet_gestaodeativos_raw_telecom
        pattern = r"^df_elet_[a-z0-9_]+_(raw|trusted|refined|governance)(_[a-z0-9_]+)?$"
        if re.match(pattern, name):
            return True, "Valid Dataform Repository name."
        return False, "Invalid Dataform Repository name. Expected format: df_elet_<núcleo>_<camada>[_dominio]"

    def validate_dataform_workspace(self, name):
        # Pattern: ws_elet_<núcleo>_<camada>
        # Example: ws_elet_gestaodeativos_raw
        pattern = r"^ws_elet[a-z0-9_]+_(raw|trusted|refined|governance)$"
        if re.match(pattern, name):
            return True, "Valid Dataform Workspace name."
        return False, "Invalid Dataform Workspace name. Expected format: ws_elet<núcleo><camada>"

    def validate_cloud_composer(self, name):
        # Pattern: cc_elet_<núcleo>_<pipeline_específico>
        # Example: cc_elet_financeiro_extracao_dados
        pattern = r"^cc_elet_[a-z0-9_]+_[a-z0-9_.]+$"
        if re.match(pattern, name):
            return True, "Valid Cloud Composer environment name."
        return False, "Invalid Cloud Composer environment name. Expected format: cc_elet_<núcleo>_<pipeline_específico>"

    def validate_data_catalog(self, name):
        # Pattern: dc_elet_<núcleo>_<tipo_dado>
        # Example: dc_elet_auditoria_brutos
        pattern = r"^dc_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Data Catalog entry name."
        return False, "Invalid Data Catalog entry name. Expected format: dc_elet_<núcleo>_<tipo_dado>"

    def validate_cloud_workflow(self, name):
        # Pattern: wf_elet_<núcleo>_<workflow_específico>
        # Example: wf_elet_operacional_carga_diaria
        pattern = r"^wf_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Cloud Workflow name."
        return False, "Invalid Cloud Workflow name. Expected format: wf_elet_<núcleo>_<workflow_específico>"

    def validate_pubsub(self, name):
        # Pattern: ps_elet_<núcleo>_<tipo>
        pattern = r"^ps_elet_[a-z0-9_]+_(topic|sub)$"
        if re.match(pattern, name):
            return True, "Valid Pub/Sub name."
        return False, "Invalid Pub/Sub name. Expected format: ps_elet_<núcleo>_<topic|sub>"

    def validate_cloud_sql(self, name):
        pattern = r"^sql_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Cloud SQL name."
        return False, "Invalid Cloud SQL name. Expected format: sql_elet_<núcleo>_<descrição>"

    def validate_cloud_scheduler(self, name):
        pattern = r"^sch_elet_[a-z0-9_]+_(raw|trusted|refined|governance)_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Cloud Scheduler name."
        return False, "Invalid Cloud Scheduler name. Expected format: sch_elet_<org>_<núcleo>_<camada>_<descrição>"

    def validate_firestore(self, name):
        pattern = r"^fs_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Firestore name."
        return False, "Invalid Firestore name. Expected format: fs_elet_<org>_<núcleo>_<descrição>"

    def validate_bigtable(self, name):
        pattern = r"^bt_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Bigtable name."
        return False, "Invalid Bigtable name. Expected format: bt_elet_<org>_<núcleo>_<descrição>"

    def validate_load_balancer(self, name):
        pattern = r"^lb_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Load Balancer name."
        return False, "Invalid Load Balancer name. Expected format: lb_elet_<org>_<núcleo>_<descrição>"

    def validate_interconnect(self, name):
        pattern = r"^int_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Interconnect name."
        return False, "Invalid Interconnect name. Expected format: int_elet_<org>_<núcleo>_<descrição>"

    def validate_logging(self, name):
        pattern = r"^log_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Logging name."
        return False, "Invalid Logging name. Expected format: log_elet_<org>_<núcleo>_<descrição>"

    def validate_monitoring(self, name):
        pattern = r"^mon_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid Monitoring name."
        return False, "Invalid Monitoring name. Expected format: mon_elet_<org>_<núcleo>_<descrição>"

    def validate_ai_notebook(self, name):
        pattern = r"^nb_elet[a-z0-9_]+_[a-z0-9._]+$"
        if re.match(pattern, name):
            return True, "Valid AI Notebook name."
        return False, "Invalid AI Notebook name. Expected format: nb_elet<projeto><descrição><autor>"

    def validate_ai_model(self, name):
        pattern = r"^ml_elet[a-z0-9_]+_[a-z0-9_]+_[a-z0-9._]+$"
        if re.match(pattern, name):
            return True, "Valid AI Model name."
        return False, "Invalid AI Model name. Expected format: ml_elet<projeto><tipo_modelo><autor>"

    def validate_ai_service(self, name):
        pattern = r"^ais_elet_[a-z0-9_]+_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid AI Service name."
        return False, "Invalid AI Service name. Expected format: ais_elet <projeto> <descricao>"

    def validate_iam_tag(self, name):
        pattern = r"^tag_elet(_[a-z0-9_]+)?_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid IAM Tag name."
        return False, "Invalid IAM Tag name. Expected format: tag_elet <projeto> <descricao>"

    def validate_policy_tag(self, name):
        pattern = r"^pol_tag_elet(_[a-z0-9_]+)?_[a-z0-9_]+$"
        if re.match(pattern, name):
            return True, "Valid IAM Policy Tag name."
        return False, "Invalid IAM Policy Tag name. Expected format: pol_tag_elet <projeto> <descricao>"

    def validate_service_account(self, name):
        pattern = r"^sa-[a-z0-9-]+$"
        if re.match(pattern, name):
            return True, "Valid Service Account name."
        return False, "Invalid Service Account name. Expected format: sa-<finalidade>"


class TaxonomyChatbot:
    """
    A simple command-line chatbot to interact with the EletrobrasGCPValidator.
    """
    def __init__(self):
        self.validator = EletrobrasGCPValidator()
        self.history = []

    def start(self):
        """Starts the chatbot's main loop."""
        print("--- Eletrobras GCP Taxonomy Validator Chatbot ---")
        print("Enter a GCP resource name to validate it, or type 'help', 'history', or 'exit'.")

        while True:
            try:
                prompt = "Enter resource name: "
                user_input = input(f"\n\033[94m{prompt}\033[0m").strip().lower()

                if user_input == "exit":
                    print("\033[92mGoodbye!\033[0m")
                    break
                elif user_input == "help":
                    self.print_help()
                elif user_input == "history":
                    self.print_history()
                elif not user_input:
                    continue
                else:
                    self.history.append(user_input)
                    is_valid, message = self.validator.validate(user_input)
                    if is_valid:
                        print(f"  \033[92m✅ VALID:\033[0m {message}")
                    else:
                        print(f"  \033[91m❌ INVALID:\033[0m {message}")

            except (KeyboardInterrupt, EOFError):
                print("\n\033[92mGoodbye!\033[0m")
                break

    def print_help(self):
        """Prints a help message with examples."""
        print("\n--- Help ---")
        print("This chatbot validates GCP resource names against the Eletrobras taxonomy.")
        print("It automatically detects the resource type based on the name's prefix.")
        print("\nCommands:")
        print("  <resource_name>  - Validates the given name.")
        print("  history          - Shows your last 10 validation attempts.")
        print("  help             - Shows this help message.")
        print("  exit             - Exits the chatbot.")
        print("\nExample Usage:")
        print("  > Enter resource name: ds_elet_comercializacao_raw_marketing")
        print("  ✅ VALID: [BigQuery Dataset] Valid BigQuery Dataset name.")
        print("\n  > Enter resource name: my-bucket")
        print("  ❌ INVALID: [Cloud Storage Bucket] Unknown resource type or invalid prefix.")


    def print_history(self):
        """Prints the user's validation history."""
        print("\n--- Validation History (last 10) ---")
        if not self.history:
            print("No history yet.")
            return
        for item in self.history[-10:]:
            print(f"- {item}")


if __name__ == "__main__":
    # To run the chatbot, execute this Python script from your terminal.
    # For example: python your_script_name.py
    chatbot = TaxonomyChatbot()
    chatbot.start()