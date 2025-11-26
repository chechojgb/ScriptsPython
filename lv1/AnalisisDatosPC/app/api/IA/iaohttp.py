import aiohttp
from dotenv import load_dotenv
import os

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

# Diccionario ID -> Nombre
CANDIDATE_LABELS = {
    1: "Communication",
    2: "Social",
    3: "Entertainment",
    4: "Navigation",
    5: "Work/Development",
    6: "Education",
    7: "Shopping/Finance",
    8: "News",
    9: "Health/Wellness",
    10: "Productivity",
    11: "Adult",
    12: "Other"
}

# Lista de nombres para HuggingFace
LABEL_NAMES = list(CANDIDATE_LABELS.values())

async def classify_domain(domain: str) -> int:
    """
    1. Envía el dominio a HuggingFace
    2. Determina la categoría (por nombre)
    3. Devuelve el ID correspondiente a esa categoría
       (devuelve 12 = 'Other' si hay error)
    """
    url = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli"
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
    }
    payload = {
        "inputs": domain,
        "parameters": {
            "candidate_labels": LABEL_NAMES,
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                result = await response.json()

        # Ahora la API devuelve una lista de dicts, no "labels"
        if not isinstance(result, list) or len(result) == 0:
            print("HuggingFace no devolvió resultados válidos:", result)
            return 12  # Other

        # Tomar la etiqueta con mayor score
        predicted_label = result[0]["label"]
        print(f"IA detecta que '{domain}' pertenece a: {predicted_label}")

        # Buscar ID basado en nombre
        for cat_id, cat_name in CANDIDATE_LABELS.items():
            if cat_name == predicted_label:
                return cat_id

        # Si no coincide nada
        return 12  # "Other"

    except Exception as e:
        print(f"Error llamando a HuggingFace para '{domain}': {e}")
        return 12  # Other
