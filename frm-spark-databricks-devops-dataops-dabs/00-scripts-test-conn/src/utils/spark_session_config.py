
from utils.logger_custom import logger
from pyspark.sql import SparkSession
from pyspark.sql import functions as F



def get_spark_will_fall_back():
    """
    Get Spark session, falling back to Databricks connect if necessary.
    """

    try:
        spark = SparkSession.getActiveSession()
        if spark is not None:
            logger.info("Using existing Spark session.")
            return spark
        
        spark = SparkSession.builder.getOrCreate()
        logger.info("Created new Spark session.")
        return spark
    except Exception as e:
        logger.warn(f"Standard Spark session retrieval failed: {str(e)}. ")
        logger.info("Attempting Databricks connect ....")

        try:
            from databricks.connect import DatabricksSession
            spark = DatabricksSession.builder.serverless().getOrCreate()
            # case not using serverless : spark = DatabricksSession.builder.connect().getOrCreate()
            logger.info("Databricks connect session created successfully.")
            return spark
        except ImportError:
            logger.error("Databricks connect not avaible. Please install databricks-connect package.")
            raise

        except Exception as e:
            logger.error(f"Databricks connect error: {str(e)}")
            raise