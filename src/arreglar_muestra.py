import pandas as pd

print("--> Extrayendo muestra multianual equilibrada (FIFA 15 a 23) sin saturar RAM...")
cols = ['fifa_version', 'short_name', 'player_positions', 'overall', 'potential', 'value_eur', 'wage_eur', 'age', 'preferred_foot']

def extraer_multianual(ruta, genero, muestras_por_anio=1200):
    acumulado = []
    conteo_anios = {}
    
    # Leer por bloques de 25.000 filas para mantener bajo consumo de memoria
    for chunk in pd.read_csv(ruta, usecols=cols, chunksize=25000, low_memory=False):
        chunk['fifa_version'] = pd.to_numeric(chunk['fifa_version'], errors='coerce')
        chunk = chunk.dropna(subset=['fifa_version'])
        chunk['fifa_version'] = chunk['fifa_version'].astype(int)
        
        for anio, grupo in chunk.groupby('fifa_version'):
            if 15 <= anio <= 23:
                ya_tengo = conteo_anios.get(anio, 0)
                if ya_tengo < muestras_por_anio:
                    faltan = muestras_por_anio - ya_tengo
                    tomar = grupo.sample(n=min(faltan, len(grupo)), random_state=42).copy()
                    tomar['gender'] = genero
                    acumulado.append(tomar)
                    conteo_anios[anio] = ya_tengo + len(tomar)
                    
        # Detener lectura si ya tenemos todas las temporadas completas (15 a 23)
        if len(conteo_anios) == 9 and all(v >= muestras_por_anio for v in conteo_anios.values()):
            break
            
    return pd.concat(acumulado, ignore_index=True)

df_m = extraer_multianual('/app/data/male_players.csv', 'Male', muestras_por_anio=1200)
df_f = extraer_multianual('/app/data/female_players.csv', 'Female', muestras_por_anio=1200)

df_total = pd.concat([df_m, df_f], ignore_index=True)

# Casteo estricto
df_total['overall'] = pd.to_numeric(df_total['overall'], errors='coerce')
df_total['age'] = pd.to_numeric(df_total['age'], errors='coerce')
df_total['value_eur'] = pd.to_numeric(df_total['value_eur'], errors='coerce').fillna(0)
df_total['wage_eur'] = pd.to_numeric(df_total['wage_eur'], errors='coerce').fillna(0)

def clasificar_pos(pos):
    pos = str(pos)
    if 'GK' in pos: return 'Portero'
    if any(p in pos for p in ['CB', 'LB', 'RB', 'RWB', 'LWB']): return 'Defensa'
    if any(p in pos for p in ['CM', 'CDM', 'CAM', 'LM', 'RM']): return 'Centrocampista'
    return 'Delantero'

df_total['primary_position'] = df_total['player_positions'].apply(clasificar_pos)

df_final = df_total.dropna(subset=['overall', 'age'])
df_final = df_final[
    (df_final['overall'] >= 45) & (df_final['overall'] <= 95) &
    (df_final['age'] >= 16) & (df_final['age'] <= 42)
]

df_final.to_csv('/app/data/procesados/muestra_distribucion.csv', index=False)
print("--> ¡muestra_distribucion.csv multianual generado con éxito!")
print("Versiones incluidas:", sorted(df_final['fifa_version'].unique().tolist()))
print(f"Total registros: {len(df_final)}")