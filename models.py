# models.py - Modelos de datos para el Editor de Dungeons Dragonbane

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Optional


DIRECTIONS = ["norte", "sur", "este", "oeste", "arriba", "abajo", "especial"]
OPPOSITE = {"norte": "sur", "sur": "norte", "este": "oeste", "oeste": "este",
            "arriba": "abajo", "abajo": "arriba", "especial": "especial"}
DIR_DELTA = {
    "norte": (0, 1, 0), "sur": (0, -1, 0), "este": (1, 0, 0), "oeste": (-1, 0, 0),
    "arriba": (0, 0, 1), "abajo": (0, 0, -1), "especial": (0, 0, 0),
}


@dataclass
class Item:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    descripcion: str = ""
    estado: str = "en_room"

    def to_dict(self):
        return self.__dict__.copy()

    @staticmethod
    def from_dict(d):
        return Item(**d)


@dataclass
class Monstruo:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    descripcion: str = ""
    presente: bool = True

    def to_dict(self):
        return self.__dict__.copy()

    @staticmethod
    def from_dict(d):
        return Monstruo(**d)


@dataclass
class PNJ:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    descripcion: str = ""
    presente: bool = True
    actitud: str = "neutral"

    def to_dict(self):
        return self.__dict__.copy()

    @staticmethod
    def from_dict(d):
        return PNJ(**d)


@dataclass
class EfectoMecanismo:
    tipo: str = "ninguno"
    puntos: int = 0
    monedas: int = 0
    item_id: str = ""
    direccion: str = ""
    sentido: str = "ambos"

    def to_dict(self):
        return self.__dict__.copy()

    @staticmethod
    def from_dict(d):
        return EfectoMecanismo(**d)


@dataclass
class Mecanismo:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    descripcion: str = ""
    estado: str = "off"
    texto_on: str = ""
    texto_off: str = ""
    texto_on_a_off: str = ""
    texto_off_a_on: str = ""
    texto_destruido: str = ""
    texto_ya_destruido: str = ""
    efecto_on: EfectoMecanismo = field(default_factory=EfectoMecanismo)
    efecto_off: EfectoMecanismo = field(default_factory=EfectoMecanismo)

    def to_dict(self):
        d = self.__dict__.copy()
        d["efecto_on"] = self.efecto_on.to_dict()
        d["efecto_off"] = self.efecto_off.to_dict()
        return d

    @staticmethod
    def from_dict(d):
        d = d.copy()
        d["efecto_on"] = EfectoMecanismo.from_dict(d.get("efecto_on", {}))
        d["efecto_off"] = EfectoMecanismo.from_dict(d.get("efecto_off", {}))
        return Mecanismo(**d)


@dataclass
class Salida:
    direccion: str = ""
    room_destino_id: str = ""
    estado_hacia_destino: str = "abierta"
    estado_hacia_origen: str = "abierta"
    especial_destino_id: str = ""

    def to_dict(self):
        return self.__dict__.copy()

    @staticmethod
    def from_dict(d):
        return Salida(**d)


@dataclass
class Room:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    descripcion: str = ""
    imagen: str = ""
    x: int = 0
    y: int = 0
    z: int = 0
    items: list = field(default_factory=list)
    monstruos: list = field(default_factory=list)
    pnjs: list = field(default_factory=list)
    mecanismos: list = field(default_factory=list)
    salidas: list = field(default_factory=list)

    def to_dict(self):
        return {
            "id": self.id, "numero": self.numero, "nombre": self.nombre,
            "descripcion": self.descripcion, "imagen": self.imagen,
            "x": self.x, "y": self.y, "z": self.z,
            "items": [i.to_dict() for i in self.items],
            "monstruos": [m.to_dict() for m in self.monstruos],
            "pnjs": [p.to_dict() for p in self.pnjs],
            "mecanismos": [m.to_dict() for m in self.mecanismos],
            "salidas": [s.to_dict() for s in self.salidas],
        }

    @staticmethod
    def from_dict(d):
        d = d.copy()
        d["items"] = [Item.from_dict(i) for i in d.get("items", [])]
        d["monstruos"] = [Monstruo.from_dict(m)
                          for m in d.get("monstruos", [])]
        d["pnjs"] = [PNJ.from_dict(p) for p in d.get("pnjs", [])]
        d["mecanismos"] = [Mecanismo.from_dict(
            m) for m in d.get("mecanismos", [])]
        d["salidas"] = [Salida.from_dict(s) for s in d.get("salidas", [])]
        return Room(**d)

    def salida_en(self, direccion: str) -> Optional[Salida]:
        for s in self.salidas:
            if s.direccion == direccion:
                return s
        return None


