import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, round, when, desc, lit

DATA_DIR = "/app/data"
OUTPUT_DIR = "/app/data/procesados"

def ejecutar_spark():
    print("--- 1. Inicializando Apache Spark con memoria optimizada ---")
    spark = SparkSession.builder \
        .appName("FIFA_BigData_Analytics") \
        .master("local[*]") \
        .config("spark.driver.memory", "4g") \
        .config("spark.executor.memory", "4g") \
        .config("spark.sql.shuffle.partitions", "10") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    print("\n--- 2. Cargando datasets distribuidos en PySpark ---")
    
    # 2.1 Cargar masculinos
    df_male_raw = spark.read.csv(f"{DATA_DIR}/male_players.csv", header=True, inferSchema=True)
    df_male = df_male_raw.select(
        col("fifa_version").cast("int"),
        lit("Male").alias("gender"),
        col("short_name").cast("string"),
        col("overall").cast("int"),
        col("potential").cast("int"),
        col("value_eur").cast("double"),
        col("wage_eur").cast("double"),
        col("age").cast("int"),
        col("player_positions").cast("string"),
        col("club_name").cast("string"),
        col("league_name").cast("string"),
        col("preferred_foot").cast("string"),
        col("pace").cast("int"),
        col("shooting").cast("int"),
        col("passing").cast("int"),
        col("dribbling").cast("int"),
        col("defending").cast("int"),
        col("physic").cast("int")
    )

    # 2.2 Cargar femeninos
    df_female_raw = spark.read.csv(f"{DATA_DIR}/female_players.csv", header=True, inferSchema=True)
    df_female = df_female_raw.select(
        col("fifa_version").cast("int"),
        lit("Female").alias("gender"),
        col("short_name").cast("string"),
        col("overall").cast("int"),
        col("potential").cast("int"),
        col("value_eur").cast("double"),
        col("wage_eur").cast("double"),
        col("age").cast("int"),
        col("player_positions").cast("string"),
        col("club_name").cast("string"),
        col("league_name").cast("string"),
        col("preferred_foot").cast("string"),
        col("pace").cast("int"),
        col("shooting").cast("int"),
        col("passing").cast("int"),
        col("dribbling").cast("int"),
        col("defending").cast("int"),
        col("physic").cast("int")
    )

    df_spark = df_male.unionByName(df_female)

    print("Limpiando nulos y estandarizando campos...")
    df_spark = df_spark.fillna({
        "value_eur": 0.0, "wage_eur": 0.0, "pace": 0, "shooting": 0,
        "passing": 0, "dribbling": 0, "defending": 0, "physic": 0
    })

    # Simplificar posición principal en el campo
    df_spark = df_spark.withColumn(
        "primary_position",
        when(col("player_positions").contains("GK"), "Portero")
        .when(col("player_positions").rlike("CB|LB|RB|RWB|LWB"), "Defensa")
        .when(col("player_positions").rlike("CM|CDM|CAM|LM|RM"), "Centrocampista")
        .otherwise("Delantero")
    )

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # -------------------------------------------------------------
    # Métrica 1: Evolución temporal por Año y Género
    # -------------------------------------------------------------
    print("\n--- 3. Procesando tendencias multianuales ---")
    df_evolucion = df_spark.groupBy("fifa_version", "gender").agg(
        count("*").alias("total_registros"),
        round(avg("overall"), 2).alias("avg_overall"),
        round(avg("value_eur"), 2).alias("avg_value_eur"),
        round(avg("wage_eur"), 2).alias("avg_wage_eur"),
        round(avg("pace"), 2).alias("avg_pace"),
        round(avg("physic"), 2).alias("avg_physic")
    ).orderBy("fifa_version", "gender")

    df_evolucion.show(15)
    df_evolucion.toPandas().to_csv(f"{OUTPUT_DIR}/evolucion_temporal.csv", index=False)

    # -------------------------------------------------------------
    # Métrica 2: Rendimiento por Edad y Posición
    # -------------------------------------------------------------
    print("\n--- 4. Calculando rendimiento físico según Edad y Posición ---")
    df_edad_pos = df_spark.groupBy("age", "primary_position", "gender").agg(
        count("*").alias("conteo"),
        round(avg("overall"), 2).alias("avg_overall"),
        round(avg("pace"), 2).alias("avg_pace"),
        round(avg("physic"), 2).alias("avg_physic")
    ).filter(col("conteo") > 100).orderBy("age")

    df_edad_pos.toPandas().to_csv(f"{OUTPUT_DIR}/rendimiento_edad_posicion.csv", index=False)

    # -------------------------------------------------------------
    # Métrica 3: Top Ligas por nivel deportivo
    # -------------------------------------------------------------
    print("\n--- 5. Agregando métricas por Ligas ---")
    df_ligas = df_spark.filter(col("league_name").isNotNull()).groupBy("league_name", "gender").agg(
        count("*").alias("total_jugadores"),
        round(avg("overall"), 2).alias("avg_overall"),
        round(avg("wage_eur"), 2).alias("avg_salario"),
        round(avg("value_eur"), 2).alias("avg_valor_mercado")
    ).filter(col("total_jugadores") >= 500).orderBy(desc("avg_overall")).limit(20)

    df_ligas.toPandas().to_csv(f"{OUTPUT_DIR}/top_ligas.csv", index=False)

    # -------------------------------------------------------------
    # Métrica 4: Muestra representativa limpia para Boxplots y Dispersión
    # -------------------------------------------------------------
    print("\n--- 6. Generando muestra filtrada para Streamlit ---")
    cols_muestra = [
        "fifa_version", "gender", "short_name", "overall", "potential",
        "value_eur", "wage_eur", "age", "primary_position", "preferred_foot",
        "pace", "shooting", "passing", "dribbling"
    ]

    # Filtrar anomalías numéricas para que 'overall' nunca sea un ID
    df_muestra = df_spark.select(cols_muestra).filter(
        (col("overall") >= 45) & (col("overall") <= 99) &
        (col("age") >= 16) & (col("age") <= 45)
    ).sample(withReplacement=False, fraction=0.03, seed=42)

    df_muestra.toPandas().to_csv(f"{OUTPUT_DIR}/muestra_distribucion.csv", index=False)

    print(f"\n¡Procesamiento con PySpark completado! Archivos guardados en {OUTPUT_DIR}")
    spark.stop()

if __name__ == "__main__":
    ejecutar_spark()