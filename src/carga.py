import os
import pandas as pd
from pymongo import MongoClient

# Configuración mediante variables de entorno (con fallback para ejecución sin .env)
MONGO_USER = os.getenv("MONGO_INITDB_ROOT_USERNAME", "admin")
MONGO_PASS = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "password123")
MONGO_HOST = os.getenv("MONGO_HOST", "mongodb")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")

MONGO_URI = os.getenv(
    "MONGO_URI",
    f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/admin?authSource=admin"
)
DB_NAME = os.getenv("MONGO_DB_NAME", "fifa_analytics_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "jugadores")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "15000"))

ARCHIVOS = [
    {"path": "/app/data/male_players.csv", "gender": "Male"},
    {"path": "/app/data/female_players.csv", "gender": "Female"}
]

COLUMNAS_SELECCIONADAS = [
    'fifa_version',
    'short_name',
    'player_positions',
    'overall',
    'potential',
    'value_eur',
    'wage_eur',
    'age',
    'club_name',
    'league_name',
    'nationality_name',
    'preferred_foot',
    'pace',
    'shooting',
    'passing',
    'dribbling',
    'defending',
    'physic'
]

def cargar_datos():
    print("--- 1. Conectando a MongoDB en Docker ---")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    collection.drop()
    print("Colección 'jugadores' reiniciada.")

    total_acumulado = 0

    for item in ARCHIVOS:
        ruta = item["path"]
        genero = item["gender"]

        if not os.path.exists(ruta):
            print(f"Advertencia: Archivo no encontrado en {ruta}")
            continue

        print(f"\nIniciando carga de {genero} desde {ruta}...")
        
        # Leer solo columnas presentes en el CSV
        cols_presentes = pd.read_csv(ruta, nrows=1).columns.tolist()
        cols_utiles = [c for c in COLUMNAS_SELECCIONADAS if c in cols_presentes]

        for i, chunk in enumerate(pd.read_csv(ruta, usecols=cols_utiles, chunksize=CHUNK_SIZE, low_memory=False)):
            chunk["gender"] = genero
            registros = chunk.to_dict(orient='records')
            if registros:
                collection.insert_many(registros)
                total_acumulado += len(registros)
                print(f"[{genero}] Lote {i+1} insertado. Total en BD: {total_acumulado}")

    print("\n--- Creando índices en MongoDB ---")
    collection.create_index("fifa_version")
    collection.create_index("gender")
    collection.create_index("overall")
    collection.create_index("league_name")

    total_final = collection.count_documents({})
    print(f"\n¡Carga completada! Total de documentos en MongoDB: {total_final}")

if __name__ == "__main__":
    cargar_datos()