@dataclass
class Dungeon:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    numero: int = 0
    nombre: str = ""
    fecha_creacion: str = ""
    rooms: list = field(default_factory=list)
    items_globales: list = field(default_factory=list)
    monstruos_globales: list = field(default_factory=list)
    pnjs_globales: list = field(default_factory=list)
    mecanismos_globales: list = field(default_factory=list)
    _next_room: int = 1
    _next_item: int = 1
    _next_monstruo: int = 1
    _next_pnj: int = 1
    _next_mecanismo: int = 1

    def next_room_num(self):
        n = self._next_room
        self._next_room += 1
        return n

    def next_item_num(self):
        n = self._next_item
        self._next_item += 1
        return n

    def next_monstruo_num(self):
        n = self._next_monstruo
        self._next_monstruo += 1
        return n

    def next_pnj_num(self):
        n = self._next_pnj
        self._next_pnj += 1
        return n

    def next_mecanismo_num(self):
        n = self._next_mecanismo
        self._next_mecanismo += 1
        return n

    def room_en(self, x, y, z) -> Optional[Room]:
        for r in self.rooms:
            if r.x == x and r.y == y and r.z == z:
                return r
        return None

    def room_por_id(self, rid) -> Optional[Room]:
        for r in self.rooms:
            if r.id == rid:
                return r
        return None

    def to_dict(self):
        return {
            "id": self.id, "nombre": self.nombre, "fecha_creacion": self.fecha_creacion,
            "numero": self.numero,
            "rooms": [r.to_dict() for r in self.rooms],
            "items_globales": [i.to_dict() for i in self.items_globales],
            "monstruos_globales": [m.to_dict() for m in self.monstruos_globales],
            "pnjs_globales": [p.to_dict() for p in self.pnjs_globales],
            "mecanismos_globales": [m.to_dict() for m in self.mecanismos_globales],
            "_next_room": self._next_room, "_next_item": self._next_item,
            "_next_monstruo": self._next_monstruo, "_next_pnj": self._next_pnj,
            "_next_mecanismo": self._next_mecanismo,
        }

    @staticmethod
    def from_dict(d):
        d = d.copy()
        d["rooms"] = [Room.from_dict(r) for r in d.get("rooms", [])]
        d["items_globales"] = [Item.from_dict(
            i) for i in d.get("items_globales", [])]
        d["monstruos_globales"] = [Monstruo.from_dict(
            m) for m in d.get("monstruos_globales", [])]
        d["pnjs_globales"] = [PNJ.from_dict(p)
                              for p in d.get("pnjs_globales", [])]
        d["mecanismos_globales"] = [Mecanismo.from_dict(
            m) for m in d.get("mecanismos_globales", [])]
        return Dungeon(**d)

    # Dentro de la clase Dungeon en models.py

    def validar_y_reparar_ids(self):
        """
        Recorre todo el dungeon y regenera cualquier ID que esté duplicado.
        Útil después de clonar habitaciones o importar datos.
        """
        ids_vistos = set()

        def obtener_id_unico(id_actual):
            # Si el ID ya existe, generamos uno nuevo
            if id_actual in ids_vistos or not id_actual:
                nuevo_id = str(uuid.uuid4())[:8]
                while nuevo_id in ids_vistos:
                    nuevo_id = str(uuid.uuid4())[:8]
                return nuevo_id
            return id_actual

        # 1. Revisar IDs de las habitaciones
        for r in self.rooms:
            r.id = obtener_id_unico(r.id)
            ids_vistos.add(r.id)

            # 2. Revisar elementos dentro de cada habitación
            for lista in [r.items, r.monstruos, r.pnjs, r.mecanismos]:
                for elem in lista:
                    elem.id = obtener_id_unico(elem.id)
                    ids_vistos.add(elem.id)

        # 3. Revisar listas globales del dungeon
        for lista_global in [self.items_globales, self.monstruos_globales,
                             self.pnjs_globales, self.mecanismos_globales]:
            for elem in lista_global:
                elem.id = obtener_id_unico(elem.id)
                ids_vistos.add(elem.id)
