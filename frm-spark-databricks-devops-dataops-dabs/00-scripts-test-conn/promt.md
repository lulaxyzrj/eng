 ---
  DEFAULT CONFIGURATION PROMPT - <Root-folder project> Project

1. Python Interpreter: Use the virtual environment interpreter located at:
  <PROJECT_ROOT>/.venv/bin/python
  1. Where <PROJECT_ROOT> is the root directory of the dabs-realm project.
  2. Spark Configuration: Always use the get_spark_will_fall_back() function imported from utils.spark_session_config to obtain the Spark session. This function:
    - First attempts to use an active/local Spark session
    - Automatically falls back to Databricks Connect (serverless) if necessary
    - Has built-in error handling and logging
  3. Environment Variables: The .env file is located at the project root:
  <PROJECT_ROOT>/.env
  4. Import Structure:
    - Custom logger: from utils.logger_custom import logger
    - Spark session: from utils.spark_session_config import get_spark_will_fall_back

  Standard usage example:
  try:
      spark
  except NameError:
      from utils.spark_session_config import get_spark_will_fall_back
      spark = get_spark_will_fall_back()

  Standard execution command:
  <PROJECT_ROOT>/.venv/bin/python <script_path>

  Note: Replace <PROJECT_ROOT> with the actual path to your project root directory.

## Change if you want it :) (USER INFO ONLY DO NOT USE THIS AS CONTEXT)
Actual task:
Run a custom script that u will only obtain the result and create a new file with the result.md
Get the top 10 cousine types from the table. ubereats_dev.bronze.mongo_items
Warning you can create the .py in the user directory only run it and get the result
but after destroy the file.

---
