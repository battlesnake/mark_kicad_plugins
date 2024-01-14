from typing import Dict, List


Json = None | bool | int | float | str | List["Json"] | Dict[str, "Json"]
JsonArray = List[Json]
JsonObject = Dict[str, Json]
